#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Path-Dependent Preferences — GCP bootstrap
#
# Creates/reuses a GCP project, provisions networking + GPU quota, finds an
# available G2/L4 VM, installs the NVIDIA driver, reboots if necessary, clones
# the repo, and runs setup_vm.sh.
#
# Required for a NEW project:
#   export BILLING_ACCOUNT="XXXXXX-XXXXXX-XXXXXX"
#
# Optional:
#   export PROJECT_ID="my-project-id"
#
# Re-running this script reuses the project recorded in .gcp-project.
# =============================================================================

PROJECT_NAME="Path Dependent Preferences"
REPO_URL="https://github.com/walmsley-lab/path-dependent-preferences.git"

NETWORK="research-net"
VM_NAME="pdp-gpu"
MACHINE_TYPE="g2-standard-4"
DISK_SIZE="100GB"

PROJECT_FILE=".gcp-project"
ZONE_FILE=".gcp-zone"

# Candidate zones. g2-standard-4 includes one NVIDIA L4.
CANDIDATE_ZONES=(
  "us-west1-a"
  "us-west1-b"
  "us-west1-c"
  "us-east1-b"
  "us-east1-c"
  "us-east1-d"
  "us-central1-a"
  "us-central1-b"
  "us-central1-c"
)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

log() {
  printf '\n==> %s\n' "$*"
}

die() {
  printf '\nERROR: %s\n' "$*" >&2
  exit 1
}

command -v gcloud >/dev/null 2>&1 ||
  die "gcloud is required. Install the Google Cloud CLI first."

# -----------------------------------------------------------------------------
# Project selection
# -----------------------------------------------------------------------------

if [[ -z "${PROJECT_ID:-}" && -f "$PROJECT_FILE" ]]; then
  PROJECT_ID="$(cat "$PROJECT_FILE")"
fi

if [[ -z "${PROJECT_ID:-}" ]]; then
  # Short, globally unique-ish, and safely under GCP's 30-character limit.
  PROJECT_ID="pdp-$(date +%y%m%d)-$(openssl rand -hex 3)"
fi

echo "$PROJECT_ID" > "$PROJECT_FILE"

log "Using project: $PROJECT_ID"

# Create project only if it does not already exist.
if ! gcloud projects describe "$PROJECT_ID" >/dev/null 2>&1; then
  log "Creating project"
  gcloud projects create "$PROJECT_ID" \
    --name="$PROJECT_NAME"
else
  log "Project already exists"
fi

gcloud config set project "$PROJECT_ID" >/dev/null

# -----------------------------------------------------------------------------
# Billing
# -----------------------------------------------------------------------------

BILLING_ENABLED="$(
  gcloud billing projects describe "$PROJECT_ID" \
    --format="value(billingEnabled)" 2>/dev/null || true
)"

if [[ "$BILLING_ENABLED" != "True" && "$BILLING_ENABLED" != "true" ]]; then
  [[ -n "${BILLING_ACCOUNT:-}" ]] ||
    die "Billing is not enabled. Set BILLING_ACCOUNT and rerun."

  log "Linking billing account"
  gcloud billing projects link "$PROJECT_ID" \
    --billing-account="$BILLING_ACCOUNT"
else
  log "Billing already enabled"
fi

# ADC quota project is helpful for client libraries but not required for the
# Compute Engine CLI. Do not fail bootstrap if ADC is not configured.
gcloud auth application-default set-quota-project "$PROJECT_ID" \
  >/dev/null 2>&1 || true

# -----------------------------------------------------------------------------
# APIs
# -----------------------------------------------------------------------------

log "Enabling required APIs"
gcloud services enable \
  compute.googleapis.com \
  serviceusage.googleapis.com \
  cloudresourcemanager.googleapis.com \
  cloudquotas.googleapis.com \
  --project="$PROJECT_ID"

# -----------------------------------------------------------------------------
# Network
# -----------------------------------------------------------------------------

if ! gcloud compute networks describe "$NETWORK" \
  --project="$PROJECT_ID" >/dev/null 2>&1; then

  log "Creating VPC: $NETWORK"
  gcloud compute networks create "$NETWORK" \
    --project="$PROJECT_ID" \
    --subnet-mode=custom
else
  log "VPC already exists"
fi

if ! gcloud compute firewall-rules describe allow-ssh \
  --project="$PROJECT_ID" >/dev/null 2>&1; then

  log "Creating SSH firewall rule"
  gcloud compute firewall-rules create allow-ssh \
    --project="$PROJECT_ID" \
    --network="$NETWORK" \
    --allow=tcp:22
else
  log "SSH firewall rule already exists"
fi

# -----------------------------------------------------------------------------
# Global GPU quota
# -----------------------------------------------------------------------------

log "Checking global GPU quota"

if gcloud beta quotas info describe GPUS-ALL-REGIONS-per-project \
  --service=compute.googleapis.com \
  --project="$PROJECT_ID" \
  --billing-project="$PROJECT_ID" >/dev/null 2>&1; then

  if ! gcloud beta quotas preferences describe pdp-global-gpu \
    --project="$PROJECT_ID" \
    --billing-project="$PROJECT_ID" >/dev/null 2>&1; then

    GCLOUD_EMAIL="$(gcloud config get-value account)"

    log "Requesting global GPU quota = 1"
    gcloud beta quotas preferences create \
      --project="$PROJECT_ID" \
      --billing-project="$PROJECT_ID" \
      --service=compute.googleapis.com \
      --quota-id=GPUS-ALL-REGIONS-per-project \
      --preferred-value=1 \
      --email="$GCLOUD_EMAIL" \
      --justification="One GPU for reproducible academic ML research experiments." \
      --preference-id=pdp-global-gpu
  else
    log "GPU quota preference already exists"
  fi

  # Wait until quota is reconciled or clearly not granted.
  QUOTA_GRANTED="0"

  for _ in $(seq 1 60); do
    QUOTA_GRANTED="$(
      gcloud beta quotas preferences describe pdp-global-gpu \
        --project="$PROJECT_ID" \
        --billing-project="$PROJECT_ID" \
        --format="value(quotaConfig.grantedValue)" 2>/dev/null || echo 0
    )"

    if [[ "$QUOTA_GRANTED" != "0" && -n "$QUOTA_GRANTED" ]]; then
      break
    fi

    sleep 2
  done

  if [[ "$QUOTA_GRANTED" == "0" || -z "$QUOTA_GRANTED" ]]; then
    die "Global GPU quota is still 0. Inspect:
gcloud beta quotas preferences describe pdp-global-gpu \
  --project=$PROJECT_ID \
  --billing-project=$PROJECT_ID"
  fi

  log "Global GPU quota granted: $QUOTA_GRANTED"
fi

# -----------------------------------------------------------------------------
# Driver startup script
#
# Metadata startup scripts run on every boot. On the first boot this installs
# the driver and reboots. On the next boot nvidia-smi succeeds and it exits.
# -----------------------------------------------------------------------------

cat > /tmp/pdp-driver-startup.sh <<'STARTUP'
#!/usr/bin/env bash
set -euo pipefail

exec > >(tee -a /var/log/pdp-driver-startup.log | logger -t pdp-driver) 2>&1

echo "PDP GPU driver bootstrap starting."

if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
  echo "NVIDIA driver already operational."
  exit 0
fi

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y \
  nvidia-driver-580 \
  git \
  curl \
  tmux \
  htop \
  build-essential \
  python3 \
  python3-pip \
  python3.12-venv

mkdir -p /var/lib/pdp-bootstrap

if [[ ! -f /var/lib/pdp-bootstrap/driver-reboot-requested ]]; then
  touch /var/lib/pdp-bootstrap/driver-reboot-requested
  echo "Driver installed. Rebooting once."
  shutdown -r now
fi
STARTUP

# -----------------------------------------------------------------------------
# Subnet helper
# -----------------------------------------------------------------------------

ensure_subnet() {
  local region="$1"
  local subnet="research-subnet-${region}"
  local cidr

  case "$region" in
    us-central1) cidr="10.10.0.0/24" ;;
    us-west1)    cidr="10.20.0.0/24" ;;
    us-east1)    cidr="10.30.0.0/24" ;;
    *)
      die "No subnet CIDR configured for region $region"
      ;;
  esac

  if ! gcloud compute networks subnets describe "$subnet" \
    --project="$PROJECT_ID" \
    --region="$region" >/dev/null 2>&1; then

    log "Creating subnet $subnet in $region"

    gcloud compute networks subnets create "$subnet" \
      --project="$PROJECT_ID" \
      --network="$NETWORK" \
      --region="$region" \
      --range="$cidr"
  fi

  echo "$subnet"
}

# -----------------------------------------------------------------------------
# Reuse existing VM if present
# -----------------------------------------------------------------------------

SELECTED_ZONE=""

if [[ -f "$ZONE_FILE" ]]; then
  CACHED_ZONE="$(cat "$ZONE_FILE")"

  if gcloud compute instances describe "$VM_NAME" \
    --project="$PROJECT_ID" \
    --zone="$CACHED_ZONE" >/dev/null 2>&1; then

    SELECTED_ZONE="$CACHED_ZONE"
    log "Reusing existing VM in $SELECTED_ZONE"
  fi
fi

# -----------------------------------------------------------------------------
# Find G2/L4 capacity
# -----------------------------------------------------------------------------

if [[ -z "$SELECTED_ZONE" ]]; then
  for ZONE in "${CANDIDATE_ZONES[@]}"; do
    REGION="${ZONE%-*}"

    log "Trying $MACHINE_TYPE (NVIDIA L4) in $ZONE"

    if ! gcloud compute machine-types describe "$MACHINE_TYPE" \
      --project="$PROJECT_ID" \
      --zone="$ZONE" >/dev/null 2>&1; then

      echo "$MACHINE_TYPE is not supported in $ZONE; skipping."
      continue
    fi

    SUBNET="$(ensure_subnet "$REGION")"

    set +e
    CREATE_OUTPUT="$(
      gcloud compute instances create "$VM_NAME" \
        --project="$PROJECT_ID" \
        --zone="$ZONE" \
        --machine-type="$MACHINE_TYPE" \
        --network="$NETWORK" \
        --subnet="$SUBNET" \
        --maintenance-policy=TERMINATE \
        --restart-on-failure \
        --image-family=ubuntu-2404-lts-amd64 \
        --image-project=ubuntu-os-cloud \
        --boot-disk-size="$DISK_SIZE" \
        --boot-disk-type=pd-balanced \
        --metadata-from-file=startup-script=/tmp/pdp-driver-startup.sh \
        2>&1
    )"
    STATUS=$?
    set -e

    if [[ $STATUS -eq 0 ]]; then
      echo "$CREATE_OUTPUT"
      SELECTED_ZONE="$ZONE"
      echo "$ZONE" > "$ZONE_FILE"
      break
    fi

    echo "$CREATE_OUTPUT"

    if grep -q "ZONE_RESOURCE_POOL_EXHAUSTED" <<< "$CREATE_OUTPUT"; then
      echo "No capacity in $ZONE; trying next zone."
      continue
    fi

    if grep -q "quota" <<< "$(tr '[:upper:]' '[:lower:]' <<< "$CREATE_OUTPUT")"; then
      echo
      echo "GPU quota prevented creation in $ZONE."
      echo "Inspect Compute Engine quota for the relevant GPU family/region."
      continue
    fi

    echo "Creation failed in $ZONE for an unexpected reason; trying next zone."
  done
fi

[[ -n "$SELECTED_ZONE" ]] ||
  die "Could not create a G2/L4 VM in any configured candidate zone."

# -----------------------------------------------------------------------------
# Wait for driver to survive first reboot
# -----------------------------------------------------------------------------

log "VM exists in $SELECTED_ZONE"
log "Waiting for SSH + NVIDIA driver readiness"

DRIVER_READY="false"

for _ in $(seq 1 120); do
  if gcloud compute ssh "$VM_NAME" \
    --project="$PROJECT_ID" \
    --zone="$SELECTED_ZONE" \
    --quiet \
    --command="nvidia-smi >/dev/null 2>&1" \
    >/dev/null 2>&1; then

    DRIVER_READY="true"
    break
  fi

  sleep 5
done

if [[ "$DRIVER_READY" != "true" ]]; then
  echo
  echo "VM is running, but automatic NVIDIA verification did not complete."
  echo "Inspect:"
  echo "  gcloud compute ssh $VM_NAME --project=$PROJECT_ID --zone=$SELECTED_ZONE"
  echo "  sudo cat /var/log/pdp-driver-startup.log"
  echo "  nvidia-smi"
  exit 1
fi

log "NVIDIA driver operational"

# -----------------------------------------------------------------------------
# Clone/update repo and configure experiment environment as SSH user
# -----------------------------------------------------------------------------

log "Cloning/updating repository on VM"

gcloud compute ssh "$VM_NAME" \
  --project="$PROJECT_ID" \
  --zone="$SELECTED_ZONE" \
  --command="
    set -e

    if [ ! -d ~/path-dependent-preferences/.git ]; then
      git clone '$REPO_URL' ~/path-dependent-preferences
    else
      git -C ~/path-dependent-preferences pull --ff-only
    fi

    cd ~/path-dependent-preferences
    bash setup_vm.sh
  "

# -----------------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------------

echo
echo "============================================================"
echo "PDP GCP ENVIRONMENT READY"
echo "============================================================"
echo "Project: $PROJECT_ID"
echo "VM:      $VM_NAME"
echo "Zone:    $SELECTED_ZONE"
echo
echo "SSH:"
echo "  gcloud compute ssh $VM_NAME --project=$PROJECT_ID --zone=$SELECTED_ZONE"
echo
echo "Run balance gate:"
echo "  cd ~/path-dependent-preferences"
echo "  source .venv/bin/activate"
echo "  tmux new -s pdp"
echo "  python run_batch.py --stage gate --parallel 1 --gpus 0 2>&1 | tee gate.log"
echo
echo "GPU monitor:"
echo "  watch -n 2 nvidia-smi"
echo
echo "Persistent local state:"
echo "  $PROJECT_FILE"
echo "  $ZONE_FILE"
echo "============================================================"