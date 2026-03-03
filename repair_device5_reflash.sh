#!/usr/bin/env bash
set -euo pipefail

echo "[1/9] Repairing dpkg status (NUL-byte corruption guard)"
if python3 - <<'PY'
from pathlib import Path
b = Path('/var/lib/dpkg/status').read_bytes()
print('nul_bytes', b.count(b'\x00'))
raise SystemExit(0 if b.count(b'\x00') else 1)
PY
then
  echo "[INFO] Restoring /var/lib/dpkg/status from backup"
  sudo cp /var/backups/dpkg.status.0 /var/lib/dpkg/status
  sudo cp /var/backups/dpkg.status.0 /var/lib/dpkg/status-old
fi

echo "[2/9] Cleaning apt cache/lists"
sudo rm -f /var/cache/apt/archives/*.deb || true
sudo apt clean || true
sudo rm -rf /var/lib/apt/lists/* || true

echo "[3/9] Restoring apt/dpkg health"
sudo apt update --allow-releaseinfo-change
sudo dpkg --configure -a || true
sudo apt --fix-broken install -y || true

echo "[4/9] Installing core packages"
sudo apt install --fix-missing -o Acquire::Retries=5 -y \
  git python3-pip python3-venv libcamera-apps python3-picamera2 \
  python3-opencv python3-dev libffi-dev libjpeg-dev zlib1g-dev

echo "[5/9] Getting ME_CAM source"
cd /home/pi
rm -rf ME_CAM-DEV ME_CAM-DEV-main mecamdev-main.tar.gz
curl -L https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV/archive/refs/heads/main.tar.gz -o mecamdev-main.tar.gz
tar -xzf mecamdev-main.tar.gz
mv ME_CAM-DEV-main ME_CAM-DEV

cd /home/pi/ME_CAM-DEV

echo "[6/9] Building virtualenv + Python deps"
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "[7/9] Generating config for Device 5"
python3 scripts/generate_config.py --profile device4 --device-number 5 --force \
  || python3 scripts/generate_config.py --profile device3 --device-number 5 --force

echo "[8/9] Setting camera profile to switch-safe auto-detect"
sudo python3 scripts/set_camera_profile.py --profile auto || true

echo "[9/9] Installing and starting service"
sudo tee /etc/systemd/system/mecamera.service > /dev/null <<'EOF'
[Unit]
Description=ME_CAM Security Camera
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ME_CAM-DEV
Environment=PATH=/home/pi/ME_CAM-DEV/venv/bin:/usr/bin:/bin
ExecStart=/home/pi/ME_CAM-DEV/venv/bin/python3 /home/pi/ME_CAM-DEV/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable mecamera
sudo systemctl restart mecamera
sleep 8

echo "----- SERVICE STATUS -----"
sudo systemctl status mecamera --no-pager -n 25 || true

echo "----- API CHECKS -----"
curl -s -m 8 http://localhost:8080/api/battery || true
echo
curl -s -m 8 http://localhost:8080/ | head -c 120 || true
echo

echo "[DONE] Device 5 bootstrap attempted. If camera still blank, run: rpicam-hello --list-cameras"
