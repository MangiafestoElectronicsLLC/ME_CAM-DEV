# 🚀 ME_CAM v2.0 - Pi Zero 2W Deployment & Testing Guide

**Target Device:** Raspberry Pi Zero 2W
**Status:** Ready to deploy
**Estimated Time:** 1.5-2 hours
**Difficulty:** Medium (follow steps exactly)

---

## 🎯 Your 10-Step Deployment Plan

### STEP 1: Verify SSH Connection ✅
**Status:** Already complete (QUICK SETUP ONLY)

```bash
# On your Windows PC (PowerShell):
ping raspberrypi.local

# Should respond with IP. If not, try:
ping 192.168.x.x  # Use Pi's actual IP
```

If this fails, restart your Pi and try again. Continue only if ping works.

---

### STEP 2: Deploy Code to Pi
**Status:** IN PROGRESS - Do this now

Choose ONE option below:

#### Option A: Using Git (Recommended - Easiest)

```bash
# Open PowerShell and SSH to Pi:
ssh pi@raspberrypi.local

# Once connected (you see pi@raspberrypi:~$ prompt):
cd ~

# Backup old code (IMPORTANT!)
tar czf ME_CAM-DEV.old.backup.$(date +%Y%m%d_%H%M%S).tar.gz ME_CAM-DEV/ 2>/dev/null || echo "No old backup needed"

# Remove old directory
rm -rf ME_CAM-DEV

# Clone fresh repository
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git

# Navigate to it
cd ME_CAM-DEV

# Verify all files there
ls -la | head -20
```

Expected output should show:
```
total 456
drwxr-xr-x 11 pi pi  4096 Jan 14 10:30 .
drwxr-xr-x 5 pi pi  4096 Jan 14 10:25 ..
-rw-r--r--  1 pi pi  2541 Jan 14 10:30 README.md
drwxr-xr-x  2 pi pi  4096 Jan 14 10:30 config
drwxr-xr-x  2 pi pi  4096 Jan 14 10:30 docs
drwxr-xr-x  2 pi pi  4096 Jan 14 10:30 scripts
drwxr-xr-x  2 pi pi  4096 Jan 14 10:30 src
drwxr-xr-x  2 pi pi  4096 Jan 14 10:30 templates
drwxr-xr-x  2 pi pi  4096 Jan 14 10:30 web
-rw-r--r--  1 pi pi  1204 Jan 14 10:30 main.py
```

#### Option B: Copy from Your PC (If Git fails)

```powershell
# On your Windows PC (PowerShell):
$PI_IP = "raspberrypi.local"
$PI_USER = "pi"

# Delete old code on Pi
ssh $PI_USER@$PI_IP "rm -rf ~/ME_CAM-DEV"

# Copy new code to Pi
scp -r "C:\Users\nickp\Downloads\ME_CAM-DEV\ME_CAM-DEV" ${PI_USER}@${PI_IP}:~/

# Verify it copied
ssh $PI_USER@$PI_IP "ls -la ~/ME_CAM-DEV | head -10"
```

---

### STEP 3: Run Automated Setup Script
**Status:** Do this next (30-45 minutes)

```bash
# Make sure you're on the Pi and in the right directory:
ssh pi@raspberrypi.local
cd ~/ME_CAM-DEV

# Make setup script executable
chmod +x scripts/setup.sh

# Run the setup (this will take 30-45 minutes on Pi Zero 2W!)
./scripts/setup.sh
```

**What the setup script does:**
1. Updates system packages (5-10 min)
2. Installs Python development libraries (5 min)
3. Creates Python virtual environment (2 min)
4. Installs all Python dependencies (10-15 min)
5. Creates `mecamera` system user (1 min)
6. Sets up systemd service (2 min)
7. Configures log rotation (1 min)
8. Creates logs/ and recordings/ directories (1 min)
9. Sets proper permissions (1 min)
10. Validates installation (1 min)

**Watch for errors:**
- If you see red text with "ERROR" or "FAILED", stop and note the exact error
- Most errors are harmless (like missing optional packages)
- Critical errors will be obvious (Python won't install, etc.)

**Example output:**
```
[SETUP] Starting ME_CAM v2.0 installation...
[SETUP] Updating system packages...
[SETUP] Installing Python dependencies...
[SETUP] Creating virtual environment...
[SETUP] Installing pip packages...
[SETUP] Creating mecamera user...
[SETUP] Setting up systemd service...
[SETUP] Installation complete!
```

---

### STEP 4: Install Fast Camera Support
**Status:** Do this after setup.sh completes (10 minutes)

```bash
# Still on Pi, in ~/ME_CAM-DEV:
sudo chmod +x scripts/install_fast_camera.sh
sudo ./scripts/install_fast_camera.sh
```

This installs `picamera2` which gives you 15-30 FPS streaming instead of 1-2 FPS.

**Expected output:**
```
[FAST_CAMERA] Installing picamera2 library...
[FAST_CAMERA] Installing related packages...
[FAST_CAMERA] Validating installation...
[FAST_CAMERA] ✓ picamera2 successfully installed!
```

---

### STEP 5: Enable and Start the Service
**Status:** Do this after fast camera installation

```bash
# Start the mecamera service
sudo systemctl start mecamera

# Enable autoboot (so it starts on reboot)
sudo systemctl enable mecamera

# Check if it's running
sudo systemctl status mecamera
```

**Expected output:**
```
● mecamera.service - ME_CAM v2.0
   Loaded: loaded (/etc/systemd/system/mecamera.service)
   Active: active (running)
   
[MAIN] Flask app started on http://0.0.0.0:8080
[CAMERA] Fast streamer initialized: 640x480 @ 15 FPS
[MOTION] Motion detection service started
```

If you see "failed" or "inactive", check the logs:
```bash
sudo journalctl -u mecamera -n 50 --no-pager
```

---

### STEP 6: Verify Camera Hardware
**Status:** Check camera detection

```bash
# Test camera is detected
libcamera-still --list-cameras

# Should show something like:
# Available cameras
# 0 : imx219 [3280x2464] (/base/soc/i2c0mux/i2c@1/imx219@10)
```

If you get "No cameras available":
1. Check ribbon cable is fully inserted into camera slot
2. Reboot Pi: `sudo reboot`
3. Try again after reboot

---

### STEP 7: Access the Dashboard
**Status:** Test web interface (do this from your PC)

**In your browser, open:**
```
http://raspberrypi.local:8080
```

or if that doesn't work, use Pi's IP:
```
http://192.168.x.x:8080
```

**What you should see:**
- Dashboard loads (white/light background)
- Live camera feed shows video (or black rectangle initially)
- Real-time stats show (FPS, resolution, etc.)
- Buttons visible: Settings, Motion Events, Storage, etc.

**If dashboard doesn't load:**
- Check service is running: `sudo systemctl status mecamera`
- Check logs: `sudo journalctl -u mecamera -n 20`
- Wait 30 seconds and refresh browser

---

### STEP 8: Test Motion Logging Integration
**Status:** Verify motion events save with timestamps

```bash
# SSH to Pi and check motion events file
ssh pi@raspberrypi.local
cat ~/ME_CAM-DEV/logs/motion_events.json

# Should show empty array [] if no motion yet:
# []

# Now wave your hand in front of camera for 5 seconds...
# Wait 5 seconds, then check again:
cat ~/ME_CAM-DEV/logs/motion_events.json

# Should now show events like:
# [
#   {"timestamp":"2026-01-14T10:30:45.123456","type":"motion","confidence":0.87,...},
#   {"timestamp":"2026-01-14T10:30:50.654321","type":"motion","confidence":0.92,...}
# ]
```

**If no events appear:**
1. Check motion detection is running: `sudo journalctl -u mecamera | grep MOTION`
2. Make sure you're in good lighting
3. Wave hand slowly (sudden motion triggers better detection)
4. Check sensitivity setting: `grep "motion_sensitivity" ~/ME_CAM-DEV/config/config.json`

---

### STEP 9: Test Dashboard Features
**Status:** Verify all interactive features work

#### Test Motion Events Modal

1. Open browser to `http://raspberrypi.local:8080`
2. Look for **"Motion Events"** section in dashboard
3. Click **"View Motion Events"** button
4. Modal should appear showing:
   - List of motion events from last 24 hours
   - Timestamp for each event
   - Confidence level (0.0-1.0)
   - Duration in seconds

**If modal is empty:**
- Make sure you created motion events (Step 8)
- Wait a few seconds for API to respond
- Check browser console for errors (F12 → Console tab)

#### Test Storage Details Modal

1. Find **"Storage"** section in dashboard
2. Click **"View Storage Details"** button
3. Modal should show:
   - Used GB / Total GB
   - Percentage bar (visual representation)
   - Cleanup settings
   - Retention policy

#### Test Recordings Browser Modal

1. Find **"Recordings"** section in dashboard
2. Click **"Browse Recordings"** button
3. Modal should show:
   - List of all video files (if any exist)
   - File size and date
   - Download and delete buttons

#### Test Stream Quality Selector

1. Look at dashboard header (top-right corner)
2. Find quality dropdown (should say "Standard" or similar)
3. Click dropdown and select "Low"
4. Camera stream should switch to 320x240 resolution
5. Try selecting "High" - stream should switch to 1280x720
6. Return to "Standard"

---

### STEP 10: Verify End-to-End Functionality
**Status:** Final comprehensive test

```bash
# 1. SSH to Pi and run this test suite:
ssh pi@raspberrypi.local

# Check service is running
echo "=== SERVICE STATUS ==="
sudo systemctl status mecamera | head -5

# Check camera is detected
echo "=== CAMERA DETECTION ==="
libcamera-still --list-cameras | head -3

# Check motion events exist
echo "=== MOTION EVENTS ==="
cat ~/ME_CAM-DEV/logs/motion_events.json | head -1

# Check API endpoints respond
echo "=== API TESTS ==="
curl -s http://localhost:8080/api/motion/events | head -1
curl -s http://localhost:8080/api/storage | head -1
curl -s http://localhost:8080/api/camera/stats | head -1

# Check logs look good
echo "=== APPLICATION LOGS ==="
tail -5 ~/ME_CAM-DEV/logs/mecam.log
```

**Expected output should show no errors and successful responses.**

---

## 🧪 Comprehensive Testing Checklist

### Pre-Testing Requirements
- [ ] Pi is powered on and connected to WiFi
- [ ] SSH connection works (`ping raspberrypi.local` succeeds)
- [ ] Camera is physically connected to Pi
- [ ] At least 5GB free space on SD card
- [ ] Service is running (`sudo systemctl status mecamera`)

### Phase 1: Dashboard Access
- [ ] Dashboard loads at `http://raspberrypi.local:8080`
- [ ] Page layout displays correctly
- [ ] No 404 or connection errors
- [ ] Real-time stats display (FPS, resolution, etc.)

### Phase 2: Camera Streaming
- [ ] Live video shows (not black screen)
- [ ] Video is smooth (no extreme lag)
- [ ] Resolution appears to be 640x480 or higher
- [ ] FPS shows 15+ (not 1-2)

### Phase 3: Quality Selection
- [ ] Quality dropdown exists in header
- [ ] Can select "Low" without crashing
- [ ] Can select "Standard" without crashing
- [ ] Can select "High" without crashing
- [ ] Can select "Ultra" without crashing
- [ ] Stream quality visibly changes when switching

### Phase 4: Motion Detection
- [ ] Motion events logged to `logs/motion_events.json`
- [ ] Each event has timestamp
- [ ] Each event has confidence score
- [ ] File updates when motion detected
- [ ] No permission errors in logs

### Phase 5: Dashboard Modals
- [ ] Motion Events modal opens
- [ ] Motion Events modal shows data
- [ ] Motion Events modal has close button
- [ ] Storage Details modal opens
- [ ] Storage Details modal shows usage
- [ ] Recordings Browser modal opens
- [ ] Recordings Browser shows files (if any)

### Phase 6: API Endpoints
- [ ] `/api/motion/events` returns JSON
- [ ] `/api/motion/stats` returns JSON
- [ ] `/api/storage` returns JSON
- [ ] `/api/camera/stats` returns JSON
- [ ] All endpoints respond in < 1 second

### Phase 7: Encryption & Security
- [ ] New recordings are encrypted (check file extensions)
- [ ] Dashboard requires login on first access
- [ ] Can create user account with password
- [ ] Password prevents unauthorized access

### Phase 8: Log Management
- [ ] `logs/mecam.log` exists and has content
- [ ] Log file grows over time
- [ ] No ERROR lines in logs (warnings OK)
- [ ] Motion events logged with timestamps
- [ ] API calls logged appropriately

### Phase 9: Service Management
- [ ] Service survives reboot (`sudo reboot`, then check later)
- [ ] Service auto-restarts on crash
- [ ] Can stop service: `sudo systemctl stop mecamera`
- [ ] Can restart service: `sudo systemctl restart mecamera`
- [ ] Service status shows "active (running)"

### Phase 10: Storage Management
- [ ] Videos save to `recordings/` directory
- [ ] Videos organized by date (YYYY/MM/DD)
- [ ] Dashboard storage shows accurate usage
- [ ] Can delete videos via dashboard
- [ ] Auto-cleanup works at threshold

---

## 🔧 Testing Commands Cheat Sheet

### Dashboard & Streaming
```bash
# Test dashboard loads
curl http://localhost:8080 | head -20

# Test live stream works
curl -I http://localhost:8080/api/stream | head -5
```

### Motion Events API
```bash
# Get recent motion events
curl http://localhost:8080/api/motion/events | python -m json.tool

# Get motion statistics
curl http://localhost:8080/api/motion/stats | python -m json.tool

# Get events from last 48 hours
curl http://localhost:8080/api/motion/events?hours=48 | python -m json.tool
```

### Storage & System
```bash
# Get storage information
curl http://localhost:8080/api/storage | python -m json.tool

# Get camera statistics
curl http://localhost:8080/api/camera/stats | python -m json.tool

# Get device information
curl http://localhost:8080/api/devices | python -m json.tool
```

### Service & Logs
```bash
# Check service status
sudo systemctl status mecamera

# View real-time logs
sudo journalctl -u mecamera -f

# View last 50 log lines
sudo journalctl -u mecamera -n 50 --no-pager

# Filter logs for MOTION only
sudo journalctl -u mecamera | grep MOTION

# Filter logs for CAMERA only
sudo journalctl -u mecamera | grep CAMERA

# Filter logs for ERRORS
sudo journalctl -u mecamera | grep ERROR
```

### File System
```bash
# Check motion events file
cat ~/ME_CAM-DEV/logs/motion_events.json

# Check application logs
tail -f ~/ME_CAM-DEV/logs/mecam.log

# Check recordings directory
ls -lh ~/ME_CAM-DEV/recordings/

# Check disk usage
df -h

# Check camera detection
libcamera-still --list-cameras
```

---

## ⚠️ Common Issues During Testing

### Issue 1: Dashboard Shows Black Screen / No Video

**Symptoms:** Dashboard loads but camera area is black

**Quick Fixes:**
```bash
# 1. Restart service
sudo systemctl restart mecamera

# 2. Check camera is detected
libcamera-still --list-cameras

# 3. Check camera cable
# (Physically inspect Pi camera connector - should be fully inserted)

# 4. Check if using fast streamer
grep "use_fast_streamer" ~/ME_CAM-DEV/config/config.json
# Should show: "use_fast_streamer": true

# 5. If false, edit config
sudo nano ~/ME_CAM-DEV/config/config.json
# Find: "use_fast_streamer": false
# Change to: "use_fast_streamer": true
# Save (Ctrl+X, Y, Enter)
# Restart: sudo systemctl restart mecamera
```

### Issue 2: Motion Events Not Logging

**Symptoms:** `logs/motion_events.json` stays empty or doesn't update

**Quick Fixes:**
```bash
# 1. Check motion service is running
sudo journalctl -u mecamera | grep -i motion

# 2. Check motion sensitivity
grep "motion_sensitivity" ~/ME_CAM-DEV/config/config.json

# 3. Increase sensitivity (lower number = more sensitive)
sudo nano ~/ME_CAM-DEV/config/config.json
# Find: "motion_sensitivity": 0.6
# Try: "motion_sensitivity": 0.4
# Save and restart

# 4. Test motion detection manually
# Wave hand in front of camera for 5 seconds
# Then check: cat ~/ME_CAM-DEV/logs/motion_events.json

# 5. Check for permissions
ls -la ~/ME_CAM-DEV/logs/
# Should show mecamera user can write
```

### Issue 3: Dashboard Very Slow (1-2 FPS)

**Symptoms:** Camera stream lags, moves in slow motion

**Quick Fixes:**
```bash
# 1. Check if using fast streamer
grep "use_fast_streamer" ~/ME_CAM-DEV/config/config.json

# 2. Verify picamera2 installed
python3 -c "import picamera2; print('picamera2 OK')"
# If error: sudo ./scripts/install_fast_camera.sh

# 3. Try lower quality
# Dashboard → Settings → Stream Quality → Select "Low"

# 4. Check CPU usage
top -bn1 | grep %
# If > 80%, restart service or reduce quality

# 5. Check network bandwidth
# If WiFi weak, switch to wired or reduce quality
```

### Issue 4: Storage Shows Wrong Usage

**Symptoms:** Dashboard storage doesn't match actual disk usage

**Quick Fixes:**
```bash
# 1. Check actual disk usage
df -h ~/ME_CAM-DEV/

# 2. Check recordings directory
du -sh ~/ME_CAM-DEV/recordings/

# 3. Refresh dashboard
# Hard refresh in browser (Ctrl+Shift+R)

# 4. Restart service
sudo systemctl restart mecamera

# 5. Check storage API
curl http://localhost:8080/api/storage | python -m json.tool
```

### Issue 5: Service Won't Start

**Symptoms:** `sudo systemctl start mecamera` fails or says "inactive"

**Quick Fixes:**
```bash
# 1. Check what the error is
sudo systemctl status mecamera

# 2. View detailed logs
sudo journalctl -u mecamera -n 50 --no-pager

# 3. Check if Python files have syntax errors
python3 -m py_compile ~/ME_CAM-DEV/main.py
python3 -m py_compile ~/ME_CAM-DEV/web/app.py

# 4. Test running manually to see error
cd ~/ME_CAM-DEV
python3 main.py
# (Press Ctrl+C to stop)

# 5. Check dependencies installed
source ~/ME_CAM-DEV/venv/bin/activate
pip list | grep -E "flask|loguru|cryptography|picamera2"
```

---

## ✅ Success Indicators

### You'll Know It's Working When:

1. ✅ Dashboard loads in browser without errors
2. ✅ Camera stream shows live video (not black)
3. ✅ Video is smooth (15+ FPS, not 1-2 FPS)
4. ✅ Motion Events modal opens and shows data
5. ✅ Motion events file updates when motion detected
6. ✅ Each motion event has timestamp
7. ✅ Storage Details shows accurate usage
8. ✅ Quality selector changes stream resolution
9. ✅ API endpoints return JSON (test with curl)
10. ✅ Service runs automatically after reboot

### If All Checkmarks Pass:
**🎉 Your ME_CAM v2.0 system is fully operational!**

---

## 📊 Post-Testing Optimization

### After Basic Testing Passes, Try These:

**Performance Tuning:**
1. Monitor CPU: `top -b -n 1 | grep python`
2. If > 50%, reduce FPS: Edit config.json, change `stream_fps` from 15 to 10
3. If still high, reduce resolution: Change 640x480 to 320x240
4. Test different quality presets and pick sweet spot

**Security Hardening:**
1. Change default password (Dashboard → Settings → Change Password)
2. Enable encryption (should be default)
3. Set strong password (12+ chars, mixed case, symbols)

**Storage Optimization:**
1. Set retention period (Dashboard → Settings → Retention Days)
2. Set cleanup threshold (90% triggers auto-delete)
3. Monitor free space: `df -h`

**Motion Tuning:**
1. Adjust sensitivity: Too high = false alarms, too low = misses real motion
2. Set motion_only mode if only want person recordings
3. Test AI detection threshold

---

## 🎬 What to Test First (Priority Order)

### First 10 Minutes (Critical Tests)
1. Dashboard loads
2. Camera shows video
3. Service is running
4. Logs show no errors

### Next 10 Minutes (Important Tests)
5. Motion detection works (wave hand)
6. Motion events save with timestamps
7. API endpoints respond

### Next 15 Minutes (Feature Tests)
8. Motion Events modal opens
9. Storage Details modal shows usage
10. Quality selector changes resolution

### Final 15 Minutes (Verification)
11. All features work together
12. No errors in logs
13. Service survives restart
14. Performance is acceptable

---

## 🚨 If Something's Wrong

### Golden Rules:
1. **Always check logs first:** `sudo journalctl -u mecamera -n 50`
2. **Always restart after config change:** `sudo systemctl restart mecamera`
3. **Always wait 30 seconds for service to fully start**
4. **Always hard-refresh browser:** Ctrl+Shift+R (not just F5)

### When to Check Logs:
- Dashboard doesn't load → Check logs
- Camera is black → Check logs
- Motion not logging → Check logs
- API returns error → Check logs
- Service won't start → Check logs

**Logs are your best friend!** They tell you exactly what's wrong.

---

## 🎯 Final Verification

Run this complete test on your Pi:

```bash
#!/bin/bash
echo "=== ME_CAM v2.0 DEPLOYMENT VERIFICATION ==="
echo ""

echo "1. Service Status:"
sudo systemctl status mecamera | head -3

echo ""
echo "2. Camera Detection:"
libcamera-still --list-cameras | head -1

echo ""
echo "3. Motion Events Count:"
cat ~/ME_CAM-DEV/logs/motion_events.json | wc -l

echo ""
echo "4. Dashboard Access:"
curl -s http://localhost:8080 | head -1

echo ""
echo "5. API Motion Events:"
curl -s http://localhost:8080/api/motion/events | head -1

echo ""
echo "6. Storage Status:"
df -h ~/ME_CAM-DEV/ | tail -1

echo ""
echo "7. Recent Logs:"
tail -3 ~/ME_CAM-DEV/logs/mecam.log

echo ""
echo "=== VERIFICATION COMPLETE ==="
```

Save this as `test.sh`, run with `bash test.sh`, and you'll get a quick health check.

---

**Status:** Ready to test! Follow steps 1-10 in order and you'll have a fully functional ME_CAM v2.0 system! 🚀
