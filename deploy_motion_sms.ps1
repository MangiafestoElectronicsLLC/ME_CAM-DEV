# Deployment script for SMS + Motion detection update
# Copies updated files to Pi and restarts service

$pi_ip = "10.2.1.47"
$pi_user = "pi"
$local_path = "C:\Users\nickp\Downloads\ME_CAM-DEV\ME_CAM-DEV"

Write-Host "=== Deploying Motion + SMS Updates to Pi ===" -ForegroundColor Green
Write-Host "Target: $pi_ip" -ForegroundColor Cyan

# Files to copy
$files_to_copy = @(
    "src/core/sms_notifier.py",
    "src/core/__init__.py",
    "main.py",
    "main_lite.py",
    "web/app.py",
    "web/app_lite.py",
    "web/templates/dashboard_lite.html",
    "config/config_default.json"
)

Write-Host "Copying files..." -ForegroundColor Yellow

foreach ($file in $files_to_copy) {
    $local_file = Join-Path $local_path $file
    
    if (Test-Path $local_file) {
        # Determine remote path
        $remote_file = "~/ME_CAM-DEV/$($file -replace '\\', '/')"
        
        Write-Host "  Copying: $file" -ForegroundColor Cyan
        
        # Use scp to copy
        & scp -r $local_file "${pi_user}@${pi_ip}:${remote_file}" 2>&1 | ForEach-Object {
            if ($_ -notmatch "password:") {
                Write-Host "    $_" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "  WARNING: File not found: $file" -ForegroundColor Red
    }
}

Write-Host "Files copied successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Restarting mecamera-lite service..." -ForegroundColor Yellow

ssh pi@$pi_ip "sudo systemctl restart mecamera-lite && sleep 3 && echo 'Service restarted'"

Write-Host "Done! Service restarted." -ForegroundColor Green
Write-Host ""
Write-Host "Testing endpoints..." -ForegroundColor Yellow

# Test basic status
Write-Host "  Status API:" -ForegroundColor Cyan
ssh pi@$pi_ip "curl -s http://localhost:8080/api/status | head -c 100"
Write-Host ""
Write-Host ""

# Test motion events
Write-Host "  Motion Events API:" -ForegroundColor Cyan
ssh pi@$pi_ip "curl -s http://localhost:8080/api/motion/events 2>/dev/null | head -c 100"
Write-Host ""
Write-Host ""

Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Configure SMS in ~/ME_CAM-DEV/config.json"
Write-Host "2. Test SMS: curl -X POST http://10.2.1.47:8080/api/motion/log -H 'Content-Type: application/json' -d '{\"type\":\"motion\",\"confidence\":0.9}'"
Write-Host "3. View dashboard: http://10.2.1.47:8080"
Write-Host "4. Check logs: ssh pi@10.2.1.47 'tail logs/mecam_lite.log'"
