#!/bin/bash
# Fix Device 6 RpicamStreamer to support quality parameter

echo "Fixing Device 6 rpicam_streamer.py..."

cd ~/ME_CAM-DEV/src/camera

# Backup original
cp rpicam_streamer.py rpicam_streamer.py.backup

# Add quality parameter to __init__
sed -i 's/def __init__(self, width=640, height=480, fps=15, timeout=5):/def __init__(self, width=640, height=480, fps=15, timeout=5, quality=95):/' rpicam_streamer.py

# Add quality attribute
sed -i '/self.timeout = timeout/a\        self.quality = quality' rpicam_streamer.py

# Update rpicam-jpeg command to use quality
sed -i 's/--quality 85/--quality {self.quality}/g' rpicam_streamer.py

echo "✓ Fixed! Restarting service..."
sudo systemctl restart mecamera

echo "✓ Done! Check logs:"
echo "sudo journalctl -u mecamera -n 30"
