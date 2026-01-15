#!/bin/bash
# Test motion detection on Pi

echo "=== Motion Detection Test ==="
echo ""
echo "Capturing 10 frames to test motion detection..."

# Create test motion by moving camera or object in front
# For now, just verify the system is working

# Check if logs directory exists
if [ -d ~/ME_CAM-DEV/logs ]; then
    echo "✓ Logs directory exists"
else
    echo "✗ Logs directory missing"
    exit 1
fi

# Check if motion_events.json was created
if [ -f ~/ME_CAM-DEV/logs/motion_events.json ]; then
    echo "✓ Motion events file exists"
    echo ""
    echo "Contents:"
    cat ~/ME_CAM-DEV/logs/motion_events.json | head -50
else
    echo "✗ Motion events file not created yet (will be created on first motion detection)"
fi

echo ""
echo "Service status:"
sudo systemctl status mecamera-lite --no-pager | head -5

echo ""
echo "Recent log entries:"
tail -10 ~/ME_CAM-DEV/logs/mecam_lite.log | grep -E "MOTION|CAMERA|SMS"

echo ""
echo "To test motion detection:"
echo "1. Move an object in front of the camera for 2-3 seconds"
echo "2. Wait 10 seconds for detection"
echo "3. Check motion_events.json:"
echo "   cat ~/ME_CAM-DEV/logs/motion_events.json"
echo ""
echo "To configure SMS:"
echo "1. Edit ~/ME_CAM-DEV/config.json"
echo "2. Add Twilio credentials to notifications.sms section"
echo "3. Restart service: sudo systemctl restart mecamera-lite"
