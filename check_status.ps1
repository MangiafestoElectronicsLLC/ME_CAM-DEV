# Complete Status Check - v2.2.3
Write-Host "=============================================="  -ForegroundColor Cyan
Write-Host "  ME_CAM v2.2.3 Status Check" -ForegroundColor Cyan
Write-Host "==============================================`n" -ForegroundColor Cyan

Write-Host "[1] Checking service status..." -ForegroundColor Yellow
ssh pi@mecamdev1 "sudo systemctl status mecamera --no-pager | head -10"

Write-Host "`n[2] Checking motion detection service..." -ForegroundColor Yellow
ssh pi@mecamdev1 "ps aux | grep -i motion | grep -v grep"

Write-Host "`n[3] Testing dashboard..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://10.2.1.3:8080" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Dashboard responding" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Dashboard not responding: $_" -ForegroundColor Red
}

Write-Host "`n[4] Testing camera stream..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://10.2.1.3:8080/stream.mjpg" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Camera stream working" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Camera stream error: $_" -ForegroundColor Red
}

Write-Host "`n[5] Checking recent motion events..." -ForegroundColor Yellow
ssh pi@mecamdev1 "ls -lh ~/ME_CAM-DEV/motion_videos/ | tail -10"

Write-Host "`n[6] Checking logs for errors..." -ForegroundColor Yellow
ssh pi@mecamdev1 "sudo journalctl -u mecamera --since '5 minutes ago' | grep -i error"

Write-Host "`n==============================================`n" -ForegroundColor Cyan
Write-Host "Summary:" -ForegroundColor White
Write-Host "  - Camera orientation: Fixed (removed vflip)" -ForegroundColor Green
Write-Host "  - Image quality: Increased to 95" -ForegroundColor Green
Write-Host "  - FPS target: ~30 FPS" -ForegroundColor Green
Write-Host "  - Version: v2.2.3-LITE (v3.0 changes reverted)" -ForegroundColor Green
Write-Host ""
Write-Host "Dashboard: http://10.2.1.3:8080" -ForegroundColor Cyan
Write-Host "Motion Events: http://10.2.1.3:8080/motion-events" -ForegroundColor Cyan
Write-Host ""
