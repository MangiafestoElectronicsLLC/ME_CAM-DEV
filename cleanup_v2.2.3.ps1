param(
    [switch]$Confirm = $false
)

Write-Host "🧹 ME_CAM v2.2.3 Cleanup & Sanitization (Windows)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

$filesToRemove = @(
    # Temporary test files
    "test_imports.py", "fix_first_run.py", "web_dashboard.py", "hub.py", "main_lite.py",
    
    # Old deployment scripts
    "deploy_camera_fix.sh", "deploy_camera_improvements.ps1", "deploy_device3_fix.sh",
    "DEPLOY_FIXES_JAN26.ps1", "deploy_lite.ps1", "DEPLOY_MANUAL_JAN26.ps1",
    "deploy_motion_sms.ps1", "deploy_pi_zero.ps1", "deploy_pi_zero.sh",
    "DEPLOY_PI.ps1", "DEPLOY_PI.sh", "deploy_urgent.ps1",
    "deploy_v2.1.2_updates.ps1", "deploy_v2.1.2_updates.sh",
    "deploy_vpn_support.ps1", "deploy_vpn_support.sh", "DEPLOY_TO_PI.ps1",
    "commit_v2.1.2.ps1", "commit_v2.1.2.sh", "diagnose_pi.ps1",
    
    # Old documentation
    "ANALYSIS_COMPLETE_JAN26.md", "BUG_REPORT_AND_FIXES.md", "CAMERA_IMPROVEMENTS_JAN26.md",
    "CAMERA_STATUS.txt", "check_device3_status.sh", "CODE_CHANGES_VISUAL.md",
    "CRITICAL_FIXES_JAN15.md", "CRITICAL_FIXES_JAN26.md", "DASHBOARD_IMPROVEMENTS.md",
    "DEPLOYMENT_CHECKLIST.md", "DEPLOYMENT_COMPLETE.md", "DEPLOYMENT_FIXES_JAN13.md",
    "DEPLOYMENT_FIXES_JAN26.md", "DEPLOYMENT_VALIDATED.md", "DEVICE3_CAMERA_FIX.md",
    "DEVICE3_FIXES_BEFORE_AUTOBOOT.md", "DEVICE3_IMX519_FIX.md", "DEVICE3_IMX519_TROUBLESHOOT_JAN27.md",
    "DEVICE3_RECOVERY_CHECKLIST_JAN27.md", "EMERGENCY_FIX_APP_CRASH.md", "FIXES_AND_IMPROVEMENTS_SUMMARY.md",
    "FIXES_COMPLETE.md", "FIXES_STATUS_JAN26.md", "FIXES_SUMMARY.md", "IMPLEMENTATION_COMPLETE.md",
    "IMPLEMENTATION_COMPLETE_V2.1.0.md", "IMPLEMENTATION_GUIDE.md", "IMPLEMENTATION_SUMMARY.md",
    
    # Summary files
    "ACTION_CARD.md", "ACTION_SUMMARY.txt", "DELIVERY_SUMMARY.txt", "CUSTOMER_DEPLOYMENT.txt",
    "DEPLOYMENT_PLAN.md", "FINAL_SUMMARY.txt", "COMPLETE_DOCUMENTATION_LIBRARY.md", "COMPLETE_SYSTEM_ROADMAP.md",
    "COMPLETION_CHECKLIST_V2.1.0.md", "COMPLETION_REPORT.md", "DOCS_REFERENCE.md", "DOCUMENTATION_INDEX.md",
    "DOCUMENTATION_INDEX_V2.1.0.md", "INDEX.md", "INSTALL.md", "LAUNCH_READY.txt",
    
    # VPN/HTTPS/SSL
    "HTTPS_COMPLETE.txt", "HTTPS_DOMAIN_SETUP.md", "HTTPS_DOMAIN_SETUP.txt", "HTTPS_SETUP_COMPLETE_GUIDE.md",
    "QUICK_CERT_SETUP.txt", "QUICK_REF_HTTPS.txt", "VPN_IMPLEMENTATION_COMPLETE.md", "VPN_QUICK_REFERENCE.md",
    "VPN_SETUP_GUIDE.md", "SSL_CERTIFICATE_SETUP.md", "setup_ssl.sh", "generate_certs.ps1", "generate_certs.sh",
    
    # SMS/Notification
    "SMS_NOTIFICATIONS_SETUP_GUIDE.md", "MOTION_SMS_SETUP.sh",
    
    # GitHub/Release
    "GIT_COMMIT_V2.1.2.md", "GITHUB_V2.1_RELEASE.md", "GITHUB_RELEASE_CHECKLIST.md", "github_v2.1_prepare.sh",
    
    # Fix scripts
    "FIX_ARDUCAM.sh", "FIX_BULLSEYE_PI_ZERO.sh", "FIX_CAMERA_HARDWARE.md", "FIX_CAMERA_IMX7098.md",
    "FIX_OPENCV.sh", "FIX_SUMMARY_VISUAL.txt", "FIXES_COMMANDS.sh", "auto_fix_imx519.sh",
    "fix_imx519.sh", "quick_fix_device3.sh", "update_device.sh",
    
    # Device guides
    "PI_ZERO_2W_CAMERA_EXPLANATION.md", "PI_ZERO_2W_SETUP.md", "PI_ZERO_AUTOBOOT_SETUP.md", "DEVICE_UPDATE_GUIDE.md",
    
    # Misc
    "pi_deployment_commands.txt", "PI_DEPLOYMENT_TESTING.md", "notes.txt", "deployment_notes.txt",
    "CUSTOMER_SETUP_MANUAL.md", "QUICK_TROUBLESHOOT.md", "DEVELOPER_QUICK_REFERENCE.md", "QUICK_REFERENCE_CARD.md",
    "HARDWARE_GUIDE.md", "PERFORMANCE_GUIDE.md", "VISUAL_IMPROVEMENTS_GUIDE.md", "nginx-me-camera.conf",
    "CHANGELOG.md", "COMPREHENSIVE_FIXES.md", "COMPLETE_ANALYSIS_AND_FIXES.md",
    
    # Windows batch
    "add-domain-to-hosts.bat", "setup-domain-windows.bat",
    
    # Old deployment guides
    "DEPLOYMENT_GUIDE.md", "DEPLOYMENT_GUIDE_COMPLETE.md", "DEPLOYMENT_REBUILD_GUIDE.md",
    "DEPLOYMENT_TO_PI_GUIDE.md", "DEPLOYMENT_V2.1.0.md", "DEPLOYMENT.md", "DEPLOY_QUICK_START.md",
    "QUICK_DEPLOY_GUIDE.md", "QUICK_DEPLOY_NOW.md", "QUICK_DEPLOY_NOW.txt", "QUICK_START.md", "QUICK_UPDATE.md",
    
    # Improvement guides
    "MOBILE_UI_IMPROVEMENTS.md", "MOTION_SMS_COMPLETE.md", "MOTION_VIDEO_IMPROVEMENTS.md",
    "PERFORMANCE_IMPROVEMENTS.md", "PI_CLEANUP_RESTRUCTURE.md", "QUICK_REFERENCE_IMPROVEMENTS.md",
    "RELEASE_COMPLETE.md", "REORGANIZATION_SUMMARY.md", "SESSION_SUMMARY_JAN26.md",
    "TUTORIAL_UPDATES_SUMMARY.md", "UPDATE_SUMMARY_JAN26_2026.md", "URGENT_UPDATES.md", "VALIDATION_REPORT.md"
)

$removed = 0
foreach ($file in $filesToRemove) {
    $path = Join-Path (Get-Location) $file
    if (Test-Path $path) {
        Write-Host "  ✗ Removing: $file" -ForegroundColor Yellow
        Remove-Item $path -Force -ErrorAction SilentlyContinue
        $removed++
    }
}

Write-Host "`n✓ Cleanup complete! Removed $removed files" -ForegroundColor Green

Write-Host "`nRemaining important files:" -ForegroundColor Cyan
@("README.md", "FRESH_SD_CARD_TUTORIAL.md", "CUSTOMER_QUICK_START_v2.1.1.md", "IMPLEMENTATION_COMPLETE_FEB2026.md", "DELIVERY_SUMMARY_FEB2_2026.md", "DOCUMENTATION_INDEX_v2.1.1.md") | ForEach-Object {
    Write-Host "  ✓ $_" -ForegroundColor Green
}

Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Run: git status" -ForegroundColor White
Write-Host "  2. Run: git add ." -ForegroundColor White
Write-Host "  3. Run: git commit -m 'v2.2.3: UI Redesign & Cleanup'" -ForegroundColor White
Write-Host "  4. Run: git push" -ForegroundColor White
