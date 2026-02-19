# ME_CAM Automated Setup Scripts

**Version:** 2.2.3  
**Location:** `scripts/` directory

Quick reference for setting up Raspberry Pi devices with ME_CAM v2.2.3

## 📋 Files Included

### 1. `auto_setup_mecam.sh` (Main Setup Script)
**Runs on:** Raspberry Pi  
**Purpose:** Fully automated setup with auto-detection

**What it detects:**
- ✅ Pi hardware (Zero 2W, Pi 4, Pi 5)
- ✅ RAM and CPU capabilities
- ✅ Camera type (IMX519, OV547, etc.)
- ✅ SD card capacity (32GB, 64GB, 128GB, 256GB)
- ✅ Device number (1-99)

**What it installs:**
- Python 3 with venv
- Camera libraries (libcamera, picamera2)
- OpenCV and dependencies
- Flask and web server
- Systemd service for auto-boot

**Time required:** 10-15 minutes

### 2. `setup_mecam_devices.ps1` (Windows Helper)
**Runs on:** Windows PowerShell  
**Purpose:** Interactive menu to setup and manage Pi devices

**Features:**
- Setup single device
- Setup multiple devices in batch
- Check device status
- View live logs
- Reboot devices

**Requirements:** SSH access (OpenSSH or Git Bash)

---

## 🚀 Quick Start

### On Raspberry Pi (Easiest)

```bash
# Method A: Download and run
curl -sSL https://raw.githubusercontent.com/MangiafestoElectronicsLLC/ME_CAM-DEV/main/scripts/auto_setup_mecam.sh | bash

# Method B: Clone repo first, then run
cd ~
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV
bash scripts/auto_setup_mecam.sh
```

**When prompted, enter device number (1-99)**

### From Windows

#### Option 1: Using PowerShell Helper
```powershell
cd .\ME_CAM-DEV
.\scripts\setup_mecam_devices.ps1
# Follow the interactive menu
```

#### Option 2: Manual SSH
```powershell
ssh pi@mecamdev6.local
# Then follow "On Raspberry Pi" steps above
```

---

## 📊 What Gets Auto-Configured

### Device Information
```json
{
  "device_name": "ME_CAM_6",
  "device_id": "pi-cam-006",
  "hostname": "mecamdev6",
  "hardware": {
    "pi_model": "Raspberry Pi Zero 2W",
    "ram_mb": 512,
    "camera": "IMX519 (I2C)",
    "sd_capacity_gb": 64
  }
}
```

### Performance Settings
| Pi Model | Framerate | Resolution | Memory Limit |
|----------|-----------|-----------|-------------|
| Zero 2W  | 30 FPS    | 640x480   | 256MB      |
| Pi 4 (1GB) | 30 FPS  | 640x480   | 256MB      |
| Pi 4 (2GB+) | 40 FPS | 640x480   | 512MB      |
| Pi 5     | 60 FPS    | 1280x720  | 1GB        |

### Storage Calculation
| SD Card | Storage Limit |
|---------|---------------|
| 32GB    | 16GB video    |
| 64GB    | 32GB video    |
| 128GB   | 64GB video    |
| 256GB   | 100GB video   |

---

## 🔧 Configuration Files Created

After setup completes:

### Main Config
**File:** `~/ME_CAM-DEV/config/config.json`

```bash
# View config
cat ~/ME_CAM-DEV/config/config.json

# Edit config
nano ~/ME_CAM-DEV/config/config.json

# Restart service after editing
sudo systemctl restart mecamera
```

### Device Number
**File:** `~/ME_CAM-DEV/config/device_number.txt`

Contains the device number (1-99) for reference

### System Service
**File:** `/etc/systemd/system/mecamera.service`

Starts ME_CAM automatically on boot

---

## 📱 Accessing Your Camera

After setup and reboot:

```
http://mecamdev6.local:8080
```

Replace `6` with your device number.

**First login:**
1. Sign in with temporary admin credentials
2. Redirect to setup page to create customer account
3. Admin account auto-deleted
4. Future logins use customer account

---

## 🔧 Common Commands

```bash
# Check service status
sudo systemctl status mecamera

# View live logs
sudo journalctl -u mecamera -f

# Restart service
sudo systemctl restart mecamera

# Stop service
sudo systemctl stop mecamera

# Manual test
cd ~/ME_CAM-DEV
source venv/bin/activate
python3 main.py

# Change hostname
sudo hostnamectl set-hostname mecamdev7
sudo reboot

# Check camera directly
rpicam-jpeg -o test.jpg --width 640 --height 480
```

---

## 🐛 Troubleshooting

### Script Fails to Run
```bash
# Make script executable
chmod +x auto_setup_mecam.sh

# Run with explicit bash
bash auto_setup_mecam.sh

# Or download fresh
curl -O https://raw.githubusercontent.com/MangiafestoElectronicsLLC/ME_CAM-DEV/main/scripts/auto_setup_mecam.sh
bash auto_setup_mecam.sh
```

### Camera Not Detected
```bash
# Check what's configured
grep "dtoverlay\|camera" /boot/firmware/config.txt

# For IMX519 (I2C), manually add:
sudo nano /boot/firmware/config.txt
# Add these lines:
camera_auto_detect=0
dtoverlay=imx519
gpu_mem=128

sudo reboot
```

### Web Dashboard Won't Load
```bash
# Check if service is running
sudo systemctl status mecamera

# View full logs
sudo journalctl -u mecamera -n 100

# Try manual start
cd ~/ME_CAM-DEV
source venv/bin/activate
python3 main.py
```

### Hostname Not Resolving
```bash
# Find IP directly
hostname -I

# Access via IP instead
# Example: http://10.2.1.50:8080

# Or try numeric hostname
ping 10.2.1.50
```

---

## 📝 For Multiple Devices

**Setup Device 1:**
```bash
ssh pi@mecamdev1.local
bash auto_setup_mecam.sh
# Enter: 1
```

**Setup Device 2:**
```bash
ssh pi@mecamdev2.local
bash auto_setup_mecam.sh
# Enter: 2
```

**Or batch from Windows:**
```powershell
.\scripts\setup_mecam_devices.ps1
# Select "Setup Multiple Devices"
# Enter: mecamdev1.local, mecamdev2.local, mecamdev3.local
```

---

## 🔐 Security Notes

⚠️ **Change Default Credentials!**

After first login:
1. Dashboard → Settings → Change Password
2. SSH Password: `passwd` on Pi
3. Consider disabling password login in `/etc/ssh/sshd_config`

---

## 📚 Full Guides

- **Manual Setup:** See [FRESH_SD_CARD_TUTORIAL_SIMPLE.md](../FRESH_SD_CARD_TUTORIAL_SIMPLE.md)
- **Automated Setup Details:** See [AUTOMATED_SETUP_GUIDE.md](../AUTOMATED_SETUP_GUIDE.md)
- **Customer Guide:** See [CUSTOMER_INSTRUCTION_MANUAL.md](../CUSTOMER_INSTRUCTION_MANUAL.md)

---

## 📞 Support

**Script Issues:**
```bash
# Get diagnostic info
pi@mecamdev6:~ $ echo "=== System Info ===" && \
  uname -a && \
  echo "=== Git Status ===" && \
  cd ~/ME_CAM-DEV && git log -1 && \
  echo "=== Python Version ===" && \
  python3 --version && \
  echo "=== Camera Status ===" && \
  rpicam-hello --version
```

**Share this output for support**

---

## 📋 Script Checklist

After running `auto_setup_mecam.sh`, you should have:

- ✅ System updated
- ✅ All dependencies installed
- ✅ Repository cloned/updated
- ✅ Python virtual environment created
- ✅ Configuration file created with detected specs
- ✅ Systemd service registered
- ✅ Camera overlay configured (if applicable)
- ✅ Reboot required (for hostname and camera changes)

---

## Version Info

- **Script Version:** 2.2.3
- **Release Date:** February 2026
- **Tested On:** Raspberry Pi Zero 2W, Pi 4, Pi 5
- **OS:** Raspberry Pi OS Lite (32-bit & 64-bit)

---

**Created by:** MangiafestoElectronics LLC  
**Last Updated:** February 2026
