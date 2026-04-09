# Quick Device Update - Copy & Paste Commands

## For Device 1 & 2 (Local SSH)

### From your PC Command Line:

```powershell
# Device 1
ssh pi@<device1-hostname-or-ip> "cd ~/ME_CAM-DEV && git pull origin main && pkill -f 'python.*main_lite.py'; sleep 2 && source venv/bin/activate && nohup python main_lite.py > /tmp/mecam.log 2>&1 & sleep 3 && echo 'Device 1 Updated!'"

# Device 2  
ssh pi@<device2-hostname-or-ip> "cd ~/ME_CAM-DEV && git pull origin main && pkill -f 'python.*main_lite.py'; sleep 2 && source venv/bin/activate && nohup python main_lite.py > /tmp/mecam.log 2>&1 & sleep 3 && echo 'Device 2 Updated!'"
```

### Or SSH into each device and run:

```bash
cd ~/ME_CAM-DEV
git pull origin main
pkill -f 'python.*main_lite.py'
sleep 2
source venv/bin/activate
nohup python main_lite.py > /tmp/mecam.log 2>&1 &
sleep 3
ps aux | grep 'python.*main_lite' | grep -v grep && echo "✓ App Running" || echo "✗ App Failed"
```

---

## For Device 3 Camera Fix

### SSH into Device 3:

```bash
# Power down
sudo shutdown -h now

# (Wait 30 seconds, physically reseat cable, power back on)

# SSH back in and test
vcgencmd get_camera

# Should show: supported=1 detected=1
# If detected=0, it's the tape/connector issue
```

### If you see `detected=1`:

```bash
# Test camera
rpicam-hello --list-cameras

# Should show IMX519 details

# Test preview (5 seconds)
rpicam-hello -t 5000

# Restart ME_CAM app
cd ~/ME_CAM-DEV
source venv/bin/activate
pkill -f 'python.*main_lite.py'
python main_lite.py &

# Check web dashboard at http://<device3-ip>:8080
```

### If still `detected=0`:

The ESD tape isn't providing good contact. Options:
1. **Print a CSI clip** - Thingiverse "Pi Zero CSI camera clip"
2. **Buy a connector clamp** - ~$3-5 from Amazon
3. **Use thermal conductive tape** - Better than regular ESD tape

---

## Device Hostnames (if available via .local)

Based on your app showing "ME_CAM_3":

```
Device 1: ME_CAM_1.local  or  mecamdev1.local
Device 2: ME_CAM_2.local  or  mecamdev2.local  
Device 3: ME_CAM_3.local  or  mecamdev3.local
```

---

## Current GitHub Status

**Latest Commit:** e631661 (Jan 25, 2026)
**Files Updated:** `web/app_lite.py`

**What's Fixed:**
- ✅ First-run setup form renders without errors
- ✅ All config fields now properly defined
- ✅ Setup form save/submit works correctly

---

## Verify Update Success

After running update script, check:

```bash
# 1. App is running
ps aux | grep 'python.*main_lite' | grep -v grep

# 2. Web server responding
curl -s http://localhost:8080/ | head -5

# 3. Check latest code
git log -1 --oneline

# 4. Camera detection
vcgencmd get_camera
```

All should show green checkmarks!
