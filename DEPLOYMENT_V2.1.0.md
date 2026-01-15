# ME Camera v2.1.0 - Complete Deployment Guide
## From Fresh SD Card to Production Ready

**Author**: Mangiafesto Electronics LLC  
**Date**: January 15, 2026  
**Version**: 2.1.0  
**Status**: Production Ready  

---

## Table of Contents
1. [Hardware Setup](#hardware-setup)
2. [SD Card Preparation](#sd-card-preparation)
3. [Initial Pi Configuration](#initial-pi-configuration)
4. [Software Installation](#software-installation)
5. [Service Setup](#service-setup)
6. [Configuration](#configuration)
7. [SMS Integration](#sms-integration)
8. [Verification & Testing](#verification--testing)
9. [Troubleshooting](#troubleshooting)
10. [Production Checklist](#production-checklist)

---

## Hardware Setup

### Components Needed
```
✓ Raspberry Pi (Zero 2W, 3B+, 4, or 5)
✓ USB-C Power Supply (5V 2.5A minimum, 3A recommended)
✓ microSD Card (32GB+ UHS-II recommended)
✓ Raspberry Pi Camera Module (any version)
✓ Ethernet cable OR WiFi setup
✓ Computer with SSH client
✓ USB Card Reader
```

### Assembly
1. **Power Connection**: Connect power supply to Pi USB-C port
2. **Camera Connection**: Insert camera into CSI ribbon connector
   - Open plastic latch on Pi
   - Insert ribbon with gold contacts facing inward
   - Close latch firmly
3. **Network**: Connect ethernet OR configure WiFi

⚠️ **DO NOT connect power yet** - Wait until after OS installation

---

## SD Card Preparation

### Windows Instructions
```powershell
# 1. Download Raspberry Pi Imager
# https://www.raspberrypi.com/software/

# 2. Insert microSD card into reader/USB adapter

# 3. Open Raspberry Pi Imager
# - Click "CHOOSE OS"
# - Select: Raspberry Pi OS (Other) → Raspberry Pi OS Lite (Bullseye)
# 
# - Click "CHOOSE STORAGE"
# - Select your microSD card
#
# - Click GEAR ICON (⚙️) - Advanced Options:
#   ├─ Hostname: mecamera
#   ├─ Enable SSH: ☑ (Use password auth)
#   ├─ Username: pi
#   ├─ Password: [strong password]
#   ├─ Configure WiFi: Enter your SSID and password
#   ├─ WiFi country: US (or your country)
#   ├─ Set locale settings:
#   │  ├─ Timezone: America/New_York (or your timezone)
#   │  └─ Keyboard layout: us
#   └─ Skip first-run wizard: ☑
#
# 4. Click "WRITE" (this will take 5-15 minutes)
#    Warning: All data on card will be deleted!
#
# 5. When complete, safely eject card
```

### macOS/Linux Instructions
```bash
# Download Raspberry Pi Imager
# https://www.raspberrypi.com/software/

# Or use command line:
wget https://downloads.raspberrypi.org/imager/imager_latest_arm64.zip
unzip imager_latest_arm64.zip

# Follow same steps as Windows above
```

### ⚠️ CRITICAL: Disable Legacy Camera
**This must be done AFTER first boot to detect camera on Pi 3B+/4/5**

```bash
# After connecting to Pi for first time:
ssh pi@mecamera.local

# Run configuration
sudo raspi-config

# Navigate to: 3 Interface Options → I1 Legacy Camera → Select "No"
# Then: 3 Interface Options → I3 Camera → Select "Yes"
# Select "Finish" and choose "Yes" to reboot

# After reboot, verify camera is detected:
vcgencmd get_camera
# Expected output: supported=1 detected=1
```

---

## Initial Pi Configuration

### First Boot
```bash
# 1. Insert SD card into Pi
# 2. Connect power supply (USB-C)
# 3. Wait 2-3 minutes for first boot
#    - Green LED will flash during startup
#    - Stabilizes when boot complete

# 4. Verify connectivity
ping mecamera.local  # or ping [IP-address]

# 5. SSH into Pi
ssh pi@mecamera.local
# Password: [the password you set in Imager]
```

### System Update
```bash
# Update package lists (takes 2-3 minutes)
sudo apt update

# Upgrade all packages (takes 5-10 minutes)
sudo apt upgrade -y

# Verify Bullseye (important!)
lsb_release -a
# Should show: Release: 11 (Bullseye)

# Install prerequisites
sudo apt install -y \
  git \
  python3-pip \
  python3-venv \
  python3-dev \
  libjpeg-dev \
  libpng-dev \
  libatlas-base-dev \
  libjasper-dev

# Enable SPI and I2C (if using sensors later)
sudo raspi-config
# 3 Interface Options → I4 SPI → Yes
# 3 Interface Options → I5 I2C → Yes
# 3 Interface Options → I6 Serial → Yes (for serial console)

# Reboot to apply changes
sudo reboot
```

### Verify Python Version
```bash
python3 --version
# Must be 3.9 or higher (typically 3.10+ in Bullseye)

python3 -m venv --help
# Confirms venv module installed
```

---

## Software Installation

### Clone Repository
```bash
# Navigate to home directory
cd ~

# Clone the ME Camera repository
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git

# Navigate into project
cd ME_CAM-DEV

# Verify structure
ls -la
# You should see: web/, src/, config/, scripts/, requirements.txt
```

### Create Virtual Environment
```bash
# Create venv
python3 -m venv .venv

# Activate venv
source .venv/bin/activate
# Prompt should change to: (.venv) pi@mecamera:~/ME_CAM-DEV $

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install required packages
pip install -r requirements.txt
# This takes 3-5 minutes (installs Flask, OpenCV, Pillow, etc.)

# Verify installation
python3 -c "import flask, cv2, PIL; print('All packages OK')"
```

### Test Run (Before Service)
```bash
# Make sure in .venv environment
source .venv/bin/activate

# Run with lite mode for Pi Zero 2W
python3 main_lite.py --mode lite --pi zero2w

# For other Pi models:
python3 main_lite.py --mode lite --pi 3bplus
python3 main_lite.py --mode lite --pi 4
python3 main_lite.py --mode lite --pi 5

# Output should show:
# [SUCCESS] Camera initialized: 640x480
# [INFO] First-run setup detected
# [INFO] Running on http://0.0.0.0:8080

# Test in browser from another computer:
# http://[pi-ip]:8080

# Press Ctrl+C to stop test server
```

---

## Service Setup

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

# Security hardening
NoNewPrivileges=yes
PrivateTmp=yes

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mecamera

[Install]
WantedBy=multi-user.target
```

**Note**: Change `--pi zero2w` to your Pi model:
- `zero2w` - Pi Zero 2W
- `3bplus` - Pi 3B+
- `4` - Pi 4
- `5` - Pi 5

### Enable & Start Service
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (starts on reboot)
sudo systemctl enable mecamera-lite

# Start service
sudo systemctl start mecamera-lite

# Check status
sudo systemctl status mecamera-lite
# Should show: ✓ Active (running)

# View logs (last 20 lines)
journalctl -u mecamera-lite -n 20

# Follow logs in real-time (Ctrl+C to exit)
journalctl -u mecamera-lite -f

# Check service is serving on port 8080
netstat -tuln | grep 8080
# Or: ss -tuln | grep 8080
```

### Auto-restart on Crash
```bash
# Service already configured with:
# Restart=always
# RestartSec=10

# Verify by killing process
sudo kill -9 $(pgrep -f "python3.*main_lite")

# Wait 10 seconds, then verify it restarted
sudo systemctl status mecamera-lite
# Should show: Active (running) with shorter uptime
```

---

## Configuration

### First-Run Setup
```
1. Open browser: http://mecamera.local:8080
   (Or use IP: http://[pi-ip]:8080)

2. First-run wizard appears:
   ├─ Device Name: ME_CAM_1 (or your choice)
   ├─ Device ID: camera-001 (auto-generated)
   └─ Click "Continue"

3. Default login credentials:
   ├─ Username: admin
   └─ Password: admin123

⚠️ CHANGE THESE IMMEDIATELY!
```

### Access Dashboard
```
1. Go to: http://mecamera.local:8080
2. Login with admin / admin123
3. Click gear icon (⚙️) for settings
4. Update device information:
   ├─ Device Name: [friendly name]
   ├─ Device Location: [room/location]
   ├─ Emergency Phone: [your phone number]
   ├─ Motion Threshold: 0.5 (0-1, lower=more sensitive)
   ├─ Motion Recording: ☑ enabled
   ├─ Recording Duration: 10 seconds (per clip)
   └─ Storage Cleanup: 7 days (delete videos older than)
5. Change admin password (⚙️ → Change Password)
6. Click "Save Configuration"
```

### SMS Configuration (Optional)
```
1. Go to Configuration (⚙️)
2. Scroll to SMS Settings:
   ├─ Enable SMS: ☑ checked
   ├─ API URL: https://your-sms-api.com/send
   ├─ API Key: [your api key]
   ├─ Phone To: [destination number +1XXXXXXXXXX]
   └─ Rate Limit: 5 minutes between alerts
3. Save Configuration
4. Test in Motion Events: Click "Share" button

Note: API should accept POST with:
{
  "to": "+1XXXXXXXXXX",
  "from": "ME_CAM_1",
  "message": "Alert text"
}
```

---

## SMS Integration

### Generic HTTP API Integration
The system sends POST requests to your SMS provider:

```bash
POST /send
Content-Type: application/json
Authorization: Bearer [api_key]  (if configured)

{
  "to": "+14155552555",
  "from": "ME_CAM_1",
  "message": "🎥 Motion Alert from ME_CAM_1\nTime: 2026-01-15 14:33:22 EST\nType: MOTION\nConfidence: 95%"
}
```

### Example Providers

#### Twilio SMS
```bash
# Requires Twilio account: https://twilio.com

API_URL: https://api.twilio.com/2010-04-01/Accounts/ACXXXXXXXX/Messages.json
API_Key: Basic [base64(AccountSID:AuthToken)]

# Body format (URL-encoded):
To=+14155552555&From=+15551234567&Body=Alert+message
```

#### Plivo SMS
```bash
# Requires Plivo account: https://plivo.com

API_URL: https://api.plivo.com/v1/Account/XXXXXXXXX/Message/
API_Key: Bearer [auth_token]

Body:
{
  "src": "15551234567",
  "dst": "+14155552555",
  "text": "Alert message"
}
```

#### AWS SNS
```bash
# Requires AWS account: https://aws.amazon.com

API_URL: http://localhost:9200  (local SNS simulator)
or deploy Lambda function for SMS
```

#### Custom HTTP API
```bash
# Any custom endpoint that accepts POST:

POST /send
{
  "to": "+14155552555",
  "from": "ME_CAM",
  "message": "Motion detected at 2:33 PM",
  "timestamp": "2026-01-15T14:33:22Z"
}

# Expected response (200/201):
{
  "status": "success",
  "message_id": "msg_abc123"
}
```

---

## Verification & Testing

### 1. Camera Test
```bash
# SSH into Pi
ssh pi@mecamera.local

# Test camera detection
vcgencmd get_camera
# Expected: supported=1 detected=1

# Test camera capture
libcamera-hello --list-cameras
# Should show your camera model

# 30-second camera preview
libcamera-jpeg -o test.jpg
ls -lh test.jpg  # Check file created (~50-100KB)
```

### 2. Web Interface Test
```bash
# Open browser
http://mecamera.local:8080

# Check components:
├─ Live stream plays (black/test pattern OK)
├─ Battery shows percentage + runtime
├─ Storage shows GB available
├─ Dashboard loads without errors
└─ Settings page accessible
```

### 3. Motion Detection Test
```bash
# 1. Go to Motion Events page
# 2. Wave hand in front of camera for 5 seconds
# 3. Wait 5 seconds
# 4. Check if new event appears
# 5. Click video button to view recording
# 6. Verify timestamp shows in local timezone
```

### 4. SMS Alert Test
```bash
# 1. Go to Motion Events
# 2. Click "Share" on any event
# 3. Enter phone number (e.g., +14155552555)
# 4. Should see "SMS sent successfully"
# 5. Check SMS received on phone

# Or test API manually:
curl -X POST http://localhost:8080/api/motion/send \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_1234567890",
    "phone": "+14155552555",
    "media_type": "video"
  }'
```

### 5. Emergency Alert Test
```bash
# Via web interface:
# Dashboard → Click SOS button → Confirm

# Via API:
curl -X POST http://localhost:8080/api/emergency/alert \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Emergency test from ME_CAM_1",
    "type": "test_alert"
  }'
```

### 6. Storage Cleanup Test
```bash
# Manually trigger cleanup
curl -X POST http://localhost:8080/api/storage/cleanup \
  -H "Content-Type: application/json" \
  -d '{"days": 7}'

# Response should show: {"ok": true, "deleted": X, "freed_mb": Y}
```

---

## Troubleshooting

### Camera Issues

#### Error: "Camera not detected"
```bash
# Check hardware connection
vcgencmd get_camera
# Should show: supported=1 detected=1

# If not detected:
# 1. Reseat camera ribbon (disconnect, reconnect)
# 2. Verify legacy camera is DISABLED
sudo raspi-config
# 3 Interface Options → I1 Legacy Camera → NO (CRITICAL)
# 3 Interface Options → I3 Camera → YES

# Reboot
sudo reboot

# Check again
vcgencmd get_camera
```

#### Error: "Cannot connect to camera"
```bash
# Test camera directly
libcamera-hello  # Should show 30-second preview
# If this fails, camera hardware issue

# Restart service
sudo systemctl restart mecamera-lite

# Check logs
journalctl -u mecamera-lite -n 50 | grep -i camera
```

### Network Issues

#### Cannot connect to http://mecamera.local
```bash
# Find Pi IP address (on Pi):
hostname -I

# Or from another device on network:
ping mecamera.local  # Should respond
# If not, use IP: http://[IP]:8080

# Verify service listening on port 8080
sudo netstat -tuln | grep 8080
# Or: ss -tuln | grep 8080

# Should show:
# tcp  0  0 0.0.0.0:8080  0.0.0.0:*  LISTEN
```

#### WiFi Connection Issues
```bash
# SSH via ethernet (if available)
ssh pi@[ethernet-ip]

# Edit WiFi config
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf

# Add or edit WiFi network:
network={
    ssid="Your_SSID"
    psk="Your_Password"
}

# Restart WiFi
sudo systemctl restart wpa_supplicant
sudo systemctl restart dhcpcd

# Check connection
iwconfig wlan0
```

### Motion Detection Issues

#### Motion not being detected
```bash
# Lower threshold (more sensitive)
# Config → Motion Threshold: 0.3 (was 0.5)

# Check motion events logged
curl http://localhost:8080/api/motion/events

# Increase contrast
# Move closer to camera, wave hands faster
```

#### Recording files not saving
```bash
# Check disk space
df -h ~/ME_CAM-DEV/recordings/
# Need at least 100MB free

# Check permissions
ls -la ~/ME_CAM-DEV/recordings/
# Should show: drwxr-xr-x pi:pi

# Check service can write
touch ~/ME_CAM-DEV/recordings/test.txt
# Should succeed

# Review logs
journalctl -u mecamera-lite -n 50 | grep -i "motion\|record"
```

### Timezone Issues

#### Events showing wrong time
```bash
# Check Pi timezone
timedatectl status
# Should show: Timezone: America/New_York (EST/EDT)

# Set correct timezone
sudo timedatectl set-timezone America/New_York

# Verify
timedatectl status

# Restart service
sudo systemctl restart mecamera-lite
```

### Service Issues

#### Service won't start
```bash
# Check service file syntax
sudo systemctl start mecamera-lite
sudo systemctl status mecamera-lite

# View detailed error
journalctl -u mecamera-lite -n 20 --full

# Common issues:
# - Wrong Python path
# - Wrong working directory
# - Missing permissions
# - Port 8080 already in use

# Kill any conflicting process on 8080:
sudo lsof -i :8080
sudo kill -9 [PID]
```

#### Service crashes after startup
```bash
# Check logs for error
journalctl -u mecamera-lite -n 50

# Common causes:
# - Camera initialization error
# - Missing dependencies
# - Out of memory

# For memory issues (Pi Zero 2W):
free -m  # Check available RAM
# Need at least 100MB free
```

---

## Production Checklist

Before deploying to production:

### Security
- [ ] Change admin password from default
- [ ] Generate strong PIN code (if using)
- [ ] Disable SSH password auth (use keys)
- [ ] Enable firewall (ufw)
- [ ] Set up reverse proxy with HTTPS (nginx + certbot)
- [ ] Restrict network access (VPN/private network)

### Configuration
- [ ] Set device name and location
- [ ] Configure emergency contact phone
- [ ] Set motion detection threshold
- [ ] Configure storage cleanup (7-14 days)
- [ ] Set up SMS alerts (if needed)
- [ ] Test email notifications (if configured)

### Testing
- [ ] Motion detection works (test with hand)
- [ ] Video recording creates MP4 files
- [ ] Timestamps show correct timezone
- [ ] SMS alerts send successfully
- [ ] Storage cleanup removes old files
- [ ] Battery monitoring shows correct value
- [ ] Nanny cam toggle works

### Monitoring
- [ ] Set up log rotation (journalctl max size)
- [ ] Monitor disk usage (enable auto-cleanup)
- [ ] Check memory usage (should be <200MB)
- [ ] Monitor CPU temperature
- [ ] Verify service auto-restarts on crash

### Documentation
- [ ] Document device IP/hostname
- [ ] Record admin credentials (secure location)
- [ ] Note SMS API endpoint and key
- [ ] Document any customizations
- [ ] Create backup of /home/pi/ME_CAM-DEV

### Maintenance Plan
- [ ] Weekly: Check logs for errors
- [ ] Monthly: Review storage usage
- [ ] Quarterly: Update OS and packages
- [ ] Quarterly: Review security settings
- [ ] Annually: Replace microSD card if needed

---

## Performance Benchmarks (Pi Zero 2W)

```
Memory Usage:
  - Idle: 80-100 MB
  - With streaming: 140-160 MB
  - Recording: 180-200 MB
  - Max safe: 350 MB (leave headroom for OS)

CPU Usage:
  - Motion detection: 15-25%
  - Video streaming: 20-30%
  - Recording: 40-60%
  - Combined all tasks: 60-80%

Storage:
  - Per 3-second video: 40-60 KB
  - Per JPEG snapshot: 10-15 KB
  - 32GB card = ~500k hours of motion events
  - Auto-cleanup at 7 days = sustainable operation

Network (WiFi):
  - Live stream: 300-500 Kbps
  - Recording: 200 Kbps
  - Alerts: <1 Kbps
  - Suitable for: 1-5 Mbps WiFi minimum
```

---

## Success Indicators

You'll know the system is working when:

✅ Camera stream appears in web browser  
✅ Battery percentage displays with runtime  
✅ Motion events record as MP4 videos  
✅ Event timestamps show in local timezone  
✅ SMS alerts send to configured phone  
✅ Service auto-restarts after crash  
✅ Old recordings auto-delete after 7 days  
✅ Disk usage stays below 80% capacity  
✅ CPU usage stays below 80%  
✅ RAM usage stays below 250MB  

---

## Next Steps

1. **Customize Dashboard**: Edit templates/ files for branding
2. **Add Multi-Camera Support**: Run multiple instances on network
3. **Cloud Integration**: Configure Google Drive backup
4. **Advanced Alerts**: Set up webhooks for custom integrations
5. **Scale Horizontally**: Deploy to multiple Pi devices

---

## Support & Resources

- **GitHub**: https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV
- **Issues**: Report bugs and feature requests
- **Documentation**: See docs/ folder
- **Community**: GitHub Discussions

---

**Deployment Complete! Your ME Camera system is ready for production use.**

