# ME_CAM v2.1.2 Release Notes

**Release Date:** January 20, 2026  
**Target Platform:** Raspberry Pi Zero 2W  
**Status:** Production Ready

## 🎯 Overview

Version 2.1.2 is a major stability and performance update focused on Pi Zero 2W optimization, motion detection reliability, and security camera functionality.

---

## ✨ New Features

### 1. **User Registration System**
- Self-service account creation
- Username validation (minimum 3 characters)
- Password validation (minimum 6 characters)
- Duplicate prevention
- Professional registration page

### 2. **WiFi Configuration UI**
- Web-based WiFi settings management
- SSID, password, and country code configuration
- Settings persistence for system reconfiguration
- Located in Config page

### 3. **Enhanced Motion Detection Algorithm**
- **Shadow/Sunlight Filtering**: Gaussian blur + edge detection to ignore lighting changes
- **Person Detection Focus**: Requires sharp contrast, defined edges, and substantial area change
- **Frame Buffering**: Captures 0.5 seconds BEFORE motion detected
- **Smart Thresholds**: 
  - max_diff > 80 (sharp contrast)
  - motion_percent > 2% (substantial area)
  - edge_motion > 1000 (clear object boundaries)
  - mean_diff > 15 (overall significance)

### 4. **Improved Video Recording**
- **H.264 Codec**: Universal browser compatibility (AVC1)
- **Pre-buffered Recording**: Captures motion from start to finish
- **Optimized Duration**: 5-second clips with pre-buffer
- **Quality Balance**: 15 FPS for Pi Zero performance

### 5. **Storage Management Enhancements**
- **Automatic File Deletion**: Deletes video files when clearing events
- **Space Reporting**: Shows freed storage in MB
- **Individual Event Deletion**: Removes both database entry and video file
- **Path Resolution**: Fixed recordings/ folder handling

---

## 🐛 Bug Fixes

### Critical Fixes
1. **Timezone Correction**: Events now stored in EST (UTC-5) instead of GMT
2. **Video Codec**: Changed from mp4v to H.264 for browser playback
3. **JSON Serialization**: Fixed numpy uint8 type errors in motion events
4. **File Deletion**: Corrected path resolution for video file cleanup
5. **Motion Detection Timing**: Fixed recording to capture DURING motion, not after

### UI/UX Fixes
1. **Latest Event Timestamp**: Now displays in correct local timezone (EST)
2. **Mobile Responsiveness**: Motion events page fully responsive
3. **Video Playback**: Fixed 0:00 stuck issue with H.264 codec
4. **Battery Calculation**: Enhanced uptime-based charge estimation
5. **SSL Certificate Naming**: Fixed certificate.pem/private_key.pem references

---

## 🚀 Performance Improvements

### Motion Detection Optimization
- **Frame Skipping**: Checks every 2nd frame (50% CPU reduction)
- **Reduced Buffer**: 8 frames instead of 15 (memory optimization)
- **Shorter Cooldown**: 3 seconds between events (was 5 seconds)
- **Selective Processing**: Only processes frames for motion check

### Pi Zero 2W Specific
- **15 FPS Recording**: Balanced quality vs. performance
- **640x480 Resolution**: Optimal for 512MB RAM
- **Lightweight Mode**: Minimal background processing
- **Efficient Buffering**: Small memory footprint

---

## 📋 Changed Files

### Core Components
- `src/core/motion_logger.py` - EST timezone support
- `src/core/battery_monitor.py` - Enhanced calculation
- `web/app_lite.py` - Registration, WiFi config, improved motion detection

### Templates
- `web/templates/motion_events.html` - Responsive design, timestamp fixes
- `web/templates/config.html` - WiFi settings section
- `web/templates/dashboard_lite.html` - UI improvements

---

## 🔒 Security Considerations

### Excluded from Repository (via .gitignore)
- ✅ SSL/TLS certificates (`certs/*.pem`, `certs/*.key`)
- ✅ User database (`config/users.db`)
- ✅ Configuration files (`config/config.json`)
- ✅ Video recordings (`recordings/*.mp4`)
- ✅ Log files (`logs/*.log`)
- ✅ Environment variables (`.env*`)

### Included (Safe for Public)
- ✅ Source code (no hardcoded credentials)
- ✅ Default configuration template
- ✅ Documentation
- ✅ Deployment scripts

---

## 📦 Installation

### Quick Setup
```bash
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV
python3 -m pip install -r requirements.txt
python3 main_lite.py
```

### Full Documentation
See `SETUP_GUIDE_V2.1.0.md` for comprehensive installation instructions.

---

## 🧪 Testing

### Verified On
- ✅ Raspberry Pi Zero 2W (512MB RAM)
- ✅ Raspberry Pi Camera Module v3 (IMX708)
- ✅ Debian Bullseye (Raspberry Pi OS)
- ✅ Chrome/Edge (HTML5 video playback)

### Test Scenarios
- ✅ Motion detection with person movement
- ✅ Shadow/sunlight filtering
- ✅ Video recording and playback
- ✅ File deletion and storage cleanup
- ✅ User registration and authentication
- ✅ WiFi configuration persistence
- ✅ Battery monitoring accuracy

---

## 🔧 Known Issues

1. **Audio Recording**: Pi Camera Module v3 has no built-in microphone (requires USB mic)
2. **WiFi Application**: Settings saved but require reboot to apply system-wide
3. **HTTPS Warnings**: Self-signed certificates show browser warnings (expected)

---

## 📚 Documentation

- `README.md` - Project overview
- `SETUP_GUIDE_V2.1.0.md` - Installation guide
- `DEPLOYMENT_GUIDE.md` - Pi deployment instructions
- `TROUBLESHOOTING.md` - Common issues and fixes
- `HTTPS_SETUP_COMPLETE_GUIDE.md` - SSL/TLS configuration

---

## 🙏 Acknowledgments

Built for lightweight security camera applications on resource-constrained devices.

---

## 📞 Support

Report issues: https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV/issues

---

**Enjoy your enhanced security camera system! 📹**
