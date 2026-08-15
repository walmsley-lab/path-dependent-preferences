#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="pdp-sprint-$(date +%s)"
PROJECT_NAME="Path Dependent Preferences"

BILLING_ACCOUNT="${BILLING_ACCOUNT:?Set BILLING_ACCOUNT first}"

ZONE="${ZONE:-us-central1-a}"
REGION="${ZONE%-*}"

NETWORK="research-net"
SUBNET="research-subnet"
VM_NAME="pdp-gpu"

GPU_TYPE="${GPU_TYPE:-nvidia-tesla-t4}"
GPU_COUNT="${GPU_COUNT:-1}"
MACHINE_TYPE="${MACHINE_TYPE:-n1-standard-8}"
DISK_SIZE="${DISK_SIZE:-100GB}"

echo "Creating project: $PROJECT_ID"

gcloud projects create "$PROJECT_ID" \
  --name="$PROJECT_NAME"

gcloud billing projects link "$PROJECT_ID" \
  --billing-account="$BILLING_ACCOUNT"

gcloud config set project "$PROJECT_ID"

gcloud services enable \
  compute.googleapis.com \
  serviceusage.googleapis.com \
  cloudresourcemanager.googleapis.com

gcloud compute networks create "$NETWORK" \
  --subnet-mode=custom

gcloud compute networks subnets create "$SUBNET" \
  --network="$NETWORK" \
  --region="$REGION" \
  --range=10.10.0.0/24

gcloud compute firewall-rules create allow-ssh \
  --network="$NETWORK" \
  --allow=tcp:22

echo
echo "Checking GPU availability in $ZONE..."
gcloud compute accelerator-types list \
  --filter="zone:($ZONE) AND name=$GPU_TYPE"

cat > /tmp/pdp-startup.sh <<'STARTUP'
#!/bin/bash
set -euxo pipefail

apt-get update
apt-get install -y \
  git \
  python3 \
  python3-pip \
  python3-venv \
  build-essential \
  tmux \
  htop \
  curl

mkdir -p /opt/google/cuda-installer
cd /opt/google/cuda-installer

curl -fSsL \
  https://storage.googleapis.com/compute-gpu-installation-us/installer/latest/cuda_installer.pyz \
  -o cuda_installer.pyz

python3 cuda_installer.pyz install_driver || true

cd /opt
git clone https://github.com/walmsley-lab/path-dependent-preferences.git || true
STARTUP

gcloud compute instances create "$VM_NAME" \
  --zone="$ZONE" \
  --machine-type="$MACHINE_TYPE" \
  --accelerator="type=$GPU_TYPE,count=$GPU_COUNT" \
  --maintenance-policy=TERMINATE \
  --restart-on-failure \
  --network="$NETWORK" \
  --subnet="$SUBNET" \
  --image-family=ubuntu-2404-lts-amd64 \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size="$DISK_SIZE" \
  --boot-disk-type=pd-balanced \
  --metadata-from-file=startup-script=/tmp/pdp-startup.sh

echo
echo "Project: $PROJECT_ID"
echo "VM:      $VM_NAME"
echo "Zone:    $ZONE"
echo
echo "SSH:"
echo "gcloud compute ssh $VM_NAME --zone=$ZONE"
