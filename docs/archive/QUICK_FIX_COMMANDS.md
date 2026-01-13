# Quick Fix Commands for Pi Camera Issue

## Immediate Fix (Run on Pi via SSH)

```bash
# Kill the process holding the camera
sudo kill -9 665

# Or kill all python processes
sudo pkill -9 -f "setup_mode/setup_server.py"
sudo pkill -9 python3

# Verify nothing is using the camera
ps aux | grep -E "python|libcamera" | grep -v grep

# Test camera
libcamera-still -t 2000 -o ~/test.jpg
```

## Complete Clean Setup

```bash
# 1. Upload and run the fix script
cd ~/ME_CAM/ME_CAM-DEV
chmod +x fix_camera_and_setup.sh
./fix_camera_and_setup.sh
```

## Manual Step-by-Step

```bash
# Stop everything
sudo systemctl stop me_cam.service 2>/dev/null || true
sudo pkill -9 -f "python3"
sleep 3

# Verify camera is free
lsof /dev/video0 2>/dev/null

# If still busy - REBOOT
sudo reboot

# After reboot, test camera
libcamera-hello --list-cameras
libcamera-still -t 2000 -o ~/test.jpg

# Fresh install
cd ~
rm -rf ME_CAM_OLD
mv ME_CAM ME_CAM_OLD 2>/dev/null || true
mkdir -p ME_CAM/ME_CAM-DEV
cd ME_CAM/ME_CAM-DEV

# Copy your files here, then:
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# BEFORE running main.py, make sure no other process is using camera:
ps aux | grep python | grep -v grep

# Run the application
python3 main.py
```

## Troubleshooting

### Camera still busy?
```bash
# Check what's using the camera
sudo lsof /dev/video0
sudo fuser /dev/video0

# Force kill the process
sudo kill -9 <PID_FROM_ABOVE>
```

### Camera not detected?
```bash
# Check camera interface is enabled
sudo raspi-config
# Go to: Interface Options -> Camera -> Enable

# Check camera cable
vcgencmd get_camera

# Should show: supported=1 detected=1

# Reboot if needed
sudo reboot
```

### Still having issues?
```bash
# Nuclear option - reboot
sudo reboot

# After reboot, test IMMEDIATELY before starting any app
libcamera-still -t 2000 -o ~/test.jpg
```

## Root Cause

The error `/dev/video0[13:cap]: Unable to set format: Device or resource busy` means:
1. Another process is already using the camera
2. Most likely `setup_mode/setup_server.py` (PID 665) from your logs
3. Each `libcamera-still` call tries to acquire exclusive camera access
4. When camera is busy, it fails immediately

## Solution

**ONLY ONE process can use the camera at a time!**
- Make sure setup_server.py is NOT running when you start main.py
- The web interface spawns multiple `libcamera-still` processes
- Each one needs exclusive access, so they must be sequential, not parallel
