# Fix missing flask-cors dependency
Write-Host "Installing flask-cors on Device 1..." -ForegroundColor Yellow

ssh pi@mecamdev1 "cd ~/ME_CAM-DEV && source venv/bin/activate && pip install flask-cors"

Write-Host "`nRestarting mecamera service..." -ForegroundColor Yellow
ssh pi@mecamdev1 "sudo systemctl restart mecamera"

Write-Host "`nWaiting 5 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "`nChecking service status..." -ForegroundColor Yellow
ssh pi@mecamdev1 "sudo systemctl status mecamera --no-pager -l"

Write-Host "`nTesting v3.0 endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://10.2.1.3:8080/api/v3/status" -UseBasicParsing
    Write-Host "✓ v3.0 API is working!" -ForegroundColor Green
    Write-Host $response.Content
} catch {
    Write-Host "✗ API still not responding" -ForegroundColor Red
    Write-Host "Check logs: ssh pi@mecamdev1 'sudo journalctl -u mecamera -n 30'" -ForegroundColor Yellow
}
