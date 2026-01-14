# 🔧 ME_CAM v2.0 - Quick Troubleshooting Reference

## Immediate Actions by Problem

### 🔴 Can't SSH to Pi

```bash
# Step 1: Find Pi's IP
ping raspberrypi.local

# Step 2: If that fails, try alternatives:
nmap -p 22 192.168.1.0/24  # scan subnet
arp -a | findstr /i "raspberry"

# Step 3: Clear old SSH keys
ssh-keygen -R raspberrypi.local

# Step 4: Try connecting
ssh pi@[IP_ADDRESS]
# Password: raspberry (default) or your set password
```

### ⬛ Black Screen / No Camera Display

**Quick Fix:**
1. Restart service: `sudo systemctl restart mecamera`
2. Check logs: `sudo journalctl -u mecamera | tail -20`
3. Verify camera: `libcamera-still --list-cameras`
4. Enable fast streaming: Edit `config.json` → `"use_fast_streamer": true`
5. Install fast camera: `sudo ./scripts/install_fast_camera.sh`

### 📊 No Motion Events Logged

```bash
# Check motion service
sudo journalctl -u mecamera | grep MOTION

# Check if motion file exists
cat ~/ME_CAM-DEV/logs/motion_events.json

# If empty, test detection
# Wave hand in front of camera for 5 seconds

# Increase sensitivity in config
grep "motion_sensitivity" ~/ME_CAM-DEV/config/config.json
# Default: 0.6, try 0.4 for more sensitive
```

### 💾 Storage Full

```bash
# Check disk
df -h

# See what's using space
du -sh ~/ME_CAM-DEV/recordings/

# Delete old files
rm ~/ME_CAM-DEV/recordings/2026-01-01*.h264

# Or trigger cleanup API
curl -X POST http://localhost:8080/api/storage/cleanup
```

### 🐌 Dashboard Very Slow (1-2 FPS)

1. Check config: `grep "use_fast_streamer" ~/ME_CAM-DEV/config/config.json`
2. If `false`, change to `true` and restart
3. Install picamera2: `sudo ./scripts/install_fast_camera.sh`
4. Check CPU: Dashboard → Performance → Current CPU %
5. If >80%, reduce quality: Dashboard → Settings → Stream Quality → Standard/Low

---

## Critical Commands Cheat Sheet

```bash
# ===== SERVICE CONTROL =====
sudo systemctl status mecamera      # Check service
sudo systemctl restart mecamera     # Restart service
sudo systemctl stop mecamera        # Stop service
sudo systemctl enable mecamera      # Enable autoboot

# ===== LOGS =====
sudo journalctl -u mecamera -f      # Real-time logs
sudo journalctl -u mecamera -n 50   # Last 50 lines
tail -f ~/ME_CAM-DEV/logs/mecam.log # App logs
tail -f ~/ME_CAM-DEV/logs/motion_events.json  # Motion events

# ===== CAMERA =====
libcamera-still --list-cameras      # Check camera detected
libcamera-hello                     # Test camera works

# ===== FILE CHECKS =====
ls -la ~/ME_CAM-DEV/                # Directory listing
df -h                               # Disk usage
ps aux | grep python                # Running processes

# ===== CONFIG =====
cat ~/ME_CAM-DEV/config/config.json      # View config
sudo nano ~/ME_CAM-DEV/config/config.json # Edit config (Ctrl+X, Y, Enter)

# ===== API TEST =====
curl http://localhost:8080/api/motion/events      # Test motion API
curl http://localhost:8080/api/storage            # Test storage API
curl http://localhost:8080/api/camera/stats       # Test camera stats
```

---

## Dashboard URLs & API Endpoints

### Dashboard Access
- **Primary:** `http://raspberrypi.local:8080`
- **By IP:** `http://192.168.x.x:8080`

### Key API Endpoints
```
GET  /api/motion/events              # Get motion events (last 24h)
GET  /api/motion/stats               # Motion statistics
POST /api/motion/log                 # Log new motion event
GET  /api/motion/export              # Export events as CSV

GET  /api/storage                    # Storage info
GET  /api/storage/stats              # Storage details
POST /api/storage/cleanup            # Trigger cleanup

GET  /api/stream                     # Live MJPEG stream
GET  /api/camera/stats               # Camera performance

GET  /api/devices                    # Multi-device list
POST /api/devices                    # Add new device
```

---

## Configuration Quick Edit

**File:** `~/ME_CAM-DEV/config/config.json`

### Enable/Disable Features

```json
{
  "camera": {
    "use_fast_streamer": true,       // 15-30 FPS (picamera2)
    "resolution": "640x480",
    "stream_fps": 15
  },
  "motion": {
    "enabled": true,
    "sensitivity": 0.6,
    "check_interval": 0.2            // Every 0.2 seconds
  },
  "storage": {
    "max_gb": 10,
    "retention_days": 7,
    "cleanup_threshold": 0.90        // 90% full triggers cleanup
  },
  "encryption": {
    "enabled": true,
    "cipher": "aes256"
  }
}
```

After editing: `sudo systemctl restart mecamera`

---

## Common Error Messages & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `No module named 'loguru'` | Dependencies not installed | Run `pip install -r requirements.txt` |
| `No cameras available` | Camera not detected | Check cable, enable in raspi-config, reboot |
| `Permission denied: /dev/video0` | Wrong user permissions | `sudo usermod -aG video mecamera` |
| `Address already in use: 8080` | Port conflict | Kill process: `lsof -ti:8080 \| xargs kill -9` |
| `Connection refused` | Service not running | `sudo systemctl start mecamera` |
| `Storage full` | SD card 100% | Delete old videos: `rm recordings/2026-01-01*` |
| `Failed to open camera` | Camera busy | Restart: `sudo systemctl restart mecamera` |

---

## Performance Optimization Tips

### 1. Reduce CPU Usage
- Dashboard → Settings → Camera → Lower FPS (15 instead of 25)
- Disable AI detection: `grep "ai_detection_enabled": false`
- Use Standard resolution instead of Ultra

### 2. Reduce Storage Usage
- Dashboard → Settings → Storage → Lower retention (3 days instead of 7)
- Enable auto-cleanup: Check "Auto-cleanup at 90% full"
- Lower video bitrate in config

### 3. Improve Stream Smoothness
- Install fast camera: `sudo ./scripts/install_fast_camera.sh`
- Check if using fast mode: `grep "use_fast_streamer": true`
- Close other apps on Pi: `ps aux | grep python`
- Use wired connection if possible (better than WiFi)

---

## Quick Test Suite

Run these to verify everything works:

```bash
# 1. Service running?
sudo systemctl status mecamera

# 2. Camera detected?
libcamera-still --list-cameras

# 3. Motion events file created?
cat ~/ME_CAM-DEV/logs/motion_events.json

# 4. API working?
curl http://localhost:8080/api/motion/events

# 5. Dashboard accessible?
curl http://localhost:8080 | head -20

# 6. Disk space OK?
df -h | grep /dev/

# 7. CPU usage reasonable?
top -bn1 | grep python

# All good? 🎉 Your system is healthy!
```

---

**Last Updated:** January 14, 2026
**For Full Guide:** See `DEPLOYMENT_REBUILD_GUIDE.md`
