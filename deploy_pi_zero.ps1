# ME_CAM-DEV Pi Zero Deployment Script (PowerShell)
# Usage: .\deploy_pi_zero.ps1 -IP "10.2.1.47" -Username "pi"

param(
    [string]$IP = "10.2.1.47",
    [string]$Username = "pi"
)

$PI = "$Username@$IP"

function RunSSH {
    param(
        [string]$Command,
        [string]$Description
    )
    Write-Host "[*] $Description..." -ForegroundColor Cyan
    try {
        ssh $PI $Command
        Write-Host "[OK] Done" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] $_" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "ME_CAM-DEV Deployment to Pi Zero" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Target: $PI`n" -ForegroundColor Cyan

# Step 1: Clean
RunSSH @"
sudo systemctl stop mecamera 2>/dev/null || true
sudo systemctl disable mecamera 2>/dev/null || true
sudo rm -f /etc/systemd/system/mecamera.service
sudo systemctl daemon-reload
rm -rf ~/ME_CAM-DEV
rm -rf ~/.cache/pip
sudo apt autoremove -y > /dev/null 2>&1
sudo apt clean > /dev/null 2>&1
"@ "[1/8] Cleaning old installation"

# Step 2: Clone
RunSSH @"
cd ~
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV
"@ "[2/8] Cloning repository"

# Step 3: Virtual Environment
RunSSH @"
cd ~/ME_CAM-DEV
python3 -m venv venv
"@ "[3/8] Creating virtual environment"

# Step 4: Dependencies
Write-Host "[*] [4/8] Installing dependencies (5-10 minutes)..." -ForegroundColor Cyan
ssh $PI @"
cd ~/ME_CAM-DEV
source venv/bin/activate
pip install --upgrade pip setuptools wheel 2>&1 | tail -5
pip install -r requirements.txt 2>&1 | tail -10

if pip list | grep -q 'numpy 2'; then
    echo '[*] Found NumPy 2.x, downgrading...'
    pip install 'numpy<2' > /dev/null 2>&1
    pip uninstall opencv-python opencv-python-headless opencv-contrib-python -y > /dev/null 2>&1
    pip install opencv-python-headless 2>&1 | tail -5
fi
"@
Write-Host "[OK] Done" -ForegroundColor Green

# Step 5: Setup script
RunSSH @"
cd ~/ME_CAM-DEV
chmod +x setup.sh
./setup.sh
"@ "[5/8] Running setup script"

# Step 6: Service
RunSSH @"
cd ~/ME_CAM-DEV
sudo cp etc/systemd/system/mecamera.service /etc/systemd/system/
sudo systemctl daemon-reload
"@ "[6/8] Installing systemd service"

# Step 7: Start service
RunSSH @"
sudo systemctl enable mecamera
sudo systemctl start mecamera
sleep 2
sudo systemctl status mecamera --no-pager
"@ "[7/8] Starting ME_CAM service"

# Step 8: Verify
Write-Host "[*] [8/8] Verifying deployment..." -ForegroundColor Cyan
ssh $PI @"
echo ''
echo '[*] Service Status:'
sudo systemctl is-active mecamera >/dev/null 2>&1 && echo '    [OK] Service running' || echo '    [ERROR] Service not running'

echo ''
echo '[*] Directory Check:'
test -d ~/ME_CAM-DEV && echo '    [OK] Code cloned' || echo '    [ERROR] Code missing'

echo ''
echo '[*] Access Dashboard at:'
IP=`hostname -I | awk '{print `$1`}'`
echo '    http://'`$IP':8080'
echo '    http://raspberrypi.local:8080'
"@

Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Yellow
Write-Host @"

NEXT STEPS:
  1. Open http://raspberrypi.local:8080 in browser
  2. Complete first-run wizard
  3. Configure settings (motion, storage, alerts)
  4. View logs: ssh $PI 'sudo journalctl -u mecamera.service -f'

QUICK COMMANDS:
  Status: ssh $PI 'sudo systemctl status mecamera'
  Logs:   ssh $PI 'sudo journalctl -u mecamera.service -f'
  Restart: ssh $PI 'sudo systemctl restart mecamera'

"@ -ForegroundColor Cyan
