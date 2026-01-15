# ME Camera v2.1.0 - Complete Setup & Reference Guide
## From Fresh SD Card to Production-Ready System

**Status**: Production Ready ✅  
**Version**: 2.1.0  
**Release Date**: January 15, 2026  
**Last Updated**: January 15, 2026  

---

## QUICK FACTS

- **Framework**: Python 3.9+ with Flask 2.2.5
- **OS**: Raspberry Pi OS Bullseye (32-bit)
- **Target Hardware**: Pi Zero 2W, 3B+, 4, 5
- **RAM Required**: 512MB minimum (Pi Zero 2W)
- **Storage**: 32GB+ microSD (UHS-II recommended)
- **Video Format**: MP4 (H.264 codec)
- **Stream Resolution**: 640x480 @ 20 FPS
- **Recording**: 3-second clips per motion event
- **Power**: USB-C 5V 2.5A (Pi Zero 2W)
- **Network**: Ethernet or WiFi 5GHz
- **GitHub**: https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV

---

## TABLE OF CONTENTS

1. [Hardware Setup](#hardware-setup)
2. [SD Card Flashing](#sd-card-flashing)
3. [Initial Pi Configuration](#initial-pi-configuration)
4. [Software Installation](#software-installation)
5. [Service Setup](#service-setup)
6. [Configuration & First Run](#configuration--first-run)
7. [SMS Integration](#sms-integration)
8. [Verification & Testing](#verification--testing)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance & Updates](#maintenance--updates)

---

## HARDWARE SETUP

### Components Checklist
```
☐ Raspberry Pi (Zero 2W, 3B+, 4, or 5)
☐ USB-C Power Supply (5V 2.5A minimum)
☐ microSD Card 32GB+ (UHS-II preferred)
☐ Raspberry Pi Camera Module (any version)
☐ Network cable (Ethernet) OR WiFi setup
☐ Computer with SSH client
☐ USB microSD Card Reader
```

### Assembly Instructions

1. **Insert Camera**
   - Open CSI ribbon connector latch on Pi
   - Insert camera ribbon with gold contacts facing inward
   - Close latch firmly until it clicks

2. **Connect Network**
   - Option A: Ethernet cable to Pi Ethernet port
   - Option B: Configure WiFi in next steps

3. **Power Supply Connection**
   - Connect USB-C power supply to Pi
   - ⚠️ DO NOT power on yet - wait for OS installation

### Recommended Setup for Locations

**Brockport, NY (Eastern Time)**
```
Timezone: America/New_York (UTC-5 EST, UTC-4 EDT)
WiFi: Configure during Imager setup
```

---

## SD CARD FLASHING

### Windows/Mac/Linux Instructions

1. **Download Raspberry Pi Imager**
   - Visit: https://www.raspberrypi.com/software/
   - Download for your OS
   - Install and launch

2. **Select Operating System**
   - Click "CHOOSE OS"
   - Navigate to: Raspberry Pi OS (Other)
   - Select: **Raspberry Pi OS Lite (Bullseye)**
   - ⚠️ CRITICAL: Do NOT select Bookworm - incompatible!

3. **Choose Storage Device**
   - Click "CHOOSE STORAGE"
   - Select your microSD card
   - ⚠️ WARNING: All data will be erased!

4. **Configure Advanced Options**
   - Click GEAR ICON (⚙️)
   - Enable SSH: ☑ Use password authentication
   - Set hostname: mecamera
   - Username: pi
   - Password: [strong password - you'll use this frequently]
   - Configure WiFi:
     - SSID: [your network name]
     - Password: [your WiFi password]
     - WiFi country: [your country - US for Brockport]
   - Set locale settings:
     - Timezone: America/New_York
     - Keyboard layout: us
   - Skip first-run wizard: ☑

5. **Write Image**
   - Click "WRITE"
   - Confirm warning about data erasure
   - Wait 5-15 minutes for completion
   - System shows "Write successful" when done

6. **Eject Card**
   - Safely eject microSD card from reader
   - Insert into Pi (slot on bottom/side depending on model)

---

## INITIAL PI CONFIGURATION

### First Boot

1. **Connect Hardware**
   - Insert microSD card into Pi
   - Connect camera (if not already done)
   - Connect Ethernet cable OR ensure WiFi will work
   - Connect USB-C power supply
   - Green LED should flash, then stabilize after 2-3 minutes

2. **Verify Connectivity**
   ```bash
   # From your computer
   ping mecamera.local
   # Should respond with: Reply from... (timeout after 3-5 attempts = working)
   
   # If hostname doesn't work, find IP:
   # Check your router for connected devices
   # Look for "mecamera" in DHCP client list
   ```

3. **SSH Access**
   ```bash
   ssh pi@mecamera.local
   # Password: [the password you set in Imager]
   
   # Or use IP address:
   ssh pi@[your-pi-ip-address]
   ```

### System Updates

```bash
# Update package lists
sudo apt update
# This takes 2-3 minutes

# Upgrade all packages
sudo apt upgrade -y
# This takes 5-10 minutes

# Verify OS version (must be Bullseye)
lsb_release -a
# Output should show: Release: 11

# Install essential packages
sudo apt install -y \
  git \
  python3-pip \
  python3-venv \
  python3-dev \
  libjpeg-dev \
  libpng-dev \
  libatlas-base-dev

# Verify Python version
python3 --version
# Must be 3.9 or higher
```

### ⚠️ CRITICAL: Disable Legacy Camera Support

This step is REQUIRED for Pi 3B+, 4, and 5 to detect the camera!

```bash
sudo raspi-config
# Navigate: 3 Interface Options → I1 Legacy Camera → Select "No"
# Then: 3 Interface Options → I3 Camera → Select "Yes"
# Select "Finish" and "Yes" to reboot

# After reboot, verify detection:
vcgencmd get_camera
# Expected output: supported=1 detected=1
```

---

## SOFTWARE INSTALLATION

### Clone Repository

```bash
# Navigate to home
cd ~

# Clone ME Camera
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git

# Enter directory
cd ME_CAM-DEV

# Verify structure
ls -la
# You should see: web/, src/, config/, scripts/, etc.
```

### Create Virtual Environment

```bash
# Create isolated Python environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate
# Prompt changes to: (.venv) pi@mecamera:~/ME_CAM-DEV $

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install all dependencies
pip install -r requirements.txt
# Takes 3-5 minutes

# Verify success
python3 -c "import flask, cv2, PIL; print('✅ All packages installed')"
```

### Test Run

```bash
# Make sure venv is active
source .venv/bin/activate

# Start application (lite mode for Pi Zero 2W)
python3 main_lite.py --mode lite --pi zero2w

# For other Pi models:
# python3 main_lite.py --mode lite --pi 3bplus
# python3 main_lite.py --mode lite --pi 4
# python3 main_lite.py --mode lite --pi 5

# Expected output:
# [SUCCESS] Camera initialized: 640x480
# [INFO] First-run setup detected
# [INFO] Running on http://0.0.0.0:8080

# Stop with: Ctrl+C
```

---

## SERVICE SETUP

### Create Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/mecamera-lite.service
```

Paste this content:
```ini
[Unit]
Description=ME Camera - Lightweight Motion Detection
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ME_CAM-DEV
Environment="PATH=/home/pi/ME_CAM-DEV/.venv/bin"
ExecStart=/home/pi/ME_CAM-DEV/.venv/bin/python3 /home/pi/ME_CAM-DEV/main_lite.py --mode lite --pi zero2w
Restart=always
RestartSec=10

NoNewPrivileges=yes
PrivateTmp=yes

StandardOutput=journal
StandardError=journal
SyslogIdentifier=mecamera

[Install]
WantedBy=multi-user.target
```

**Note**: Change `--pi zero2w` to your model:
- `zero2w` = Pi Zero 2W
- `3bplus` = Pi 3B+
- `4` = Pi 4
- `5` = Pi 5

### Enable & Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable mecamera-lite

# Start service
sudo systemctl start mecamera-lite

# Check status
sudo systemctl status mecamera-lite
# Should show: Active (running) since...

# View logs
journalctl -u mecamera-lite -n 20 -f
# Press Ctrl+C to exit
```

---

## CONFIGURATION & FIRST RUN

### Access Web Interface

1. **Open Browser**
   ```
   http://mecamera.local:8080
   or
   http://[your-pi-ip]:8080
   ```

2. **First-Run Setup**
   - Device Name: ME_CAM_1 (or your preferred name)
   - Device ID: camera-001 (auto-generated)
   - Click "Continue"

3. **Login**
   - Username: admin
   - Password: admin123
   - ⚠️ **CHANGE THESE IMMEDIATELY in Settings!**

### Configure Settings

1. **Go to Settings (⚙️)**
   - Device Name: [friendly name, e.g., "Kitchen Camera"]
   - Device Location: [room/location]
   - Emergency Phone: [your phone number]

2. **Motion Recording**
   - Motion Recording: ☑ Enabled
   - Motion Threshold: 0.5 (0.1=very sensitive, 0.9=rarely triggers)
   - Recording Duration: 10 seconds per clip
   - Nanny Cam Mode: ☐ Disabled (enable to view-only)

3. **Storage**
   - Storage Cleanup: 7 days (delete videos older than)

4. **SMS Alerts (Optional)**
   - Enable SMS: ☑ Checked
   - API URL: https://your-sms-api.com/send
   - API Key: [your api key]
   - Phone To: +1[your number]
   - Rate Limit: 5 minutes between alerts

5. **Save Configuration**
   - Click "Save Configuration"
   - Should show: "✅ Configuration saved"

### Change Admin Password

1. **Click Settings (⚙️)**
2. **Change Password**
   - Enter new secure password
   - Confirm password
   - Click "Update"

---

## SMS INTEGRATION

### Supported Providers

#### Generic HTTP API (Recommended)
```bash
# Any SMS provider that accepts HTTP POST

API_URL: https://api.your-provider.com/send
Method: POST
Headers: 
  Content-Type: application/json
  Authorization: Bearer [api_key] (optional)

Body:
{
  "to": "+14155552555",
  "from": "ME_CAM_1",
  "message": "Motion Alert from ME_CAM_1..."
}

Response:
{
  "status": "success",
  "message_id": "msg_abc123"
}
```

#### Twilio
```bash
# 1. Create account at https://twilio.com
# 2. Get Account SID and Auth Token
# 3. Set API URL to: https://api.twilio.com/2010-04-01/Accounts/[SID]/Messages.json
# 4. Encode credentials as Base64
```

#### Plivo
```bash
# 1. Create account at https://plivo.com
# 2. Get Auth ID and Token
# 3. Set API URL to: https://api.plivo.com/v1/Account/[ID]/Message/
```

### Test SMS Integration

```bash
# 1. Configure SMS in Settings (see Configuration section)
# 2. Go to Motion Events page (📊 Events)
# 3. Click "Share" on any event
# 4. Enter phone number: +1[your-number]
# 5. Should see: "✅ SMS sent successfully"
# 6. Check phone for message
```

---

## VERIFICATION & TESTING

### Camera Test
```bash
# Verify hardware detection
vcgencmd get_camera
# Expected: supported=1 detected=1

# Test camera capture
libcamera-hello --list-cameras
# Shows your camera model

# Capture test image
libcamera-jpeg -o test.jpg
# File should be 50-100KB
```

### Web Interface Test
```
1. Open: http://mecamera.local:8080
2. Login with admin credentials
3. Check:
   ✓ Live stream appears (video or test pattern)
   ✓ Battery percentage displays
   ✓ Storage shows available space
   ✓ Settings page accessible
```

### Motion Detection Test
```
1. Go to Motion Events (📊 Events button)
2. Wave hand in front of camera for 5 seconds
3. Wait 5 seconds
4. New event should appear with:
   ✓ Timestamp in local time (e.g., 02:33:45 PM EST)
   ✓ Video or image button (📹)
   ✓ Confidence percentage
5. Click video button to view recording
```

### Timezone Verification
```bash
# Check system timezone
timedatectl status
# Should show: Timezone: America/New_York

# Events should display in local time
# Example: 2:47:38 PM EST (not 7:47:38 PM GMT)
```

---

## TROUBLESHOOTING

### Camera Not Detected
```bash
# 1. Check detection
vcgencmd get_camera
# If: supported=0 detected=0 → Camera not detected

# 2. Disable legacy camera (CRITICAL!)
sudo raspi-config
# 3 Interface Options → I1 Legacy Camera → NO

# 3. Reseat camera
# - Power off Pi
# - Open CSI connector latch
# - Remove and reinsert ribbon
# - Close latch firmly
# - Power on

# 4. Reboot
sudo reboot
```

### Cannot Access Web Interface
```bash
# 1. Find Pi IP address
hostname -I
# Note the IP (e.g., 192.168.1.100)

# 2. Try IP instead of hostname
http://[ip-address]:8080

# 3. Verify service is running
sudo systemctl status mecamera-lite
# Should show: Active (running)

# 4. Check port 8080 is listening
sudo netstat -tuln | grep 8080
# Should show: tcp 0 0 0.0.0.0:8080 LISTEN
```

### Motion Not Recording
```bash
# 1. Check threshold is reasonable
# Settings → Motion Threshold: 0.5

# 2. Verify disk space
df -h ~/ME_CAM-DEV/recordings/
# Need at least 100MB free

# 3. Check motion detection is working
# Perform test (see Verification section)

# 4. Check nanny cam mode is OFF
# Settings → Nanny Cam Mode should be ☐ disabled
```

### Wrong Timezone
```bash
# 1. Verify system timezone
timedatectl status

# 2. Set to Eastern Time
sudo timedatectl set-timezone America/New_York

# 3. Verify change
timedatectl status
# Should show: Timezone: America/New_York

# 4. Restart service
sudo systemctl restart mecamera-lite
```

### Service Won't Start
```bash
# 1. Check service file
systemctl status mecamera-lite

# 2. View detailed logs
journalctl -u mecamera-lite -n 50 --full

# 3. Test manually
cd ~/ME_CAM-DEV
source .venv/bin/activate
python3 main_lite.py --mode lite --pi zero2w
# Press Ctrl+C to stop

# 4. Common issues:
# - Wrong Python path in service file
# - Wrong working directory
# - Missing venv activation
# - Port 8080 already in use
```

---

## MAINTENANCE & UPDATES

### Regular Maintenance

**Weekly**
```bash
# Check service status
sudo systemctl status mecamera-lite

# View recent logs
journalctl -u mecamera-lite -n 20
# Look for errors

# Check disk usage
du -sh ~/ME_CAM-DEV/recordings/
```

**Monthly**
```bash
# Check available updates
sudo apt update
sudo apt list --upgradable

# Update if needed
sudo apt upgrade
sudo reboot

# Monitor storage cleanup
# Should auto-delete videos >7 days old
```

**Quarterly**
```bash
# Security updates
sudo apt full-upgrade

# Backup configuration
cp ~/ME_CAM-DEV/config/*.json ~/backups/

# Review logs for patterns
journalctl -u mecamera-lite --since="1 month ago" | grep ERROR
```

### Log Management
```bash
# View real-time logs
sudo journalctl -u mecamera-lite -f

# View last N lines
journalctl -u mecamera-lite -n 100

# View since timestamp
journalctl -u mecamera-lite --since "2 hours ago"

# Export logs to file
journalctl -u mecamera-lite > ~/logs_backup.txt

# Clear old logs (keeps last 2 weeks)
sudo journalctl --vacuum-time=2w
```

### Disk Cleanup
```bash
# Manual cleanup (delete videos >7 days old)
# Via web interface:
# Motion Events → [cleanup button]
# Or API:
curl -X POST http://localhost:8080/api/storage/cleanup \
  -H "Content-Type: application/json" \
  -d '{"days": 7}'

# Check actual usage
du -sh ~/ME_CAM-DEV/recordings/
df -h /
```

---

## PERFORMANCE METRICS

### Pi Zero 2W Benchmark
```
Memory Usage:
  Idle: 80-100 MB
  With streaming: 140-160 MB  
  Recording: 180-200 MB
  Max safe: 350 MB

CPU Usage:
  Motion detection: 15-25%
  Video streaming: 20-30%
  Recording: 40-60%
  Combined: 60-80%

Storage:
  Per 3-second video: 40-60 KB
  Per JPEG image: 10-15 KB
  32GB card = ~500,000 clips
  At 1 clip/30sec = 416 days storage

Network:
  Live stream: 300-500 Kbps
  Recording upload: 200 Kbps
  Alerts: <1 Kbps
  Minimum WiFi: 1 Mbps
```

---

## PRODUCTION CHECKLIST

Before deploying to production:

```
Security
  ☑ Changed admin password
  ☑ Set device location
  ☑ Configured emergency phone
  ☐ (Optional) Disabled SSH password auth
  ☐ (Optional) Set up firewall

Features
  ☑ Camera streaming works
  ☑ Motion detection triggers
  ☑ Videos save and playback
  ☑ Timestamps show correct timezone
  ☑ Storage auto-cleanup works
  ☑ Battery monitoring active
  ☐ (Optional) SMS alerts configured

Testing
  ☑ Motion events recorded
  ☑ Videos downloadable
  ☑ Events shareable
  ☑ Service auto-restarts
  ☑ Logs accessible
  ☑ Configuration persists

Monitoring
  ☑ Disk usage <80%
  ☑ Memory usage <200MB
  ☑ CPU usage <80%
  ☑ Service running (check weekly)
  ☑ Logs monitored (check monthly)

Backup
  ☑ Configuration backed up
  ☑ Important videos archived
  ☑ Access credentials recorded securely
  ☑ Documentation available offline
```

---

## QUICK REFERENCE

### Useful Commands
```bash
# SSH connection
ssh pi@mecamera.local

# View service status
systemctl status mecamera-lite

# View logs real-time
journalctl -u mecamera-lite -f

# Restart service
sudo systemctl restart mecamera-lite

# Find Pi IP
hostname -I

# Check disk usage
df -h

# Check RAM
free -m

# Check temperature
vcgencmd measure_temp
```

### File Locations
```bash
# Application directory
~/ME_CAM-DEV/

# Configuration
~/ME_CAM-DEV/config/config.json

# Recordings
~/ME_CAM-DEV/recordings/

# Logs
journalctl (system logs)

# Service file
/etc/systemd/system/mecamera-lite.service
```

### Important URLs
```bash
# Web interface
http://mecamera.local:8080

# API battery status
http://mecamera.local:8080/api/battery

# API motion events
http://mecamera.local:8080/api/motion/events

# API storage info
http://mecamera.local:8080/api/storage
```

---

## COMMON TASKS

### Accessing Dashboard from Outside Network
```bash
# If not on same WiFi/network:
# Option 1: Use VPN to connect to home network first
# Option 2: Forward port 8080 on router (not recommended)
# Option 3: Use SSH tunnel:
ssh -L 8080:localhost:8080 pi@[router-ip] -N
# Then visit: http://localhost:8080
```

### Backing Up Videos
```bash
# Copy all recordings to computer
scp -r pi@mecamera.local:~/ME_CAM-DEV/recordings ~/backup/mecam_videos/

# Or use rsync for incremental backup
rsync -avz --delete pi@mecamera.local:~/ME_CAM-DEV/recordings/ ~/backup/mecam_videos/
```

### Updating System
```bash
# Pull latest code
cd ~/ME_CAM-DEV
git pull origin main

# Restart service
sudo systemctl restart mecamera-lite

# Check new version
cat README_V2.1.0.md | head -20
```

---

## SUPPORT & RESOURCES

**Documentation**
- README_V2.1.0.md - Product overview
- DEPLOYMENT_V2.1.0.md - Complete deployment guide
- COMPLETION_CHECKLIST_V2.1.0.md - Features & checklist

**GitHub Repository**
https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV

**Report Issues**
https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV/issues

---

## VERSION INFORMATION

```
Application: ME Camera
Version: 2.1.0
Status: Production Ready ✅
Release Date: January 15, 2026
Last Updated: January 15, 2026

Framework: Flask 2.2.5
Python: 3.9+
OS: Raspberry Pi OS Bullseye
Hardware: Pi Zero 2W, 3B+, 4, 5

Key Features (v2.1.0):
✅ MP4 video recording
✅ Motion detection & alerts
✅ Battery monitoring
✅ SMS integration (generic HTTP API)
✅ Emergency alerts
✅ Web dashboard
✅ Event management
✅ Storage cleanup
✅ Timezone support
✅ Professional documentation
```

---

**Setup Complete!**

Your ME Camera system is now ready to monitor and record. 
Visit http://mecamera.local:8080 to access the dashboard.

For support, visit: https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV

