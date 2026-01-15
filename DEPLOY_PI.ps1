# ME_CAM-DEV Quick Deploy to Pi Zero 2W (PowerShell)
# Usage: .\DEPLOY_PI.ps1 10.2.1.47 pi

param(
    [string]$PI_IP = "10.2.1.47",
    [string]$PI_USER = "pi"
)

$TARGET = "${PI_USER}@${PI_IP}"
$PROJECT = "ME_CAM-DEV"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  ME_CAM-DEV Deployment to Pi Zero 2W" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Target: ${TARGET}" -ForegroundColor Yellow
Write-Host ""

# Test connection
Write-Host "[1/8] Testing connection to Pi..." -ForegroundColor White
$pingResult = Test-Connection -ComputerName $PI_IP -Count 1 -Quiet
if (-not $pingResult) {
    Write-Host "ERROR: Cannot reach ${PI_IP}" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Connection OK" -ForegroundColor Green

# Stop existing service
Write-Host "[2/8] Stopping existing service..." -ForegroundColor White
ssh ${TARGET} "sudo systemctl stop mecamera 2>/dev/null || true"
Write-Host "[OK] Service stopped" -ForegroundColor Green

# Backup existing installation
Write-Host "[3/8] Backing up existing installation..." -ForegroundColor White
$timestamp = [int](Get-Date -UFormat %s)
ssh ${TARGET} "if [ -d ~/${PROJECT} ]; then mv ~/${PROJECT} ~/${PROJECT}.backup.${timestamp}; fi"
Write-Host "[OK] Backup complete" -ForegroundColor Green

# Create project directory
Write-Host "[4/8] Creating project directory..." -ForegroundColor White
ssh ${TARGET} "mkdir -p ~/${PROJECT}"
Write-Host "[OK] Directory created" -ForegroundColor Green

# Transfer files using scp (tar method for Windows)
Write-Host "[5/8] Transferring files..." -ForegroundColor White
Write-Host "   Creating archive..." -ForegroundColor Gray

# Use PowerShell to create tar archive
$tempFile = "$env:TEMP\${PROJECT}.tar.gz"
$sourceDir = Get-Location

# Create list of files to exclude
$excludePatterns = @('.git', '__pycache__', '*.pyc', '.venv', 'logs', 'recordings', 'encrypted_videos', '.backup.*')

# Use tar if available (Windows 10+)
if (Get-Command tar -ErrorAction SilentlyContinue) {
    tar -czf $tempFile --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' `
        --exclude='.venv' --exclude='logs' --exclude='recordings' --exclude='encrypted_videos' `
        -C . .
} else {
    Write-Host "   Note: tar not found, using file-by-file transfer..." -ForegroundColor Yellow
    # Fallback: use scp for each directory
    scp -r src templates web cloud config docs etc notifications scripts setup_mode tests utils ${TARGET}:~/${PROJECT}/
    scp *.py *.txt *.md *.sh *.json *.bat ${TARGET}:~/${PROJECT}/ 2>$null
}

# Transfer tar file if created
if (Test-Path $tempFile) {
    Write-Host "   Uploading archive..." -ForegroundColor Gray
    scp $tempFile ${TARGET}:~/
    ssh ${TARGET} "cd ~/${PROJECT} && tar -xzf ~/${PROJECT}.tar.gz && rm ~/${PROJECT}.tar.gz"
    Remove-Item $tempFile
}
Write-Host "[OK] Files transferred" -ForegroundColor Green

# Setup Python environment
Write-Host "[6/8] Installing system packages (OpenCV, NumPy)..." -ForegroundColor White
ssh ${TARGET} "sudo apt update -qq && sudo apt install -y python3-opencv python3-numpy python3-pil libatlas-base-dev"
Write-Host "[OK] System packages installed" -ForegroundColor Green

Write-Host "[6.5/8] Installing Python packages (~3 min)..." -ForegroundColor White
ssh ${TARGET} "cd ~/ME_CAM-DEV && pip3 install Flask==2.2.5 Werkzeug==2.2.3 psutil==5.9.5 qrcode cryptography yagmail Pillow --break-system-packages"
Write-Host "[OK] Python environment ready" -ForegroundColor Green

# Run setup script
Write-Host "[7/8] Running setup script..." -ForegroundColor White
ssh ${TARGET} "cd ~/${PROJECT} && chmod +x setup.sh && ./setup.sh"
Write-Host "[OK] Setup complete" -ForegroundColor Green

# Install systemd service
Write-Host "[8/8] Installing systemd service..." -ForegroundColor White
ssh ${TARGET} "cd ~/ME_CAM-DEV && sudo cp etc/systemd/system/mecamera.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable mecamera && sudo systemctl start mecamera && sleep 3"
Write-Host "[OK] Service installed and started" -ForegroundColor Green

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access Dashboard: http://${PI_IP}:8080" -ForegroundColor Yellow
Write-Host "Default PIN: 1234" -ForegroundColor Yellow
Write-Host ""
Write-Host "Check Status:" -ForegroundColor White
Write-Host "  ssh ${TARGET} 'sudo systemctl status mecamera'" -ForegroundColor Gray
Write-Host ""
Write-Host "View Logs:" -ForegroundColor White
Write-Host "  ssh ${TARGET} 'tail -f ~/ME_CAM-DEV/logs/mecam.log'" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
