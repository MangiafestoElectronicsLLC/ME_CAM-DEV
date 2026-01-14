# IMX7098 Camera Setup Guide for Pi Zero 2 W

## Current Status
✅ Dashboard is running at `http://10.2.1.47:8080`  
⚠️ Camera hardware not detected - Test Mode is enabled  
🎯 Goal: Get the physical camera recognized and streaming

---

## What's Happening Now

**Test Mode Active**: The dashboard is displaying a test pattern instead of real video. This proves:
- ✅ Flask web server working
- ✅ Dashboard UI responsive
- ✅ Settings page functional
- ❌ Camera hardware not detected

---

## Troubleshooting Steps

### Step 1: Verify Hardware Connection

First, SSH into your Pi and check if the camera is detected:

```bash
ssh pi@10.2.1.47

# Check camera detection
libcamera-hello --list-cameras

# Check available video devices
ls -la /dev/video*

# Check USB devices (if IMX7098 is USB camera)
lsusb | grep -i camera

# Check kernel messages for camera-related errors
dmesg | grep -i camera | tail -20
```

**Expected Output:**
- If CSI camera (ribbon cable): Should see camera in libcamera-hello output
- If USB camera: Should see device in lsusb output

---

### Step 2: Configuration File

Check `/boot/config.txt` for camera settings:

```bash
cat /boot/config.txt | grep -E "camera|dtoverlay|gpu_mem"
```

Should include:
```
camera_auto_detect=1
dtoverlay=vc4-kms-v3d
gpu_mem=128
```

---

### Step 3: Enable CSI Camera (if using ribbon cable)

If you have a **CSI camera module** (not USB):

```bash
sudo raspi-config
# Navigate to: Interfacing Options > Legacy Camera > Enable
# Select "Yes" when prompted
# Exit and reboot
sudo reboot

# Then check again
libcamera-hello --list-cameras
```

---

### Step 4: USB Camera Setup (if IMX7098 is USB)

If your **IMX7098 is a USB camera**:

```bash
# Install USB camera tools
sudo apt update
sudo apt install -y v4l-utils ffmpeg

# List USB video devices
v4l2-ctl --list-devices

# Test USB camera with ffplay
ffplay /dev/video0

# Or test with libcamera
libcamera-hello -t 5 -o test.jpg
```

---

### Step 5: Camera Permissions

Ensure the `pi` user has camera access:

```bash
# Add pi to video group
sudo usermod -aG video pi

# Apply group changes without logout
newgrp video

# Verify
groups pi
# Should include: video
```

---

### Step 6: Camera Module Type Detection

To determine **if your IMX7098 is CSI or USB**:

```bash
# If ribbon cable (CSI)
dtc -I fs /proc/device-tree | grep -i camera

# If USB
dmesg | grep -i usb | grep -i camera

# Check camera detection module
sudo modprobe -l | grep camera
```

---

### Step 7: Enable Fast Streaming (picamera2)

Once camera is detected, enable fast streaming:

```bash
# SSH to Pi
ssh pi@10.2.1.47

# Edit config
nano ~/ME_CAM-DEV/config/config.json

# Add this to "camera" section:
"use_fast_streamer": true,
"resolution": "640x480",
"stream_fps": 30

# Save (Ctrl+X, Y, Enter)

# Restart service
sudo systemctl restart mecamera

# Check logs
sudo journalctl -u mecamera -n 50
```

---

## Automatic Fix Script

Run this script on your Pi to auto-detect and configure the camera:

```bash
ssh pi@10.2.1.47 'bash' << 'EOF'
#!/bin/bash

echo "🔍 Detecting camera type..."
echo ""

# Check for CSI camera
if libcamera-hello --list-cameras 2>/dev/null | grep -q "Camera"; then
    echo "✅ CSI Camera Detected!"
    echo "Camera info:"
    libcamera-hello --list-cameras
    
elif [ -e /dev/video0 ]; then
    echo "✅ USB Camera Detected at /dev/video0"
    v4l2-ctl -d /dev/video0 --all 2>/dev/null | head -20
    
else
    echo "❌ No camera detected"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check ribbon cable (CSI) or USB connection"
    echo "2. Run: sudo raspi-config"
    echo "3. Enable Camera in Interfacing Options"
    echo "4. Reboot and try again"
    exit 1
fi

echo ""
echo "✅ Camera detected! Updating configuration..."

# Update camera config
python3 << 'PYTHON'
import json

config_path = "/home/pi/ME_CAM-DEV/config/config.json"
with open(config_path) as f:
    config = json.load(f)

# Enable fast streamer
config["camera"]["use_fast_streamer"] = True
config["camera"]["resolution"] = "640x480"
config["camera"]["stream_fps"] = 30

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("✅ Configuration updated")
print(f"   Resolution: 640x480")
print(f"   FPS: 30")
print(f"   Fast Streamer: Enabled")
PYTHON

# Restart service
echo "🔄 Restarting ME_CAM service..."
sudo systemctl restart mecamera
sleep 3

# Check status
echo "📊 Service status:"
sudo systemctl status mecamera --no-pager | grep -E "Active|Failed"

echo ""
echo "✅ Done! Access dashboard at: http://10.2.1.47:8080"

EOF
```

---

## Testing Live Camera

Once hardware is detected:

```bash
# Quick camera test
libcamera-still -o ~/test.jpg

# View test image
file ~/test.jpg
# Should show: JPEG image data, JFIF standard

# Test picamera2 directly
python3 << 'EOF'
from picamera2 import Picamera2
cam = Picamera2()
cam.start()
print("✅ Camera is working!")
cam.stop()
EOF
```

---

## Verify Streaming Works

After camera is detected:

1. Open dashboard: `http://10.2.1.47:8080`
2. Check **Quick Stats** bar for **FPS** value
   - If > 0: ✅ Streaming working!
   - If 0: ❌ Camera still not detected

3. Check logs for debug info:
```bash
ssh pi@10.2.1.47 'sudo journalctl -u mecamera -n 50 | grep STREAM'
```

---

## Performance Benchmarks

Once working, you should see:

| Metric | Target | Expected |
|--------|--------|----------|
| FPS | 15-60 | Real-time in dashboard |
| Latency | <100ms | Responsive video |
| Resolution | 640x480 | Visible in stream |
| CPU Usage | <40% | Efficient streaming |

---

## Common Issues & Solutions

### Issue: "No cameras available"

**Solution:**
1. Check physical connection (ribbon cable or USB)
2. Run `sudo raspi-config` → Interface Options → Camera → Enable
3. Reboot with `sudo reboot`
4. Verify with `libcamera-hello --list-cameras`

---

### Issue: libcamera-still works, but picamera2 fails

**Solution:**
1. Reinstall picamera2:
```bash
sudo apt update
sudo apt install -y python3-picamera2
pip3 install --upgrade picamera2
```

2. Test with Python:
```python
from picamera2 import Picamera2
Picamera2()  # Should not error
```

---

### Issue: Camera detected but low FPS

**Solution:**
1. Reduce resolution: `320x240` instead of `640x480`
2. Lower FPS: Set to `15` instead of `30`
3. Check CPU: `top` command
4. Check memory: `free -h`

---

### Issue: High latency (>1 second delay)

**Solution:**
1. Enable fast streaming mode in config
2. Check FPS isn't set too low
3. Verify network connectivity
4. Check Pi CPU load

---

## Automatic Camera Fix Script (One-Command)

Run this on your **Windows machine** to push a fix to the Pi:

```powershell
# Run on Windows PowerShell
ssh pi@10.2.1.47 "
echo '🔧 Fixing Camera Configuration...'
sudo raspi-config nonint do_camera 0  # Enable camera
echo '✅ Camera enabled'
echo '🔄 Rebooting Pi...'
sudo reboot
"
```

**Then wait 30 seconds for reboot and try again.**

---

## Quick Diagnostic Command

Copy-paste this into your Pi SSH session:

```bash
echo "=== CAMERA DIAGNOSTIC ===" && \
echo "CSI Camera:" && libcamera-hello --list-cameras 2>/dev/null && \
echo "USB Devices:" && lsusb | grep -i camera && \
echo "Video Devices:" && ls /dev/video* 2>/dev/null && \
echo "GPU Memory:" && grep gpu_mem /boot/config.txt && \
echo "Camera Permissions:" && groups pi | grep video && \
echo "=== END DIAGNOSTIC ==="
```

---

## Next Steps

1. **Run diagnostic** to identify camera type
2. **Enable camera** if not already enabled
3. **Reboot** if configuration changed
4. **Verify detection** with libcamera-hello
5. **Update config** with fast_streamer=true
6. **Restart service** and check dashboard

Once camera is detected, the dashboard will **automatically** start showing the live feed!

---

**Status**: Test Mode Active ✅  
**Dashboard**: http://10.2.1.47:8080 ✅  
**Camera**: Awaiting Hardware Detection ⏳
