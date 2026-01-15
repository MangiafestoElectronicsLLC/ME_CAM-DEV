# Deploy Urgent Updates - Battery Runtime + Emergency Alerts + Config Page
$pi_ip = "10.2.1.47"
$pi_user = "pi"
$base = "C:\Users\nickp\Downloads\ME_CAM-DEV\ME_CAM-DEV"

Write-Host "=== Deploying Urgent Updates ===" -ForegroundColor Green

# Copy battery monitor
Write-Host "Copying battery_monitor.py..." -ForegroundColor Cyan
& scp "$base\src\core\battery_monitor.py" "${pi_user}@${pi_ip}:~/ME_CAM-DEV/src/core/"

# Copy app_lite
Write-Host "Copying app_lite.py..." -ForegroundColor Cyan
& scp "$base\web\app_lite.py" "${pi_user}@${pi_ip}:~/ME_CAM-DEV/web/"

# Copy dashboard
Write-Host "Copying dashboard_lite.html..." -ForegroundColor Cyan
& scp "$base\web\templates\dashboard_lite.html" "${pi_user}@${pi_ip}:~/ME_CAM-DEV/web/templates/"

# Copy config defaults
Write-Host "Copying config_default.json..." -ForegroundColor Cyan
& scp "$base\config\config_default.json" "${pi_user}@${pi_ip}:~/ME_CAM-DEV/config/"

Write-Host "Files copied! Restarting service..." -ForegroundColor Yellow
ssh "${pi_user}@${pi_ip}" "sudo systemctl restart mecamera-lite && sleep 3"

Write-Host "Service restarted! Testing..." -ForegroundColor Green

Write-Host "`n=== Testing Battery Runtime ===" -ForegroundColor Cyan
ssh "${pi_user}@${pi_ip}" "curl -s http://localhost:8080/api/battery | python3 -m json.tool | head -10"

Write-Host "`n=== Testing Motion Events ===" -ForegroundColor Cyan
ssh "${pi_user}@${pi_ip}" "cat ~/ME_CAM-DEV/logs/motion_events.json | python3 -m json.tool | tail -20"

Write-Host "`n=== Deployment Complete! ===" -ForegroundColor Green
Write-Host "Dashboard: http://$pi_ip:8080" -ForegroundColor Yellow
Write-Host "Config Page: http://$pi_ip:8080/config" -ForegroundColor Yellow
Write-Host "Battery shows runtime in hours + minutes" -ForegroundColor White
Write-Host "Emergency alerts: Edit config to enable" -ForegroundColor White
