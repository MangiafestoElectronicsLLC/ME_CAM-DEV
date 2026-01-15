#!/bin/bash
# ME Camera v2.1 - GitHub Release Preparation Script
# This script prepares all files for GitHub commit to main branch

echo "====================================================================="
echo "ME CAMERA v2.1 - GITHUB RELEASE PREPARATION"
echo "====================================================================="
echo ""

# Check if in git repository
if [ ! -d ".git" ]; then
    echo "ERROR: Not in a git repository. Run this from ME_CAM-DEV root."
    exit 1
fi

# Check git status
echo "[1/5] Checking git status..."
git status

echo ""
echo "[2/5] Files to be committed in v2.1:"
git diff --name-only HEAD

echo ""
echo "[3/5] Verifying key files exist:"
files=(
    "notes.txt"
    ".gitignore"
    "GITHUB_V2.1_RELEASE.md"
    "web/templates/user_dashboard.html"
    "config/config_default.json"
    "CRITICAL_FIXES_JAN15.md"
    "IMMEDIATE_ACTIONS_REQUIRED.md"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ MISSING: $file"
    fi
done

echo ""
echo "[4/5] Adding all changes to staging:"
git add -A

echo ""
echo "====================================================================="
echo "READY FOR COMMIT"
echo "====================================================================="
echo ""
echo "Next steps:"
echo "1. Review changes: git diff --cached"
echo "2. Commit: git commit -m 'ME Camera v2.1 Release - Comprehensive fixes and documentation'"
echo "3. Push to main: git push origin main"
echo "4. Create release on GitHub with:"
echo "   - Version: v2.1"
echo "   - Description: See GITHUB_V2.1_RELEASE.md"
echo ""
echo "Commit message suggested:"
echo "---"
echo "ME Camera v2.1 Release"
echo ""
echo "Major Changes:"
echo "- Fixed battery display and auto-refresh on dashboard"
echo "- Fixed navbar consistency across all pages"
echo "- Fixed multi-device API responses"
echo "- Added comprehensive setup documentation (notes.txt rewritten)"
echo "- Added Pi Zero 2W hardware limitation explanation"
echo "- Improved .gitignore for production deployment"
echo "- All fixes validated and tested"
echo ""
echo "Release Notes: See GITHUB_V2.1_RELEASE.md"
echo "Setup Guide: See notes.txt"
echo "---"
