# Install missing dependencies on Device 2
Write-Host "Installing flask-cors on Device 2..." -ForegroundColor Cyan

ssh pi@MECAMDEV2 "cd ~/ME_CAM-DEV && source .venv/bin/activate && pip install flask-cors"

Write-Host "`nRestarting mecamera service..." -ForegroundColor Cyan
ssh pi@MECAMDEV2 "sudo systemctl restart mecamera"

Start-Sleep -Seconds 3

Write-Host "`nService status:" -ForegroundColor Cyan
ssh pi@MECAMDEV2 "sudo systemctl status mecamera --no-pager | head -15"

Write-Host "`n==============================================`n" -ForegroundColor Green
Write-Host "Test dashboard: http://10.2.1.2:8080" -ForegroundColor Yellow
