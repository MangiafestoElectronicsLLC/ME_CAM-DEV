Write-Host "Fixing Device 3 service file..." -ForegroundColor Cyan

# Create the service file correctly
ssh pi@mecamdev3 "sudo rm /etc/systemd/system/mecamera.service; echo '[Unit]
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
WantedBy=multi-user.target' | sudo tee /etc/systemd/system/mecamera.service"

Write-Host "`nReloading systemd..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl daemon-reload"

Write-Host "`nRestarting service..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl restart mecamera"

Start-Sleep -Seconds 3

Write-Host "`nChecking status..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo systemctl status mecamera --no-pager | head -20"

Write-Host "`nChecking logs..." -ForegroundColor Yellow
ssh pi@mecamdev3 "sudo journalctl -u mecamera -n 20 --no-pager"
