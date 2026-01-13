#!/bin/bash
# Simple fix - Just get camera working again

echo "==========================================="
echo "Simple Camera Fix - No Motion Detection"
echo "==========================================="

cd ~/ME_CAM/ME_CAM-DEV

# Stop everything
echo "Stopping all processes..."
pkill -9 python3
pkill -9 libcamera
sleep 3

# Verify camera is free
echo "Testing camera..."
libcamera-still -t 1000 -o /tmp/test.jpg --nopreview
if [ $? -eq 0 ]; then
    echo "✓ Camera is working!"
else
    echo "✗ Camera test failed - may need reboot"
    echo "Run: sudo reboot"
    exit 1
fi

# Start the app
echo ""
echo "Starting application..."
source venv/bin/activate
python3 main.py

echo ""
echo "==========================================="
echo "Camera should be working at:"
echo "http://10.2.1.4:8080"
echo "==========================================="
