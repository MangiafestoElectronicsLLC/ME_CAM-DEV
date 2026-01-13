# ME_CAM v2.0 - Professional Camera Surveillance System
### by MangiafestoElectronics LLC

🎥 High-performance Raspberry Pi camera surveillance with motion detection, AI person recognition, and emergency alerts.

## ✨ New in v2.0

- **🚀 15x Faster Streaming**: 15-30 FPS with picamera2 (vs 1-2 FPS)
- **📁 Organized Structure**: Clean src/ directory layout
- **💾 Advanced Storage**: Smart cleanup, date organization, thumbnails
- **⚡ Better Performance**: Reduced CPU usage, smoother operation
- **📊 Real-time Stats**: Performance monitoring APIs

---

## 🎯 Key Features

### Camera & Streaming
- **Fast Streaming**: 15-30 FPS using picamera2 continuous capture
- **Fallback Mode**: libcamera-still for compatibility (1-2 FPS)
- **Camera Coordinator**: Prevents conflicts between streaming and recording
- **Live Dashboard**: Real-time MJPEG stream in web browser

### Motion Detection & AI
- **Smart Detection**: AI-powered person recognition (TensorFlow Lite)
- **Background Service**: Non-blocking motion detection every 0.2 seconds
- **Intelligent Filtering**: Reduces false positives from shadows, leaves, etc.
- **Person-Only Mode**: Record only when person detected

### Emergency & Security
- **Medical Monitoring**: Seizure detection, fall alerts
- **Security Alerts**: Break-in detection, theft prevention
- **SMS Notifications**: Via carrier email gateways (Verizon, AT&T, T-Mobile, Sprint)
- **Email Alerts**: Gmail integration with video attachments
- **SOS Button**: One-click emergency alert with video evidence

### Storage Management
- **Automatic Cleanup**: Delete old files when storage reaches threshold
- **Date Organization**: Optional YYYY/MM/DD folder structure
- **Thumbnail Generation**: Video previews for faster browsing
- **Retention Policy**: Configurable days to keep recordings
- **Storage Limits**: Set maximum GB usage
- **Manual Controls**: Clear all, delete individual files via dashboard

### Web Dashboard
- **Mobile-Friendly**: Responsive design for phones/tablets
- **Real-Time Stats**: Storage, camera performance, battery status
- **Easy Configuration**: All settings via web UI
- **First-Run Wizard**: Guided setup for new installations
- **PIN Protection**: Secure access control

---

## 📦 Quick Installation

### On Raspberry Pi:

```bash
# Clone repository
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV

# Run automated setup
chmod +x scripts/setup.sh
./scripts/setup.sh

# Install fast camera support (RECOMMENDED - 15x faster!)
sudo chmod +x scripts/install_fast_camera.sh
sudo ./scripts/install_fast_camera.sh

# Enable and start service
sudo systemctl enable mecamera
sudo systemctl start mecamera
```

### Access Dashboard

Open browser: **http://raspberrypi.local:8080**

First-time setup wizard will guide you through configuration.

---

## 🗂️ Project Structure

```
ME_CAM-DEV/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
│
├── src/                   # Source code (NEW organized structure)
│   ├── core/             # Core functionality
│   │   ├── config_manager.py      # Configuration
│   │   ├── user_auth.py           # Authentication
│   │   ├── battery_monitor.py     # Power monitoring
│   │   ├── thumbnail_gen.py       # Video thumbnails
│   │   ├── qr_generator.py        # Setup QR codes
│   │   ├── emergency_handler.py   # Emergency alerts
│   │   └── encryptor.py           # Encryption
│   │
│   ├── camera/           # Camera modules
│   │   ├── camera_coordinator.py      # Prevent conflicts
│   │   ├── fast_camera_streamer.py    # FAST (15-30 FPS)
│   │   ├── libcamera_streamer.py      # SLOW (1-2 FPS)
│   │   └── camera_pipeline.py         # Legacy
│   │
│   ├── detection/        # Motion & AI
│   │   ├── motion_service.py          # Background service
│   │   ├── libcamera_motion_detector.py
│   │   ├── ai_person_detector.py      # AI recognition
│   │   ├── face_detector.py
│   │   ├── smart_motion_filter.py
│   │   └── watchdog.py
│   │
│   └── utils/            # Utilities
│       ├── cloud/        # Google Drive integration
│       └── notifications/ # Email alerts
│
├── web/                  # Web dashboard
│   ├── app.py           # Flask application
│   ├── templates/       # HTML templates
│   └── static/          # CSS, JS, images
│
├── config/              # Configuration
│   ├── config.json      # User settings
│   └── config_default.json
│
├── scripts/             # Maintenance scripts
│   ├── setup.sh                 # Initial setup
│   ├── install_fast_camera.sh  # Install picamera2
│   ├── factory_reset.sh        # Reset system
│   └── self_update.sh          # Update code
│
├── docs/                # Documentation
│   ├── INSTALL.md
│   ├── PERFORMANCE_GUIDE.md
│   ├── DEPLOYMENT.md
│   └── archive/         # Old docs
│
├── etc/systemd/system/
│   └── mecamera.service # SystemD service
│
├── logs/                # Application logs
├── recordings/          # Video storage
└── tests/               # Unit tests
```

---

## 🚀 Performance Comparison

### Old vs New Streaming Method

| Metric | Old (libcamera-still) | New (picamera2) | Improvement |
|--------|----------------------|-----------------|-------------|
| **FPS** | 1-2 | 15-30 | **15x faster** |
| **Latency** | 850ms | 35ms | **24x faster** |
| **CPU Usage** | 45% | 18% | **60% less** |
| **Motion Check** | Every 2s | Every 0.2s | **10x faster** |
| **Dashboard Feel** | Laggy | Smooth | ✨ |

**Why was it slow?** The old method spawned a new subprocess for every frame (500-1000ms overhead). The new method uses continuous capture just like a Tkinter GUI - camera stays open, frames grabbed instantly!

See **[PERFORMANCE_GUIDE.md](docs/PERFORMANCE_GUIDE.md)** for technical details.

---

## ⚙️ Configuration

### Enable Fast Streaming (15-30 FPS)

1. Dashboard → **Settings**
2. Scroll to **⚡ Performance Settings** (green section)
3. ✓ Check **"Use Fast Streaming (picamera2)"**
4. Set **Target Stream FPS**: 15-30
5. Set **Motion Check Interval**: 0.2 seconds
6. **Save Settings**
7. Restart: `sudo systemctl restart mecamera`

### Storage Management

Configure in Settings → Storage:

- **Maximum Storage**: 10 GB (default)
- **Auto-Cleanup Threshold**: 90% (starts deleting at 90% full)
- **Retention Days**: 7 days (auto-delete older files)
- **Keep Newest Files**: ✓ (delete oldest first)
- **Organize by Date**: ✓ (creates YYYY/MM/DD folders)
- **Generate Thumbnails**: ✓ (video previews)

### Emergency Alerts

Setup SMS to phone:

1. Settings → **Emergency Contacts**
2. **Primary Contact**: Enter carrier gateway
   - Verizon: `5551234567@vtext.com`
   - AT&T: `5551234567@txt.att.net`
   - T-Mobile: `5551234567@tmomail.net`
3. **Emergency Mode**: Medical / Security / Both
4. **Gmail App Password**: Required for sending
   - Get from: https://myaccount.google.com/apppasswords
5. **Save Settings**

Test with **🚨 SOS Alert** button on dashboard!

---

## 📡 API Endpoints

### Camera
- `GET /api/stream` - Live MJPEG stream
- `GET /api/camera/stats` - Performance metrics

### Storage
- `GET /api/storage` - Basic storage info
- `GET /api/storage/stats` - Detailed statistics
- `POST /api/storage/cleanup` - Trigger cleanup
- `GET /api/recordings` - List all recordings
- `GET /api/download/<filename>` - Download file
- `POST /api/delete/<filename>` - Delete file
- `POST /api/clear-storage` - Clear all recordings

### Emergency
- `POST /api/emergency/send` - Send emergency alert
- `POST /api/emergency/test` - Test alert system

---

## 🔧 Maintenance

### View Logs

```bash
# Real-time service logs
sudo journalctl -u mecamera -f

# Application logs
tail -f logs/mecam.log

# Filter by category
tail -f logs/mecam.log | grep MOTION
tail -f logs/mecam.log | grep CAMERA
tail -f logs/mecam.log | grep EMERGENCY
```

### Service Commands

```bash
# Check status
sudo systemctl status mecamera

# Restart service
sudo systemctl restart mecamera

# Stop service
sudo systemctl stop mecamera

# Disable auto-start
sudo systemctl disable mecamera

# Enable auto-start
sudo systemctl enable mecamera
```

### Update System

```bash
cd ~/ME_CAM-DEV
git pull origin main
sudo systemctl restart mecamera
```

---

## 🐛 Troubleshooting

### Dashboard is Slow (1-2 FPS)

**Solution:** Install picamera2 for 15x speed boost

```bash
cd ~/ME_CAM-DEV
sudo ./scripts/install_fast_camera.sh
```

Then enable in Settings → Performance → ✓ Use Fast Streaming

### Camera Not Detected

```bash
# Test camera
libcamera-still --list-cameras

# If shows "No cameras available", check boot config:
grep camera_auto_detect /boot/config.txt

# Should show: camera_auto_detect=1
# If it shows =0, fix it:
sudo sed -i 's/camera_auto_detect=0/camera_auto_detect=1/g' /boot/config.txt
sudo reboot
```

### Motion Detection Not Working

```bash
# Check service status
sudo systemctl status mecamera | grep MOTION

# Check logs
tail -f logs/mecam.log | grep MOTION

# Verify enabled in config
grep "motion_only" config/config.json
# Should show: "motion_only": true

# Test by waving hand in front of camera
# Recording should appear in: ls -lh recordings/
```

### Storage Full

```bash
# Check usage
df -h

# Manual cleanup via API
curl http://localhost:8080/api/storage/cleanup -X POST

# Or use dashboard: Settings → Clear All Recordings
```

### Emergency Alerts Not Sending

1. **Check email configured**: Settings → Email Notifications
2. **Use Gmail App Password** (not regular password)
   - Get from: https://myaccount.google.com/apppasswords
3. **Check carrier gateway correct**
   - Wrong gateway = no SMS received
4. **Check first message not in spam**
5. **Test**: Dashboard → 🚨 SOS Alert button

---

## 📚 Documentation

- **[INSTALL.md](docs/INSTALL.md)** - Complete installation guide
- **[PERFORMANCE_GUIDE.md](docs/PERFORMANCE_GUIDE.md)** - Speed optimization guide
- **[PERFORMANCE_IMPROVEMENTS.md](docs/PERFORMANCE_IMPROVEMENTS.md)** - What changed
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment
- **[notes.txt](notes.txt)** - Developer notes & troubleshooting history

---

## 🧑‍💻 Hardware Requirements

- **Raspberry Pi Zero 2 W** (recommended) or Pi 4
- **Pi Camera Module** (v2 or HQ) or compatible USB camera
- **16GB+ microSD card** (Class 10 or better)
- **Optional**: Battery pack, case, PoE splitter

---

## 💻 Software Requirements

- **Raspberry Pi OS**: Legacy (Bullseye) Lite
- **Python**: 3.9+
- **picamera2**: For fast streaming (installed via script)
- **OpenCV**: 4.5.1+ (headless)
- **TensorFlow Lite**: 2.7.0 (optional, for AI)

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🆘 Support

- **Issues**: https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV/issues
- **Discussions**: https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV/discussions
- **Email**: support@mangiafestoelectronics.com

---

## ✅ Project Status

- ✅ Core functionality complete
- ✅ Fast streaming implemented (v2.0)
- ✅ Motion detection working
- ✅ Emergency alerts functional
- ✅ Storage management complete
- ✅ Organized file structure (v2.0)
- 🚧 Multi-camera hub (in progress)
- 📋 Mobile app (planned)
- 📋 Cloud recording option (planned)

---

## 📝 Changelog

### v2.0.0 (January 2026)
- ✨ **NEW**: Fast streaming mode (15-30 FPS with picamera2)
- ✨ **NEW**: Organized src/ directory structure
- ✨ **NEW**: Advanced storage management with auto-cleanup
- ✨ **NEW**: Performance monitoring APIs
- ✨ **NEW**: Date-based recording organization
- ✨ **NEW**: Thumbnail generation for videos
- 🐛 **FIX**: Camera conflicts between streaming and recording
- ⚡ **IMPROVEMENT**: 60% less CPU usage
- ⚡ **IMPROVEMENT**: 10x faster motion detection (every 0.2s vs 2s)
- 📚 **DOCS**: Complete performance guide added
- 🏗️ **REFACTOR**: Clean module organization

### v1.x (2025)
- Initial release with basic functionality
- Motion detection
- Emergency alerts
- Web dashboard
- Multi-camera support

---

**Version**: 2.0.0  
**Last Updated**: January 13, 2026  
**Maintained by**: MangiafestoElectronics LLC
