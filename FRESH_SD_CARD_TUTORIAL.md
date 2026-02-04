# Fresh SD Card to Working Camera - Complete Tutorial

**Date:** January 29, 2026  
**Hardware:** Raspberry Pi Zero 2W (512MB RAM) + IMX519 Camera  
**Goal:** Compare Replit automated installer vs GitHub manual installation

---

## Prerequisites

### Hardware Required
- Raspberry Pi Zero 2W
- IMX519 Camera Module (Arducam)
- MicroSD card (16GB minimum, 32GB recommended)
- MicroSD card reader
- Power supply (5V 2.5A recommended)
- Camera ribbon cable

### Software Required
- [Raspberry Pi Imager](https://www.raspberrypi.com/software/) (Windows/Mac/Linux)
- SSH client (PuTTY on Windows, or built-in terminal on Mac/Linux)
- Your WiFi network name and password

### Network Information
- Router access to find Pi IP address
- OR use `raspberrypi.local` hostname (if mDNS works on your network)

---

## Step 1: Flash SD Card with Raspberry Pi Imager

### 1.1 Download and Install Raspberry Pi Imager
- Download from: https://www.raspberrypi.com/software/
- Install and launch the application

### 1.2 Configure OS Image
1. Click **"CHOOSE OS"**
2. Select: **Raspberry Pi OS (other)** → **Raspberry Pi OS Lite (32-bit)**
   - Why Lite? Smaller footprint, faster boot, no desktop GUI needed
   - Why 32-bit? Better compatibility with older packages on Pi Zero 2W

### 1.3 Choose Storage
1. Insert your microSD card
2. Click **"CHOOSE STORAGE"**
3. Select your SD card (⚠️ WARNING: All data will be erased!)

### 1.4 Pre-Configure Settings (CRITICAL STEP)
1. Click the **⚙️ Gear Icon** (Settings)
2. **General Tab:**
   - ✅ Set hostname: `raspberrypi` (or custom like `mecam4`)
   - ✅ Enable SSH: **Use password authentication**
   - ✅ Set username: `pi`
   - ✅ Set password: `<your-secure-password>`
   - ✅ Configure wireless LAN:
     - SSID: `<your-wifi-name>`
     - Password: `<your-wifi-password>`
     - Country: `US` (or your country code)
   - ✅ Set locale settings:
     - Timezone: `America/New_York` (or your timezone)
     - Keyboard: `us` (or your layout)

3. **Services Tab:**
   - ✅ Enable SSH

4. Click **"SAVE"**

### 1.5 Write Image
1. Click **"WRITE"**
2. Confirm warning prompt
3. Wait 5-10 minutes for write + verification
4. When complete, safely eject SD card

**Total Time: ~10 minutes**

---

## Step 2: Initial Boot and SSH Access

### 2.1 Insert SD Card and Boot
1. Insert SD card into Pi Zero 2W
2. Connect camera module (gently, CSI port with blue tab facing USB ports)
3. Power on the Pi
4. Wait 1-2 minutes for first boot (longer on first boot due to resize)

### 2.2 Find Pi IP Address

**Option A: Check Router**
- Log into your router admin panel
- Look for device named `raspberrypi` or your custom hostname
- Note the IP address (example: `<pi-ip-address>`)

**Option B: Use hostname (if mDNS works)**
```bash
ping raspberrypi.local
```

### 2.3 SSH into Pi

**Windows (PowerShell):**
```powershell
ssh pi@raspberrypi.local
# OR with IP:
ssh pi@<pi-ip-address>
```

**First connection will ask:**
```
Are you sure you want to continue connecting (yes/no)? yes
```

Enter your password when prompted.

**Expected output:**
```
Linux raspberrypi 6.1.21+ #1642 SMP Mon Apr  3 17:20:52 BST 2023 armv7l
pi@raspberrypi:~ $
```

**Total Time: ~2 minutes after boot**

---

## Step 3A: Replit Method (Automated Installer)

### 3A.1 One-Liner Installation

```bash
curl -sSL http://me-cam.replit.app/api/pi-agent/install.sh | sudo bash -s -- https://me-cam.replit.app
```

**What happens automatically:**
1. ✅ Updates system packages (`apt-get update`)
2. ✅ Installs dependencies:
   - python3, python3-pip, python3-venv
   - python3-picamera2, python3-numpy
   - libcamera-apps, libcamera-dev
   - git, curl
3. ✅ Creates `/opt/me_cam/` directory
4. ✅ Downloads all agent files:
   - main.py, config_manager.py
   - motion_detector.py, stream_server.py
   - web_dashboard.py, encryptor.py
5. ✅ Creates Python venv with system packages
6. ✅ Installs Python packages:
   - flask, pillow, qrcode[pil]
   - cryptography, requests, psutil
7. ✅ Generates device ID from CPU serial
8. ✅ Creates config.json
9. ✅ Installs systemd service (`me_cam.service`)
10. ✅ Enables auto-start on boot

**Installation Output:**
```
==================================================
ME_CAM Security Camera Installer
by MangiafestoElectronics LLC
==================================================

[1/7] Updating system packages...
[2/7] Installing system dependencies...
[3/7] Setting up installation directory...
[4/7] Copying agent files...
[5/7] Creating Python virtual environment...
[6/7] Creating configuration...
[7/7] Installing systemd service...

==================================================
ME_CAM Installation Complete!
==================================================

Installation directory: /opt/me_cam
Device ID: pi-cam-abc123456
Dashboard URL: https://me-cam.replit.app

Services (after starting):
   - Local Dashboard: http://<pi-ip-address>:5000
   - Live Stream:     http://<pi-ip-address>:8080/stream.mjpg

Commands:
  sudo systemctl start me_cam     # Start service
  sudo systemctl status me_cam    # Check status
  sudo systemctl restart me_cam   # Restart service
  sudo systemctl stop me_cam      # Stop service
  sudo journalctl -u me_cam -f    # View logs
```

**Total Time: 5-10 minutes**

### 3A.2 Start the Service

```bash
sudo systemctl start me_cam
sudo systemctl status me_cam
```

### 3A.2.1 Replit Dashboard Device Registration & Token (Required)

If motion events show **"Invalid or missing DEVICE_TOKEN"** or **405** errors in logs, you must manually pair the device in the Replit dashboard.

1. Open the Devices page: https://me-cam.replit.app/devices
2. Find your device by **Device ID** (from `/etc/me_cam.conf` on the Pi). This corresponds to the device card in the dashboard.
3. Get the **full token** (not truncated):
   - Open DevTools → Console and run:
     ```javascript
     document.querySelector('[data-testid="text-device-token"]').textContent
     ```
   - Copy the full token.
4. On the Pi, set the token in `/etc/me_cam.conf`:
   ```bash
   sudo nano /etc/me_cam.conf
   # Set: DEVICE_TOKEN=<FULL_TOKEN>
   sudo systemctl restart me_cam
   ```

### 3A.2.2 Replit API Endpoints (Required for Uploads)

If the device logs show **405** errors on upload, your Replit app is missing upload endpoints. Add the API endpoints to the Replit app (dashboard server), then restart the Replit app. Required endpoints:

- `POST /api/snapshot`
- `POST /api/video`
- `POST /api/status`
- `POST /api/motion`

Once added, restart the Pi service:
```bash
sudo systemctl restart me_cam
sudo journalctl -u me_cam -n 20 -f
```

**Expected output:**
```
● me_cam.service - ME_CAM Security Camera Service
     Loaded: loaded (/etc/systemd/system/me_cam.service; enabled)
     Active: active (running) since Wed 2026-01-29 10:30:00 EST
```

### 3A.3 Test Access

**Local Dashboard:**
```
http://<pi-ip-address>:5000
```

**Live Stream:**
```
http://<pi-ip-address>:8080/stream.mjpg
```

**Remote Dashboard:**
```
https://me-cam.replit.app
```

### 3A.4 View Logs
```bash
sudo journalctl -u me_cam -f
```

---

## Step 3B: GitHub Method (Manual Installation)

### 3B.1 Update System

```bash
sudo apt update && sudo apt upgrade -y
```

**Time: 3-5 minutes**

### 3B.2 Install System Dependencies

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
    libatlas-base-dev \
    git
```

**Time: 5-7 minutes**

### 3B.3 Clone Repository

```bash
cd ~
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV
```

### 3B.4 Create Python Virtual Environment

```bash
python3 -m venv venv --system-site-packages
source venv/bin/activate
```

**Note:** `--system-site-packages` allows access to system python3-opencv, avoiding NumPy 2.x compatibility issues.

### 3B.5 Upgrade pip

```bash
pip install --upgrade pip
```

**Output:**
```
Successfully installed pip-25.3
```

### 3B.6 Install Python Packages

```bash
pip install -r requirements.txt
```

**This installs 40+ packages including:**
- Flask==3.0.0, Werkzeug==3.0.0
- cryptography==41.0.0
- qrcode[pil]==7.4.2
- psutil==5.9.5
- yagmail==0.15.293
- pydrive2==1.19.0
- loguru==0.7.2
- And all their dependencies...

**⚠️ Note:** OpenCV is provided by system package (python3-opencv). Some packages compile from source (cffi, Pillow) which takes time on Pi Zero 2W.

**Time: 10-15 minutes**

### 3B.7 Create Configuration

```bash
mkdir -p config
nano config/config.json
```

**Paste this configuration:**
```json
{
    "first_run_completed": true,
    "device_name": "ME_CAM_4",
    "device_id": "pi-cam-004",
    "wifi_ssid": "",
    "wifi_password": "",
    "sensitivity": 0.2,
    "resolution": "640x480",
    "framerate": 15,
    "motion_detection": true,
    "video_length": 30,
    "storage_limit_gb": 50,
    "auto_delete_old": true,
    "stream_enabled": true,
    "stream_port": 8080,
    "web_port": 8080
}
```

**Save:** Ctrl+O, Enter, Ctrl+X

### 3B.8 Test Run

```bash
python3 main.py
```

**Expected output:**
```
2026-02-02 05:53:07.527 | INFO     | __main__:<module>:14 - [MAIN] Pi Zero 2W detected (416MB RAM) - Loading LITE v2.1
[MAIN] Starting ME_CAM LITE v2.1...
[MAIN] Purple gradient UI loaded
[MAIN] Camera: IMX519 detected
[MAIN] Resolution: 640x480 @ 15 FPS
[MAIN] Stream available at: http://0.0.0.0:8080/stream.mjpg
[MAIN] Dashboard running on: http://0.0.0.0:8080
```

**Test dashboard from your computer:**
```
http://<pi-hostname>.local:8080
# OR use Pi's IP address:
http://10.2.1.3:8080
```

**⚠️ Important:** Use the Pi's IP address or hostname, NOT `127.0.0.1` or `localhost` (those only work from the Pi itself).

Press Ctrl+C to stop.

### 3B.9 Create Systemd Service

```bash
sudo nano /etc/systemd/system/mecamera.service
```

**Paste this configuration:**
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

**Save:** Ctrl+O, Enter, Ctrl+X

### 3B.10 Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable mecamera
sudo systemctl start mecamera
sudo systemctl status mecamera
```

**Expected output:**
```
● mecamera.service - ME_CAM Security Camera
     Loaded: loaded (/etc/systemd/system/mecamera.service; enabled)
     Active: active (running) since Wed 2026-01-29 10:45:00 EST
```

**Total Time: 20-30 minutes**

### 3B.11 View Logs

```bash
sudo journalctl -u mecamera -f
```

---

## Step 4: Verification and Testing

### 4.1 Check Services

**Replit:**
```bash
sudo systemctl status me_cam
```

**GitHub:**
```bash
sudo systemctl status mecamera
```

### 4.2 Test Stream

Open browser to:
```
http://<pi-ip-address>:8080/stream.mjpg
```

**Expected:** Live camera feed

### 4.3 Test Dashboard

**Replit Local:**
```
http://<pi-ip-address>:5000
```

**Replit Remote:**
```
https://me-cam.replit.app
```

**GitHub:**
```
http://<pi-ip-address>:8080
```

### 4.4 Test Auto-Boot

```bash
sudo reboot
```

Wait 1-2 minutes, then check if service auto-started:

```bash
ssh pi@<ip-address>
sudo systemctl status me_cam    # or mecamera
```

### 4.5 Check System Resources

```bash
free -h
df -h
vcgencmd measure_temp
```

**Expected on Pi Zero 2W:**
- RAM: ~416MB total, ~150-200MB used
- Storage: Depends on SD card size
- Temp: 40-55°C idle, 55-70°C under load

---

## Comparison Table

| Feature | Replit Method | GitHub Method |
|---------|---------------|---------------|
| **Installation Time** | 5-10 minutes | 20-30 minutes |
| **Commands Required** | 1 command | 15+ commands |
| **Internet Required** | Yes (downloads from Replit) | Yes (apt + pip) |
| **Python Packages** | 8 packages | 40+ packages |
| **Install Location** | `/opt/me_cam` | `/home/pi/ME_CAM-DEV` |
| **Service Name** | `me_cam.service` | `mecamera.service` |
| **Local Dashboard** | Port 5000 | Port 8080 (combined) |
| **Stream Port** | Port 8080 | Port 8080 |
| **Remote Dashboard** | ✅ Yes (Replit cloud) | ❌ No (local only) |
| **Auto-Configuration** | ✅ Yes (device ID from CPU) | ❌ Manual config.json |
| **Architecture** | Multi-process (3 services) | Monolithic Flask app |
| **Auto-Restart** | ✅ Built into main.py | ✅ Via systemd |
| **UI Mode** | Standard | Auto-detects LITE for Pi Zero 2W |
| **Version Control** | Latest from Replit | Git branches available |
| **Customization** | Limited | Full source access |
| **Dependencies** | System packages + minimal pip | Everything via pip |
| **Compilation** | ❌ No (uses system OpenCV) | ⚠️ Minimal (cffi, Pillow only, uses system OpenCV) |
| **Offline Operation** | ⚠️ Needs dashboard URL | ✅ Fully local |
| **Update Process** | Re-run installer | `git pull` + `pip install` |
| **File Structure** | Flat (all .py in one dir) | Organized (web/, config/, utils/) |
| **Email Alerts** | ❌ Not in installer | ✅ Via yagmail |
| **Cloud Backup** | ❌ Not in installer | ✅ Via pydrive2 |
| **Setup Mode** | ✅ QR code setup | ❌ Manual config |

---

## Architecture Comparison

### Replit Multi-Process Architecture
```
main.py (supervisor)
├── motion_detector.py (subprocess) - Detects motion, records clips
├── web_dashboard.py (subprocess)   - Flask UI on port 5000
└── stream_server.py (subprocess)   - MJPEG stream on port 8080
```

**Advantages:**
- Process isolation (one crash doesn't kill all)
- Auto-restart failed services
- Cleaner separation of concerns

**Disadvantages:**
- More memory overhead (3 Python processes)
- Inter-process communication needed

### GitHub Monolithic Architecture
```
main.py
└── Flask app (single process)
    ├── Dashboard routes (/)
    ├── Stream routes (/stream.mjpg)
    ├── API routes (/api/*)
    └── Motion detection (threading)
```

**Advantages:**
- Lower memory usage (1 Python process)
- Easier state sharing
- Better for Pi Zero 2W (512MB RAM)

**Disadvantages:**
- Single point of failure
- More complex codebase

---

## Which Method Should You Use?

### Choose **Replit** if:
- ✅ You want the fastest setup (5-10 minutes)
- ✅ You need remote dashboard access
- ✅ You're deploying multiple cameras quickly
- ✅ You don't need email/cloud backup features
- ✅ You prefer automated configuration
- ✅ You want minimal dependencies

### Choose **GitHub** if:
- ✅ You need offline/local-only operation
- ✅ You want email alerts on motion
- ✅ You need cloud backup (Google Drive)
- ✅ You want to customize the code
- ✅ You need specific package versions
- ✅ You prefer organized project structure
- ✅ You want Git version control
- ✅ You're comfortable with longer setup time (25-35 minutes)

---

## Troubleshooting

### Issue: Pi won't connect to WiFi
**Solution:**
1. Re-flash SD card with correct WiFi credentials
2. Check WiFi country code matches your location
3. Verify 2.4GHz network (Pi Zero 2W doesn't support 5GHz)

### Issue: Can't find Pi IP address
**Solution:**
```bash
# On Windows PowerShell:
arp -a | Select-String "raspberrypi"

# Or use network scanner:
# Download Advanced IP Scanner (Windows)
```

### Issue: SSH connection refused
**Solution:**
1. Verify SSH was enabled in Imager settings
2. Wait 2-3 minutes after first boot
3. Check Pi has green LED activity (SD card access)

### Issue: Camera not detected (Replit)
**Solution:**
```bash
sudo journalctl -u me_cam -n 50
# Check for camera errors

# Test camera manually:
rpicam-jpeg -o test.jpg --width 1280 --height 720
```

### Issue: Camera not detected (GitHub)
**Solution:**
```bash
sudo journalctl -u mecamera -n 50

# Test camera:
rpicam-jpeg -o test.jpg --width 640 --height 480
```

### Issue: ImportError - cannot import name 'get_ram_mb'
**Symptoms:**
- `ImportError: cannot import name 'get_ram_mb' from 'src.utils.pi_detect'`
- Application fails during startup with import error

**Fix:**
Ensure you have the latest version of `main.py`. The correct function name is `get_total_ram()` not `get_ram_mb()`:
```bash
cd ~/ME_CAM-DEV
git pull origin main
```

---

### Issue: NumPy compatibility error with OpenCV
**Symptoms:**
- `ImportError: numpy.core.multiarray failed to import`
- `AttributeError: _ARRAY_API not found`
- `A module that was compiled using NumPy 1.x cannot be run in NumPy 2.4.2`

**Root Cause:**
Pip's opencv-python requires NumPy 1.x but pip installs NumPy 2.x by default. Compiling NumPy 1.x from source fails on Pi Zero 2W due to limited RAM.

**Fix (Use system python3-opencv):**
```bash
# Stop service
sudo systemctl stop mecamera

# Uninstall pip's opencv-python
source venv/bin/activate
pip uninstall opencv-python -y

# Install system opencv
sudo apt install python3-opencv -y

# Recreate venv with system site packages
deactivate
cd ~/ME_CAM-DEV
rm -rf venv
python3 -m venv venv --system-site-packages
source venv/bin/activate

# Reinstall requirements (skips opencv now)
pip install -r requirements.txt

# Verify opencv works
python3 -c "import cv2; print('OpenCV:', cv2.__version__)"

# Restart service
sudo systemctl restart mecamera
```

---

### Issue: Can't access dashboard - "refused to connect"
**Symptoms:**
- Browser shows "127.0.0.1 refused to connect"
- Logs show: `Running on http://127.0.0.1:8080` and `Running on http://10.2.1.3:8080`
- Service is running correctly

**Root Cause:**
You're trying to access `127.0.0.1` (localhost) from your computer, but that address only works **on the Pi itself**.

**Fix:**
Use the Pi's actual IP address or hostname from your computer:
```
http://<pi-hostname>.local:8080
# OR
http://10.2.1.3:8080
```

**To find Pi's IP:**
```bash
ssh pi@<pi-hostname>.local
hostname -I
```

---

### Issue: IMX519 shows "no cameras available" or "failed to read chip id"
**Symptoms:**
- `ERROR: *** no cameras available ***`
- `imx519 ... failed to read chip id 519`

**Fix (force IMX519 overlay):**
```bash
# Stop the service first (Replit or GitHub)
sudo systemctl stop me_cam || true
sudo systemctl stop mecamera || true

# Edit boot config (Bookworm/Trixie)
sudo nano /boot/firmware/config.txt
```

Add these lines:
```
camera_auto_detect=0
dtoverlay=imx519
dtparam=i2c_vc=on
```

Reboot and re-test:
```bash
sudo reboot
```

After reboot:
```bash
rpicam-jpeg -o test.jpg --width 1280 --height 720
```

If it works, restart the service:
```bash
sudo systemctl start me_cam || true
sudo systemctl start mecamera || true
```

### Issue: Out of memory on Pi Zero 2W
**Solution:**
```bash
# Increase swap:
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### Issue: Service fails to start
**Solution:**
```bash
# Replit:
sudo systemctl status me_cam
sudo journalctl -u me_cam -n 100

# GitHub:
sudo systemctl status mecamera
sudo journalctl -u mecamera -n 100

# Common fixes:
sudo systemctl restart me_cam    # or mecamera
sudo reboot
```

### Issue: Can't access dashboard
**Solution:**
1. Find Pi IP: `hostname -I`
2. Test stream directly: `http://<ip>:8080/stream.mjpg`
3. Check firewall (usually not needed on local network)
4. Verify service is running

---

## Next Steps After Installation

### 1. Test Motion Detection
- Walk in front of camera
- Check logs: `sudo journalctl -u me_cam -f` (or mecamera)
- Verify video clips saved in motion_videos/

### 2. Adjust Settings

**Replit:**
```bash
sudo nano /opt/me_cam/config.json
sudo systemctl restart me_cam
```

**GitHub:**
```bash
nano ~/ME_CAM-DEV/config/config.json
sudo systemctl restart mecamera
```

### 3. Set Up Remote Access (Optional)

**Option A: Port Forwarding**
- Forward port 8080 on router to Pi IP
- Access: `http://<your-public-ip>:8080`

**Option B: Tailscale VPN**
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

**Option C: ngrok**
```bash
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
ngrok config add-authtoken <your-token>
ngrok http 8080
```

### 4. Monitor System Health

```bash
# CPU temperature:
vcgencmd measure_temp

# Memory usage:
free -h

# Disk space:
df -h

# Service uptime:
sudo systemctl status me_cam    # or mecamera

# Recent logs:
sudo journalctl -u me_cam -n 50
```

### 5. Backup Configuration

```bash
# Replit:
sudo cp /opt/me_cam/config.json ~/config_backup.json

# GitHub:
cp ~/ME_CAM-DEV/config/config.json ~/config_backup.json
```

---

## Quick Reference Commands

### Replit System
```bash
# Service control
sudo systemctl start me_cam
sudo systemctl stop me_cam
sudo systemctl restart me_cam
sudo systemctl status me_cam

# Logs
sudo journalctl -u me_cam -f        # Follow logs
sudo journalctl -u me_cam -n 100    # Last 100 lines

# Configuration
sudo nano /opt/me_cam/config.json
sudo systemctl restart me_cam

# Manual start (for testing)
cd /opt/me_cam
source venv/bin/activate
python3 main.py
```

### GitHub System
```bash
# Service control
sudo systemctl start mecamera
sudo systemctl stop mecamera
sudo systemctl restart mecamera
sudo systemctl status mecamera

# Logs
sudo journalctl -u mecamera -f      # Follow logs
sudo journalctl -u mecamera -n 100  # Last 100 lines

# Configuration
nano ~/ME_CAM-DEV/config/config.json
sudo systemctl restart mecamera

# Manual start (for testing)
cd ~/ME_CAM-DEV
source venv/bin/activate
python3 main.py

# Update code
git pull
pip install -r requirements.txt
sudo systemctl restart mecamera
```

---

## Summary

You now have a complete tutorial for deploying ME_CAM on a Raspberry Pi Zero 2W from a fresh SD card using either:

1. **Replit Method:** 1 command, 10 minutes, remote dashboard
2. **GitHub Method:** Full control, 30 minutes, local operation

Both methods work reliably on Pi Zero 2W with IMX519 camera. Choose based on your needs for automation vs customization.

---

**Created:** January 29, 2026  
**Tested On:** Raspberry Pi Zero 2W, Bullseye Lite 32-bit  
**Camera:** IMX519 (Arducam)  
**By:** MangiafestoElectronics LLC
