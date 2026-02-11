Write-Host "Installing all required Python packages on Device 3..." -ForegroundColor Cyan
Write-Host ""

ssh pi@mecamdev3 "sudo pip3 install --break-system-packages `
    Flask==3.0.0 `
    Werkzeug==3.0.0 `
    cryptography==41.0.0 `
    'qrcode[pil]'==7.4.2 `
    psutil==5.9.5 `
    yagmail==0.15.293 `
    pydrive2==1.19.0 `
    loguru==0.7.2 `
    flask-cors==6.0.2"

Write-Host "`nStopping and restarting service..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl stop mecamera && sleep 2 && sudo systemctl start mecamera"

Start-Sleep -Seconds 5

Write-Host "`nChecking service status..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl status mecamera --no-pager | head -15"

Write-Host "`nChecking logs..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo journalctl -u mecamera -n 5 --no-pager"

Write-Host "`n==============================================`n" -ForegroundColor Green
Write-Host "Device 3 should be running now!" -ForegroundColor Green
Write-Host "Test Dashboard: http://10.2.1.4:8080`n" -ForegroundColor Yellow
