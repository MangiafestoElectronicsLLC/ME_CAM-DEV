#!/bin/bash

# ME_CAM Performance Upgrade Script
# Installs picamera2 for 10-15x faster camera streaming

set -e

echo "========================================="
echo "ME_CAM Performance Upgrade"
echo "Installing picamera2 for FAST streaming"
echo "========================================="
echo

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script requires sudo access."
    echo "Run with: sudo ./install_fast_camera.sh"
    exit 1
fi

echo "📦 Installing picamera2 system package..."
apt update
apt install -y python3-picamera2

echo
echo "✅ picamera2 installed successfully!"
echo
echo "Performance comparison:"
echo "  BEFORE (libcamera-still): 500-1000ms per frame = 1-2 FPS"
echo "  AFTER (picamera2):        30-60ms per frame = 15-30 FPS"
echo
echo "Next steps:"
echo "1. Go to Settings → Performance Settings"
echo "2. Check '✓ Use Fast Streaming (picamera2)'"
echo "3. Set Target FPS to 15-30"
echo "4. Save settings and restart service:"
echo "   sudo systemctl restart mecamera"
echo
echo "Your camera will now respond as fast as your Tkinter GUI!"
