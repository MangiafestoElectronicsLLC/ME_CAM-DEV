# ME Camera LITE MODE Deployment Script
# Deploy from Windows to Raspberry Pi

Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  ME CAMERA LITE MODE - Deployment to Pi" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$piHost = "10.2.1.47"
$piUser = "pi"

# Test connection
Write-Host "[1/4] Testing connection to Pi..." -NoNewline
$pingTest = Test-Connection -ComputerName $piHost -Count 1 -Quiet -ErrorAction SilentlyContinue
if (-not $pingTest) {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Cannot reach Pi at $piHost" -ForegroundColor Red
    Write-Host "Please check Pi is powered on and connected." -ForegroundColor Yellow
    exit 1
}
Write-Host " OK" -ForegroundColor Green

# Copy files to Pi
Write-Host "[2/4] Copying files to Pi (this may take 2-3 minutes)..." -ForegroundColor Yellow
Write-Host "      You will be prompted for Pi password" -ForegroundColor Gray
Write-Host ""

scp -r "$PSScriptRoot\*" "${piUser}@${piHost}:~/ME_CAM-DEV/"
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Failed to copy files" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[3/4] Installing LITE MODE on Pi..." -ForegroundColor Yellow
Write-Host ""

# Run installer on Pi (using bash -c to avoid line ending issues)
ssh -t "${piUser}@${piHost}" "bash -c 'cd ~/ME_CAM-DEV && chmod +x scripts/install_lite_mode.sh && ./scripts/install_lite_mode.sh'"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Installation had errors" -ForegroundColor Yellow
    Write-Host "Check output above for details" -ForegroundColor Gray
    exit 1
}

Write-Host ""
Write-Host "[4/4] Verifying installation..." -NoNewline
Start-Sleep -Seconds 3
$statusCheck = ssh "${piUser}@${piHost}" "systemctl is-active mecamera-lite 2>/dev/null"
if ($statusCheck -match "active") {
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " WARNING" -ForegroundColor Yellow
    Write-Host "Service may not be running, check output above" -ForegroundColor Gray
}

Write-Host ""
Write-Host "====================================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT COMPLETE" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access your camera at:" -ForegroundColor White
Write-Host "  http://${piHost}:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "Login credentials:" -ForegroundColor White
Write-Host "  Username: admin" -ForegroundColor Gray
Write-Host "  Password: admin123" -ForegroundColor Gray
Write-Host ""
