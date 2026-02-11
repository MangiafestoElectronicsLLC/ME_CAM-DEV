# Fix Device 2 - Check Logs and Retry
Write-Host "Checking Device 2 logs..." -ForegroundColor Yellow

ssh pi@MECAMDEV2 "sudo journalctl -u mecamera -n 50 | grep -i error"

Write-Host "`nRe-uploading CSS file..." -ForegroundColor Yellow
scp C:/Users/nickp/Downloads/ME_CAM-DEV/ME_CAM-DEV/web/static/lite.css pi@MECAMDEV2:~/ME_CAM-DEV/web/static/

Write-Host "`nRestarting service..." -ForegroundColor Yellow
ssh pi@MECAMDEV2 "sudo systemctl restart mecamera && sleep 5 && sudo systemctl status mecamera --no-pager | head -15"

Write-Host "`nCheck dashboard: http://10.2.1.2:8080" -ForegroundColor Cyan
