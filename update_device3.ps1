Write-Host "==============================================`n" -ForegroundColor Cyan
Write-Host "  Updating Device 3 to v2.2.3 (Match Device 1)`n" -ForegroundColor Cyan
Write-Host "==============================================`n" -ForegroundColor Cyan

Write-Host "[1/6] Deploying updated files to Device 3..." -ForegroundColor Yellow
Write-Host "  - Uploading rpicam_streamer.py..." -ForegroundColor Gray
scp C:/Users/nickp/Downloads/ME_CAM-DEV/ME_CAM-DEV/src/camera/rpicam_streamer.py pi@mecamdev3:~/ME_CAM-DEV/src/camera/

Write-Host "  - Uploading app_lite.py..." -ForegroundColor Gray
scp C:/Users/nickp/Downloads/ME_CAM-DEV/ME_CAM-DEV/web/app_lite.py pi@mecamdev3:~/ME_CAM-DEV/web/

Write-Host "  - Uploading lite.css..." -ForegroundColor Gray
scp C:/Users/nickp/Downloads/ME_CAM-DEV/ME_CAM-DEV/web/static/lite.css pi@mecamdev3:~/ME_CAM-DEV/web/static/

Write-Host "`n[2/6] Verifying files..." -ForegroundColor Yellow
ssh pi@mecamdev3 "ls -lh ~/ME_CAM-DEV/src/camera/rpicam_streamer.py ~/ME_CAM-DEV/web/app_lite.py ~/ME_CAM-DEV/web/static/lite.css"

Write-Host "`n[3/6] Installing flask-cors..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo pip3 install flask-cors --break-system-packages"

Write-Host "`n[4/6] Killing any stuck processes on port 8080..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo pkill -f 'python.*main_lite.py' || true"

Write-Host "`n[5/6] Restarting mecamera service..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl restart mecamera"

Start-Sleep -Seconds 3

Write-Host "`n[6/6] Checking Device 3 status..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl status mecamera --no-pager | head -15"

Write-Host "`n==============================================`n" -ForegroundColor Green
Write-Host "Device 3 Updated!" -ForegroundColor Green
Write-Host "`nChanges Applied:" -ForegroundColor Cyan
Write-Host "  ✓ Camera quality: 95 (was 85)" -ForegroundColor Green
Write-Host "  ✓ FPS: 30 (was 15)" -ForegroundColor Green
Write-Host "  ✓ CSS rotation: Removed (camera right-side up)" -ForegroundColor Green
Write-Host "  ✓ vflip parameter: Removed" -ForegroundColor Green
Write-Host "`nTest Dashboard:" -ForegroundColor Cyan
Write-Host "  http://10.2.1.4:8080`n" -ForegroundColor Yellow
Write-Host "Check logs:" -ForegroundColor Cyan
Write-Host "  ssh pi@mecamdev3" -ForegroundColor Gray
Write-Host "  sudo journalctl -u mecamera -f`n" -ForegroundColor Gray
