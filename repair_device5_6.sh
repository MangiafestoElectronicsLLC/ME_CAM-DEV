#!/usr/bin/env bash
set -e

DEVICE_NUMBER="${1:-}"
PROFILE="${2:-device4}"

if [ -z "${DEVICE_NUMBER}" ]; then
  echo "Usage: $0 <device-number> [profile]"
  exit 1
fi

echo "=================================================="
echo "ME_CAM Repair Script (Device ${DEVICE_NUMBER})"
echo "Profile: ${PROFILE}"
echo "=================================================="

recover_apt_if_needed() {
  echo "Checking APT/DPKG health..."
  if sudo dpkg --audit >/dev/null 2>&1 && sudo apt update >/dev/null 2>&1; then
    echo "APT/DPKG health check passed."
    return 0
  fi

  echo "APT/DPKG appears broken. Running recovery..."
  if [ -f /var/backups/dpkg.status.0 ]; then
    sudo cp /var/backups/dpkg.status.0 /var/lib/dpkg/status
    sudo cp /var/backups/dpkg.status.0 /var/lib/dpkg/status-old
  fi

  sudo rm -f /var/cache/apt/archives/*.deb || true
  sudo apt clean || true
  sudo rm -rf /var/lib/apt/lists/* || true

  sudo apt update --allow-releaseinfo-change
  sudo dpkg --configure -a || true
  sudo apt --fix-broken install -y || true
}

cd "$HOME"

echo "[1/8] Preparing clean repository clone..."
if [ -d "$HOME/ME_CAM-DEV" ]; then
  mv "$HOME/ME_CAM-DEV" "$HOME/ME_CAM-DEV.bak.$(date +%Y%m%d_%H%M%S)"
fi

git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd "$HOME/ME_CAM-DEV"

echo "[2/8] Installing core OS dependencies..."
recover_apt_if_needed
sudo apt update --allow-releaseinfo-change
sudo apt install --fix-missing -o Acquire::Retries=5 -y python3-pip python3-venv libcamera-apps python3-picamera2 python3-opencv python3-dev libffi-dev libjpeg-dev zlib1g-dev git

echo "[3/8] Rebuilding virtual environment..."
rm -rf venv
python3 -m venv venv --system-site-packages
./venv/bin/python -m pip install --upgrade pip setuptools wheel

echo "[4/8] Ensuring base requirements excludes optional WebRTC packages..."
cp requirements.txt "requirements.txt.bak.$(date +%Y%m%d_%H%M%S)"
sed -i '/^[[:space:]]*aiortc[<=>]/d;/^[[:space:]]*av[<=>]/d' requirements.txt

echo "[5/8] Installing Python dependencies..."
./venv/bin/pip install --no-cache-dir -r requirements.txt

echo "[6/8] Verifying Python source compiles..."
./venv/bin/python -m compileall -q main.py web/app_lite.py src

echo "[7/8] Generating config for device ${DEVICE_NUMBER}..."
./venv/bin/python scripts/generate_config.py --profile "${PROFILE}" --device-number "${DEVICE_NUMBER}" --force

echo "[8/8] Running startup smoke check..."
./venv/bin/python -c "import flask, loguru; print('Python env OK')"

echo
echo "Repair complete for Device ${DEVICE_NUMBER}."
echo "Next steps:"
echo "  ./venv/bin/python main.py"
echo "  sudo systemctl restart mecamera"
