#!/bin/bash
# Fix OpenCV Installation on Pi Zero 2W
# Use system packages instead of compiling from source

IP="${1:-10.2.1.47}"
USER="${2:-pi}"

echo "[1/3] Killing stuck pip processes..."
ssh $USER@$IP 'sudo pkill -9 -f pip; sudo pkill -9 -f python' || true

echo "[2/3] Installing system OpenCV packages (pre-built)..."
ssh $USER@$IP 'sudo apt update && sudo apt install -y python3-opencv python3-numpy python3-pil libatlas-base-dev'

echo "[3/3] Installing remaining Python packages..."
ssh $USER@$IP 'cd ~/ME_CAM-DEV && pip3 install Flask==2.2.5 Werkzeug==2.2.3 psutil==5.9.5 qrcode cryptography yagmail --no-deps'

echo ""
echo "[OK] Fixed! System OpenCV installed"
echo "Now restart the service:"
echo "  ssh $USER@$IP 'sudo systemctl restart mecamera'"
