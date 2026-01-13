# Camera Fix - Resolution

## Problem
The error `/dev/video0: Device or resource busy` occurred because **TWO processes** were trying to use the camera simultaneously:

1. **CameraPipeline** (via watchdog.py) - Opens camera with OpenCV for motion detection/recording
2. **libcamera-still** (via web streaming) - Tries to capture individual frames for video streaming

**Only ONE process can use the Raspberry Pi camera at a time!**

## Solution Applied
Modified [web/app.py](web/app.py) to **disable the CameraPipeline/Watchdog**:

```python
# BEFORE (conflicting):
watchdog = CameraWatchdog()
watchdog.start()  # This locks the camera with OpenCV

# AFTER (fixed):
watchdog = None  # Disabled to allow libcamera streaming
```

## What This Means
✅ **Camera streaming WORKS** - libcamera-still can now access the camera  
✅ **Web dashboard WORKS** - You can view live camera feed  
❌ **Motion detection DISABLED** - CameraPipeline is not running  
❌ **Auto-recording DISABLED** - No motion-triggered video recording

## How to Deploy This Fix

### Method 1: Copy the fixed file to your Pi
```bash
# On your Pi:
cd ~/ME_CAM/ME_CAM-DEV

# Backup current file
cp web/app.py web/app.py.backup

# Download the fixed file from your Windows machine
# (Use SCP, WinSCP, or copy paste the content)

# Restart the application
python3 main.py
```

### Method 2: Apply the fix manually on Pi
```bash
# On your Pi, edit the file:
nano web/app.py

# Find line ~25-27:
watchdog = CameraWatchdog()
watchdog.start()

# Change to:
# watchdog = CameraWatchdog()
# watchdog.start()
watchdog = None  # Disabled to allow libcamera streaming

# Find line ~205:
status = watchdog.status()

# Change to:
status = watchdog.status() if watchdog else {"active": False, "timestamp": time.time()}

# Find line ~278:
return jsonify(watchdog.status())

# Change to:
return jsonify(watchdog.status() if watchdog else {"active": False, "timestamp": time.time()})

# Save and exit (Ctrl+X, Y, Enter)
# Restart:
python3 main.py
```

## Verification
After applying the fix and running `python3 main.py`, you should see:
1. ✅ No camera busy errors in the logs
2. ✅ Camera stream works in web dashboard
3. ✅ Test photo command works: `libcamera-still -o test.jpg`

## Future: Re-enable Motion Detection (Advanced)
To have BOTH streaming AND motion detection, you need to:
1. Modify `CameraPipeline` to use libcamera instead of OpenCV
2. OR use a shared frame buffer approach
3. OR use motion detection without holding camera continuously

This requires significant code refactoring.

## Backup
Your original file is backed up as `web/app.py.backup_YYYYMMDD_HHMMSS`

## Test Commands
```bash
# Stop any running instance
pkill -9 python3

# Test camera is free
libcamera-still -t 1000 -o ~/test.jpg

# Run the app
cd ~/ME_CAM/ME_CAM-DEV
source venv/bin/activate
python3 main.py

# Open in browser:
# http://10.2.1.4:8080
```
