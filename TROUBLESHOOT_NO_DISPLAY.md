# 🚨 TROUBLESHOOTING: No Display, No Recordings, No Storage Info

## Your Issues:
1. ❌ Camera display not showing (black screen?)
2. ❌ No recorded events (motion not saving videos)
3. ❌ Can't see local storage space on SD card

---

## 🔍 STEP-BY-STEP DIAGNOSTIC

### Step 1: Verify You're On The Raspberry Pi

These commands MUST run on your Pi Zero 2W, not your PC!

```bash
ssh pi@raspberrypi.local
```

---

### Step 2: Check Service Running

```bash
# Check if mecamera service is running
sudo systemctl status mecamera

# Look for:
# ✓ Active: active (running)
# ✓ [MAIN] Flask app started
# ✓ [MOTION] Motion detection service started

# If NOT running, start it:
sudo systemctl start mecamera

# If failed, check error:
sudo journalctl -u mecamera -n 50 --no-pager
```

---

### Step 3: Check Recordings Directory Exists

```bash
# Create recordings directory if missing
mkdir -p ~/ME_CAM-DEV/recordings
chmod 755 ~/ME_CAM-DEV/recordings

# Verify it exists
ls -la ~/ME_CAM-DEV/recordings/

# Check disk space
df -h
# Make sure SD card not full!
```

---

### Step 4: Test Camera Hardware

```bash
# Test camera works
libcamera-still --list-cameras

# Should show:
# Available cameras
# 0 : imx219 [3280x2464] (/base/soc/i2c0mux/i2c@1/imx219@10)

# If "No cameras available":
# 1. Check cable connected
# 2. Check legacy camera disabled in raspi-config
# 3. Reboot: sudo reboot
```

---

### Step 5: Check Latest Code Deployed

```bash
cd ~/ME_CAM-DEV

# Pull latest fixes
git pull origin main

# You should see files updated:
# - web/templates/dashboard.html (video display fix)
# - web/app.py (storage API)
# - etc.

# If errors, check git status:
git status
```

---

### Step 6: Restart Service

```bash
# After pulling latest code, restart:
sudo systemctl restart mecamera

# Wait 10 seconds for startup
sleep 10

# Check logs for errors
sudo journalctl -u mecamera -n 100 --no-pager | grep -i error
```

---

### Step 7: Test Dashboard Access

Open browser on your PC: **http://raspberrypi.local:8080**

**What you should see:**
- ✅ Dashboard loads (not timeout/connection refused)
- ✅ Live camera feed displaying (not black screen)
- ✅ Storage section shows numbers (not "0.0 GB" or "-")
- ✅ Recordings list (even if empty)

**If timeout/connection refused:**
```bash
# Check Flask running on port 8080
sudo netstat -tulpn | grep 8080

# Should show: python3 ... :8080

# If not, check service logs:
tail -f ~/ME_CAM-DEV/logs/mecam.log
```

---

### Step 8: Test Motion Recording Manually

```bash
# Test camera can record video
cd ~/ME_CAM-DEV/recordings
libcamera-vid -t 5000 -o test.mp4 --width 1280 --height 720

# Wait 5 seconds for recording...
# Check file created:
ls -lh test.mp4

# Should show file size like: -rw-r--r-- 1 pi pi 1.2M Jan 13 18:30 test.mp4

# If file is 0 bytes or missing:
# - SD card full
# - Camera not working
# - Permissions issue
```

---

### Step 9: Enable Motion Recording in Dashboard

1. Open: **http://raspberrypi.local:8080**
2. Login
3. Click: **⚙️ Configure** (bottom of page)
4. Scroll to: **📹 Camera & Recording Settings**
5. Check: **✓ Enable Motion Recording to SD Card**
6. Set: **Recording Resolution: 1280x720**
7. Set: **Recording Duration: 30 seconds**
8. Set: **Motion Sensitivity: Medium**
9. Click: **Save Settings**
10. Service will auto-restart

---

### Step 10: Test Motion Detection

```bash
# Watch motion logs in real-time
tail -f ~/ME_CAM-DEV/logs/mecam.log | grep MOTION

# Now wave your hand in front of camera...

# You should see:
# [MOTION] Motion detected
# [MOTION] Recording started: recordings/motion_20260113_183045.mp4
# [MOTION] Recording in progress...
# [MOTION] Recording saved: recordings/motion_20260113_183045.mp4 (12.34 MB)

# If you see "timeout" or "camera busy":
# This is NORMAL - coordinator gives streaming priority
# It will retry automatically

# Check recordings created:
ls -lh ~/ME_CAM-DEV/recordings/

# Should see motion_*.mp4 files with timestamps
```

---

### Step 11: Check Storage API Working

```bash
# Test storage API from Pi
curl http://localhost:8080/api/storage

# Should return JSON like:
# {"ok":true,"used_gb":0.25,"available_gb":28.5,"total_gb":29.3,"file_count":5}

# If error or timeout:
# - Service not running
# - Flask crashed
# - Check logs: tail -f ~/ME_CAM-DEV/logs/mecam.log
```

---

### Step 12: Check Browser Console for Errors

In your browser:
1. Open: **http://raspberrypi.local:8080**
2. Press **F12** (Developer Tools)
3. Click **Console** tab
4. Look for red errors

**Common errors:**

**"Failed to load /api/stream"**
- Service not running
- Camera not initialized
- Check: sudo systemctl status mecamera

**"Failed to load /api/storage"**
- API endpoint error
- Check logs: tail -f ~/ME_CAM-DEV/logs/mecam.log

**"NetworkError"**
- Can't reach Pi
- Check: ping raspberrypi.local

---

## 🔧 COMMON FIXES

### Fix 1: Black Screen (No Video Display)

```bash
# Pull latest dashboard.html fix
cd ~/ME_CAM-DEV
git pull origin main

# Restart service
sudo systemctl restart mecamera

# Open dashboard, should now show camera feed
```

**If still black:**
```bash
# Check camera initialized
grep "camera" ~/ME_CAM-DEV/logs/mecam.log | tail -20

# Should see: [CAMERA] Fast streamer initialized
# OR: [CAMERA] Libcamera streamer initialized

# If "failed to initialize":
libcamera-still --list-cameras
# Check camera detected
```

---

### Fix 2: No Recordings / Motion Not Working

```bash
# Check motion service started
grep "MOTION" ~/ME_CAM-DEV/logs/mecam.log | tail -20

# Should see:
# [MOTION] Motion detection service started

# If missing, check config:
grep "motion_only" ~/ME_CAM-DEV/config/config.json

# Should show: "motion_only": true

# If false, enable in dashboard:
# Settings → Camera & Recording → ✓ Enable Motion Recording
```

---

### Fix 3: Storage Shows "0.0 GB" or Dashes

**Problem**: Storage API not returning data

```bash
# Check recordings path exists
cat ~/ME_CAM-DEV/config/config.json | grep recordings_dir

# Should show path like: ~/ME_CAM-DEV/recordings

# Verify directory exists:
ls -la ~/ME_CAM-DEV/recordings/

# Create if missing:
mkdir -p ~/ME_CAM-DEV/recordings
chmod 755 ~/ME_CAM-DEV/recordings

# Test API manually:
curl http://localhost:8080/api/storage

# Should return JSON with numbers
```

**If dashboard still shows dashes:**
1. Open browser console (F12)
2. Look for JavaScript errors
3. Try hard refresh: **Ctrl + Shift + R** (Windows) or **Cmd + Shift + R** (Mac)

---

### Fix 4: "Connection Refused" or Can't Access Dashboard

```bash
# Check Flask running
sudo netstat -tulpn | grep 8080

# If nothing shown, service not running:
sudo systemctl start mecamera

# Check firewall (should not block on local network):
sudo iptables -L | grep 8080

# Test from Pi itself:
curl http://localhost:8080

# Should return HTML (dashboard page)
```

---

### Fix 5: SD Card Full / No Space

```bash
# Check disk space
df -h

# If SD card full (100%):
# Delete old recordings:
rm ~/ME_CAM-DEV/recordings/motion_*.mp4

# Or use dashboard:
# Open http://raspberrypi.local:8080
# Scroll to Recordings → 🗑️ Clear All Recordings

# Set auto-cleanup in settings:
# Settings → Storage Retention → 7 days
# Old files automatically deleted
```

---

## ✅ COMPLETE VERIFICATION CHECKLIST

Run these in order. Stop at first failure and fix before continuing.

```bash
# === ON RASPBERRY PI === (ssh pi@raspberrypi.local)

# 1. Service running?
sudo systemctl status mecamera | grep "active (running)"

# 2. Camera detected?
libcamera-still --list-cameras | grep "Available cameras"

# 3. Recordings directory exists?
ls -la ~/ME_CAM-DEV/recordings/

# 4. Disk space available?
df -h | grep "/dev/root"

# 5. Flask on port 8080?
sudo netstat -tulpn | grep 8080

# 6. Storage API working?
curl http://localhost:8080/api/storage | grep "ok"

# 7. Motion service started?
grep "Motion detection service started" ~/ME_CAM-DEV/logs/mecam.log

# 8. No critical errors?
sudo journalctl -u mecamera -n 50 --no-pager | grep -i "error\|fail\|critical"
```

**If ALL checks pass**, test from your PC browser:
- Open: http://raspberrypi.local:8080
- Should see live camera feed
- Should see storage numbers
- Wave hand → recording created

---

## 📞 QUICK DIAGNOSTIC SCRIPT

Run this one-liner to check everything:

```bash
ssh pi@raspberrypi.local << 'EOF'
echo "=== ME_CAM DIAGNOSTIC ==="
echo ""
echo "1. Service Status:"
sudo systemctl is-active mecamera
echo ""
echo "2. Camera Hardware:"
libcamera-still --list-cameras 2>&1 | head -3
echo ""
echo "3. Recordings Directory:"
ls -la ~/ME_CAM-DEV/recordings/ 2>&1 | head -5
echo ""
echo "4. Disk Space:"
df -h | grep "/dev/root"
echo ""
echo "5. Port 8080:"
sudo netstat -tulpn | grep 8080
echo ""
echo "6. Recent Logs (last 10 lines):"
tail -10 ~/ME_CAM-DEV/logs/mecam.log
echo ""
echo "=== END DIAGNOSTIC ==="
EOF
```

Copy output and check for errors.

---

## 🆘 LAST RESORT: FULL RESET

If nothing works, nuclear option:

```bash
# SSH into Pi
ssh pi@raspberrypi.local

# Stop service
sudo systemctl stop mecamera

# Backup recordings (if any)
cp -r ~/ME_CAM-DEV/recordings ~/recordings_backup

# Pull latest code
cd ~/ME_CAM-DEV
git stash  # Save local changes
git pull origin main

# Recreate directories
mkdir -p ~/ME_CAM-DEV/recordings
chmod 755 ~/ME_CAM-DEV/recordings

# Restart service
sudo systemctl start mecamera
sleep 10

# Check status
sudo systemctl status mecamera
tail -f ~/ME_CAM-DEV/logs/mecam.log
```

Then configure in dashboard:
1. Open: http://raspberrypi.local:8080
2. Enable motion recording
3. Test with hand wave

---

## 📧 NEED MORE HELP?

If still not working, gather this info:

```bash
# Run on Pi and save output:
ssh pi@raspberrypi.local << 'EOF' > ~/mecam_debug.txt
echo "=== FULL DEBUG INFO ==="
echo ""
echo "System:"
uname -a
echo ""
echo "Service Status:"
sudo systemctl status mecamera
echo ""
echo "Camera:"
libcamera-still --list-cameras
echo ""
echo "Disk:"
df -h
echo ""
echo "Port:"
sudo netstat -tulpn | grep 8080
echo ""
echo "Config:"
cat ~/ME_CAM-DEV/config/config.json
echo ""
echo "Logs (last 100):"
tail -100 ~/ME_CAM-DEV/logs/mecam.log
echo ""
echo "=== END DEBUG ==="
EOF

# Copy to PC:
scp pi@raspberrypi.local:~/mecam_debug.txt .

# Review mecam_debug.txt for errors
```

---

## 🎯 MOST LIKELY CAUSES

Based on your symptoms:

**1. Service not running** → `sudo systemctl start mecamera`
**2. Old code deployed** → `git pull origin main` + restart
**3. Recordings dir missing** → `mkdir -p ~/ME_CAM-DEV/recordings`
**4. Motion disabled in config** → Enable in dashboard settings
**5. Camera hardware issue** → Check cable, reboot Pi

Start with Step 1-3 above, that fixes 90% of issues!
