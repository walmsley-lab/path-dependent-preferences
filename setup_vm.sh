#!/usr/bin/env bash
set -euo pipefail

# Set up the Python environment on an Ubuntu NVIDIA GPU machine.
#
# Assumes the NVIDIA driver is already installed and nvidia-smi works.
# GCP-specific provisioning and driver installation belong in bootstrap_gcp.sh.

cd "$(dirname "${BASH_SOURCE[0]}")"

echo "==> Checking NVIDIA GPU"

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "ERROR: nvidia-smi not found."
  echo "Install the NVIDIA driver first, then rerun this script."
  exit 1
fi

nvidia-smi

echo
echo "==> Installing system dependencies"

sudo apt-get update
sudo apt-get install -y \
  python3 \
  python3-pip \
  python3.12-venv \
  build-essential \
  git \
  tmux \
  htop

echo
echo "==> Creating Python environment"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

source .venv/bin/activate

python -m pip install --upgrade pip

echo
echo "==> Installing CUDA-enabled PyTorch"

python -m pip install \
  torch==2.12.0 \
  --index-url https://download.pytorch.org/whl/cu130

echo
echo "==> Installing project dependencies"

python -m pip install -r requirements.txt

echo
echo "==> Verifying CUDA"

python - <<'PY'
import torch

print("torch:", torch.__version__)
print("CUDA runtime:", torch.version.cuda)
print("CUDA available:", torch.cuda.is_available())

if not torch.cuda.is_available():
    raise SystemExit("ERROR: PyTorch cannot access CUDA")

print("GPU:", torch.cuda.get_device_name(0))
print(
    "VRAM GB:",
    round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2),
)
PY

echo
echo "==> Running invariant tests"

python test_generator.py

echo
echo "======================================"
echo "Environment ready."
echo
echo "Activate later with:"
echo "  source .venv/bin/activate"
echo
echo "Run balance gate:"
echo "  python run_batch.py --stage gate --parallel 1 --gpus 0"
echo "======================================"