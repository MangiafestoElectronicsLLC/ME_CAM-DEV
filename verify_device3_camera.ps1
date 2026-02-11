Write-Host "Verifying IMX519 camera after reboot..." -ForegroundColor Cyan

Write-Host "[1/4] Checking camera detection..." -ForegroundColor Yellow
ssh pi@mecamdev3 "vcgencmd get_camera"

Write-Host ""
Write-Host "[2/4] Listing available cameras..." -ForegroundColor Yellow
ssh pi@mecamdev3 "rpicam-hello --list-cameras"

Write-Host ""
Write-Host "[3/4] Testing camera capture..." -ForegroundColor Yellow
ssh pi@mecamdev3 "rpicam-jpeg -o /tmp/test.jpg --width 1280 --height 720 -t 1000"

Write-Host ""
Write-Host "[4/4] Checking service status..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl status mecamera --no-pager | head -15"

Write-Host ""
Write-Host "If camera is working, dashboard should show video at:" -ForegroundColor Green
Write-Host "http://10.2.1.7:8080" -ForegroundColor Yellow
