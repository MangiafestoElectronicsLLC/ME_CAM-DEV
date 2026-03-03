param(
    [string]$Device5Host = "10.2.1.6",
    [string]$Device6Host = "mecamdev6.local",
    [string]$User = "pi"
)

$ErrorActionPreference = "Stop"

$remoteCmd = @'
set -e
cd ~
rm -rf ME_CAM-DEV
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV

sudo apt update
sudo apt install -y python3-pip python3-venv libcamera-apps python3-picamera2 python3-opencv python3-dev libffi-dev libjpeg-dev zlib1g-dev git python3-flask python3-flask-cors python3-loguru python3-cryptography python3-psutil python3-qrcode

rm -rf venv
python3 -m venv venv --system-site-packages
./venv/bin/python -m pip install --upgrade pip

sed -i '/^[[:space:]]*aiortc[<=>]/d;/^[[:space:]]*av[<=>]/d' requirements.txt

./venv/bin/pip install --no-cache-dir --retries 10 --timeout 120 -r requirements.txt || true

if [ -f scripts/generate_config.py ]; then
  ./venv/bin/python scripts/generate_config.py --profile device4 --force
fi

./venv/bin/python -m compileall -q main.py web/app_lite.py src

sudo systemctl restart mecamera || true
sudo systemctl enable mecamera || true

timeout 25 ./venv/bin/python main.py >/tmp/mecam_main_smoke.log 2>&1 || true
echo "===== smoke log tail ====="
tail -n 40 /tmp/mecam_main_smoke.log || true
echo "===== service status ====="
sudo systemctl status mecamera --no-pager -n 30 || true
'@

function Invoke-Repair([string]$host, [string]$deviceNum) {
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "Fixing Device $deviceNum on $host" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
  $remoteCmd | ssh "$User@$host" "bash -s"
}

Invoke-Repair -host $Device5Host -deviceNum "5"
Invoke-Repair -host $Device6Host -deviceNum "6"

Write-Host "Done. Both devices processed." -ForegroundColor Green
