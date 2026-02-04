# Quick Deployment Guide - ME_CAM v2.1.1

## For Your Customers - Easy 5-Step Setup

### Step 1: Install on Fresh Raspberry Pi

Using Raspberry Pi Imager:
- Choose: Raspberry Pi OS Lite (32-bit)
- Enable SSH during configuration
- Set WiFi credentials

### Step 2: SSH and Clone

```bash
ssh pi@raspberrypi.local
cd ~
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV
```

### Step 3: Run Installer (Auto-Handles Everything)

```bash
sudo bash -c '
apt update && apt install -y python3-pip python3-venv git
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt
'
```

### Step 4: First Run Configuration

```bash
source venv/bin/activate
python3 main.py
```

Then visit: `http://raspberrypi.local:8080`

The app will:
- ✅ Auto-detect Pi model
- ✅ Auto-detect camera type  
- ✅ Auto-rotate if needed (IMX519 on Pi Zero)
- ✅ Select optimal mode (LITE or FULL)
- ✅ Show first-run setup wizard

### Step 5: Enable Auto-Start

```bash
sudo nano /etc/systemd/system/mecamera.service
```

Paste:
```ini
[Unit]
Description=ME_CAM Security Camera
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ME_CAM-DEV
Environment="PATH=/home/pi/ME_CAM-DEV/venv/bin:/usr/bin:/bin"
ExecStart=/home/pi/ME_CAM-DEV/venv/bin/python3 /home/pi/ME_CAM-DEV/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mecamera
sudo systemctl start mecamera
```

## Verification

Check if working:
```bash
# Logs (should show hardware detection)
sudo journalctl -u mecamera -n 50

# Test camera
libcamera-hello -t 5

# Test stream
curl http://localhost:8080/stream -H "Range: bytes=0-10000" | hexdump -C | head
```

## What's Fixed in v2.1.1

### 1. Motion Detection ✅
- Events logged immediately (no delays)
- Automatic debouncing (no duplicates)
- Video attached automatically

### 2. Audio Recording ✅  
- No more hangs on Pi Zero 2W
- Graceful fallback if fails
- Proper timeout handling

### 3. Video Rotation ✅
- IMX519 auto-rotated 180° on Pi Zero
- OV5647 handled correctly
- Custom rotation in config

### 4. Alerts ✅
- Queue system for reliability
- Automatic retry (2, 4, 8, 16 min delays)
- Works offline + syncs when WiFi returns
- Rate limiting prevents spam

### 5. Hardware ✅
- Auto-selects LITE mode for Pi Zero 2W
- Auto-selects FULL mode for Pi 4/5
- Optimal frame rate & resolution per device
- Detects camera type & capabilities

### 6. Updates ✅
- Checks GitHub automatically on startup
- Shows update available in logs
- Safe download & backup system

## Customer Support - Key Commands

### Check Status
```bash
sudo systemctl status mecamera
```

### Restart
```bash
sudo systemctl restart mecamera
```

### View Live Logs
```bash
sudo journalctl -u mecamera -f
```

### Find Pi IP Address
```bash
hostname -I
```

### Test Motion Detection
```bash
# Walk in front of camera
sudo journalctl -u mecamera -f | grep MOTION

# You should see: "Motion logged: motion (95%) - abc123"
```

### Test Alert System
```bash
# Check notification queue
cat ~/ME_CAM-DEV/logs/notification_queue.json | jq .

# Should show queued notifications
```

### Clear Old Events
```bash
curl -X POST http://localhost:8080/api/motion/clear \
  -H "Content-Type: application/json" \
  -d '{}' \
  -b "session=your_session"
```

## Troubleshooting Checklist

❌ **Camera not working**
```bash
libcamera-hello -t 5  # Should show live preview
# If not: hardware issue, check ribbon cable

# Check logs:
sudo journalctl -u mecamera | grep CAMERA
```

❌ **No motion detection**
```bash
# Walk in front of camera 30 seconds
# Check: sudo journalctl -u mecamera | grep MOTION
# Should see events logged with "[MOTION] ✓ Event logged..."
```

❌ **Alerts not sending**
```bash
# Check config:
grep sms ~/ME_CAM-DEV/config/config.json

# Check queue:
cat ~/ME_CAM-DEV/logs/notification_queue.json | head

# Must have sms_enabled=true AND sms_api_url configured
```

❌ **Very slow / high CPU**
```bash
# Check what mode it selected:
sudo journalctl -u mecamera | grep "LITE\|FULL"

# Check RAM:
free -h

# If Pi Zero 2W: Should be LITE mode (slower = normal)
```

❌ **Audio not recording**
```bash
# Audio is optional - videos work without audio
# To enable audio:

# Check if arecord installed:
which arecord

# If not:
sudo apt install alsa-utils

# Restart:
sudo systemctl restart mecamera
```

## Important Notes for Customers

### RAM Usage
- **Pi Zero 2W:** 150-200MB (app), 200MB (OS) = 400MB total ✓
- **Pi 3/4:** 300MB (app), 300MB (OS) = 600MB total ✓
- **Pi 5:** Can handle 8K cameras + multiple streams

### Storage
- 1 minute of motion video ≈ 2-5MB
- Auto-cleanup after 7 days (configurable)
- 32GB SD card = ~200 hours of motion footage

### Performance
- **Pi Zero 2W:** 15-20 FPS, 640x480, streaming only
- **Pi 3/4:** 20-30 FPS, 1280x720, with motion + alerts
- **Pi 5:** 30-60 FPS, 1920x1080, multiple cameras possible

### WiFi
- Requires 2.4GHz (Pi Zero 2W doesn't support 5GHz)
- Minimum ~5Mbps for streaming
- Alert queue works offline, syncs when WiFi returns

## Version & Updates

**Current:** v2.1.1 (Feb 2, 2026)

**Check for updates:**
```bash
# Automatic: Checked on startup
# Manual: 
git pull origin main
sudo systemctl restart mecamera
```

**Upgrade steps:**
```bash
cd ~/ME_CAM-DEV
git pull origin main
source venv/bin/activate
pip install -r requirements.txt  # Install any new packages
sudo systemctl restart mecamera
sudo journalctl -u mecamera -n 20  # Verify it started
```

## Warranty Notes

This v2.1.1 release includes:
- ✅ Motion detection fixes (no missed events)
- ✅ Audio stability improvements
- ✅ Automatic hardware detection
- ✅ Notification retry system
- ✅ Update checker

Tested on:
- ✅ Raspberry Pi Zero 2W with IMX519
- ✅ Raspberry Pi 3B/4B with OV5647 & IMX219
- ✅ Raspberry Pi 5 (high-end mode)

## Contact & Support

Issues? Check GitHub: https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV

Most common issues resolved by:
1. Check logs: `sudo journalctl -u mecamera -f`
2. Restart: `sudo systemctl restart mecamera`
3. Update: `cd ~/ME_CAM-DEV && git pull && sudo systemctl restart mecamera`

---

**Deploy Date:** February 2, 2026  
**Version:** 2.1.1  
**Status:** Production Ready  
**Support:** Community & GitHub Issues
