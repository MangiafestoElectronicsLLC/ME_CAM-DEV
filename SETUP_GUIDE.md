# ME Camera - Complete Setup Guide for GitHub

This is the definitive guide for setting up ME Camera from scratch on a Raspberry Pi. Follow these steps exactly to replicate the working project.

---

## Prerequisites

- **Raspberry Pi**: Zero 2W (512MB RAM) with imx708 camera or compatible hardware
- **SD Card**: 32GB minimum recommended (for recordings storage)
- **Raspberry Pi Imager**: Latest version available
- **Network**: WiFi or Ethernet connection
- **Power Supply**: 5V 2.5A USB-C power adapter for Pi Zero 2W

---

## Step 1: Flash Raspberry Pi OS

Use **Raspberry Pi Imager** (official tool from raspberrypi.com).

### OS Selection
```
Choose OS → 
  Raspberry Pi OS (Other) → 
    Raspberry Pi OS (Legacy) →
      Raspberry Pi OS Lite (Legacy)
```

**Why Legacy?** The original ME Camera project was built on Bullseye. Bookworm has different dependencies.

### Advanced Settings (Click Gear Icon)
- ✅ **Set hostname**: `raspberrypi` (or your custom name)
- ✅ **Enable SSH**: Required for remote access
- ✅ **Set username/password**: `pi` / `raspberry` (standard)
- ✅ **Configure WiFi**: Set SSID and password
- ✅ **Set locale**: Your timezone
- ✅ **Disable telemetry**: Optional but recommended

### Burn to SD Card
Insert SD card, click "Choose Storage", select SD card, click Write. Wait 3-5 minutes.

---

## Step 2: Initial Pi Setup

After booting for the first time:

### Via Raspberry Pi Imager (Recommended)
If you have the Pi connected to display/keyboard, complete initial setup wizard.

### Via SSH (Recommended for Headless Setup)

```bash
# From your Windows/Mac/Linux computer
ssh pi@raspberrypi.local

# Or use IP address if .local doesn't work
ssh pi@10.2.1.47  # Replace with your Pi's IP
```

### First Login Tasks

```bash
# Update system
sudo apt update && sudo apt full-upgrade -y

# Disable legacy camera (required for libcamera)
sudo raspi-config
# → Interface Options → Legacy Camera → Disable
# Then: Reboot
```

---

## Step 3: Clone ME Camera Repository

```bash
cd ~
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV
```

**Verify structure:**
```bash
ls -la
# Should show: main.py, requirements.txt, web/, src/, config/, etc/
```

---

## Step 4: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate

# You should see: (venv) pi@raspberrypi:~/ME_CAM-DEV $
```

---

## Step 5: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**This takes 5-10 minutes on Pi Zero 2W.** Don't interrupt!

### If NumPy/OpenCV Errors Occur

Pi Zero 2W often ships with NumPy 2.x, which breaks pre-compiled OpenCV:

```bash
pip install "numpy<2"
pip uninstall -y opencv-python opencv-python-headless opencv-contrib-python
pip install opencv-python-headless
```

---

## Step 6: Run Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

**Expected output:**
```
=== ME Camera Setup (Bullseye) ===
[✓] Creating directories...
[✓] Copying config...
[✓] Setting permissions...
=== Setup Complete ===
```

---

## Step 7: First Manual Run

```bash
python3 main.py
```

**Expected output:**
```
=== ME_CAM v2.0 - Organized Structure ===
[INFO] Motion detection disabled (libcamera-still hangs on Pi Zero 2W)
[INFO] Running on http://127.0.0.1:8080
[INFO] Running on http://10.2.1.47:8080
```

### Access Dashboard

Open in browser:
```
http://raspberrypi.local:8080
http://10.2.1.47:8080  # (Use your Pi's IP)
```

**You'll see:** First-run setup wizard

### Complete First-Run Setup

1. **Set Device Name**: ME_CAM_1 (or your name)
2. **Set Emergency Contact**: Your phone number or email
3. **Configure Motion Detection**: Enable
4. **Set Storage Retention**: 7 days
5. **Click Save and Continue**

**Dashboard should now show:**
- ✅ System Status: Active
- ✅ Device Status: ONLINE (green)
- ✅ Battery: 100% (external power)
- ✅ Live Camera: TEST MODE (animated)
- ✅ Storage: 0.0 GB used
- ✅ Recordings: 0 files

---

## Step 8: Enable Auto-Boot

Stop the manual run: Press `Ctrl+C`

**Install systemd service:**
```bash
sudo cp etc/systemd/system/mecamera.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mecamera
sudo systemctl start mecamera
```

**Verify it's running:**
```bash
sudo systemctl status mecamera
```

**Expected output:**
```
● mecamera.service - ME Camera Service
     Loaded: loaded (/etc/systemd/system/mecamera.service; enabled; vendor preset: enabled)
     Active: active (running) since...
```

### Auto-Start After Pi Reboot

```bash
sudo reboot

# After reboot, access dashboard at http://raspberrypi.local:8080
# Service starts automatically!
```

---

## Step 9: Camera Hardware Setup

### Test Camera Detection

```bash
libcamera-still --list-cameras
```

**For Pi Zero 2W with IMX708:**
```
Available cameras
0 : imx708 [4608x3456] (/base/soc/i2c0mux/i2c@1/imx708@1a)
    Modes: 'SRGGB10_CSI2P' : 1536x864 [120.00 fps - 4608x3456 [10.00 fps]]
           'YUV420' : 1536x864 [120.00 fps - 4608x3456 [10.00 fps]]
```

### Known Issue: Pi Zero 2W Camera Memory Problem

**On Pi Zero 2W (512MB RAM), the full-resolution camera buffer allocation fails:**

```
Unable to request buffers: Cannot allocate memory
```

**This is expected behavior.** The system automatically falls back to **TEST MODE** with dummy video stream. This is NOT a bug - it's designed failover behavior.

**Solution:**
- Upgrade to **Pi 3B+** ($95-110) minimum for live camera streaming
- Or use Pi 4/5 for high-performance camera with audio (see HARDWARE_GUIDE.md)

---

## Project Structure

After git clone, you'll have:

```
ME_CAM-DEV/
├── main.py                          # Entry point
├── requirements.txt                 # Python dependencies
├── setup.sh                         # Setup automation script
├── LICENSE                          # MIT License
├── README.md                        # Project overview
├── SETUP_GUIDE.md                   # This file
├── HARDWARE_GUIDE.md               # Hardware recommendations
├── DEPLOYMENT_GUIDE.md             # Production deployment
│
├── web/                             # Flask web application
│   ├── app.py                       # Flask routes and API endpoints
│   ├── static/                      # CSS, JS, images
│   │   ├── style.css               # Main styles
│   │   └── dashboard.js            # Dashboard functionality
│   └── templates/                   # HTML templates
│       ├── dashboard.html           # Main dashboard
│       ├── login.html              # Login page
│       ├── config.html             # Settings page
│       ├── first_run.html          # Setup wizard
│       └── fallback.html           # Error fallback
│
├── src/                             # Core application modules
│   ├── __init__.py
│   ├── core/                        # Core functionality
│   │   ├── __init__.py
│   │   ├── config_manager.py       # Config file handling
│   │   ├── auth_manager.py         # User authentication
│   │   └── battery_monitor.py      # Battery/power monitoring
│   ├── camera/                      # Camera interface
│   │   ├── __init__.py
│   │   ├── camera_pipeline.py      # Pipeline architecture
│   │   ├── libcamera_streamer.py   # libcamera-still fallback
│   │   └── fast_camera_streamer.py # picamera2 high-speed mode
│   ├── detection/                   # Motion detection
│   │   ├── __init__.py
│   │   ├── motion_detector.py      # Generic motion detection
│   │   ├── motion_service.py       # Background motion service
│   │   ├── ai_person_detector.py   # Person detection with ML
│   │   └── watchdog.py             # Pipeline health monitoring
│   ├── utils/                       # Utility functions
│   │   ├── __init__.py
│   │   ├── logger.py               # Logging configuration
│   │   ├── pi_detect.py            # Pi model auto-detection
│   │   └── helpers.py              # Helper functions
│   └── web/                         # Web utilities (internal)
│       └── __init__.py
│
├── config/                          # Configuration files
│   ├── config_default.json         # Default settings (git tracked)
│   └── config.json                 # User settings (created on first run)
│
├── recordings/                      # Video storage directory
│   └── (auto-created, contains .mp4 files)
│
├── logs/                           # Application logs
│   └── mecam.log                   # Main log file (auto-created)
│
├── etc/                            # System-level configuration
│   └── systemd/
│       └── system/
│           └── mecamera.service    # systemd service file
│
├── docs/                           # Documentation
│   ├── PROJECT_GUIDE.md           # Architecture overview
│   ├── README.md                  # Quick reference
│   └── wireguard_setup.md         # VPN setup guide
│
└── cloud/                          # Cloud integration modules
    ├── gdrive_uploader.py         # Google Drive API
    └── email_notifier.py          # Email notifications
```

---

## API Endpoints

### Authentication Required

All endpoints require authentication. Login first, then use session cookie.

```bash
# Get status (requires auth)
curl -b cookies.txt http://localhost:8080/api/status

# Get storage info (requires auth)
curl -b cookies.txt http://localhost:8080/api/storage

# Get battery info (requires auth)
curl -b cookies.txt http://localhost:8080/api/battery

# Get recordings list (requires auth)
curl -b cookies.txt http://localhost:8080/api/recordings
```

### Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/login` | POST | Authenticate user |
| `/logout` | GET | Clear session |
| `/dashboard` | GET | Main dashboard |
| `/config` | GET/POST | Settings page |
| `/api/status` | GET | System status (active/offline) |
| `/api/battery` | GET | Battery percentage |
| `/api/storage` | GET | Storage usage details |
| `/api/recordings` | GET | List recordings |
| `/api/stream` | GET | MJPEG camera stream |
| `/api/download/<filename>` | GET | Download recording |

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u mecamera.service -n 50 --no-pager

# Common errors:
# "ModuleNotFoundError: No module named 'loguru'"
#   → Make sure venv is activated: source venv/bin/activate
#   → Reinstall: pip install -r requirements.txt

# "Port already in use"
#   → Kill existing process: sudo fuser -k 8080/tcp
#   → Restart service: sudo systemctl restart mecamera
```

### Dashboard Shows OFFLINE

This usually means the Flask app isn't responding:

```bash
# Check if service is running
sudo systemctl status mecamera

# Restart service
sudo systemctl restart mecamera

# Wait 3-5 seconds, then refresh browser
```

### Camera Shows "TEST MODE" Indefinitely

**This is expected on Pi Zero 2W!** The 512MB RAM cannot allocate the camera buffer. This is not a failure - it's the designed fallback.

**Solution:** Upgrade to Pi 3B+ or higher (see HARDWARE_GUIDE.md).

### SSH Connection Times Out

```bash
# Raspberry Pi might be unresponsive (high I/O during package install)
# Wait 10-30 seconds and retry

ssh pi@raspberrypi.local
# or
ssh pi@10.2.1.47
```

### Battery Shows Wrong Percentage

The dashboard displays battery percentage from the system. On Pi Zero 2W without a battery HAT:
- External power: Shows 100% (correct)
- On battery: Shows estimated value (may be inaccurate without hardware ADC)

To manually set battery percentage:

```bash
# Edit config
nano config/config.json

# Add/modify:
{
  "battery_percent_override": 85
}

# Save (Ctrl+X, Y, Enter)
# Restart service
sudo systemctl restart mecamera
```

---

## Next Steps

### 1. Configure Recordings

In **Settings** → **Storage**:
- Motion-only recording (saves space)
- Retention period (days to keep recordings)
- Auto-cleanup when storage full

### 2. Set Up Email Alerts

In **Settings** → **Email**:
- SMTP Server: `smtp.gmail.com` (for Gmail)
- SMTP Port: `587`
- Enable TLS
- Email address and password

### 3. Set Emergency Contacts

In **Settings** → **Emergency**:
- Primary contact phone
- Secondary contacts
- Emergency response mode (manual/automatic)

### 4. Upgrade Hardware

For live camera streaming:
- **Budget**: Pi 3B+ + IMX708 camera ($120 total)
- **Premium**: Pi 5 + IMX708 + audio speaker ($200+ total)

See **HARDWARE_GUIDE.md** for detailed recommendations.

---

## Production Deployment

See **DEPLOYMENT_GUIDE.md** for:
- HTTPS/SSL setup
- Nginx reverse proxy
- Domain configuration
- Cloud backup integration

---

## Support

- **GitHub Issues**: Report bugs at github.com/MangiafestoElectronicsLLC/ME_CAM-DEV
- **Documentation**: See `docs/` directory
- **Logs**: Check `logs/mecam.log` for detailed diagnostics

---

## License

MIT License - See LICENSE file for details

---

**Last Updated**: January 15, 2026  
**Version**: 2.0 (Organized Structure)  
**Tested On**: Raspberry Pi Zero 2W, Pi 3B+, Pi 4, Pi 5 (where possible)
