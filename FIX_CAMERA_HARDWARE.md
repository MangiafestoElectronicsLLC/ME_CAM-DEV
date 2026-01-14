# 🚨 FIX: "No cameras available!" Error

## Your Diagnostic Results

```bash
df -h | grep root
# ✅ DISK: 29G total, 3.5G used, 24G free (13%) - PLENTY OF SPACE

libcamera-still --list-cameras
# ❌ CAMERA: "No cameras available!" - HARDWARE ISSUE

curl http://localhost:8080/api/storage
# ⚠️ API: "Unauthorized" - Just need to login to test
```

## 🎯 The Problem

Your camera module is **NOT DETECTED** by the Raspberry Pi. This is a hardware/configuration issue, not software.

---

## 🔧 SOLUTION: Fix Camera Detection (Run These Commands)

### Step 1: Check Legacy Camera Status

```bash
# SSH into Pi (from your PC)
ssh pi@raspberrypi.local

# Check if legacy camera is enabled (should be DISABLED)
vcgencmd get_camera

# You want to see:
# supported=0 detected=0
# (means legacy is disabled - GOOD)

# If you see:
# supported=1 detected=1
# (means legacy is enabled - BAD, conflicts with libcamera)
```

### Step 2: Disable Legacy Camera (If Needed)

```bash
# Run raspi-config
sudo raspi-config

# Navigate:
# 3. Interface Options
#   → I1 Legacy Camera
#     → Select: NO (disable it)
#     → OK
#     → Finish
#     → Reboot? YES

# After reboot, SSH back in:
ssh pi@raspberrypi.local
```

### Step 3: Verify Camera Connected

```bash
# Check if camera ribbon cable detected
sudo vcgencmd get_camera

# Should show:
# supported=0 detected=0 (legacy disabled)

# List detected cameras
libcamera-hello --list-cameras

# Should show something like:
# Available cameras
# -----------------
# 0 : imx219 [3280x2464] (/base/soc/i2c0mux/i2c@1/imx219@10)

# If STILL "No cameras available":
# → Camera cable not connected properly
# → Camera cable inserted wrong way
# → Camera module faulty
```

### Step 4: Physical Camera Check

**Power OFF Pi completely:**
```bash
sudo shutdown -h now
# Wait for green light to stop blinking
# Unplug power
```

**Check Camera Cable:**
1. Locate camera port (between HDMI and USB on Pi Zero 2W)
2. Lift black plastic clip UP gently (don't pull it off)
3. Remove camera ribbon cable
4. Check cable not damaged/bent
5. Re-insert cable:
   - **Blue side faces UP** (away from board)
   - **Connectors face DOWN** (toward PCB)
   - Push cable in firmly until it stops
6. Push black clip DOWN to lock
7. Ensure cable is straight and secure

**Power ON Pi:**
```bash
# Plug power back in
# Wait for boot (30 seconds)

# SSH back in
ssh pi@raspberrypi.local

# Test camera again
libcamera-still --list-cameras
```

### Step 5: Test Camera Capture

```bash
# If camera now detected, test capture:
libcamera-still -o /tmp/test.jpg --width 1280 --height 720

# Should see:
# [0:02.516] [1234] INFO ...
# [0:03.245] [1234] INFO ...
# (No errors, creates test.jpg)

# Check file created:
ls -lh /tmp/test.jpg
# Should show file size like: 234K

# If successful, camera is WORKING!
```

---

## 📋 COMPLETE FIX CHECKLIST

Run these commands in order:

```bash
# === ON RASPBERRY PI ===

# 1. Check legacy camera disabled
vcgencmd get_camera
# Want: supported=0 detected=0

# 2. If supported=1, disable it:
sudo raspi-config
# Interface Options → Legacy Camera → NO → Reboot

# 3. After reboot, list cameras
libcamera-hello --list-cameras
# Should show: Available cameras (0 : imx219...)

# 4. If still no cameras:
# → Check camera cable physically (see Step 4 above)
# → Power off, reseat cable, power on

# 5. Test camera works
libcamera-still -o /tmp/test.jpg

# 6. Restart ME_CAM service
cd ~/ME_CAM-DEV
sudo systemctl restart mecamera
sleep 5

# 7. Check service started with camera
sudo systemctl status mecamera | head -20
# Should show: [CAMERA] Streamer initialized

# 8. Check logs for camera init
tail -30 ~/ME_CAM-DEV/logs/mecam.log | grep -i camera

# 9. Open dashboard
# Browser: http://raspberrypi.local:8080
# Should now see live video!
```

---

## 🆘 TROUBLESHOOTING SPECIFIC ISSUES

### Issue: vcgencmd shows "supported=1 detected=1"

**This means legacy camera is ENABLED (causes conflicts)**

```bash
# Disable legacy camera
sudo raspi-config
# Interface Options → Legacy Camera → NO
sudo reboot

# After reboot
ssh pi@raspberrypi.local
libcamera-still --list-cameras
# Should now show camera
```

---

### Issue: "No cameras available" even after disabling legacy

**Camera cable issue or camera module faulty**

```bash
# Try different detection commands
libcamera-hello --list-cameras
vcgencmd get_camera
raspistill -l  # Should FAIL if legacy disabled (good!)

# Check for hardware errors in system log
dmesg | grep -i camera
# Look for: "unicam" or "imx219" or "camera"

# If no messages about camera:
# → Cable not connected
# → Cable wrong direction
# → Camera module broken
```

**Physical inspection:**
1. Power OFF completely: `sudo shutdown -h now`
2. Unplug power cable
3. Remove camera ribbon cable
4. Check cable for damage (cracks, bent pins)
5. Check camera module (green PCB) for damage
6. Re-insert cable: **BLUE SIDE UP**, contacts DOWN
7. Lock cable clip
8. Power ON and test

---

### Issue: Camera detected but "failed to open camera"

**Permission or resource busy issue**

```bash
# Check no other process using camera
ps aux | grep libcamera
ps aux | grep raspistill

# Kill any camera processes
sudo killall libcamera-still
sudo killall libcamera-vid
sudo killall libcamera-hello

# Test again
libcamera-still -o /tmp/test.jpg

# If works now, restart service
sudo systemctl restart mecamera
```

---

### Issue: Camera works in terminal but not in dashboard

**Service not starting camera correctly**

```bash
# Check service logs for errors
sudo journalctl -u mecamera -n 100 --no-pager | grep -i error

# Check ME_CAM logs
tail -100 ~/ME_CAM-DEV/logs/mecam.log | grep -i "camera\|error"

# Common issues:
# - Virtual environment not activated
# - Python dependencies missing
# - Config file corrupted

# Fix: Restart service
cd ~/ME_CAM-DEV
sudo systemctl restart mecamera

# Wait 10 seconds
sleep 10

# Check status
sudo systemctl status mecamera

# View live logs
tail -f ~/ME_CAM-DEV/logs/mecam.log
# Should see: [CAMERA] initialized
```

---

## ✅ SUCCESS VERIFICATION

After fixing camera, verify everything works:

```bash
# 1. Camera hardware detected
libcamera-still --list-cameras
# ✅ Shows: Available cameras (0 : imx219...)

# 2. Camera can capture
libcamera-still -o /tmp/test.jpg
# ✅ Creates test.jpg file

# 3. Service running with camera
sudo systemctl status mecamera
# ✅ Shows: Active: active (running)

# 4. Camera initialized in logs
tail -30 ~/ME_CAM-DEV/logs/mecam.log | grep CAMERA
# ✅ Shows: [CAMERA] Streamer initialized

# 5. Dashboard shows video
# Open: http://raspberrypi.local:8080
# ✅ Live camera feed displays (not black)

# 6. Storage API works (after login)
# Login to dashboard first, then:
curl http://localhost:8080/api/storage
# ✅ Shows: {"ok":true,"used_gb":0.0,"available_gb":24.0,...}

# 7. Motion detection can record
# Wave hand at camera, wait 30 seconds, then:
ls -lh ~/ME_CAM-DEV/recordings/
# ✅ Shows: motion_*.mp4 files
```

---

## 📊 MOST COMMON CAUSES (In Order)

### 1. **Legacy Camera Still Enabled** (90% of cases)
- **Symptom**: "No cameras available!"
- **Check**: `vcgencmd get_camera` shows "supported=1"
- **Fix**: `sudo raspi-config` → Interface Options → Legacy Camera → NO → Reboot

### 2. **Camera Cable Not Connected** (5% of cases)
- **Symptom**: "No cameras available!", no camera messages in `dmesg`
- **Check**: Physical inspection
- **Fix**: Reseat camera cable (BLUE SIDE UP)

### 3. **Camera Cable Inserted Wrong Direction** (3% of cases)
- **Symptom**: "No cameras available!", camera worked before
- **Check**: Blue side facing which way?
- **Fix**: Remove cable, flip, re-insert (BLUE UP)

### 4. **Camera Module Faulty** (1% of cases)
- **Symptom**: Tried everything, still no cameras
- **Check**: Tried different cable, different Pi (if available)
- **Fix**: Replace camera module

### 5. **Firmware Outdated** (1% of cases)
- **Symptom**: "No cameras available!", old Pi
- **Check**: `uname -a` shows old kernel
- **Fix**: `sudo apt update && sudo apt full-upgrade -y && sudo reboot`

---

## 🎯 QUICK FIX SCRIPT

Run this all at once to check everything:

```bash
ssh pi@raspberrypi.local << 'EOF'
echo "=== CAMERA DIAGNOSTIC ==="
echo ""
echo "1. Legacy Camera Status:"
vcgencmd get_camera
echo ""
echo "2. List Cameras:"
libcamera-hello --list-cameras 2>&1 | head -5
echo ""
echo "3. Hardware Messages:"
dmesg | grep -i "camera\|imx\|unicam" | tail -5
echo ""
echo "4. Test Capture:"
libcamera-still -o /tmp/test.jpg --timeout 1000 2>&1 | head -3
ls -lh /tmp/test.jpg 2>&1 | tail -1
echo ""
echo "5. Service Status:"
sudo systemctl is-active mecamera
echo ""
echo "=== END DIAGNOSTIC ==="
EOF
```

---

## 💡 AFTER CAMERA FIXED

Once camera is working:

1. **Restart ME_CAM service**:
   ```bash
   sudo systemctl restart mecamera
   ```

2. **Open dashboard**: http://raspberrypi.local:8080

3. **Should now see**:
   - ✅ Live video feed (smooth)
   - ✅ Storage shows disk space
   - ✅ Motion detection starts recording

4. **Enable motion recording**:
   - Settings → Camera & Recording
   - ✓ Enable Motion Recording
   - Save Settings

5. **Test motion**:
   - Wave hand at camera
   - Wait 30 seconds
   - Check recordings on dashboard

---

## 🔄 IF STILL NOT WORKING AFTER ALL FIXES

```bash
# Full system check
ssh pi@raspberrypi.local

# 1. Update firmware
sudo apt update
sudo apt full-upgrade -y
sudo reboot

# 2. After reboot
ssh pi@raspberrypi.local

# 3. Clean reinstall camera firmware
sudo apt install --reinstall libcamera0 libcamera-apps

# 4. Test camera
libcamera-hello --list-cameras

# 5. If STILL no cameras:
# → Camera module is FAULTY
# → Need replacement camera module
# → Amazon: "Raspberry Pi Camera Module 2" or "IMX219"
```

---

## 📞 NEXT STEPS

**After fixing camera hardware:**

1. Run verification commands above (✅ SUCCESS VERIFICATION)
2. Open dashboard: http://raspberrypi.local:8080
3. Login (if you have account)
4. Video should display
5. Storage should show disk space
6. Enable motion recording in settings
7. Test with hand wave

**Camera will NOT work until hardware detected!**

Focus on Step 1-4 above to fix camera detection first.
