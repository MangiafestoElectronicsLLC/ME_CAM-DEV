Write-Host "SAFE IMX519 Setup Script" -ForegroundColor Cyan
Write-Host "Use this AFTER reflashing Device 3" -ForegroundColor Yellow
Write-Host ""

Write-Host "[1/3] Backing up original config..." -ForegroundColor Green
ssh pi@10.2.1.7 "sudo cp /boot/firmware/config.txt /boot/firmware/config.txt.orig"

Write-Host "[2/3] Adding IMX519 config (safe append)..." -ForegroundColor Green
ssh pi@10.2.1.7 "echo '
# IMX519 Camera Configuration
camera_auto_detect=0
dtoverlay=imx519
gpu_mem=128
dtparam=i2c_arm=on' | sudo tee -a /boot/firmware/config.txt > /dev/null"

Write-Host "[3/3] Rebooting..." -ForegroundColor Green
ssh pi@10.2.1.7 "sudo reboot"

Write-Host ""
Write-Host "Wait 60 seconds, then check:" -ForegroundColor Yellow
Write-Host "  ping 10.2.1.7" -ForegroundColor Gray
Write-Host "  ssh pi@10.2.1.7 'vcgencmd get_camera'" -ForegroundColor Gray
