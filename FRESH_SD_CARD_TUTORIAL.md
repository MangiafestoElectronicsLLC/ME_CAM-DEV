# Fresh SD Card to Working Camera - Simple Guide

**Version:** v2.2.3  
**Hardware:** Raspberry Pi Zero 2W + IMX519 Camera  
**Time:** 30 minutes from SD card to working camera  
**Method:** GitHub repository (Proven stable)

---

## What You Need

**Hardware:**
- Raspberry Pi Zero 2W
- IMX519 Camera Module (Arducam)  
- MicroSD card (16GB+)
- Power supply (5V 2.5A)

**Software:**
- [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
- WiFi credentials

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

## Step 3: Install ME_CAM (GitHub Method)

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

### 3.1 Update System

```bash
sudo apt update && sudo apt upgrade -y
```

**Time: 3-5 minutes**

### 3.2 Install System Dependencies

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

### 3.3 Clone Repository

```bash
cd ~
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV
```

### 3.4 Create Python Virtual Environment

```bash
python3 -m venv venv --system-site-packages
source venv/bin/activate
```

**Note:** `--system-site-packages` allows access to system python3-opencv, avoiding NumPy 2.x compatibility issues.

### 3.5 Upgrade pip

```bash
pip install --upgrade pip
```

**Output:**
```
Successfully installed pip-25.3
```

### 3.6 Install Python Packages

```bash
pip install -r requirements.txt
```

**This installs 45+ packages including:**
- Flask==3.0.0, Werkzeug==3.0.0
- cryptography==42.0.0 (upgraded for v2.2.4)
- **NEW:** pywebpush==1.14.0 (web push notifications)
- **NEW:** py-vapid==1.9.0 (VAPID authentication)
- **NEW:** firebase-admin==6.3.0 (mobile notifications)
- pydrive2==1.19.0 (cloud storage)
- qrcode[pil]==7.4.2
- psutil==5.9.5
- yagmail==0.15.293
- loguru==0.7.2
- And all their dependencies...

**⚠️ Note:** OpenCV is provided by system package (python3-opencv). Some packages compile from source (cffi, Pillow) which takes time on Pi Zero 2W.

**Time: 15-20 minutes**

### 3.7 Create Configuration

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

### 3.8 Test Run

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

### 3.9 Create Systemd Service

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

### 3.10 Enable and Start Service

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

### 3.11 View Logs

```bash
sudo journalctl -u mecamera -f
```

**🎉 Installation Complete!**

Your camera is now running at: `http://<pi-ip-address>:8080`

---

## Step 4: Verification

### 4.1 Check Service Status

```bash
cd ~/ME_CAM-DEV
source venv/bin/activate
pip install cryptography==42.0.0 pywebpush==1.14.0 py-vapid==1.9.0 firebase-admin==6.3.0
```

### 3C.2 Setup Google Drive for Cloud Backup

**Step 1: Create Google Cloud Project**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: "ME_CAM_Cloud_Backup"
3. Enable Google Drive API:
   - APIs & Services → Library → Search "Google Drive API" → Enable
4. Create OAuth 2.0 credentials:
   - APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID
   - Application type: **Desktop app**
   - Name: "ME_CAM Desktop"
   - Download JSON

**Step 2: Configure on Pi**
```bash
# Create config directory if it doesn't exist
mkdir -p ~/ME_CAM-DEV/config

# Upload the downloaded JSON file to the Pi
# On your computer (from download folder):
scp client_secrets.json pi@mecamdev6.local:~/ME_CAM-DEV/config/

# On the Pi, verify file exists:
ls -la ~/ME_CAM-DEV/config/client_secrets.json

# Set secure permissions:
chmod 600 ~/ME_CAM-DEV/config/client_secrets.json
```

### 3C.3 Setup Firebase for Mobile Push Notifications (Optional)

**Step 1: Create Firebase Project**
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create new project: "ME_CAM_Notifications"
3. Add web app or mobile app (Android/iOS)
4. Get Service Account Key:
   - Project Settings → Service Accounts
   - Generate new private key → Download JSON

**Step 2: Configure on Pi**
```bash
# Upload Firebase service account JSON
scp firebase_service_account.json pi@mecamdev6.local:~/ME_CAM-DEV/config/

# Set secure permissions:
chmod 600 ~/ME_CAM-DEV/config/firebase_service_account.json
```

### 3C.4 Access Configuration Web UIs

**Step 1: Restart the service**
```bash
sudo systemctl restart mecamera
```

**Step 2: Open web interfaces**

From your computer's browser:

**Cloud Storage Settings:**
```
http://mecamdev6.local:8080/cloud_settings
```

**Steps in Cloud Settings:**
1. Click "Authenticate Google Drive"
2. Complete OAuth flow in popup window
3. Enable "Cloud Backup" toggle
4. Configure upload schedule (Immediate recommended)
5. Enable Compression (saves space)
6. Enable Encryption (for privacy)
7. Set retention policy (7 days local, 30 days cloud)
8. Click "Save Settings"
9. Click "Test Upload" to verify

**Notification Settings:**
```
http://mecamdev6.local:8080/notification_settings
```

**Steps in Notification Settings:**
1. **Web Push (Browser Notifications):**
   - Click "Subscribe" button
   - Allow notifications when browser prompts
   - Click "Send Test" to verify
   
2. **FCM (Mobile Notifications):**
   - Get FCM token from mobile app
   - Paste token in field
   - Enter device name
   - Click "Register Device"
   - Click "Send Test" to verify

3. **Configure Preferences:**
   - Enable Motion Detection Alerts
   - Enable Security Alerts
   - Include Snapshot Images
   - Set Quiet Hours (optional)
   - Click "Save All Settings"

### 3C.5 Verify Cloud Upload Integration

Test that motion detection triggers cloud upload:

```bash
# Watch logs in real-time
sudo journalctl -u mecamera -f

# In another terminal, trigger motion
# Walk in front of camera

# You should see:
# [MOTION] Motion detected!
# [CLOUD] Queued files for cloud upload
# [CLOUD] Uploaded: snapshot_xxx.jpg → file_id_abc123
# [WEBPUSH] Sent web push notifications
```

**Check Google Drive:**
1. Open your Google Drive
2. Look for folder: `MECAM_Recordings/2026/02/06/`
3. You should see encrypted files: `filename.mp4.gz.enc`

### 3C.6 Test Decryption (Verify Backup Works)

```bash
cd ~/ME_CAM-DEV
source venv/bin/activate
python3 << 'EOF'
from src.cloud.encrypted_cloud_storage import get_cloud_storage
import os

cloud = get_cloud_storage()

# List recent uploads
stats = cloud.get_stats()
print(f"Total uploaded: {stats['total_uploaded']} files")
print(f"Total data: {stats['total_bytes'] / 1024 / 1024:.1f} MB")

# To decrypt a file later:
# 1. Download encrypted file from Google Drive
# 2. Use cloud.decrypt_file(encrypted_path, output_path, metadata)
EOF
```

**⚠️ CRITICAL: Backup Encryption Key**
```bash
# Your encryption key is stored here:
ls -la ~/ME_CAM-DEV/config/cloud_encryption.key

# BACKUP THIS FILE! Without it, you cannot decrypt uploaded files
# Copy to safe location:
scp pi@mecamdev6.local:~/ME_CAM-DEV/config/cloud_encryption.key ~/mecam_backup/
```

### 3C.7 Multi-Device Deployment

To replicate this setup on additional devices:

**Option 1: Clone SD Card (Fastest)**
1. Shutdown Pi: `sudo shutdown -h now`
2. Remove SD card
3. Use Win32DiskImager or dd to create image
4. Flash image to new SD cards
5. Boot each device
6. **Change hostname on each device:**
   ```bash
   sudo nano /etc/hostname
   # Change to: mecamdev7, mecamdev8, etc.
   sudo nano /etc/hosts
   # Update 127.0.1.1 line to match new hostname
   sudo reboot
   ```

**Option 2: Automated Script (Recommended)**
1. Flash fresh SD card with Raspberry Pi Imager (Step 1)
2. Boot and SSH into new device
3. Run deployment script:
   ```bash
   cd ~/ME_CAM-DEV
   
   # Copy deployment script from this repo
   chmod +x deploy_cloud_push_v2.2.4.sh
   ./deploy_cloud_push_v2.2.4.sh
   ```
4. Copy config files from master device:
   ```bash
   # On new device:
   scp pi@mecamdev6.local:~/ME_CAM-DEV/config/client_secrets.json ~/ME_CAM-DEV/config/
   scp pi@mecamdev6.local:~/ME_CAM-DEV/config/firebase_service_account.json ~/ME_CAM-DEV/config/
   
   # DO NOT copy cloud_encryption.key - each device should have unique key
   # OR copy it if you want all devices to share same encryption key
   ```
5. Configure device name in dashboard
6. Test cloud upload and notifications

**Option 3: Fresh Install Per Device**
Follow all steps in this tutorial for each device.

### 3C.8 Monitoring Multiple Devices

**Check Status Remotely:**
```bash
# From your computer
ssh pi@mecamdev6.local "sudo systemctl status mecamera"
ssh pi@mecamdev7.local "sudo systemctl status mecamera"
ssh pi@mecamdev8.local "sudo systemctl status mecamera"
```

**View Recent Uploads:**
```bash
ssh pi@mecamdev6.local "cat ~/ME_CAM-DEV/logs/cloud_upload_stats.json"
```

**Broadcast Test Notification:**
Open any device's notification settings:
```
http://mecamdev6.local:8080/notification_settings
```
Click "Broadcast Test to All Devices" - all subscribed browsers and mobile devices receive notification.

---

**Total Time with v2.2.4 Setup: 35-45 minutes per device**



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

| Feature | Replit Method | GitHub Method (v2.2.4) |
|---------|---------------|------------------------|
| **Installation Time** | 5-10 minutes | 20-30 minutes |
| **v2.2.4 Setup Time** | N/A | +15 minutes (cloud/notifications) |
| **Commands Required** | 1 command | 15+ commands |
| **Internet Required** | Yes (downloads from Replit) | Yes (apt + pip) |
| **Python Packages** | 8 packages | 45+ packages |
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
| **Cloud Backup** | ❌ Not in installer | ✅ **NEW v2.2.4:** Encrypted Google Drive |
| **Encryption** | ❌ Not available | ✅ **NEW v2.2.4:** AES-256-GCM |
| **Web Push Notifications** | ❌ Not available | ✅ **NEW v2.2.4:** Browser notifications |
| **Mobile Notifications** | ❌ Not available | ✅ **NEW v2.2.4:** Firebase FCM |
| **Setup Mode** | ✅ QR code setup | ❌ Manual config |
| **Production Ready** | ⚠️ Beta | ✅ **v2.2.4:** Enterprise-grade |

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
- ✅ You don't need enterprise features (encryption, cloud backup)
- ✅ You prefer automated configuration
- ✅ You want minimal dependencies
- ⚠️ **Note:** Does not include v2.2.4 features (cloud backup, push notifications)

### Choose **GitHub v2.2.4** if:
- ✅ You need **encrypted cloud backup** (Google Drive)
- ✅ You want **real-time push notifications** (browser + mobile)
- ✅ You need **enterprise-grade security** (AES-256-GCM encryption)
- ✅ You need offline/local-only operation
- ✅ You want email alerts on motion
- ✅ You want to customize the code
- ✅ You prefer organized project structure
- ✅ You want Git version control
- ✅ You need production-ready features comparable to Ring/Arlo/Blink
- ⚠️ Requires longer setup time (35-45 minutes with v2.2.4 config)

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

**Important:** Make sure `camera_auto_detect` appears **only once**. Remove any earlier `camera_auto_detect=1` line, then put the IMX519 block under the `[all]` section:
```
[all]
enable_uart=1
camera_auto_detect=0
dtoverlay=imx519
gpu_mem=128
dtparam=i2c_vc=on
dtparam=i2c_arm=on
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
- **NEW v2.2.4:** Verify cloud upload in Google Drive
- **NEW v2.2.4:** Verify push notification received

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

**GitHub v2.2.4 - Web UI Settings:**
- Cloud Storage: `http://<device>.local:8080/cloud_settings`
- Notifications: `http://<device>.local:8080/notification_settings`

### 3. Configure Cloud Backup (v2.2.4 Only)

**Initial Setup:**
1. Get Google OAuth credentials (see Step 3C.2)
2. Access cloud settings web UI
3. Authenticate Google Drive
4. Enable cloud backup
5. Test upload
6. **BACKUP ENCRYPTION KEY:**
   ```bash
   scp pi@<device>.local:~/ME_CAM-DEV/config/cloud_encryption.key ~/safe_location/
   ```

**Verify Backups:**
```bash
# Check upload statistics
ssh pi@<device>.local
cd ~/ME_CAM-DEV
source venv/bin/activate
python3 << 'EOF'
from src.cloud.encrypted_cloud_storage import get_cloud_storage
cloud = get_cloud_storage()
stats = cloud.get_stats()
print(f"Files uploaded: {stats['total_uploaded']}")
print(f"Total size: {stats['total_bytes'] / 1024 / 1024:.1f} MB")
print(f"Queue size: {stats['queue_size']}")
print(f"Failed: {stats['total_failed']}")
EOF
```

### 4. Configure Push Notifications (v2.2.4 Only)

**Browser Notifications:**
1. Access: `http://<device>.local:8080/notification_settings`
2. Click "Subscribe" under Web Push
3. Allow notifications in browser
4. Test with "Send Test" button
5. Notifications work even when browser tab is closed!

**Mobile Notifications (Optional):**
1. Setup Firebase project (see Step 3C.3)
2. Get FCM token from mobile app
3. Register device in notification settings
4. Test with "Send Test" button

**Configure Preferences:**
- Motion alerts: ON
- Security alerts: ON
- Include snapshots: ON
- Quiet hours: 10 PM - 7 AM (optional)
- Rate limit: 50 notifications/hour

### 5. Set Up Remote Access (Optional)

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

## Multi-Device Replication Guide (v2.2.4)

### Master Device Setup (First Device)

Complete the full installation with v2.2.4 features:
1. ✅ Flash SD card
2. ✅ Install ME_CAM from GitHub
3. ✅ Install v2.2.4 dependencies
4. ✅ Configure Google Drive OAuth
5. ✅ Configure Firebase (optional)
6. ✅ Test cloud upload
7. ✅ Test push notifications
8. ✅ Backup encryption key

**Hostname:** mecamdev6  
**Config Complete:** ✅

### Replicating to Additional Devices

**Method 1: Clone Master SD Card (Fastest - 10 minutes/device)**

```bash
# On master device (mecamdev6):
sudo shutdown -h now

# On your computer:
# 1. Remove SD card from mecamdev6
# 2. Use Win32DiskImager (Windows) or dd (Mac/Linux) to create image
# 3. Flash image to new SD cards (as many as needed)
# 4. Insert new SD card into new Pi
# 5. Boot and SSH in

# On each new device:
ssh pi@raspberrypi.local  # Default hostname after clone

# Change hostname:
sudo hostnamectl set-hostname mecamdev7  # or mecamdev8, mecamdev9, etc.

# Update hosts file:
sudo nano /etc/hosts
# Change line: 127.0.1.1 raspberrypi
# To:          127.0.1.1 mecamdev7

# Reboot to apply:
sudo reboot

# Verify:
ssh pi@mecamdev7.local
hostname  # Should show: mecamdev7

# Test services:
sudo systemctl status mecamera
curl http://localhost:8080
```

**Advantages:**
- ✅ All packages pre-installed
- ✅ All configurations preserved
- ✅ OAuth already authenticated
- ✅ Encryption keys copied (all devices share same key)
- ✅ Fastest replication (~10 min/device)

**Considerations:**
- All devices will share same encryption key (decrypt backups from any device)
- All devices will upload to same Google Drive folder
- Need to change hostname on each device

**Method 2: Automated Script Deploy (20 minutes/device)**

For unique encryption keys per device:

```bash
# 1. Flash fresh SD card with Raspberry Pi Imager
# 2. Set unique hostname in Imager: mecamdev7, mecamdev8, etc.
# 3. Boot and SSH into new device

# 4. Quick install from master:
ssh pi@mecamdev7.local

# Clone repository:
cd ~
git clone https://github.com/YourOrg/ME_CAM-DEV.git
cd ME_CAM-DEV

# Run automated deployment:
chmod +x deploy_cloud_push_v2.2.4.sh
./deploy_cloud_push_v2.2.4.sh

# Copy shared OAuth credentials (but NOT encryption key):
scp pi@mecamdev6.local:~/ME_CAM-DEV/config/client_secrets.json ~/ME_CAM-DEV/config/
scp pi@mecamdev6.local:~/ME_CAM-DEV/config/firebase_service_account.json ~/ME_CAM-DEV/config/

# Set permissions:
chmod 600 ~/ME_CAM-DEV/config/*.json

# Restart service:
sudo systemctl restart mecamera

# Configure in web UI:
# Open: http://mecamdev7.local:8080/cloud_settings
# Click "Authenticate Google Drive" (uses copied credentials)
# Enable cloud backup
```

**Advantages:**
- ✅ Each device has unique encryption key
- ✅ Independent backups
- ✅ Easy to identify which device created each backup

### Multi-Device Management

**Check Status of All Devices:**
```bash
# Create status check script
cat > ~/check_all_devices.sh << 'EOF'
#!/bin/bash
DEVICES="mecamdev6 mecamdev7 mecamdev8 mecamdev9"

for device in $DEVICES; do
    echo "=== $device ==="
    ssh pi@$device.local "sudo systemctl is-active mecamera && echo 'Running' || echo 'Stopped'"
    ssh pi@$device.local "hostname -I | awk '{print \"IP:\", \$1}'"
    ssh pi@$device.local "vcgencmd measure_temp"
    echo ""
done
EOF

chmod +x ~/check_all_devices.sh
./check_all_devices.sh
```

**Output:**
```
=== mecamdev6 ===
Running
IP: 10.2.1.6
temp=52.3'C

=== mecamdev7 ===
Running
IP: 10.2.1.7
temp=48.9'C

=== mecamdev8 ===
Running
IP: 10.2.1.8
temp=51.1'C
```

**Check Cloud Upload Status:**
```bash
cat > ~/check_uploads.sh << 'EOF'
#!/bin/bash
DEVICES="mecamdev6 mecamdev7 mecamdev8"

for device in $DEVICES; do
    echo "=== $device Upload Stats ==="
    ssh pi@$device.local "cat ~/ME_CAM-DEV/logs/cloud_upload_stats.json 2>/dev/null | python3 -m json.tool | grep -E 'total_uploaded|total_bytes|queue_size|total_failed'"
    echo ""
done
EOF

chmod +x ~/check_uploads.sh
./check_uploads.sh
```

**Broadcast Notification Test:**
```bash
# From any device's web UI:
# http://mecamdev6.local:8080/notification_settings
# Click: "Broadcast Test to All Devices"

# All subscribed browsers and mobile devices receive notification
```

**Update All Devices:**
```bash
cat > ~/update_all_devices.sh << 'EOF'
#!/bin/bash
DEVICES="mecamdev6 mecamdev7 mecamdev8"

for device in $DEVICES; do
    echo "=== Updating $device ==="
    ssh pi@$device.local << 'REMOTE'
        cd ~/ME_CAM-DEV
        git pull
        source venv/bin/activate
        pip install -r requirements.txt --upgrade
        sudo systemctl restart mecamera
REMOTE
    echo "✅ $device updated"
    echo ""
done
EOF

chmod +x ~/update_all_devices.sh
./update_all_devices.sh
```

### Centralized Monitoring Dashboard

**Option 1: Use Google Drive Folder**
- All devices upload to same folder: `MECAM_Recordings/`
- Subfolder per device: `MECAM_Recordings/mecamdev6/`, etc.
- View all recordings in one place

**Option 2: Custom Python Dashboard**
```python
# Create ~/multi_cam_dashboard.py
import requests
import json

DEVICES = {
    'mecamdev6': '10.2.1.6',
    'mecamdev7': '10.2.1.7',
    'mecamdev8': '10.2.1.8',
}

def check_device(name, ip):
    try:
        # Check cloud stats
        response = requests.get(f'http://{ip}:8080/api/cloud/stats', timeout=5)
        stats = response.json()
        
        print(f"\n{name} ({ip}):")
        print(f"  Status: ✅ Online")
        print(f"  Uploaded: {stats.get('total_uploaded', 0)} files")
        print(f"  Queue: {stats.get('queue_size', 0)} pending")
        print(f"  Failed: {stats.get('total_failed', 0)}")
        
    except Exception as e:
        print(f"\n{name} ({ip}):")
        print(f"  Status: ❌ Offline - {e}")

print("=== ME_CAM Multi-Device Dashboard ===")
for name, ip in DEVICES.items():
    check_device(name, ip)
```

**Run dashboard:**
```bash
python3 ~/multi_cam_dashboard.py
```

### Production Deployment Checklist

For each device:
- [ ] SD card flashed and booted
- [ ] Hostname configured (mecamdev#)
- [ ] ME_CAM v2.2.4 installed
- [ ] Cloud storage configured
- [ ] OAuth authenticated
- [ ] Test upload successful
- [ ] Push notifications subscribed
- [ ] Test notification received
- [ ] Encryption key backed up
- [ ] Service auto-starts on boot
- [ ] Motion detection tested
- [ ] Camera angle adjusted
- [ ] Power supply stable (5V 2.5A)
- [ ] Network connectivity verified
- [ ] Remote access configured (optional)
- [ ] Added to monitoring dashboard

### Backup Strategy

**Per-Device Backups (Unique Encryption Keys):**
```bash
# Backup encryption key from each device
for device in mecamdev6 mecamdev7 mecamdev8; do
    scp pi@$device.local:~/ME_CAM-DEV/config/cloud_encryption.key \
        ~/mecam_backups/${device}_encryption.key
done

# Label each file with device name
```

**Shared OAuth Credentials:**
```bash
# Only need one copy (same for all devices)
scp pi@mecamdev6.local:~/ME_CAM-DEV/config/client_secrets.json \
    ~/mecam_backups/shared_google_oauth.json
    
scp pi@mecamdev6.local:~/ME_CAM-DEV/config/firebase_service_account.json \
    ~/mecam_backups/shared_firebase.json
```

**SD Card Images:**
```bash
# Create master image after full configuration
# Use Win32DiskImager or dd to save SD card image
# Store in safe location: ~/mecam_backups/mecam_v2.2.4_master.img
```

---

## Summary

**Single Device Setup:** 35-45 minutes  
**Additional Devices (Clone Method):** 10 minutes each  
**Additional Devices (Script Method):** 20 minutes each  

**For 5 devices:**
- Clone method: 35 + (4 × 10) = **75 minutes total**
- Script method: 35 + (4 × 20) = **115 minutes total**

**Recommended:** Use clone method for speed, then customize hostnames.

---

**Created:** January 29, 2026  
**Updated:** February 6, 2026 (v2.2.4 - Cloud Storage & Push Notifications)  
**Tested On:** Raspberry Pi Zero 2W, Bullseye/Bookworm Lite 32-bit  
**Camera:** IMX519 (Arducam)  
**By:** MangiafestoElectronics LLC
