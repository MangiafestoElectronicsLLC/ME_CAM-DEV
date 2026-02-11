Write-Host "Configuring IMX519 camera on Device 3..." -ForegroundColor Cyan

Write-Host "[1/4] Backing up config.txt..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo cp /boot/firmware/config.txt /boot/firmware/config.txt.backup"

Write-Host "[2/4] Adding IMX519 overlay to boot config..." -ForegroundColor Yellow
ssh pi@mecamdev3 "echo '
# IMX519 Camera Configuration
camera_auto_detect=0
dtoverlay=imx519
' | sudo tee -a /boot/firmware/config.txt"

Write-Host "[3/4] Stopping mecamera service..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl stop mecamera"

Write-Host "[4/4] Rebooting Device 3..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo reboot"

Write-Host ""
Write-Host "Device 3 is rebooting..." -ForegroundColor Green
Write-Host "Wait 60 seconds, then run: .\verify_device3_camera.ps1" -ForegroundColor Yellow
