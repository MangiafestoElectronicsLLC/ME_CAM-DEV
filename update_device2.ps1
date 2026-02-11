# Update Device 2 to Match Device 1 (v2.2.3)
Write-Host "=============================================="  -ForegroundColor Cyan
Write-Host "  Updating Device 2 to v2.2.3 (Match Device 1)" -ForegroundColor Cyan
Write-Host "==============================================`n" -ForegroundColor Cyan

$device2 = "pi@MECAMDEV2"

# Step 1: Deploy updated files
Write-Host "[1/4] Deploying updated files to Device 2..." -ForegroundColor Yellow

Write-Host "  - Uploading rpicam_streamer.py..." -ForegroundColor Gray
scp C:/Users/nickp/Downloads/ME_CAM-DEV/ME_CAM-DEV/src/camera/rpicam_streamer.py ${device2}:~/ME_CAM-DEV/src/camera/

Write-Host "  - Uploading app_lite.py..." -ForegroundColor Gray
scp C:/Users/nickp/Downloads/ME_CAM-DEV/ME_CAM-DEV/web/app_lite.py ${device2}:~/ME_CAM-DEV/web/

Write-Host "  - Uploading lite.css..." -ForegroundColor Gray
scp C:/Users/nickp/Downloads/ME_CAM-DEV/ME_CAM-DEV/web/static/lite.css ${device2}:~/ME_CAM-DEV/web/static/

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Files uploaded successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Upload failed" -ForegroundColor Red
    exit 1
}

# Step 2: Verify files on Device 2
Write-Host "`n[2/4] Verifying updates on Device 2..." -ForegroundColor Yellow
ssh ${device2} "grep 'quality=95' ~/ME_CAM-DEV/src/camera/rpicam_streamer.py"
ssh ${device2} "grep 'fps=30' ~/ME_CAM-DEV/web/app_lite.py"
ssh ${device2} "grep -v 'rotate(180deg)' ~/ME_CAM-DEV/web/static/lite.css | head -5"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Files verified correctly" -ForegroundColor Green
} else {
    Write-Host "⚠ Verification warnings (may be ok)" -ForegroundColor Yellow
}

# Step 3: Restart service
Write-Host "`n[3/4] Restarting mecamera service on Device 2..." -ForegroundColor Yellow
ssh ${device2} "sudo systemctl restart mecamera"
Start-Sleep -Seconds 5

# Step 4: Check status
Write-Host "`n[4/4] Checking Device 2 status..." -ForegroundColor Yellow
ssh ${device2} "sudo systemctl status mecamera --no-pager | head -15"

Write-Host "`n==============================================`n" -ForegroundColor Cyan
Write-Host "Device 2 Updated!" -ForegroundColor Green
Write-Host ""
Write-Host "Changes Applied:" -ForegroundColor White
Write-Host "  ✓ Camera quality: 95 (was 85)" -ForegroundColor Green
Write-Host "  ✓ FPS: 30 (was 15)" -ForegroundColor Green
Write-Host "  ✓ CSS rotation: Removed (camera right-side up)" -ForegroundColor Green
Write-Host "  ✓ Capture delay: 0.033s (~30 FPS)" -ForegroundColor Green
Write-Host ""
Write-Host "Test Dashboard:" -ForegroundColor Yellow
Write-Host "  http://10.2.1.2:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "Check logs:" -ForegroundColor Yellow
Write-Host "  ssh pi@MECAMDEV2" -ForegroundColor Gray
Write-Host "  sudo journalctl -u mecamera -f" -ForegroundColor Gray
Write-Host ""
