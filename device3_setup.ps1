Write-Host "Installing packages on Device 3..." -ForegroundColor Cyan

ssh pi@mecamdev3 "sudo pip3 install --break-system-packages Flask==3.0.0 Werkzeug==3.0.0 cryptography==41.0.0 psutil==5.9.5 yagmail==0.15.293 pydrive2==1.19.0 loguru==0.7.2 flask-cors==6.0.2 'qrcode[pil]==7.4.2'"

Write-Host "Stopping service..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl stop mecamera"
Start-Sleep -Seconds 2

Write-Host "Starting service..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl start mecamera"
Start-Sleep -Seconds 5

Write-Host "Checking status..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl status mecamera --no-pager | head -15"

Write-Host "Device 3 is ready at http://10.2.1.4:8080" -ForegroundColor Green
