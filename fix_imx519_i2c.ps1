Write-Host "Fixing IMX519 I2C communication issue on Device 3..." -ForegroundColor Cyan

Write-Host "[1/5] Enabling I2C for camera..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo raspi-config nonint do_i2c 0"

Write-Host "[2/5] Adding GPU memory and I2C parameters..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo sed -i '/dtoverlay=imx519/d' /boot/firmware/config.txt && echo 'dtoverlay=imx519
gpu_mem=128
dtparam=i2c_vc=on
dtparam=i2c_arm=on' | sudo tee -a /boot/firmware/config.txt"

Write-Host "[3/5] Showing updated config..." -ForegroundColor Yellow
ssh pi@mecamdev3 "cat /boot/firmware/config.txt | tail -10"

Write-Host ""
Write-Host "[4/5] Stopping service..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl stop mecamera"

Write-Host "[5/5] Rebooting Device 3..." -ForegroundColor Yellow  
ssh pi@mecamdev3 "sudo reboot"

Write-Host ""
Write-Host "Device 3 rebooting with I2C enabled..." -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: While waiting, physically check:" -ForegroundColor Yellow
Write-Host "  1. Camera ribbon cable is FULLY inserted into CSI port" -ForegroundColor White
Write-Host "  2. Blue tab on ribbon faces the USB ports" -ForegroundColor White
Write-Host "  3. Ribbon cable is not twisted or damaged" -ForegroundColor White
Write-Host ""
Write-Host "Wait 60 seconds, then run: .\verify_device3_camera.ps1" -ForegroundColor Cyan
