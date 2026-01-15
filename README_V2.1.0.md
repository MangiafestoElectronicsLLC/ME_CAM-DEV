# ME Camera System v2.1.0
## Professional Motion Detection & Monitoring for Raspberry Pi

![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Pi Compatibility](https://img.shields.io/badge/Raspberry%20Pi-Zero%202W%20%7C%203%20%7C%204%20%7C%205-red.svg)

**ME Camera** is a lightweight, production-ready motion detection system for Raspberry Pi with real-time video recording, emergency alerts, battery monitoring, and cloud integration support.

---

## ✨ Key Features

### 🎥 Video & Monitoring
- **Real-time Video Streaming** - Live camera feed with configurable resolution and quality
- **Motion Detection** - Intelligent motion recording with 3-second MP4 clips
- **Nanny Cam Mode** - View-only monitoring without recording history
- **Dual Format Support** - MP4 video + JPEG snapshot fallback

### 🔔 Alerts & Notifications
- **Emergency Alerts** - Manual SOS trigger with SMS support
- **Motion Notifications** - Automatic alerts on motion detection
- **SMS Integration** - Generic HTTP API support (Twilio, Plivo, custom)
- **Event Logging** - Complete motion event history with timestamps

### 🔋 Power Management
- **Battery Monitoring** - Real-time battery status (optimized for 10Ah power banks)
- **Runtime Calculation** - Accurate remaining runtime in hours/minutes
- **External Power Detection** - Automatic mode switching

### 💾 Storage & Cleanup
- **Automatic Cleanup** - Delete recordings older than X days
- **Storage Monitoring** - Real-time disk usage tracking
- **Smart Organization** - Date-based file organization

### ⚙️ Configuration
- **Web-based Config** - Easy setup without touching code
- **Device Management** - Name, location, contacts
- **SMS Configuration** - Setup generic HTTP API endpoints
- **Threshold Tuning** - Motion sensitivity adjustment

### 🔐 Security
- **Authentication** - PIN code + username/password
- **Session Management** - Secure web sessions
- **Local Storage** - All data stays on device

---

## 📋 Hardware Requirements

### Minimum
- **Pi Model**: Raspberry Pi Zero 2W (512MB RAM)
- **Power**: USB-C 5V 2.5A power supply
- **Storage**: 32GB microSD card (UHS-II recommended)
- **Camera**: Raspberry Pi Camera Module (any version)

### Recommended
- **Pi Model**: Raspberry Pi 4 or 5 (2GB+ RAM)
- **Power**: USB-C 5V 3A power supply (Pi 4/5)
- **Storage**: 64GB+ microSD card for extended recording
- **Network**: WiFi 5GHz or Ethernet for stable streaming

### Optional
- USB Battery Pack (10000mAh, 5V output)
- USB Hub with power supply for additional accessories

---

## 🚀 Quick Start (5 minutes)

### 1. Flash SD Card
```bash
# Download Raspberry Pi Imager
# https://www.raspberrypi.com/software/

# Select:
# - OS: Raspberry Pi OS Lite (Bullseye) 
# - Storage: Your microSD card
# - Advanced: Enable SSH, configure WiFi, set timezone
# Click WRITE and wait 5-15 minutes
```

### 2. Initial Setup
```bash
# Connect to Pi via SSH
ssh pi@mecamera.local

# Update system
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3-pip python3-venv

# Clone repository
cd ~
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV

# Run install script
bash scripts/setup.sh
```

### 3. First Access
```
URL: http://10.2.1.47:8080
Username: admin
Password: admin123  (change in config!)
```

---

## 🛠️ Installation Details

### Step 1: Disable Legacy Camera (CRITICAL)
```bash
# Required for Pi 3B+, 4, 5 to detect camera
sudo raspi-config
# Go to 3 Interface Options → I1 Legacy Camera → No
# Then 3 Interface Options → I3 Camera → Yes → Reboot
```

### Step 2: Clone & Setup
```bash
cd ~
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Configure Pi
```bash
# For Pi Zero 2W (Lite mode, 3-second videos)
python3 main_lite.py --mode lite --pi zero2w

# For Pi 3B+ or higher
python3 main_lite.py --mode lite --pi 3bplus

# For Pi 4
python3 main_lite.py --mode lite --pi 4

# For Pi 5
python3 main_lite.py --mode lite --pi 5
```

### Step 4: Install Service
```bash
# Copy systemd service file
sudo cp etc/systemd/mecamera-lite.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mecamera-lite
sudo systemctl start mecamera-lite

# Verify
sudo systemctl status mecamera-lite
```

### Step 5: Access Dashboard
```
Browser: http://<pi-ip>:8080
Login: admin / admin123
```

---

## 📱 Web Interface

### Dashboard
- Live video stream from camera
- Battery status with runtime (hours/minutes)
- Storage usage overview
- Nanny Cam toggle switch
- Quick emergency alert button

### Motion Events
- Complete event history with timestamps
- Download button for individual videos/images
- Share functionality (web link, native share)
- Save events as JSON
- Delete individual or all events
- Local timezone display (configurable)

### Configuration
- Device name, location, device ID
- Emergency phone number
- Motion recording settings
- SMS configuration (API URL, key, phone)
- Storage cleanup settings
- Battery monitoring status

---

## 🔧 Configuration Reference

### config_default.json
```json
{
  "device_name": "ME_CAM_1",
  "device_location": "Kitchen",
  "emergency_phone": "+14155552555",
  "motion_threshold": 0.5,
  "motion_record_enabled": true,
  "motion_record_duration": 10,
  "sms_enabled": false,
  "sms_api_url": "https://api.sms-provider.com/send",
  "sms_api_key": "your_api_key_here",
  "sms_phone_to": "+14155552555",
  "sms_rate_limit": 5,
  "storage_cleanup_days": 7,
  "nanny_cam_enabled": false
}
```

### SMS Integration (Generic HTTP API)
```bash
# The system sends POST request to your SMS API:
POST /send
{
  "to": "+1234567890",
  "from": "ME_CAM_1",
  "message": "🎥 Motion Alert from Kitchen\nTime: 2026-01-15 14:33:22\nType: MOTION\nConfidence: 95%"
}

# API Response (expected 200/201):
{
  "status": "sent",
  "message_id": "msg_123abc"
}
```

**Supported Providers:**
- **Generic HTTP** - Any custom API endpoint
- **Twilio** - SMS/WhatsApp (requires account)
- **Plivo** - SMS service (requires account)
- **AWS SNS** - Scalable messaging

---

## 📊 Storage & Recording

### Recording Format
- **Type**: MP4 (H.264 codec)
- **Duration**: 3 seconds per motion event
- **Resolution**: 640x480 (configurable)
- **Frame Rate**: 20 FPS
- **File Size**: ~50KB per 3-second clip
- **Fallback**: JPEG snapshot if MP4 fails

### Storage Management
```bash
# Recordings stored in: ~/ME_CAM-DEV/recordings/
# Naming format: motion_YYYYMMDD_HHMMSS.{mp4|jpg}

# Auto-cleanup settings:
- Delete videos older than 7 days
- Keep JPEG snapshots separate
- Configurable retention period
- Manual cleanup via web interface
```

### Disk Usage Example (Pi Zero 2W)
```
32GB microSD card:
- OS + Software: ~3GB
- Available for recordings: ~25GB
- At 50KB per 3-second clip: ~500,000 clips stored
- At 1 clip every 30 seconds: ~416 days of continuous motion
```

---

## 🔐 Security Best Practices

### Change Default Credentials
```bash
# SSH into Pi
ssh pi@mecamera.local

# Change admin password in web UI:
# Settings → Change Password

# Change system user password:
passwd  # changes 'pi' user password
```

### Network Security
```bash
# Enable SSH key authentication (recommended)
# Disable password auth
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
# Add: PubkeyAuthentication yes

# Firewall (if desired)
sudo ufw allow 8080/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

### SSL/TLS (Optional, for production)
```bash
# Use reverse proxy with nginx + certbot
# See docs/wireguard_setup.md for examples
```

---

## 🐛 Troubleshooting

### Camera Not Detected
```bash
# Check legacy camera is disabled
sudo raspi-config

# Restart camera service
sudo systemctl restart mecamera-lite

# Check logs
tail -f ~/.cache/mecamera/logs/app.log
```

### No Video Stream
```bash
# Verify camera connection
vcgencmd get_camera

# Test with Pi camera tools
libcamera-hello --list-cameras

# Check resolution settings
# Reduce from 1280x720 to 640x480
```

### Motion Not Recording
```bash
# Check motion threshold in config
# Lower = more sensitive (0.1 = very sensitive, 0.9 = rarely triggers)

# Check disk space
df -h ~/ME_CAM-DEV/recordings/

# Verify nanny cam mode is OFF
curl http://localhost:8080/api/nanny-cam/status
```

### SMS Not Sending
```bash
# Test API endpoint
curl -X POST http://your-api-url \
  -H "X-API-Key: your_key" \
  -d '{"to":"+1234567890","message":"test"}'

# Check logs
tail -f ~/.cache/mecamera/logs/app.log | grep SMS
```

### Timezone Issues
```bash
# Set correct timezone (Brockport, NY = America/New_York)
sudo timedatectl set-timezone America/New_York
sudo timedatectl status

# Verify in web UI - should show local time for events
```

---

## 📈 Performance Monitoring

### RAM Usage (Pi Zero 2W)
- Idle: ~80MB
- With streaming: ~160MB
- Max safe: 400MB (leave headroom for OS)

### CPU Usage
- Motion detection: 15-25%
- Video streaming: 20-30%
- Recording: 40-60%
- Full load: ~80% max

### Network Bandwidth
- Live streaming: 300-500 Kbps
- Recording upload: 200 Kbps
- Event notifications: <1 Kbps

---

## 🤝 Contributing

To contribute to ME Camera:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Support & Issues

### Getting Help
- **Documentation**: [Complete Docs](docs/README.md)
- **Issues**: [GitHub Issues](https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV/issues)
- **Discussions**: [GitHub Discussions](https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV/discussions)

### Quick Links
- [Installation Guide](docs/README.md)
- [Configuration Guide](docs/wireguard_setup.md)
- [Troubleshooting](QUICK_TROUBLESHOOT.md)

---

## 📝 Version History

### v2.1.0 (Current)
- ✅ MP4 video recording (3-second clips)
- ✅ Generic HTTP SMS integration
- ✅ Timezone support (Eastern Time, configurable)
- ✅ Save/Share/Download for events
- ✅ Nanny Cam mode (view-only)
- ✅ Battery monitoring (10Ah power bank)
- ✅ Professional web dashboard

### v2.0.0
- Motion detection with JPEG snapshots
- Emergency alert system
- Basic configuration UI
- Multi-Pi compatibility

### v1.0.0
- Initial release
- Basic streaming

---

## 👨‍💼 Author

**Mangiafesto Electronics LLC**
- GitHub: [@MangiafestoElectronicsLLC](https://github.com/MangiafestoElectronicsLLC)
- Website: [mangiafestoelectronics.com](https://mangiafestoelectronics.com)

---

**Last Updated**: January 15, 2026  
**Status**: Production Ready ✅

