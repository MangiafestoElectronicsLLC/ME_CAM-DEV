Write-Host "==============================================`n" -ForegroundColor Cyan
Write-Host "  Fixing Device 2 - Complete Repair`n" -ForegroundColor Cyan
Write-Host "==============================================`n" -ForegroundColor Cyan

Write-Host "[1/3] Installing flask-cors to SYSTEM Python..." -ForegroundColor Yellow
ssh pi@MECAMDEV2 "sudo pip3 install flask-cors --break-system-packages"

Write-Host "`n[2/3] Restarting mecamera service..." -ForegroundColor Yellow
ssh pi@MECAMDEV2 "sudo systemctl restart mecamera"

Start-Sleep -Seconds 3

Write-Host "`n[3/3] Checking service status..." -ForegroundColor Yellow
ssh pi@MECAMDEV2 "sudo systemctl status mecamera --no-pager | head -10"

Write-Host "`n==============================================`n" -ForegroundColor Green
Write-Host "Device 2 should be working now!" -ForegroundColor Green
Write-Host "Test: http://10.2.1.2:8080`n" -ForegroundColor Yellow
