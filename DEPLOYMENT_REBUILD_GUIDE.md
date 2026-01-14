# 🚀 ME_CAM v2.0 - Complete Deployment & Rebuild Guide
## With All Latest Mods & Features

**Last Updated:** January 14, 2026
**Status:** Ready for Pi Zero 2W Deployment
**Features Included:** Motion logging, encrypted security, dashboard modals, quality selection, multi-device support

---

## 📋 PART 1: PRE-DEPLOYMENT CHECKLIST

### Local Development Status ✅
- [x] Organized src/core, src/camera, src/detection structure created
- [x] Motion event logging system implemented (motion_logger.py)
- [x] Dashboard enhancements with modals for motion/storage/recordings
- [x] Stream quality selector (4 presets: low/standard/high/ultra)
- [x] Multi-device dashboard enhanced (multicam.html)
- [x] AES-256 encryption module created (secure_encryption.py)
- [x] API endpoints created (7+ motion, storage, quality, device endpoints)
- [x] Deployment script ready (deploy_pi_zero.sh)
- [x] Configuration structure with quality presets
- [x] All documentation updated

### Pi Deployment Status 🔴
- [ ] SSH connection to Pi working
- [ ] Backup of old codebase created
- [ ] New v2.0 structure deployed to Pi
- [ ] Dependencies installed on Pi
- [ ] systemd service created and enabled
- [ ] Motion logging integrated with detection pipeline
- [ ] Camera display issue diagnosed and fixed
- [ ] All features tested end-to-end

---

## 🔧 PART 2: FIX PI CONNECTION

### Step 1: Find Your Pi's IP Address

```bash
# On Windows PowerShell:
ping raspberrypi.local
```

**Expected Output:**
```
Reply from 192.168.x.x: bytes=32 time=xx ms
```

If it fails, try these alternatives:

```bash
# Check your router's connected devices for "raspberrypi"
# Or scan the network:
nmap -p 22 192.168.1.0/24  # Adjust to your subnet

# Or use:
arp -a | findstr /i "raspberry"
```

### Step 2: Clean SSH Known Hosts

If you get "Host key verification failed":

```bash
# Remove old Pi host key
ssh-keygen -R raspberrypi.local
ssh-keygen -R 10.2.1.47
ssh-keygen -R 192.168.x.x   # Try your found IP

# Clear entire known_hosts if needed (WARNING: removes all stored keys)
Remove-Item $env:USERPROFILE\.ssh\known_hosts
```

### Step 3: Connect to Pi

```bash
# Use the IP you found:
ssh pi@raspberrypi.local
# or
ssh pi@192.168.x.x
```

**Troubleshooting Connection:**
- Pi offline? Check power and WiFi connection on Pi's screen
- Wrong password? Default is usually: `raspberry` (for fresh install)
- Can't find IP? Connect monitor to Pi and check network settings

---

## 💾 PART 3: BACKUP OLD CODEBASE (IMPORTANT!)

**Once SSH is working**, backup the old code:

```bash
ssh pi@raspberrypi.local

# Backup existing ME_CAM-DEV
cd ~
tar czf ME_CAM-DEV.backup.$(date +%Y%m%d_%H%M%S).tar.gz ME_CAM-DEV/

# Verify backup created
ls -lh ME_CAM-DEV.backup.*

# Backup system config too
tar czf mecamera-config.backup.tar.gz ME_CAM-DEV/config/
```

**Keep these backups safe!** You can restore if something goes wrong.

---

## 🚀 PART 4: DEPLOY NEW v2.0 STRUCTURE

### Step 4.1: Copy New Code to Pi

**Option A: Using Git (Recommended)**

```bash
ssh pi@raspberrypi.local

# If ME_CAM-DEV already exists, rename the old one
cd ~
mv ME_CAM-DEV ME_CAM-DEV.old
rm -rf ME_CAM-DEV  # Or keep the backup

# Clone fresh repository
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV
```

**Option B: Using SCP (Direct Copy from Your PC)**

```powershell
# On your Windows PC (PowerShell):
$PI_IP = "raspberrypi.local"  # or your Pi's IP
$PI_USER = "pi"

# Remove old directory on Pi
ssh $PI_USER@$PI_IP "rm -rf ~/ME_CAM-DEV"

# Copy new code
scp -r "C:\Users\nickp\Downloads\ME_CAM-DEV\ME_CAM-DEV" ${PI_USER}@${PI_IP}:~/
```

### Step 4.2: Run Automated Setup Script

```bash
ssh pi@raspberrypi.local
cd ~/ME_CAM-DEV

# Make setup script executable
chmod +x scripts/setup.sh

# Run setup (this installs everything!)
./scripts/setup.sh
```

**What setup.sh does:**
- Updates system packages
- Creates Python virtual environment
- Installs all Python dependencies
- Creates `mecamera` system user
- Sets up systemd service
- Creates logs/ and recordings/ directories
- Sets proper permissions

### Step 4.3: Install Fast Camera Support (15x Faster!)

```bash
# This installs picamera2 for 15-30 FPS streaming
sudo ./scripts/install_fast_camera.sh
```

⚠️ **Note:** This step takes 5-10 minutes on Pi Zero 2W. Be patient!

### Step 4.4: Enable Autoboot Service

```bash
# Enable the mecamera service
sudo systemctl enable mecamera
sudo systemctl start mecamera

# Verify it's running
sudo systemctl status mecamera

# Expected output:
# ● mecamera.service - ME_CAM v2.0
#    Loaded: loaded (/etc/systemd/system/mecamera.service)
#    Active: active (running)
#    [MAIN] Flask app started
#    [CAMERA] Fast streamer initialized
```

---

## 🎯 PART 5: VERIFY DEPLOYMENT

### Check Service Logs

```bash
# Real-time logs (press Ctrl+C to exit)
sudo journalctl -u mecamera -f

# Or check last 50 lines
sudo journalctl -u mecamera -n 50 --no-pager

# Expected entries:
# [MAIN] Flask app started
# [MOTION] Motion detection service started
# [CAMERA] Fast streamer initialized
# [MOTION] Motion check every 0.2 seconds
```

### Test Camera Hardware

```bash
# Verify camera detected
libcamera-still --list-cameras

# Should show:
# Available cameras
# 0 : imx219 [3280x2464]
# ... (or whatever camera you have)
```

### Check Web Dashboard

```bash
# On your PC, open browser:
http://raspberrypi.local:8080
# or
http://192.168.x.x:8080
```

**Expected:**
- Dashboard loads
- Camera stream shows live video
- Real-time stats show (storage, battery, etc.)

### Test API Endpoints

```bash
# From your PC, test motion logging API:
curl http://raspberrypi.local:8080/api/motion/events

# Should return JSON with motion events
# If empty: {}
# If full: [{"timestamp":"2026-01-14T...","type":"motion","confidence":0.85...}]
```

---

## 🎬 PART 6: FIX CAMERA DISPLAY ISSUE ("No Display Still")

### Diagnosis Flowchart

**Step 1: Is the service running?**
```bash
sudo systemctl status mecamera
# If not running: sudo systemctl start mecamera
# Check logs: sudo journalctl -u mecamera -n 20
```

**Step 2: Is the camera detected?**
```bash
libcamera-still --list-cameras
# If "No cameras available":
#   - Check cable connection
#   - Check raspi-config: Legacy camera should be DISABLED
#   - Reboot: sudo reboot
```

**Step 3: Is fast streaming enabled?**
```bash
# Check config
grep "use_fast_streamer" ~/ME_CAM-DEV/config/config.json

# If false or missing, enable it:
sudo nano ~/ME_CAM-DEV/config/config.json
# Change: "use_fast_streamer": true
# Press Ctrl+X, Y, Enter to save
# Restart: sudo systemctl restart mecamera
```

**Step 4: Test streaming directly**
```bash
# SSH to Pi and run:
python3 ~/ME_CAM-DEV/src/camera/fast_camera_streamer.py

# Should output camera initialization messages
# If error: check camera cable and libcamera installation
```

**Step 5: Check camera permissions**
```bash
# Camera should be accessible by mecamera user
ls -l /dev/video*

# If permission denied, add user to video group:
sudo usermod -aG video mecamera
sudo systemctl restart mecamera
```

### Solution Checklist
- [ ] Camera cable properly connected and locked
- [ ] Legacy camera DISABLED in raspi-config
- [ ] Camera permission fixed (mecamera in video group)
- [ ] Fast streaming ENABLED in config
- [ ] picamera2 library installed (`sudo ./scripts/install_fast_camera.sh`)
- [ ] Service restarted after changes (`sudo systemctl restart mecamera`)

---

## 📊 PART 7: VERIFY MOTION LOGGING

### Check Motion Events Are Saved

```bash
# Check if events file exists and has data
cat ~/ME_CAM-DEV/logs/motion_events.json

# Should show:
# [
#   {"timestamp":"2026-01-14T10:30:45.123456","type":"motion","confidence":0.87,...},
#   {"timestamp":"2026-01-14T10:31:02.456789","type":"motion","confidence":0.92,...}
# ]

# If empty [], motion detection might not be running
```

### Test Motion Detection

```bash
# SSH to Pi and check motion service logs
sudo journalctl -u mecamera | grep -i motion

# Should show:
# [MOTION] Motion detected at 2026-01-14 10:30:45 (confidence: 0.87)
# [MOTION] Recording motion event...
# [MOTION] Motion check complete
```

### Generate Test Motion Event

```bash
# Wave your hand in front of camera for 5 seconds
# Then check:
cat ~/ME_CAM-DEV/logs/motion_events.json | tail -20

# Should show new events with your timestamp
```

### Test Motion API

```bash
# On your PC, curl the motion API:
curl http://raspberrypi.local:8080/api/motion/events

# Should return recent motion events with timestamps

# Get statistics:
curl http://raspberrypi.local:8080/api/motion/stats

# Should show event count, average confidence, etc.
```

---

## 🎨 PART 8: DASHBOARD FEATURES & CUSTOMIZATION

### View Motion Events on Dashboard

1. **Open dashboard:** `http://raspberrypi.local:8080`
2. **Look for Motion section** with "View Motion Log" button
3. **Click the button** → Modal shows all events from last 24 hours
4. **Each event shows:** Timestamp, confidence level, event type

### View Storage Details

1. **Dashboard → Storage section**
2. **Click "View Storage Details"** button
3. **Modal shows:**
   - Used GB / Total GB
   - Retention policy (7 days default)
   - Auto-cleanup threshold (90% default)

### Browse & Download Recordings

1. **Dashboard → Recordings section**
2. **Click "Browse Recordings"** button
3. **Modal shows all video files:**
   - Click download icon → Save to PC
   - Click delete icon → Remove from Pi

### Adjust Stream Quality

1. **Dashboard header** has quality dropdown
2. **Options:**
   - Low: 320x240 @ 10 FPS (slowest Pi)
   - Standard: 640x480 @ 15 FPS (default, fast)
   - High: 1280x720 @ 25 FPS (Pi 4 recommended)
   - Ultra: 1920x1080 @ 30 FPS (needs fast connection)
3. **Select quality** → Auto-adjusts streaming
4. **Check CPU usage** in Performance section

### Configure Settings

1. **Dashboard → Settings** (gear icon)
2. **Available sections:**
   - Camera Settings (resolution, FPS, quality)
   - Storage Settings (cleanup threshold, retention days)
   - Motion Settings (sensitivity, recording interval)
   - Emergency Contacts (SMS/email alerts)
   - User Management (passwords, permissions)

---

## 🔐 PART 9: SECURITY & ENCRYPTION

### Enable Encryption

```bash
# Check if encryption enabled
grep "encryption_enabled" ~/ME_CAM-DEV/config/config.json

# Should show: "encryption_enabled": true

# If false, enable it:
sudo nano ~/ME_CAM-DEV/config/config.json
# Change: "encryption_enabled": true
# Save and restart: sudo systemctl restart mecamera
```

### Set Strong Password

```bash
# First login: Use PIN from setup wizard (8 digits)
# Then create user account with strong password:
# 1. Dashboard → Settings → User Management
# 2. Create User Account
# 3. Use password: Uppercase + Lowercase + Numbers + Symbols
# 4. Min 12 characters recommended
```

### Encrypt Recordings

```bash
# Check if new recordings are encrypted
ls -la ~/ME_CAM-DEV/recordings/

# Encrypted files will have .enc extension
# Example: 2026-01-14_10-30-45.h264.enc

# To decrypt a video file:
python3 << EOF
from src.core.secure_encryption import SecureEncryption
enc = SecureEncryption(password="YOUR_PASSWORD")
enc.decrypt_file("recordings/video.h264.enc", "output_video.h264")
EOF
```

### Backup Encryption Keys

```bash
# CRITICAL: Save these securely!
tar czf mecamera-keys.backup.tar.gz ~/.mecamera/keys/
cp mecamera-keys.backup.tar.gz ~/Dropbox/  # or USB drive

# If Pi fails, you can restore with:
tar xzf mecamera-keys.backup.tar.gz -C ~/
```

---

## 📱 PART 10: MULTI-DEVICE SUPPORT

### Add Second Device (Pi)

1. **First Pi (Primary):**
   - IP: `192.168.1.100`
   - Running: mecamera service
   - Accessible: `http://192.168.1.100:8080`

2. **Second Pi:**
   - Flash SD card with Raspberry Pi OS
   - Follow **PART 4: DEPLOY** on second Pi
   - Get its IP: `ping raspberrypi-2.local`

3. **Hub Connection:**
   - Dashboard shows **multi-camera view**
   - Each device shows: Name, Location, Online Status, Last Seen
   - Click device card → Shows live stream from that Pi

4. **Unified Recording Storage:**
   - Videos from all devices can download from main dashboard
   - Or access individually at: `http://secondary-pi-ip:8080`

---

## 🔄 PART 11: UPDATES & MAINTENANCE

### Pull Latest Updates from GitHub

```bash
ssh pi@raspberrypi.local
cd ~/ME_CAM-DEV

# Get latest code
git pull origin main

# Reinstall if dependencies changed
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl restart mecamera

# Check logs
sudo journalctl -u mecamera -n 20
```

### View System Logs

```bash
# Real-time logs
sudo journalctl -u mecamera -f

# Filter by type
sudo journalctl -u mecamera | grep MOTION
sudo journalctl -u mecamera | grep CAMERA
sudo journalctl -u mecamera | grep ERROR

# Save logs to file
sudo journalctl -u mecamera > mecam_logs.txt
```

### Factory Reset (Start Fresh)

```bash
sudo ~/ME_CAM-DEV/scripts/factory_reset.sh

# This will:
# - Delete all recordings
# - Reset configuration to defaults
# - Clear motion event history
# - Disable all custom settings
```

---

## ⚠️ TROUBLESHOOTING

### Dashboard Slow (1-2 FPS instead of 15-30)

```bash
# Check if fast streaming is enabled
grep "use_fast_streamer" ~/ME_CAM-DEV/config/config.json

# If false, enable:
sudo nano ~/ME_CAM-DEV/config/config.json
# Change "use_fast_streamer": true

# Check if picamera2 installed
python3 -c "import picamera2; print('picamera2 OK')"

# If ImportError, install:
sudo ./scripts/install_fast_camera.sh

# Restart service
sudo systemctl restart mecamera
```

### Storage Full Error

```bash
# Check disk usage
df -h

# Manually cleanup old recordings
ls -lht ~/ME_CAM-DEV/recordings/ | tail -20  # See oldest files
rm ~/ME_CAM-DEV/recordings/2026-01-01*.h264  # Delete by date

# Or use API
curl -X POST http://localhost:8080/api/storage/cleanup

# Or dashboard: Settings → Clear All Recordings
```

### Motion Not Detecting

```bash
# Check if motion service running
sudo journalctl -u mecamera | grep MOTION

# Check motion sensitivity setting
grep "motion_sensitivity" ~/ME_CAM-DEV/config/config.json

# Increase sensitivity (0.0-1.0, default 0.6)
sudo nano ~/ME_CAM-DEV/config/config.json
# Change: "motion_sensitivity": 0.4   # More sensitive
# Restart: sudo systemctl restart mecamera
```

### SSH Connection Fails

```bash
# Clear old host keys from PC
ssh-keygen -R raspberrypi.local

# Try with IP instead
ssh pi@192.168.x.x

# Check if Pi is reachable
ping raspberrypi.local

# If still fails, check Pi's IP on its screen or router admin page
```

---

## 📝 PART 12: NEW FEATURES SUMMARY

### Motion Event Logging ✨ NEW
- **What:** Every motion detection saves timestamp + confidence + metadata
- **Where:** `logs/motion_events.json`
- **API:** `/api/motion/events`, `/api/motion/stats`, `/api/motion/export`
- **Dashboard:** Motion Events Modal shows last 24 hours of activity

### Dashboard Modal Tabs ✨ NEW
- **Motion Events:** View all detected motion with timestamps
- **Storage Details:** See used space, retention policy, cleanup threshold
- **Recordings Browser:** Download or delete video files
- **Stream Quality:** 4 presets (Low/Standard/High/Ultra)

### Multi-Device Support ✨ NEW
- **Unified Dashboard:** See all cameras from main device
- **Device Cards:** Show online status, battery %, last seen, recordings
- **Add Device:** QR code or manual IP entry
- **Aggregated Stats:** Total events, combined storage, average battery

### Encryption & Security ✨ NEW
- **AES-256:** All recordings encrypted with strong cipher
- **PBKDF2:** 100,000 iterations key derivation (brute-force resistant)
- **Secure Passwords:** Strong requirement enforced
- **Encrypted Logs:** Sensitive data encrypted at rest

### Quality Selection ✨ NEW
- **4 Presets:** Automatic quality adjustment
- **Low:** 320x240 @ 10 FPS (very low bandwidth)
- **Standard:** 640x480 @ 15 FPS (recommended, Pi Zero 2W)
- **High:** 1280x720 @ 25 FPS (requires good internet)
- **Ultra:** 1920x1080 @ 30 FPS (fiber or local LAN only)

---

## ✅ FINAL CHECKLIST

- [ ] Pi SSH connection working
- [ ] Old codebase backed up
- [ ] New v2.0 code deployed
- [ ] Automated setup.sh completed
- [ ] Fast camera support installed
- [ ] systemd service enabled and running
- [ ] Dashboard accessible at `http://raspberrypi.local:8080`
- [ ] Camera displays live video (not black)
- [ ] Motion events logging to `logs/motion_events.json`
- [ ] Motion Events modal shows data on dashboard
- [ ] Storage Details modal displays usage
- [ ] Recordings Browser shows video files
- [ ] Stream quality dropdown functional
- [ ] Encryption enabled and working
- [ ] Multi-device support tested (if applicable)
- [ ] Logs rotating properly
- [ ] Autoboot working (service survives reboot)

---

## 🆘 NEED HELP?

**Check these first:**
1. Verify logs: `sudo journalctl -u mecamera -n 50`
2. Check config: `cat ~/ME_CAM-DEV/config/config.json`
3. Test camera: `libcamera-still --list-cameras`
4. Test API: `curl http://localhost:8080/api/motion/events`
5. Restart service: `sudo systemctl restart mecamera`

**If stuck:**
- GitHub Issues: https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV/issues
- Email: support@mangiafestoelectronics.com
- Review logs in detail: `sudo journalctl -u mecamera --since "1 hour ago"`

---

**Good luck with your deployment! 🚀 Your ME_CAM v2.0 system should be significantly better than Arlo/Ring with full encryption, no subscriptions, and local-only storage. Let me know when you hit any issues!**
