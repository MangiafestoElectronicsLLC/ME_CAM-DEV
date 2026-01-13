#!/bin/bash
# Deploy fixed web/app.py to disable camera pipeline conflict

echo "=========================================="
echo "Deploying Camera Fix"
echo "=========================================="

# Backup current file
echo "Creating backup..."
cp web/app.py web/app.py.backup_$(date +%Y%m%d_%H%M%S)

echo ""
echo "The fix has been applied to web/app.py"
echo ""
echo "What was fixed:"
echo "  - Disabled CameraPipeline/Watchdog that was holding /dev/video0"
echo "  - This allows libcamera-still to access the camera for streaming"
echo "  - Motion detection and recording features are temporarily disabled"
echo ""
echo "Now run: python3 main.py"
echo ""
echo "Your camera streaming should work now!"
echo "=========================================="
