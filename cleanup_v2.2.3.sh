#!/bin/bash
# ME_CAM v2.2.3 Cleanup Script
# Removes unnecessary files and prepares for production release
# Run this BEFORE committing to GitHub

set -e

echo "🧹 ME_CAM v2.2.3 Cleanup & Sanitization"
echo "========================================"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to remove file if exists
remove_if_exists() {
    if [ -f "$1" ]; then
        echo -e "${YELLOW}Removing:${NC} $1"
        rm "$1"
    fi
}

# Function to remove directory if exists
remove_dir_if_exists() {
    if [ -d "$1" ]; then
        echo -e "${YELLOW}Removing directory:${NC} $1"
        rm -rf "$1"
    fi
}

# 1. Remove temporary/test files
echo -e "\n${GREEN}Step 1: Removing temporary files...${NC}"
remove_if_exists "test_imports.py"
remove_if_exists "fix_first_run.py"
remove_if_exists "web_dashboard.py"
remove_if_exists "hub.py"
remove_if_exists "main_lite.py"

# 2. Remove old deployment scripts (keep only current)
echo -e "\n${GREEN}Step 2: Removing old deployment scripts...${NC}"
remove_if_exists "deploy_camera_fix.sh"
remove_if_exists "deploy_camera_improvements.ps1"
remove_if_exists "deploy_device3_fix.sh"
remove_if_exists "DEPLOY_FIXES_JAN26.ps1"
remove_if_exists "deploy_lite.ps1"
remove_if_exists "DEPLOY_MANUAL_JAN26.ps1"
remove_if_exists "deploy_motion_sms.ps1"
remove_if_exists "deploy_pi_zero.ps1"
remove_if_exists "deploy_pi_zero.sh"
remove_if_exists "DEPLOY_PI.ps1"
remove_if_exists "DEPLOY_PI.sh"
remove_if_exists "deploy_urgent.ps1"
remove_if_exists "deploy_v2.1.2_updates.ps1"
remove_if_exists "deploy_v2.1.2_updates.sh"
remove_if_exists "deploy_vpn_support.ps1"
remove_if_exists "deploy_vpn_support.sh"
remove_if_exists "DEPLOY_TO_PI.ps1"
remove_if_exists "commit_v2.1.2.ps1"
remove_if_exists "commit_v2.1.2.sh"
remove_if_exists "diagnose_pi.ps1"

# 3. Remove old documentation/guides (consolidated)
echo -e "\n${GREEN}Step 3: Removing old documentation...${NC}"
remove_if_exists "ANALYSIS_COMPLETE_JAN26.md"
remove_if_exists "BUG_REPORT_AND_FIXES.md"
remove_if_exists "CAMERA_IMPROVEMENTS_JAN26.md"
remove_if_exists "CAMERA_STATUS.txt"
remove_if_exists "check_device3_status.sh"
remove_if_exists "CODE_CHANGES_VISUAL.md"
remove_if_exists "CRITICAL_FIXES_JAN15.md"
remove_if_exists "CRITICAL_FIXES_JAN26.md"
remove_if_exists "DASHBOARD_IMPROVEMENTS.md"
remove_if_exists "DEPLOYMENT_CHECKLIST.md"
remove_if_exists "DEPLOYMENT_COMPLETE.md"
remove_if_exists "DEPLOYMENT_FIXES_JAN13.md"
remove_if_exists "DEPLOYMENT_FIXES_JAN26.md"
remove_if_exists "DEPLOYMENT_VALIDATED.md"
remove_if_exists "DEVICE3_CAMERA_FIX.md"
remove_if_exists "DEVICE3_FIXES_BEFORE_AUTOBOOT.md"
remove_if_exists "DEVICE3_IMX519_FIX.md"
remove_if_exists "DEVICE3_IMX519_TROUBLESHOOT_JAN27.md"
remove_if_exists "DEVICE3_RECOVERY_CHECKLIST_JAN27.md"
remove_if_exists "EMERGENCY_FIX_APP_CRASH.md"
remove_if_exists "FIXES_AND_IMPROVEMENTS_SUMMARY.md"
remove_if_exists "FIXES_COMPLETE.md"
remove_if_exists "FIXES_STATUS_JAN26.md"
remove_if_exists "FIXES_SUMMARY.md"
remove_if_exists "IMPLEMENTATION_COMPLETE.md"
remove_if_exists "IMPLEMENTATION_COMPLETE_V2.1.0.md"
remove_if_exists "IMPLEMENTATION_GUIDE.md"
remove_if_exists "IMPLEMENTATION_SUMMARY.md"
remove_if_exists "MOBILE_UI_IMPROVEMENTS.md"
remove_if_exists "MOTION_SMS_COMPLETE.md"
remove_if_exists "MOTION_VIDEO_IMPROVEMENTS.md"
remove_if_exists "PERFORMANCE_IMPROVEMENTS.md"
remove_if_exists "PI_CLEANUP_RESTRUCTURE.md"
remove_if_exists "QUICK_REFERENCE_IMPROVEMENTS.md"
remove_if_exists "RELEASE_COMPLETE.md"
remove_if_exists "REORGANIZATION_SUMMARY.md"
remove_if_exists "SESSION_SUMMARY_JAN26.md"
remove_if_exists "TUTORIAL_UPDATES_SUMMARY.md"
remove_if_exists "UPDATE_SUMMARY_JAN26_2026.md"
remove_if_exists "URGENT_UPDATES.md"
remove_if_exists "VALIDATION_REPORT.md"

# 4. Remove summary/temporary documentation
echo -e "\n${GREEN}Step 4: Removing temporary notes...${NC}"
remove_if_exists "ACTION_CARD.md"
remove_if_exists "ACTION_SUMMARY.txt"
remove_if_exists "DELIVERY_SUMMARY.txt"
remove_if_exists "CUSTOMER_DEPLOYMENT.txt"
remove_if_exists "DEPLOYMENT_PLAN.md"
remove_if_exists "FINAL_SUMMARY.txt"
remove_if_exists "COMPLETE_DOCUMENTATION_LIBRARY.md"
remove_if_exists "COMPLETE_SYSTEM_ROADMAP.md"
remove_if_exists "COMPLETION_CHECKLIST_V2.1.0.md"
remove_if_exists "COMPLETION_REPORT.md"
remove_if_exists "DELIVERY_SUMMARY.txt"
remove_if_exists "DOCS_REFERENCE.md"
remove_if_exists "DOCUMENTATION_INDEX.md"
remove_if_exists "DOCUMENTATION_INDEX_V2.1.0.md"
remove_if_exists "INDEX.md"
remove_if_exists "INSTALL.md"
remove_if_exists "LAUNCH_READY.txt"
remove_if_exists "RESTRUCTURE_COMPLETE.txt"
remove_if_exists "RESTRUCTURE_DEPLOY.txt"
remove_if_exists "RELEASE_NOTES_V2.1.0.md"
remove_if_exists "RELEASE_NOTES_V2.1.2.md"
remove_if_exists "SETUP_COMPLETE.md"
remove_if_exists "SETUP_GUIDE.md"
remove_if_exists "SETUP_GUIDE_V2.1.0.md"
remove_if_exists "START_HERE.md"
remove_if_exists "SYSTEM_SUMMARY.md"
remove_if_exists "V2.1_READY_FOR_RELEASE.md"
remove_if_exists "V2.1_RELEASE_SUMMARY.md"

# 5. Remove Windows batch scripts not needed
echo -e "\n${GREEN}Step 5: Removing Windows setup scripts...${NC}"
remove_if_exists "add-domain-to-hosts.bat"
remove_if_exists "setup-domain-windows.bat"

# 6. Remove old deployment guides (keep FRESH_SD_CARD_TUTORIAL.md)
echo -e "\n${GREEN}Step 6: Removing old deployment guides...${NC}"
remove_if_exists "DEPLOYMENT_GUIDE.md"
remove_if_exists "DEPLOYMENT_GUIDE_COMPLETE.md"
remove_if_exists "DEPLOYMENT_REBUILD_GUIDE.md"
remove_if_exists "DEPLOYMENT_TO_PI_GUIDE.md"
remove_if_exists "DEPLOYMENT_V2.1.0.md"
remove_if_exists "DEPLOYMENT.md"
remove_if_exists "DEPLOY_QUICK_START.md"
remove_if_exists "DEPLOYMENT_PLAN.md"
remove_if_exists "QUICK_DEPLOY_GUIDE.md"
remove_if_exists "QUICK_DEPLOY_NOW.md"
remove_if_exists "QUICK_DEPLOY_NOW.txt"
remove_if_exists "QUICK_START.md"
remove_if_exists "QUICK_UPDATE.md"

# 7. Remove VPN/HTTPS/SSL temporary files
echo -e "\n${GREEN}Step 7: Removing VPN/HTTPS temporary files...${NC}"
remove_if_exists "HTTPS_COMPLETE.txt"
remove_if_exists "HTTPS_DOMAIN_SETUP.md"
remove_if_exists "HTTPS_DOMAIN_SETUP.txt"
remove_if_exists "HTTPS_SETUP_COMPLETE_GUIDE.md"
remove_if_exists "QUICK_CERT_SETUP.txt"
remove_if_exists "QUICK_REF_HTTPS.txt"
remove_if_exists "VPN_IMPLEMENTATION_COMPLETE.md"
remove_if_exists "VPN_QUICK_REFERENCE.md"
remove_if_exists "VPN_SETUP_GUIDE.md"
remove_if_exists "SSL_CERTIFICATE_SETUP.md"
remove_if_exists "setup_ssl.sh"
remove_if_exists "generate_certs.ps1"
remove_if_exists "generate_certs.sh"

# 8. Remove SMS/notification setup
echo -e "\n${GREEN}Step 8: Removing SMS setup files...${NC}"
remove_if_exists "SMS_NOTIFICATIONS_SETUP_GUIDE.md"
remove_if_exists "MOTION_SMS_SETUP.sh"
remove_if_exists "deploy_motion_sms.ps1"

# 9. Remove GitHub workflow files (not needed in repo)
echo -e "\n${GREEN}Step 9: Removing temporary release notes...${NC}"
remove_if_exists "GIT_COMMIT_V2.1.2.md"
remove_if_exists "GITHUB_V2.1_RELEASE.md"
remove_if_exists "GITHUB_RELEASE_CHECKLIST.md"
remove_if_exists "github_v2.1_prepare.sh"

# 10. Remove fix scripts and troubleshoot scripts
echo -e "\n${GREEN}Step 10: Removing old fix scripts...${NC}"
remove_if_exists "FIX_ARDUCAM.sh"
remove_if_exists "FIX_BULLSEYE_PI_ZERO.sh"
remove_if_exists "FIX_CAMERA_HARDWARE.md"
remove_if_exists "FIX_CAMERA_IMX7098.md"
remove_if_exists "FIX_OPENCV.sh"
remove_if_exists "FIX_SUMMARY_VISUAL.txt"
remove_if_exists "FIXES_COMMANDS.sh"
remove_if_exists "auto_fix_imx519.sh"
remove_if_exists "fix_imx519.sh"
remove_if_exists "quick_fix_device3.sh"
remove_if_exists "update_device.sh"

# 11. Remove old device-specific guides
echo -e "\n${GREEN}Step 11: Removing device-specific guides...${NC}"
remove_if_exists "PI_ZERO_2W_CAMERA_EXPLANATION.md"
remove_if_exists "PI_ZERO_2W_SETUP.md"
remove_if_exists "PI_ZERO_AUTOBOOT_SETUP.md"
remove_if_exists "DEVICE_UPDATE_GUIDE.md"

# 12. Remove misc temporary files
echo -e "\n${GREEN}Step 12: Removing misc files...${NC}"
remove_if_exists "pi_deployment_commands.txt"
remove_if_exists "PI_DEPLOYMENT_TESTING.md"
remove_if_exists "notes.txt"
remove_if_exists "deployment_notes.txt"
remove_if_exists "CUSTOMER_SETUP_MANUAL.md"
remove_if_exists "QUICK_TROUBLESHOOT.md"
remove_if_exists "DEVELOPER_QUICK_REFERENCE.md"
remove_if_exists "QUICK_REFERENCE_CARD.md"
remove_if_exists "HARDWARE_GUIDE.md"
remove_if_exists "PERFORMANCE_GUIDE.md"
remove_if_exists "VISUAL_IMPROVEMENTS_GUIDE.md"
remove_if_exists "FIX_CAMERA_HARDWARE.md"
remove_if_exists "nginx-me-camera.conf"
remove_if_exists "CHANGELOG.md"

# 13. Remove old analysis files
echo -e "\n${GREEN}Step 13: Removing analysis files...${NC}"
remove_if_exists "COMPREHENSIVE_FIXES.md"
remove_if_exists "COMPLETE_ANALYSIS_AND_FIXES.md"

# 14. Remove directories that are not needed
echo -e "\n${GREEN}Step 14: Cleaning up directories...${NC}"
remove_dir_if_exists "setup_mode"

echo -e "\n${GREEN}✓ Cleanup complete!${NC}"
echo ""
echo "Remaining important files:"
echo "  ✓ README.md"
echo "  ✓ FRESH_SD_CARD_TUTORIAL.md"
echo "  ✓ CUSTOMER_QUICK_START_v2.1.1.md"
echo "  ✓ IMPLEMENTATION_COMPLETE_FEB2026.md"
echo "  ✓ DELIVERY_SUMMARY_FEB2_2026.md"
echo "  ✓ DOCUMENTATION_INDEX_v2.1.1.md"
echo ""
echo "Next steps:"
echo "  1. Run: git status"
echo "  2. Run: git add ."
echo "  3. Run: git commit -m 'v2.2.3: UI Redesign & Cleanup'"
echo "  4. Run: git push"
