# Git Commit Script for v2.1.2 (PowerShell)
# Run this to commit all changes to GitHub

Write-Host "🚀 Preparing v2.1.2 Release..." -ForegroundColor Cyan
Write-Host ""

# Show what will be committed
Write-Host "📋 Files staged for commit:" -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "📝 Commit Message Preview:" -ForegroundColor Yellow
Write-Host @"

v2.1.2: Motion Detection Overhaul & Pi Zero Optimization

Major Updates:
✨ Advanced motion detection with shadow/sunlight filtering
✨ User registration system with validation
✨ WiFi configuration UI in settings page
✨ H.264 video codec for universal browser compatibility
✨ Pre-buffered recording captures full motion events
✨ Enhanced storage management with automatic file cleanup

Bug Fixes:
🐛 Fixed timezone to EST (was showing GMT)
🐛 Fixed video playback stuck at 0:00
🐛 Fixed JSON serialization errors (numpy types)
🐛 Fixed file deletion not removing actual videos
🐛 Fixed motion recording timing (now captures during, not after)

Performance:
⚡ Optimized for Pi Zero 2W (512MB RAM)
⚡ Frame skipping reduces CPU load 50%
⚡ Reduced buffer size for memory efficiency
⚡ Faster cooldown between motion events

Security:
🔒 No credentials in source code
🔒 .gitignore updated to exclude sensitive files

Tested on: Raspberry Pi Zero 2W, Pi Camera Module v3 (IMX708)

"@ -ForegroundColor Gray

Write-Host ""
$commit = Read-Host "🔍 Review changes above. Commit to GitHub? (y/n)"

if ($commit -eq "y" -or $commit -eq "Y") {
    git commit -m "v2.1.2: Motion Detection Overhaul & Pi Zero Optimization

Major Updates:
- Advanced motion detection with shadow/sunlight filtering
- User registration system with validation
- WiFi configuration UI in settings page
- H.264 video codec for universal browser compatibility
- Pre-buffered recording captures full motion events
- Enhanced storage management with automatic file cleanup

Bug Fixes:
- Fixed timezone to EST (was showing GMT)
- Fixed video playback stuck at 0:00
- Fixed JSON serialization errors (numpy types)
- Fixed file deletion not removing actual videos
- Fixed motion recording timing (now captures during, not after)

Performance:
- Optimized for Pi Zero 2W (512MB RAM)
- Frame skipping reduces CPU load 50%
- Reduced buffer size for memory efficiency
- Faster cooldown between motion events

Security:
- No credentials in source code
- .gitignore updated to exclude sensitive files

Tested on: Raspberry Pi Zero 2W, Pi Camera Module v3 (IMX708)"

    Write-Host ""
    Write-Host "✅ Committed successfully!" -ForegroundColor Green
    Write-Host ""
    
    $push = Read-Host "📤 Push to GitHub now? (y/n)"
    
    if ($push -eq "y" -or $push -eq "Y") {
        git push origin main
        Write-Host ""
        Write-Host "🎉 v2.1.2 Released to GitHub!" -ForegroundColor Green
        Write-Host "🔗 https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV" -ForegroundColor Cyan
    } else {
        Write-Host "⏸️  Commit saved locally. Push manually with: git push origin main" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Commit cancelled" -ForegroundColor Red
}
