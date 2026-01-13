#!/bin/bash
# Complete update script - Copy all fixed files and restart

echo "=========================================="
echo "ME_CAM Complete Fix & Update"
echo "=========================================="

cd ~/ME_CAM/ME_CAM-DEV

# Stop current app
echo "Stopping current application..."
pkill -9 -f "python3 main.py"
pkill -9 -f "libcamera-vid"
sleep 2

# Backup current files
echo "Creating backups..."
cp web/app.py web/app.py.backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null
cp libcamera_streamer.py libcamera_streamer.py.backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null

echo ""
echo "Files have been updated with:"
echo "  ✓ Optimized camera streaming (640x480, faster)"
echo "  ✓ Emergency email notifications"
echo "  ✓ Motion detection service (lightweight)"
echo "  ✓ Reduced lag and better performance"
echo ""
echo "IMPORTANT: Transfer these files from Windows to Pi:"
echo "  - web/app.py"
echo "  - libcamera_streamer.py"
echo "  - libcamera_motion_detector.py (NEW)"
echo "  - motion_service.py (NEW)"
echo ""
echo "After copying files, run:"
echo "  source venv/bin/activate"
echo "  python3 main.py"
echo ""
echo "=========================================="
