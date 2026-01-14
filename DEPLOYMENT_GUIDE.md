# ME_CAM v2.0 - Complete Deployment & Security Guide

## 🎯 Project Overview

ME_CAM is a **secure, private, self-hosted video surveillance system** that:
- ✅ Works WITHOUT subscriptions (unlike Arlo/Ring)
- ✅ Keeps video **100% private on your device**
- ✅ Supports multiple devices per user account
- ✅ Features encrypted motion logging with timestamps
- ✅ Mobile-friendly dashboard
- ✅ Works on Pi Zero 2W with fast response times
- ✅ Professional-grade encryption
- ✅ Emergency alerts (SMS/Email)

---

## 📋 Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [Quick Start (15 minutes)](#quick-start)
3. [Detailed Setup Guide](#detailed-setup-guide)
4. [Security Hardening](#security-hardening)
5. [Configuration Guide](#configuration-guide)
6. [Troubleshooting](#troubleshooting)
7. [Features Breakdown](#features-breakdown)

---

## 📱 Hardware Requirements

### Minimum
- **Raspberry Pi Zero 2W** (or newer Pi)
- **Power Supply**: 5V 2.5A USB-C
- **microSD Card**: 32GB (Class 10)
- **Camera Module**: Pi Camera v2 or IMX7098 (USB)

### Recommended
- **Raspberry Pi 4** or **Pi 5** (better performance)
- **64GB microSD** (longer storage)
- **Fast USB Camera** (better FPS)
- **Cooling Case** (thermal management)
- **PoE Adapter** (optional, for network power)

---

## 🚀 Quick Start

### 1. Flash SD Card

```bash
# Download Raspberry Pi Imager
# https://www.raspberrypi.com/software/

# Select:
# - Raspberry Pi OS Lite (latest)
# - 32GB SD card
# - Enable SSH (in advanced options)
# - Set hostname: me-cam-1
# - Set username: pi
# - Set password: [your-password]
```

### 2. SSH into Pi

```bash
ssh pi@me-cam-1.local
# Or: ssh pi@<pi-ip-address>
```

### 3. One-Line Deploy

```bash
# Download and run deployment script
curl -O https://raw.githubusercontent.com/YOUR_REPO/ME_CAM-DEV/main/scripts/deploy_pi_zero.sh

# Make executable and run (as root)
chmod +x deploy_pi_zero.sh
sudo bash deploy_pi_zero.sh

# The script will:
# ✓ Create dedicated user
# ✓ Install all dependencies
# ✓ Setup Python environment
# ✓ Create systemd service
# ✓ Enable autoboot
```

### 4. Access Dashboard

```
http://me-cam-1.local:8080
# Or: http://<pi-ip>:8080
```

---

## 🔧 Detailed Setup Guide

### Manual Installation (if deploy script fails)

```bash
# 1. Update system
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install dependencies
sudo apt-get install -y python3-pip python3-venv python3-dev \
    libopenjp2-7 libtiff5 libjasper1 git curl ffmpeg \
    libffi-dev libssl-dev

# 3. Create directory
mkdir -p ~/ME_CAM-DEV
cd ~/ME_CAM-DEV

# 4. Clone repo (or download ZIP)
git clone https://github.com/YOUR_REPO/ME_CAM-DEV.git .

# 5. Create virtual environment
python3 -m venv --system-site-packages venv
source venv/bin/activate

# 6. Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 7. Run application
python3 main.py

# 8. Access dashboard
# Open: http://raspberrypi.local:8080
```

---

## 🔐 Security Hardening

### 1. Change Default Password

**On First Run:**
- Open http://pi-ip:8080
- Complete setup wizard
- Create strong admin password (min 12 chars)
- Enable PIN code (optional)

### 2. Enable Encryption

**In Dashboard → Settings:**
```
✓ Enable data encryption
✓ Enable video encryption
✓ Store encryption keys locally only
```

### 3. Secure Network Access

```bash
# SSH into Pi
ssh pi@me-cam-1.local

# Disable weak SSH access
sudo nano /etc/ssh/sshd_config

# Make these changes:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
X11Forwarding no

# Restart SSH
sudo systemctl restart ssh
```

### 4. Firewall Setup

```bash
# Enable UFW firewall
sudo apt-get install ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8080/tcp  # Dashboard
sudo ufw enable
```

### 5. Backup Encryption Keys

```bash
# CRITICAL: Backup encryption keys
sudo cp config/.encryption_key ~/encryption_key.backup

# Store backup in secure location (password manager, cloud, etc)
# WITHOUT THIS, YOU CANNOT DECRYPT YOUR VIDEOS!
```

---

## ⚙️ Configuration Guide

### 1. First-Run Setup (In Dashboard)

**Device Information:**
- Device Name: "Front Door Camera"
- Location: "Porch"
- Device Type: Camera (v2 or USB)

**Camera Settings:**
- Resolution: 640x480 (Pi Zero) or 1280x720 (Pi 4+)
- Frame Rate: 15 FPS (Pi Zero) or 30 FPS (Pi 4+)
- Stream Quality: Standard (adjustable in settings)

**Motion Detection:**
- Sensitivity: 0.6 (0.0=sensitive, 1.0=ignore noise)
- Person Detection: ON (requires extra CPU)
- Minimum Duration: 3 seconds

**Storage:**
- Max Storage: 10 GB (adjust for your card)
- Retention: 7 days
- Cleanup When Full: 90%

**Emergency Contacts:**
- Primary Phone: +1-555-0123
- Email: your@email.com
- SMS Gateway: Twilio (optional)

### 2. Advanced Settings

**Motion Logging:**
- ✓ Log all motion events
- ✓ Include timestamps
- ✓ Store locally + cloud backup

**Video Quality:**
- Preview: 320x240 (dashboard only)
- Recording: 1280x720 (local storage)
- Cloud Backup: 640x480 (bandwidth optimized)

**Detection Options:**
- Motion Detection: ✓
- Person Detection: ✓
- Face Detection: ✗ (privacy)
- Intruder Alert: ✓

---

## 🐛 Troubleshooting

### No Video Feed

```bash
# Check camera is recognized
vcgencmd get_camera

# View camera logs
sudo journalctl -u mecamera -n 50

# Check if camera is busy
ps aux | grep libcamera

# Fix: Restart service
sudo systemctl restart mecamera
```

### Motion Events Not Logging

```bash
# Check if motion service started
sudo systemctl status mecamera

# View motion logs
cat logs/motion_events.json | python3 -m json.tool | head -20

# Check disk space
df -h

# Check if storage path exists
ls -la recordings/
```

### Dashboard Won't Load

```bash
# Check Flask is running
ps aux | grep python3

# Check port 8080
netstat -tuln | grep 8080

# Restart service
sudo systemctl restart mecamera

# Check logs for errors
sudo journalctl -u mecamera -f
```

### High CPU Usage

```bash
# Reduce frame rate in settings (15 FPS for Pi Zero)

# Disable person detection if not needed

# Check running processes
top -b -n 1 | head -20

# View memory usage
free -h
```

### Storage Full

**Automatic Cleanup:**
- Dashboard → Settings → Storage
- Set "Cleanup When Full" to 80%

**Manual Cleanup:**
```bash
# Delete old recordings
cd recordings
ls -lat | tail -10 | awk '{print $NF}' | xargs rm

# OR via dashboard: 🗑️ Clear All button
```

---

## 🎯 Features Breakdown

### 1. Live Camera Feed
- Real-time MJPEG stream
- Mobile responsive
- Pause/Resume control
- Screenshot capture
- Fullscreen mode

### 2. Motion Detection & Logging
- **Real-time detection** with timestamp
- **Event history** searchable by date/type
- **Confidence scoring** (0-100%)
- **Export as CSV** for analysis
- Motion event trends

### 3. Video Recording
- **Auto-recording** on motion (configurable)
- **30-second clips** (adjustable)
- **Multiple quality levels**
- **Automatic cleanup** after N days
- **Local + cloud backup** options

### 4. Security & Privacy
- **End-to-end encryption** (AES-256)
- **User authentication** (password + PIN)
- **No cloud storage required**
- **All data stays on device**
- **No subscriptions**

### 5. Emergency Alerts
- **🚨 General Emergency** - Sends to all contacts
- **🏥 Medical Alert** - Flags as medical emergency
- **🔒 Security Alert** - Flags as intrusion/security

Send via:
- SMS (Twilio integration)
- Email (SMTP)
- Webhooks (custom integrations)

### 6. Multi-Device Support
- Add multiple cameras
- View unified dashboard
- Combined event timeline
- Synchronized recording

### 7. Smart Storage Management
- **Automatic retention** (e.g., 7 days)
- **Intelligent cleanup** when full
- **Size-based limits** per device
- **Compression** options
- **Migration to USB** support

### 8. Mobile-First Dashboard
- Responsive design
- Touch-optimized controls
- Works on phones/tablets
- Offline capability
- Fast performance

---

## 📊 Comparison: ME_CAM vs Arlo/Ring

| Feature | ME_CAM | Arlo | Ring |
|---------|--------|------|------|
| **Subscription** | ❌ None | ✅ $10-100/mo | ✅ $100-200/yr |
| **Privacy** | ✅ 100% Local | ❌ Cloud Storage | ❌ Cloud Storage |
| **Encryption** | ✅ AES-256 E2E | ⚠️ Proprietary | ⚠️ Proprietary |
| **Multiple Devices** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Motion Logging** | ✅ Yes, Timestamped | ✅ Limited | ✅ Limited |
| **Mobile App** | ✅ Web-based | ✅ App | ✅ App |
| **Open Source** | ✅ Yes | ❌ No | ❌ No |
| **Self-Hosted** | ✅ Yes | ❌ No | ❌ No |
| **Hardware Cost** | $30-150 | $100-400 | $100-400 |
| **24hr Events** | ✅ Unlimited | ✅ Limited | ✅ Limited |
| **Emergency Alerts** | ✅ Yes | ❌ Ring Protect | ✅ Premium |

---

## 🔄 Maintenance

### Weekly
- Check disk usage (Dashboard → Storage)
- Review motion logs for unusual activity
- Test emergency alert system

### Monthly
- Backup encryption keys
- Update system: `sudo apt-get update && upgrade`
- Review camera angle, clean lens

### Quarterly
- Full database cleanup (7+ day old events)
- Test disaster recovery (restore from backup)
- Security audit (logs, access patterns)

---

## 📞 Support & Contributions

- **Issues**: Report via GitHub
- **Questions**: Check wiki/docs
- **Contributions**: Pull requests welcome
- **Security**: Report privately to maintainers

---

## 📄 License

MIT License - See LICENSE file

**Made with ❤️ for privacy-conscious users**
