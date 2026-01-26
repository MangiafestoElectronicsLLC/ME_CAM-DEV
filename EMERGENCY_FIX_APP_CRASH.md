# Emergency Fix Guide - App Crash on Pi Zero 2W

## Issue: Service keeps restarting with exit code 1

**Symptoms:**
- `systemctl status mecamera` shows "activating (auto-restart)"
- `Process: exit-code) status=1/FAILURE`
- App never fully starts (just hangs and crashes)

**Root Cause:**
Likely Python import hanging or timeout during startup on 512MB RAM device.

---

## Quick Diagnostic Steps

1. **Check which import is hanging:**
   ```bash
   ssh pi@mecamdev2.local
   cd ~/ME_CAM-DEV
   
   # Test imports one by one
   python3 -c "from loguru import logger; print('[OK] loguru')"
   python3 -c "import flask; print('[OK] flask')"  
   python3 -c "from web.app_lite import create_lite_app; print('[OK] app_lite')"
   python3 -c "from main_lite import main_lite; print('[OK] main_lite')"
   ```

2. **Check if it's a resource issue:**
   ```bash
   free -h  # Check available RAM
   ps aux   # Check running processes
   ```

3. **Check service logs:**
   ```bash
   sudo journalctl -u mecamera -n 50 --no-pager
   tail -100 logs/mecam_lite.log | tail -50
   ```

---

## Immediate Fix Attempts (in order)

### Fix 1: Increase Import Timeout
Edit `/home/pi/ME_CAM-DEV/main_lite.py` line 22:

```python
# Add this before imports
import signal
def timeout_handler(signum, frame):
    raise TimeoutError("Import timeout - device overloaded")
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)  # 30 second timeout for imports

# Then do imports...
```

### Fix 2: Disable Unused Features Temporarily
Edit `/home/pi/ME_CAM-DEV/web/app_lite.py` around line 150:

Comment out any heavy imports:
```python
# Temporarily disable face detection to reduce memory
# from detection.face_detector import FaceDetector

# Remove any AI model loading
# try:
#     import tensorflow as tf  # Very memory intensive
# except ImportError:
#     pass
```

### Fix 3: Restart Service with Memory Limit
```bash
sudo systemctl set-environment MALLOC_TRIM_THRESHOLD_=256000
sudo systemctl restart mecamera
```

### Fix 4: Kill Zombie Processes
```bash
# Kill any hung Python processes
pkill -9 python3

# Kill any hung rpicam processes  
pkill -9 rpicam-jpeg

# Wait a moment
sleep 2

# Restart service
sudo systemctl restart mecamera
```

---

## Working Workaround (Tested on Pi Zero 2W)

If service won't start, run app manually in screen/tmux:

```bash
ssh pi@mecamdev2.local

# Kill systemd service
sudo systemctl stop mecamera

# Create a screen session
screen -S mecam

# Inside screen, run:
cd ~/ME_CAM-DEV
python3 main_lite.py

# Keep screen running with Ctrl+A then D to detach
```

Then access dashboard at: `http://mecamdev2.local:5000`

---

## Monitoring During Deployment

Use these commands to watch for issues:

```bash
# Terminal 1: Watch service status
watch -n 1 'systemctl status mecamera --no-pager | head -5'

# Terminal 2: Watch logs in real-time
ssh pi@mecamdev2.local 'tail -f ~/ME_CAM-DEV/logs/mecam_lite.log | grep -E "ERROR|WARNING|Motion|Camera|WiFi"'

# Terminal 3: Monitor resource usage
ssh pi@mecamdev2.local 'watch -n 2 "ps aux | head -1; ps aux | grep python3 | grep -v grep"'
```

---

## Performance Tuning for Pi Zero 2W

### Reduce Motion Detection CPU
Edit `web/app_lite.py` line 934:

Change from:
```python
if frame_count % 2 == 0:  # Skip every other frame
```

To:
```python
if frame_count % 4 == 0:  # Skip 3 of 4 frames (reduce CPU)
```

### Reduce Flask Workers
Edit service file: `/etc/systemd/system/mecamera.service`

Add to `[Service]` section:
```ini
Environment="FLASK_ENV=production"
Environment="PYTHONUNBUFFERED=1"
```

### Reduce Camera Resolution Temporarily
Edit `src/camera/rpicam_streamer.py` line 26:

Change from:
```python
def __init__(self, width=640, height=480, fps=15, timeout=5):
```

To:
```python
def __init__(self, width=320, height=240, fps=10, timeout=5):  # Lower res = lower CPU
```

---

## Memory Profiling

Check which Python modules use the most memory:

```bash
ssh pi@mecamdev2.local
cd ~/ME_CAM-DEV

python3 << 'EOF'
import sys
import psutil

# Get current process
p = psutil.Process()
print(f"Memory before imports: {p.memory_info().rss / 1024 / 1024:.1f} MB")

try:
    from loguru import logger
    print(f"After loguru: {p.memory_info().rss / 1024 / 1024:.1f} MB")
    
    import flask
    print(f"After flask: {p.memory_info().rss / 1024 / 1024:.1f} MB")
    
    import cv2
    print(f"After cv2: {p.memory_info().rss / 1024 / 1024:.1f} MB")
    
    from web.app_lite import create_lite_app
    print(f"After app_lite: {p.memory_info().rss / 1024 / 1024:.1f} MB")
except Exception as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
EOF
```

---

## Rollback to Last Known Good

If all fixes fail:

```bash
ssh pi@mecamdev2.local
cd ~/ME_CAM-DEV

# List backups
ls -la backup_*

# Restore from backup
cp backup_<TIMESTAMP>/app_lite.py.bak web/app_lite.py
cp backup_<TIMESTAMP>/rpicam_streamer.py.bak src/camera/rpicam_streamer.py
cp backup_<TIMESTAMP>/dashboard_lite.html.bak web/templates/dashboard_lite.html

# Restart
sudo systemctl restart mecamera
```

---

## Success Indicators

✅ Service should show:
```
● mecamera.service - ME Camera Service
   Active: active (running)
   PID: 12345 (/usr/bin/python3 /home/pi/ME_CAM-DEV/main_lite.py)
```

✅ Dashboard should be accessible:
```
curl http://mecamdev2.local:5000/camera  # Returns JPEG stream
curl http://mecamdev2.local:5000/api/status  # Returns JSON
```

✅ Logs should show:
```
[CAMERA] RPiCam initialized: 640x480 @ 15 FPS
[HTTPS] Running with SSL/TLS
[NETWORK] VPN Support: Enabled
```

---

## Contact Support

If the app continues to crash after all fixes:

1. Collect logs:
   ```bash
   ssh pi@mecamdev2.local 'tail -200 ~/ME_CAM-DEV/logs/mecam_lite.log > mecam_logs.txt'
   scp pi@mecamdev2.local:mecam_logs.txt ./
   ```

2. Check device resources:
   ```bash
   ssh pi@mecamdev2.local 'uname -a; cat /proc/meminfo; cat /proc/cpuinfo'
   ```

3. Verify dependencies:
   ```bash
   ssh pi@mecamdev2.local 'pip list | grep -E "flask|opencv|pillow|loguru"'
   ```

