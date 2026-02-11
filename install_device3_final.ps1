Write-Host "Installing Python packages on Device 3 (take 2)..." -ForegroundColor Cyan

# Use a single pip command without line continuations
ssh pi@mecamdev3 "sudo pip3 install --break-system-packages Flask==3.0.0 Werkzeug==3.0.0 cryptography==41.0.0 'qrcode[pil]==7.4.2' psutil==5.9.5 yagmail==0.15.293 pydrive2==1.19.0 loguru==0.7.2 flask-cors==6.0.2"

Write-Host "`n✓ Packages installed" -ForegroundColor Green

Write-Host "`nStopping service..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl stop mecamera"
Start-Sleep -Seconds 2

Write-Host "Starting service..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl start mecamera"
Start-Sleep -Seconds 5

Write-Host "`nService status:" -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl status mecamera --no-pager | head -20"

Write-Host "`nLatest logs:" -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo journalctl -u mecamera -n 3 --no-pager"

Write-Host ""
Write-Host "=============================================="
Write-Host "Device 3: http://10.2.1.4:8080" -ForegroundColor Yellow
Write-Host ""
