# Fresh SD Card to Working Camera - Simple Guide

**Version:** ME_CAM v2.2.3  
**Hardware:** Raspberry Pi Zero 2W + IMX519 (I2C) or OV547 Camera  
**Time:** 30 minutes total  
**Method:** GitHub repository (proven stable on devices 1, 2, 3)

**Hardware Compatibility:**

| Model | Architecture | RAM | Speed | Best For | Notes |
|-------|--------------|-----|-------|----------|-------|
| **Pi Zero 2W** | ARM v7 (32-bit) | 512MB | 1 GHz quad-core | Budget deployment, single camera | Lite OS only (32-bit). Slower, but sufficient for one camera. Fits tight spaces. |
| **Pi 5** | ARM v8 (64-bit) | 4GB+ | 2.4 GHz 8-core | Performance, multi-camera hub | Full OS (64-bit). 4-8x faster, better multitasking. Runs full ME_CAM stack easily. |

**Device Notes:**
- **Device 3:** Pi Zero 2W + IMX519 over I2C (use IMX519 overlay below)
- **Device 4:** Pi Zero 2W + OV547 OmniVision (same setup flow as Device 6 with OV547 overlay)
- **Device 7:** Pi 5 (4GB) + Any camera (IMX519 or OV547) — **Recommended for testing/hub**

**Developer Note (Use This Doc):** This guide is the developer/installer workflow. The customer-facing guide is in CUSTOMER_INSTRUCTION_MANUAL.md.

---

## What You Need

**Hardware:**
- Raspberry Pi Zero 2W
- IMX519 Camera Module (I2C) for Device 3
- OV547 Camera Module (OmniVision) for Device 4
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

**Choose the correct OS for your Pi:**

#### For Raspberry Pi Zero 2W (Devices 3, 4):
1. Click **CHOOSE OS** → **Raspberry Pi OS (other)** → **Raspberry Pi OS Lite (32-bit)**
2. Click **CHOOSE STORAGE** → Select your SD card
3. Click **⚙️ Settings Icon**:
    - ✅ Set hostname: `mecamdev3` or `mecamdev4`
    - ✅ Enable SSH (password authentication)
    - ✅ Username: `pi`
    - ✅ Password: (your secure password)
    - ✅ Configure WiFi:
      - SSID: (your network name)
      - Password: (your WiFi password)
      - Country: `US`
    - ✅ Set timezone: `America/New_York` (or yours)
4. Click **SAVE**, then **WRITE**

#### For Raspberry Pi 5 (Device 7 and later):
1. Click **CHOOSE OS** → **Raspberry Pi OS (other)** → **Raspberry Pi OS Lite (64-bit)** ← **64-bit, NOT 32-bit**
2. Click **CHOOSE STORAGE** → Select your SD card
3. Click **⚙️ Settings Icon**:
    - ✅ Set hostname: `mecamdev7` (or `mecamdev8`, `mecamdev9`, etc.)
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
ssh pi@mecamdev1.local  # Device 1
# or
ssh pi@mecamdev2.local  # Device 2
# or
ssh pi@mecamdev3.local  # Device 3 (Pi Zero 2W)
# or
ssh pi@mecamdev4.local  # Device 4 (Pi Zero 2W)
# or
ssh pi@mecamdev5.local  # Device 5
# or
ssh pi@mecamdev6.local  # Device 6
# or
ssh pi@mecamdev7.local  # Device 7 (Pi 5 - 4GB)
# Enter your password when prompted
```

**Expected:** `pi@mecamdev3:~ $` or `pi@mecamdev7:~ $`

---

## Step 3: Install ME_CAM (20 minutes)

### 3.1 Update System
```bash
sudo apt update
```
*(3-5 minutes)*

If `apt update` reports a release metadata change, run:

```bash
sudo apt update --allow-releaseinfo-change
```

Only if APT is broken/corrupted (not for normal fresh flash), run recovery:

```bash
sudo apt clean
sudo rm -rf /var/lib/apt/lists/*
sudo apt update --allow-releaseinfo-change
sudo dpkg --configure -a
sudo apt --fix-broken install -y
```

**Important (fresh SD cards):** Do **not** run full `apt upgrade` before dependencies. Install app dependencies first to avoid large kernel/system upgrades during initial provisioning.

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

If your network is unstable, retry with:
```bash
sudo apt install --fix-missing -o Acquire::Retries=5 -y \
   python3-pip python3-venv libcamera-apps python3-picamera2 \
   python3-opencv python3-dev libffi-dev libjpeg-dev zlib1g-dev git
```

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

Optional (only if you need WebRTC remote streaming on capable hardware):
```bash
pip install -r requirements-webrtc.txt
```

If your cloned repo is older and `pip install -r requirements.txt` still tries to install `aiortc`/`av`, remove those lines and retry:
```bash
cp requirements.txt requirements.txt.bak
sed -i '/^aiortc/d;/^av>=/d' requirements.txt
pip install -r requirements.txt
```

### 3.5 Generate Configuration (Automated)
Use the built-in generator instead of creating `config.json` manually:

```bash
# Device 3 (Pi Zero 2W + IMX519)
python3 scripts/generate_config.py --profile device3

# Device 4 (Pi Zero 2W + OV547)
python3 scripts/generate_config.py --profile device4

# Device 7 (Pi 5 testing/hub)
python3 scripts/generate_config.py --profile device7
```

If `config/config.json` already exists (re-run on same device), use `--force`:

```bash
python3 scripts/generate_config.py --profile device3 --force
```

Optional: set a custom device number while keeping profile defaults:

```bash
python3 scripts/generate_config.py --profile device7 --device-number 8 --force
```

Verify:

```bash
cat config/config.json
```

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

**Test in browser:** `http://mecamdev3.local:8080` or `http://mecamdev4.local:8080` or `http://mecamdev7.local:8080`

**First Login Flow (Security):**
1. Sign in with the temporary admin credentials you created during setup.
2. You will be redirected to **/customer-setup** to create the customer account.
3. The temporary admin account is removed automatically.
4. All future logins must use the customer credentials.

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
Open browser: `http://mecamdev3.local:8080` or `http://mecamdev4.local:8080` or `http://mecamdev7.local:8080`

**Expected:** Purple dashboard with live camera feed (Pi 5 should be smoother at higher FPS)

### 4.3 Test Auto-Boot
```bash
sudo reboot
```

Wait 2 minutes, then check: `http://mecamdev3.local:8080` or `http://mecamdev4.local:8080` or `http://mecamdev7.local:8080`

---

## ✅ Done!

Your camera is working at: `http://mecamdev3.local:8080` or `http://mecamdev4.local:8080` or `http://mecamdev7.local:8080`

**Performance expectations:**
- **Pi Zero 2W:** Smooth 30-40 FPS, single camera, minimal resources
- **Pi 5 (4GB):** Smooth 60+ FPS, higher resolution, multi-camera capable

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

# If app says libcamera not installed:
which rpicam-hello || which libcamera-hello
sudo apt install -y libcamera-apps python3-picamera2

# If fails, force IMX519 overlay (Device 3, I2C):
sudo nano /boot/firmware/config.txt
# Add under [all]:
camera_auto_detect=0
dtoverlay=imx519
gpu_mem=128

sudo reboot
```

### Device 6 Camera Swapped (IMX519 ↔ OV5647) and Feed Is Blank
When you physically switch sensors, use a switch-safe profile before reboot so the next boot comes up cleanly.

```bash
cd ~/ME_CAM-DEV

# Recommended for frequent camera swaps:
sudo python3 scripts/set_camera_profile.py --profile auto

# Then reboot
sudo reboot
```

After reboot, verify camera detection:
```bash
rpicam-hello --list-cameras
```

If you want to pin a specific sensor instead of auto:
```bash
# IMX519
sudo python3 scripts/set_camera_profile.py --profile imx519

# OV5647
sudo python3 scripts/set_camera_profile.py --profile ov5647

# OV547
sudo python3 scripts/set_camera_profile.py --profile ov547

sudo reboot
```

Notes:
- `auto` is best when Device 6 hardware changes often.
- Script backups are created automatically as `/boot/firmware/config.txt.mecam_backup_*`.
- If `rpicam-hello --list-cameras` still shows no camera, reseat/replace CSI ribbon and power-cycle.

**Device 4 (OV547 OmniVision) overlay:**
```bash
sudo nano /boot/firmware/config.txt
# Add under [all]:
camera_auto_detect=0
dtoverlay=ov547
gpu_mem=128

sudo reboot
```

### Can't Access Dashboard
- ✅ Use Pi's IP or hostname, NOT `127.0.0.1`
- ✅ Find IP: `hostname -I` on the Pi
- ✅ Try: `http://10.2.1.x:8080` (your Pi's IP)

### Device 7 Not Detected (Pi 5 Fresh Install)
```bash
# On Device 7 (local console or SSH by IP):
hostname
hostname -I
cat /etc/hostname
grep 127.0.1.1 /etc/hosts
sudo systemctl status mecamera
curl -s http://localhost:8080/api/status
```

If hostname is wrong, fix and reboot:
```bash
sudo hostnamectl set-hostname mecamdev7
sudo nano /etc/hosts
# Ensure line is:
# 127.0.1.1 mecamdev7
sudo reboot
```

Then test from your PC:
```bash
ssh pi@mecamdev7.local
curl http://mecamdev7.local:8080/api/status
```

If `.local` does not resolve, use IP directly (`http://<device7-ip>:8080`).

### Device 6 Shows Offline But Has Power
Power does not guarantee network/app health. Check:
```bash
# From your PC:
ssh pi@mecamdev6.local "hostname -I; sudo systemctl is-active mecamera; sudo journalctl -u mecamera -n 40"

# On Device 6:
vcgencmd measure_temp
free -h
df -h
iwgetid
```

If service is not active:
```bash
sudo systemctl restart mecamera
sudo systemctl status mecamera
```

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

### Device 5/6 Fast Recovery (Feb 26, 2026)
If Device 5 or 6 fails with either of these errors:
- `Failed to build 'av'` while installing dependencies
- `ValueError: source code string cannot contain null bytes`

Run this from your Windows workstation in the repo root:

```powershell
.\repair_device5_6.ps1
```

This pushes and runs `repair_device5_6.sh` on `mecamdev5.local` and `mecamdev6.local`, then:
- hard-resets repo to latest `origin/main` or `origin/master`
- rebuilds venv with `--system-site-packages`
- removes accidental `aiortc`/`av` lines from base `requirements.txt`
- reinstalls dependencies
- checks all `.py` files for null-byte corruption
- regenerates config for each device number

Then test each device:

```bash
ssh pi@mecamdev5.local
cd ~/ME_CAM-DEV
source venv/bin/activate
python3 main.py
```

```bash
ssh pi@mecamdev6.local
cd ~/ME_CAM-DEV
source venv/bin/activate
python3 main.py
```

Important: in terminal, run raw commands only. Do not paste Markdown links like:
`python3 [generate_config.py](...)`.
Use:
`python3 scripts/generate_config.py --profile device4 --device-number 5 --force`

### APT/DPKG Corruption (`not a Debian format archive`, `status` parse errors)
This indicates corrupted package cache and/or filesystem writes (often SD card, power, or interrupted writes).

```bash
# 1) Restore dpkg status file from backup
sudo cp /var/backups/dpkg.status.0 /var/lib/dpkg/status
sudo cp /var/backups/dpkg.status.0 /var/lib/dpkg/status-old

# 2) Clear all broken cached .deb files and apt lists
sudo rm -f /var/cache/apt/archives/*.deb
sudo apt clean
sudo rm -rf /var/lib/apt/lists/*

# 3) Rebuild package metadata and repair state
sudo apt update --allow-releaseinfo-change
sudo dpkg --configure -a
sudo apt --fix-broken install -y

# 4) Install ME_CAM dependencies (no full apt upgrade yet)
sudo apt install --fix-missing -o Acquire::Retries=5 -y \
   python3-pip python3-venv libcamera-apps python3-picamera2 \
   python3-opencv python3-dev libffi-dev libjpeg-dev zlib1g-dev git
```

If this repeats on a fresh card, verify hardware before retrying:
```bash
sudo dmesg -T | egrep -i "mmc|i/o error|ext4|corrupt|voltage|under-voltage"
```
Use a known-good PSU (5V 2.5A+) and a high-endurance SD card.

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

### Tailscale + Config Hardening Tutorial
Use this flow after Tailscale is connected so the camera only accepts VPN clients.

1) Install and connect Tailscale on the Pi:
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
tailscale ip -4
```

2) Open camera config in browser and sign in:
- `http://<device-ip>:8080/config`

3) In `config/config.json`, under `security`, set:
```json
{
   "security": {
      "tailscale_only": true,
      "allow_localhost": true,
      "allow_setup_without_vpn": false,
      "session_timeout_minutes": 720
   }
}
```

4) Save and restart app service:
```bash
sudo systemctl restart mecamera
```

5) Validate policy:
- From local LAN browser: API/dashboard should be blocked (`403`) when not on Tailscale.
- From a Tailscale-connected device: camera should load at `http://<tailscale-ip>:8080`.

6) Emergency rollback (local LAN access restore):
```bash
cd ~/ME_CAM-DEV
python3 - << 'PY'
import json
from pathlib import Path
p = Path('config/config.json')
cfg = json.loads(p.read_text())
sec = cfg.setdefault('security', {})
sec['tailscale_only'] = False
cfg['security'] = sec
p.write_text(json.dumps(cfg, indent=2))
print('tailscale_only disabled')
PY
sudo systemctl restart mecamera
```

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

**Last Updated:** February 26, 2026  
**Tested On:** Raspberry Pi Zero 2W, Debian Bookworm/Trixie  
**Camera:** Arducam IMX519 16MP  
**By:** MangiafestoElectronics LLC
