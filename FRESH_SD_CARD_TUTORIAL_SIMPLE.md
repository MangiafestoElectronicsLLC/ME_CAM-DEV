# Fresh SD Card to Working Camera - Simple Guide

**Version:** ME_CAM v2.2.3  
**Hardware:** Raspberry Pi Zero 2W + IMX519 Camera  
**Time:** 30 minutes total  
**Method:** GitHub repository (proven stable on devices 1, 2, 3)

---

## What You Need

**Hardware:**
- Raspberry Pi Zero 2W
- IMX519 Camera Module (Arducam)
- MicroSD card (16GB+, 32GB recommended)
- Power supply (5V 2.5A)
- Camera ribbon cable

**Software:**
- [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
- Your WiFi name and password

---

## Step 1: Flash SD Card (10 minutes)

### 1.1 Download Raspberry Pi Imager
https://www.raspberrypi.com/software/

### 1.2 Configure Image
1. Click **CHOOSE OS** → **Raspberry Pi OS (other)** → **Raspberry Pi OS Lite (32-bit)**
2. Click **CHOOSE STORAGE** → Select your SD card
3. Click **⚙️ Settings Icon**:
   - ✅ Set hostname: `mecamdev6` (or your preferred name)
   - ✅ Enable SSH (password authentication)
   - ✅ Username: `pi`
   - ✅ Password: (your secure password)
   - ✅ Configure WiFi:
     - SSID: (your network name)
     - Password: (your WiFi password)
     - Country: `US`
   - ✅ Set timezone: `America/New_York` (or yours)
4. Click **SAVE**, then **WRITE**

### 1.3 Boot Pi
1. Insert SD card into Pi
2. Connect camera (blue tab facing USB ports)
3. Power on
4. Wait 2 minutes for first boot

---

## Step 2: Connect via SSH (2 minutes)

Find your Pi's IP address from your router, or use hostname:

```bash
ssh pi@mecamdev6.local
# Enter your password when prompted
```

**Expected:** `pi@mecamdev6:~ $`

---

## Step 3: Install ME_CAM (20 minutes)

### 3.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
```
*(3-5 minutes)*

### 3.2 Install Dependencies
```bash
sudo apt install -y \
    python3-pip \
    python3-venv \
    libcamera-apps \
    python3-picamera2 \
    python3-opencv \
    python3-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    git
```
*(5-7 minutes)*

**Note:** Skip `libatlas-base-dev` if not available on your OS version.

### 3.3 Clone Repository
```bash
cd ~
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV
```

### 3.4 Setup Python Environment
```bash
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
*(15-20 minutes - many packages to install)*

### 3.5 Create Configuration
```bash
mkdir -p config
nano config/config.json
```

**Paste this:**
```json
{
    "first_run_completed": true,
    "device_name": "ME_CAM_6",
    "device_id": "pi-cam-006",
    "resolution": "640x480",
    "framerate": 40,
    "motion_detection": true,
    "video_length": 30,
    "storage_limit_gb": 50,
    "auto_delete_old": true,
    "web_port": 8080
}
```

Save: **Ctrl+O**, **Enter**, **Ctrl+X**

### 3.6 Test Run
```bash
python3 main.py
```

You should see:
```
[APP] Loading LITE version for Raspberry Pi Zero 2W
[CAMERA] RPiCam initialized: 640x480 @ 40 FPS
[FLASK] Starting on 0.0.0.0:8080
```

**Test in browser:** `http://mecamdev6.local:8080`

Press **Ctrl+C** to stop.

### 3.7 Create Auto-Start Service
```bash
sudo nano /etc/systemd/system/mecamera.service
```

**Paste this:**
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

Save: **Ctrl+O**, **Enter**, **Ctrl+X**

### 3.8 Enable and Start
```bash
sudo systemctl daemon-reload
sudo systemctl enable mecamera
sudo systemctl start mecamera
sudo systemctl status mecamera
```

**Expected:** `Active: active (running)`

---

## Step 4: Verify Everything Works

### 4.1 Check Service
```bash
sudo systemctl status mecamera
sudo journalctl -u mecamera -n 20
```

### 4.2 Test Dashboard
Open browser: `http://mecamdev6.local:8080`

**Expected:** Purple dashboard with live camera feed

### 4.3 Test Auto-Boot
```bash
sudo reboot
```

Wait 2 minutes, then check: `http://mecamdev6.local:8080`

---

## ✅ Done!

Your camera is working at: `http://mecamdev6.local:8080`

---

## Quick Reference Commands

```bash
# Service control
sudo systemctl restart mecamera
sudo systemctl status mecamera
sudo systemctl stop mecamera

# View logs
sudo journalctl -u mecamera -f

# Manual test
cd ~/ME_CAM-DEV
source venv/bin/activate
python3 main.py

# Update code
cd ~/ME_CAM-DEV
git pull
pip install -r requirements.txt
sudo systemctl restart mecamera

# System health
vcgencmd measure_temp
free -h
df -h
hostname -I
```

---

## Common Issues & Fixes

### Camera Not Detected
```bash
# Test camera:
rpicam-jpeg -o test.jpg --width 640 --height 480

# If fails, force IMX519 overlay:
sudo nano /boot/firmware/config.txt
# Add under [all]:
camera_auto_detect=0
dtoverlay=imx519
gpu_mem=128

sudo reboot
```

### Can't Access Dashboard
- ✅ Use Pi's IP or hostname, NOT `127.0.0.1`
- ✅ Find IP: `hostname -I` on the Pi
- ✅ Try: `http://10.2.1.x:8080` (your Pi's IP)

### ImportError on Startup
```bash
# Check which imports are missing:
sudo journalctl -u mecamera -n 50

# Most common fixes:
cd ~/ME_CAM-DEV
source venv/bin/activate
pip install flask-cors  # If missing
pip install -r requirements.txt --upgrade
sudo systemctl restart mecamera
```

### Low FPS (15 instead of 40-60)
```bash
# Check config:
cat ~/ME_CAM-DEV/config/config.json | grep framerate

# Update if needed:
nano ~/ME_CAM-DEV/config/config.json
# Change "framerate": 15 to "framerate": 40 or 60
sudo systemctl restart mecamera
```

### Service Won't Start
```bash
# Check logs for errors:
sudo journalctl -u mecamera -n 50

# Test manually:
cd ~/ME_CAM-DEV
source venv/bin/activate
python3 main.py
# Watch for error messages
```

### NumPy Compatibility Error
```bash
# Use system OpenCV instead of pip version:
source ~/ME_CAM-DEV/venv/bin/activate
pip uninstall opencv-python -y
sudo apt install python3-opencv -y

# Recreate venv with system packages:
cd ~/ME_CAM-DEV
deactivate
rm -rf venv
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart mecamera
```

---

## Multi-Device Setup

### Quick Clone Method (10 min per device)

1. **Create master image:**
   - Shutdown Pi: `sudo shutdown -h now`
   - Remove SD card
   - Use Win32DiskImager or `dd` to create image
   - Save as: `mecam_v2.2.3_master.img`

2. **Flash to new cards:**
   - Flash image to new SD cards
   - Insert in new Pis

3. **Change hostname on each:**
   ```bash
   ssh pi@raspberrypi.local  # Default after clone
   sudo hostnamectl set-hostname mecamdev7  # Or mecamdev8, etc.
   sudo nano /etc/hosts
   # Update line: 127.0.1.1 raspberrypi
   # To:          127.0.1.1 mecamdev7
   sudo reboot
   ```

4. **Verify:**
   ```bash
   ssh pi@mecamdev7.local
   hostname  # Should show mecamdev7
   curl http://localhost:8080  # Should respond
   ```

### Monitor All Devices

```bash
# Check all at once:
for device in mecamdev6 mecamdev7 mecamdev8; do
    echo "=== $device ==="
    ssh pi@$device.local "sudo systemctl is-active mecamera && hostname -I"
done
```

---

## Advanced Features (Optional)

### Remote Access via Tailscale (Recommended)
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```
Access from anywhere: `http://100.x.x.x:8080`

### Port Forwarding
- Forward router port 8080 → Pi IP
- Access: `http://your-public-ip:8080`
- ⚠️ Add authentication first!

### Email Alerts (Already included)
Configure in config.json:
```json
{
    "email_alerts": true,
    "email_from": "your@gmail.com",
    "email_to": "notify@gmail.com",
    "email_password": "app-password"
}
```

---

## Appendix A: Cloud Storage & Push Notifications (v2.2.4)

Want encrypted Google Drive backup and real-time push notifications? 

**Requirements:**
- Google Cloud account (OAuth setup)
- Firebase account (optional, for mobile push)
- Additional 15 minutes setup time

**Benefits:**
- Encrypted cloud backup (AES-256)
- Browser push notifications
- Mobile app notifications
- 30-day cloud retention
- Automatic upload on motion

**Setup Guide:** See original FRESH_SD_CARD_TUTORIAL.md Section 3C

---

## Appendix B: Replit Method (Alternative)

**Note:** GitHub method above is recommended (works on devices 1-6). Use Replit only if you need cloud dashboard.

### One-Command Install
```bash
curl -sSL http://me-cam.replit.app/api/pi-agent/install.sh | sudo bash -s -- https://me-cam.replit.app
```

**What it does:**
- Installs to `/opt/me_cam/`
- Creates `me_cam.service`
- Auto-generates device ID
- Provides cloud dashboard at me-cam.replit.app

**Trade-offs:**
- ✅ Faster setup (5-10 min)
- ✅ Remote dashboard included
- ❌ Less customization
- ❌ No v2.2.4 features (cloud backup, push notifications)
- ❌ Requires internet for dashboard

**Commands:**
```bash
sudo systemctl start me_cam
sudo systemctl status me_cam
sudo journalctl -u me_cam -f
```

---

**Last Updated:** February 9, 2026  
**Tested On:** Raspberry Pi Zero 2W, Debian Bookworm/Trixie  
**Camera:** Arducam IMX519 16MP  
**By:** MangiafestoElectronics LLC
