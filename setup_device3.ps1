Write-Host "==============================================`n" -ForegroundColor Cyan
Write-Host "  Setting Up Device 3 (IMX519 Camera)`n" -ForegroundColor Cyan
Write-Host "==============================================`n" -ForegroundColor Cyan

Write-Host "[1/7] Checking camera hardware..." -ForegroundColor Yellow
ssh pi@mecamdev3 "libcamera-hello --list-cameras"

Write-Host "`n[2/7] Installing flask-cors..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo pip3 install flask-cors --break-system-packages"

Write-Host "`n[3/7] Creating systemd service file..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo tee /etc/systemd/system/mecamera.service > /dev/null << 'EOF'
[Unit]
Description=ME Camera Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ME_CAM-DEV
ExecStart=/usr/bin/python3 /home/pi/ME_CAM-DEV/main_lite.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF"

Write-Host "`n[4/7] Reloading systemd..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl daemon-reload"

Write-Host "`n[5/7] Enabling service..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl enable mecamera"

Write-Host "`n[6/7] Starting service..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl start mecamera"

Start-Sleep -Seconds 5

Write-Host "`n[7/7] Checking status..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl status mecamera --no-pager | head -15"

Write-Host "`n==============================================`n" -ForegroundColor Green
Write-Host "Device 3 Setup Complete!" -ForegroundColor Green
Write-Host "`nCamera: IMX519" -ForegroundColor Cyan
Write-Host "Test Dashboard: http://10.2.1.4:8080`n" -ForegroundColor Yellow
Write-Host "Check logs:" -ForegroundColor Cyan
Write-Host "  ssh pi@mecamdev3" -ForegroundColor Gray
Write-Host "  sudo journalctl -u mecamera -f`n" -ForegroundColor Gray
