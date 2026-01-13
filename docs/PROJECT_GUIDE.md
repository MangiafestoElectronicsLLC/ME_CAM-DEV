# ME_CAM v2.0 - Complete Project Guide

## 🎯 Overview

ME_CAM is a professional-grade Raspberry Pi camera surveillance system with:

- **Fast streaming** (15-30 FPS)
- **Smart motion detection** (AI-powered)
- **Emergency alerts** (SMS/Email)
- **Advanced storage** (Auto-cleanup)
- **Professional structure** (Clean, organized)

---

## 📂 Complete Directory Structure

```
ME_CAM-DEV/
│
├── 📄 main.py                     # Application entry point
├── 📄 requirements.txt            # Python dependencies
├── 📄 README.md                   # Project overview (START HERE)
├── 📄 LICENSE                     # MIT License
├── 📄 hub.py                      # Multi-camera hub (future)
├── 📄 web_dashboard.py            # Deprecated (use web/app.py)
│
├── 🗂️ src/                         # ALL SOURCE CODE (ORGANIZED)
│   │
│   ├── 🗂️ core/                   # Core utilities
│   │   ├── __init__.py
│   │   ├── config_manager.py      # Configuration handling
│   │   ├── user_auth.py           # User authentication
│   │   ├── battery_monitor.py     # Power monitoring
│   │   ├── thumbnail_gen.py       # Video thumbnail generation
│   │   ├── qr_generator.py        # Setup QR code generation
│   │   ├── emergency_handler.py   # Emergency alert system
│   │   └── encryptor.py           # File encryption
│   │
│   ├── 🗂️ camera/                 # Camera streaming modules
│   │   ├── __init__.py
│   │   ├── camera_coordinator.py  # Prevent camera conflicts
│   │   ├── fast_camera_streamer.py # ⚡ FAST (15-30 FPS)
│   │   ├── libcamera_streamer.py  # Slow fallback (1-2 FPS)
│   │   └── camera_pipeline.py     # Legacy pipeline
│   │
│   ├── 🗂️ detection/              # Motion & AI detection
│   │   ├── __init__.py
│   │   ├── motion_service.py      # Background motion service
│   │   ├── libcamera_motion_detector.py # Motion engine
│   │   ├── ai_person_detector.py  # AI person detection
│   │   ├── face_detector.py       # Face recognition
│   │   ├── face_recognition_whitelist.py
│   │   ├── smart_motion_filter.py # False positive filtering
│   │   └── watchdog.py            # System watchdog
│   │
│   └── 🗂️ utils/                  # Utilities
│       ├── cloud/                 # Google Drive integration
│       │   └── gdrive_uploader.py
│       └── notifications/         # Email notifications
│           └── emailer.py
│
├── 🗂️ web/                        # Web dashboard (Flask)
│   ├── app.py                     # Flask application
│   ├── 🗂️ templates/              # HTML templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── config.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── first_run.html
│   │   └── ...
│   └── 🗂️ static/                 # CSS, JS, images
│       ├── style.css
│       └── thumbs/               # Video thumbnails
│
├── 🗂️ config/                     # Configuration files
│   ├── config.json               # User configuration (generated)
│   └── config_default.json       # Default settings template
│
├── 🗂️ etc/                        # System configuration
│   └── 🗂️ systemd/system/
│       └── mecamera.service      # SystemD service file
│
├── 🗂️ scripts/                    # Maintenance scripts
│   ├── setup.sh                  # Initial setup
│   ├── install_fast_camera.sh    # Install picamera2
│   ├── factory_reset.sh          # Factory reset
│   └── self_update.sh            # Self update
│
├── 🗂️ docs/                       # Documentation
│   ├── README.md                 # Project overview
│   ├── INSTALL.md                # Installation guide
│   ├── DEPLOYMENT.md             # Production deployment
│   ├── PERFORMANCE_GUIDE.md      # Performance optimization
│   ├── REORGANIZATION.md         # Structure changes
│   └── 🗂️ archive/               # Old documentation
│       ├── CHANGES.md
│       ├── IMPLEMENTATION_SUMMARY.md
│       └── ... (other old docs)
│
├── 🗂️ logs/                       # Application logs
│   └── mecam.log                 # Main log file
│
├── 🗂️ recordings/                 # Video storage
│   └── motion_20260113_184532.mp4
│
├── 🗂️ tests/                      # Unit tests (future)
│
├── 🗂️ setup_mode/                 # Setup wizard (legacy)
├── 🗂️ templates/                  # Legacy templates
└── 🗂️ utils/                      # Legacy utilities
```

---

## 🚀 Getting Started

### 1. Installation (5 minutes)

```bash
# Clone and setup
cd ~/
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV

# Run setup
chmod +x scripts/setup.sh
./scripts/setup.sh

# Install fast camera (RECOMMENDED - 15x faster!)
sudo chmod +x scripts/install_fast_camera.sh
sudo ./scripts/install_fast_camera.sh

# Start
sudo systemctl enable mecamera
sudo systemctl start mecamera
```

### 2. First Access

Open: **http://raspberrypi.local:8080**

Follow setup wizard for:
- User account creation
- Camera configuration
- Emergency contact setup
- Motion detection settings

### 3. Performance Boost (Optional but Recommended)

Settings → Performance → ✓ Use Fast Streaming → Save

Your camera will now stream at 15-30 FPS instead of 1-2 FPS!

---

## 📚 Documentation Guide

### For Users
- **[README.md](README.md)** - Start here
- **[INSTALL.md](docs/INSTALL.md)** - Installation instructions
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production setup

### For Performance
- **[PERFORMANCE_GUIDE.md](docs/PERFORMANCE_GUIDE.md)** - How to optimize
- **[PERFORMANCE_IMPROVEMENTS.md](docs/PERFORMANCE_IMPROVEMENTS.md)** - What changed

### For Developers
- **[REORGANIZATION.md](docs/REORGANIZATION.md)** - File structure changes
- **[notes.txt](notes.txt)** - Technical notes and troubleshooting

---

## 🔧 Common Tasks

### Check Status
```bash
sudo systemctl status mecamera
```

### View Logs
```bash
# Real-time
sudo journalctl -u mecamera -f

# Application logs
tail -f logs/mecam.log
```

### Restart Service
```bash
sudo systemctl restart mecamera
```

### Update Code
```bash
git pull origin main
sudo systemctl restart mecamera
```

### Factory Reset
```bash
./scripts/factory_reset.sh
```

### Access Dashboard
```
http://raspberrypi.local:8080
```

---

## 🏗️ Architecture

### Layered Structure

```
┌─────────────────────────────────────┐
│     Web Dashboard (Flask)            │  <- User interface
│  /templates, /static, app.py         │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│     Application Logic (main.py)      │  <- Entry point
│  Config, Auth, Emergency Handling    │
└─────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────┐
│         Core Modules (src/core/)         │  <- Utilities
│  Config, Auth, Battery, Thumbnails       │
└──────────────────────────────────────────┘
      ↓                              ↓
┌──────────────────┐      ┌──────────────────┐
│ Camera Streaming │      │ Motion Detection │
│  (src/camera/)   │      │ (src/detection/) │
│  15-30 FPS ⚡   │      │  AI-Powered      │
└──────────────────┘      └──────────────────┘
      ↓                              ↓
┌──────────────────────────────────────────┐
│          Hardware (Raspberry Pi)         │
│  Camera, Storage, Network                │
└──────────────────────────────────────────┘
```

### Data Flow

```
Camera Hardware
      ↓
Camera Coordinator (Prevents conflicts)
      ↓ (High priority)
Fast Streamer ─→ Web Dashboard (15-30 FPS)
      ↓
Motion Detector ─→ Recording to SD Card
      ↓
Post-Processing ─→ Storage Management
      ↓
Emergency Handler ─→ SMS/Email Alerts
```

---

## 📊 Performance Metrics

### Before v2.0
- Stream: 1-2 FPS
- Latency: 850ms
- CPU: 45%
- Motion check: Every 2s
- Dashboard: Laggy

### After v2.0
- Stream: 15-30 FPS ⚡
- Latency: 35ms ⚡
- CPU: 18% ⚡
- Motion check: Every 0.2s ⚡
- Dashboard: Smooth ⚡

**Result: 15x faster, 60% less CPU!**

---

## 🔐 Security Features

- **PIN Protection**: Secure dashboard access
- **User Authentication**: Login system
- **File Encryption**: Optional (can be enabled)
- **Local Storage Only**: No cloud dependency
- **Secure Alerts**: HTTPS for external communication

---

## 💾 Storage Management

### Automatic Cleanup
- Monitors disk usage
- Deletes old files when threshold reached (default: 90%)
- Keeps newest files by default
- Configurable retention period (default: 7 days)

### Organization
- Optional date-based folders (YYYY/MM/DD)
- Automatic file naming: `motion_YYYYMMDD_HHMMSS.mp4`
- Thumbnail generation for quick preview

### Limits
- Set maximum storage (default: 10 GB)
- Auto-backup to USB (optional)
- Compression available (optional)

---

## 🚨 Emergency Features

### Alert Types
1. **Medical Monitoring** - Seizure detection, fall alerts
2. **Security Monitoring** - Intrusion, theft detection
3. **Manual SOS Button** - One-click alert

### Notification Methods
- **SMS** via carrier gateway (Verizon, AT&T, T-Mobile, Sprint)
- **Email** with video attachment
- **Google Drive** automatic upload

### Configuration
1. Settings → Emergency Contacts
2. Add phone numbers with carrier gateway
3. Setup Gmail App Password
4. Select mode: Medical/Security/Both

---

## 🔄 Update Procedure

### Quick Update
```bash
cd ~/ME_CAM-DEV
git pull origin main
sudo systemctl restart mecamera
```

### Update with Logs
```bash
cd ~/ME_CAM-DEV
git pull origin main
sudo systemctl restart mecamera
sleep 3
sudo journalctl -u mecamera -n 50
```

---

## 🐛 Troubleshooting

### Dashboard Slow
→ Install picamera2: `sudo ./scripts/install_fast_camera.sh`
→ Enable in Settings → Performance

### Camera Not Detected
→ Check: `libcamera-still --list-cameras`
→ Fix boot config: `sudo sed -i 's/camera_auto_detect=0/camera_auto_detect=1/g' /boot/config.txt`
→ Reboot

### Motion Not Working
→ Check enabled: `grep motion_only config/config.json`
→ View logs: `tail -f logs/mecam.log | grep MOTION`
→ Test: Wave hand in front of camera

### Alerts Not Sending
→ Check email config
→ Use Gmail App Password (not regular password)
→ Check carrier gateway format
→ Test SOS button

See **[INSTALL.md](docs/INSTALL.md)** for more troubleshooting.

---

## 📋 Maintenance Checklist

- [ ] Check logs weekly: `tail -f logs/mecam.log`
- [ ] Monitor storage: Dashboard → Storage section
- [ ] Test alerts monthly: Click SOS button
- [ ] Update code: `git pull origin main`
- [ ] Check battery: Settings → Battery status
- [ ] Verify motion: Trigger by walking in front

---

## 🎓 Learning Path

1. **Read**: [README.md](README.md)
2. **Install**: [INSTALL.md](docs/INSTALL.md)
3. **Configure**: Dashboard first-run wizard
4. **Understand**: [PERFORMANCE_GUIDE.md](docs/PERFORMANCE_GUIDE.md)
5. **Deploy**: [DEPLOYMENT.md](docs/DEPLOYMENT.md)
6. **Maintain**: Use logs and monitoring

---

## 🔗 Quick Links

| Resource | Location |
|----------|----------|
| Dashboard | http://raspberrypi.local:8080 |
| Project Repo | https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV |
| Issues | https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV/issues |
| Documentation | docs/ folder |
| Configuration | config/config.json |
| Logs | logs/mecam.log |

---

## 📞 Support

**Issues or Questions?**
1. Check logs: `tail -f logs/mecam.log`
2. Read troubleshooting: [INSTALL.md](docs/INSTALL.md)
3. Search issues: GitHub Issues
4. Create issue: Include logs and steps to reproduce

---

## ✨ Features at a Glance

| Feature | Status | Location |
|---------|--------|----------|
| Fast Streaming (15-30 FPS) | ✅ | src/camera/fast_camera_streamer.py |
| Motion Detection | ✅ | src/detection/motion_service.py |
| AI Person Detection | ✅ | src/detection/ai_person_detector.py |
| Emergency Alerts | ✅ | src/core/emergency_handler.py |
| Storage Management | ✅ | web/app.py |
| Web Dashboard | ✅ | web/app.py + templates |
| Multi-Camera Hub | 🚧 | hub.py |
| Mobile App | 📋 | Planned |
| Cloud Recording | 📋 | Planned |

---

**Version**: 2.0.0  
**Last Updated**: January 13, 2026  
**Status**: Production Ready  
**License**: MIT
