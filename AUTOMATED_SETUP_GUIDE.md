# ME_CAM Automated Setup Guide

**Version:** 2.2.3  
**Date:** February 2026  
**Script:** `scripts/auto_setup_mecam.sh`

## Quick Start (Easiest)

Once your Raspberry Pi is booted with a fresh OS and has internet/WiFi:

```bash
# Method 1: Via GitHub (Recommended)
curl -sSL https://raw.githubusercontent.com/MangiafestoElectronicsLLC/ME_CAM-DEV/main/scripts/auto_setup_mecam.sh | bash

# Method 2: Manual
cd ~
wget https://raw.githubusercontent.com/MangiafestoElectronicsLLC/ME_CAM-DEV/main/scripts/auto_setup_mecam.sh
bash auto_setup_mecam.sh
```

## What It Does Automatically

### Hardware Detection
- **Pi Model**: Detects Zero 2W, Pi 4, Pi 5, etc.
- **RAM**: Measures available memory
- **Camera**: Detects IMX519, OV547, OV5647, IMX708, or auto-configures
- **SD Card**: Detects 32GB, 64GB, 128GB, 256GB+

### Device Configuration
- **Hostname**: Sets to `mecamdev#` (auto-numbered 1-99)
- **Config File**: Creates `config.json` with detected specs
- **Framerate**: Optimizes based on Pi model (30-60 FPS)
- **Storage**: Calculates limits based on SD card size

### System Setup
- Updates system packages
- Installs all dependencies (libcamera, Python, OpenCV, etc.)
- Clones or updates ME_CAM repository
- Creates Python virtual environment
- Installs Python packages from requirements.txt

### Service Configuration
- Registers systemd service for auto-boot
- Enables automatic startup on power
- Provides logging via journalctl

## Running the Script

### Option 1: From Your PC (Windows)

```powershell
# On Windows, in PowerShell (in the repo directory):
$piHost = "mecamdev6.local"  # Change to your Pi hostname
$piUser = "pi"
$piPass = "your_password"    # Your Pi password

# Copy script to Pi
scp .\scripts\auto_setup_mecam.sh pi@$piHost`:~/
ssh pi@$piHost "bash ~/auto_setup_mecam.sh"
```

### Option 2: Direct on Pi

```bash
# SSH into your Pi first:
ssh pi@raspberrypi.local

# Run the script:
bash ~/auto_setup_mecam.sh

# Or download it first:
cd ~
curl -O https://raw.githubusercontent.com/MangiafestoElectronicsLLC/ME_CAM-DEV/main/scripts/auto_setup_mecam.sh
bash auto_setup_mecam.sh
```

### Option 3: With Git Clone (If repo not yet installed)

```bash
# Pi has internet and Git installed:
cd ~
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV
bash scripts/auto_setup_mecam.sh
```

## What You'll Be Asked

The script will prompt you for:

1. **Device Number** (1-99)
   - Used to create hostname: `mecamdev1`, `mecamdev2`, etc.
   - If already set, it will detect and use existing number
   - Example: Enter `6` → hostname becomes `mecamdev6`

That's it! Everything else is automatic.

## After Setup Completes

You'll see a summary like:

```
========================================
  ME_CAM Setup Complete!
========================================

Device Information:
  Hostname:       mecamdev6
  Device ID:      pi-cam-006
  Pi Model:       Raspberry Pi Zero 2W
  RAM:            512MB
  Camera:         IMX519 (I2C)
  SD Card:        64GB

Access your camera at:
  http://mecamdev6.local:8080

Next Steps:
  1. Configure WiFi (if not already done)
  2. Reboot the Pi:
     sudo reboot
```

### Important: Reboot After Setup

```bash
sudo reboot
```

After reboot (2 minutes), access your camera:
- **Browser**: `http://mecamdev6.local:8080`
- **Direct IP**: Find with `hostname -I` on the Pi

## Accessing the Camera

Once running:

```bash
# View live status
sudo systemctl status mecamera

# View real-time logs
sudo journalctl -u mecamera -f

# Restart service
sudo systemctl restart mecamera

# Stop service
sudo systemctl stop mecamera

# Check camera manually
cd ~/ME_CAM-DEV
source venv/bin/activate
python3 main.py
```

## Troubleshooting

### "Device number from hostname: X" appears but I want to change it
The script detects existing device numbers from the hostname. To change it:

```bash
# Edit the saved number:
nano ~/ME_CAM-DEV/config/device_number.txt
# Change the number and save
sudo hostname mecamdevNEW
sudo reboot
```

### Camera Still Not Detected After Reboot
The script configures camera overlays in `/boot/firmware/config.txt` for known cameras. If detection failed:

```bash
# Check what's in config.txt:
grep -i "dtoverlay\|camera" /boot/firmware/config.txt

# If nothing, manually add for IMX519 (Device 3 example):
sudo nano /boot/firmware/config.txt
# Add:
camera_auto_detect=0
dtoverlay=imx519
gpu_mem=128
# Then: sudo reboot
```

### Web Dashboard Won't Load
```bash
# Check if service is running:
sudo systemctl status mecamera

# Check recent logs:
sudo journalctl -u mecamera -n 50

# Try manually:
cd ~/ME_CAM-DEV
source venv/bin/activate
python3 main.py
```

### Hostname Not Applied
Hostname changes take effect after reboot:

```bash
sudo reboot
# Wait 2 minutes
ping mecamdev6.local
```

## Generated Configuration

The script creates `~/ME_CAM-DEV/config/config.json`:

```json
{
    "first_run_completed": true,
    "device_name": "ME_CAM_6",
    "device_id": "pi-cam-006",
    "hardware": {
        "pi_model": "Raspberry Pi Zero 2W",
        "pi_ram_mb": 512,
        "camera": "IMX519 (I2C)",
        "sd_capacity_gb": 64
    },
    "resolution": "640x480",
    "framerate": 30,
    "motion_detection": true,
    "video_length": 30,
    "storage_limit_gb": 32,
    "auto_delete_old": true,
    "web_port": 8080,
    "setup_timestamp": "2026-02-19T15:30:45Z",
    "setup_automated": true
}
```

Edit this file to fine-tune settings:

```bash
nano ~/ME_CAM-DEV/config/config.json
sudo systemctl restart mecamera
```

## Multi-Device Setup with Script

For multiple devices, just run the script on each Pi with a different device number:

```bash
# Device 1
ssh pi@mecamdev1.local
bash auto_setup_mecam.sh
# When prompted: Enter 1

# Device 2
ssh pi@mecamdev2.local
bash auto_setup_mecam.sh
# When prompted: Enter 2

# ... repeat for each Pi
```

Each will get:
- Unique hostname
- Unique device ID
- Same optimized configuration based on that Pi's hardware

## Advanced: Batch Setup Script

To setup multiple devices at once from Windows, create this PowerShell script:

**File: `setup_all_devices.ps1`**

```powershell
# Configuration
$devices = @(
    @{ hostname = "raspberrypi.local"; number = 1 },
    @{ hostname = "raspberrypi.local"; number = 2 }
)
$piUser = "pi"
$piPassword = "your_password"

foreach ($device in $devices) {
    Write-Host "Setting up device $($device.number)..." -ForegroundColor Green
    
    # Copy script
    scp -p .\scripts\auto_setup_mecam.sh "$piUser@$($device.hostname)`:~/"
    
    # Run with device number (non-interactive)
    $cmd = "cd ~; bash auto_setup_mecam.sh"
    # Note: For fully automated, modify script to accept CLI args for device number
    ssh "$piUser@$($device.hostname)" $cmd
    
    Write-Host "Device $($device.number) setup complete" -ForegroundColor Green
    Start-Sleep -Seconds 10
}
```

## Script Features

### Color-Coded Output
- 🔵 **[INFO]** - Information messages
- ✅ **[SUCCESS]** - Successful operations
- ⚠️ **[WARN]** - Warnings (like camera not detected yet)
- ❌ **[ERROR]** - Errors requiring attention

### Safety Features
- Checks for existing installations and updates instead of overwriting
- Validates device numbers (1-99)
- Handles missing dependencies gracefully
- Uses `set -e` to stop on errors

### Efficiency
- Downloads all packages in one pass
- Uses parallel apt-get where possible
- Caches git operations
- Skips already-installed packages

## Support

If script fails:

1. Check the error message (RED text with [ERROR])
2. Run manually:
   ```bash
   cd ~/ME_CAM-DEV
   source venv/bin/activate
   python3 main.py
   ```
3. Share the error from:
   ```bash
   sudo journalctl -u mecamera -n 100
   ```

## Modifying the Script

The script is well-commented. To customize:

```bash
# Edit on the Pi:
nano ~/auto_setup_mecam.sh

# Or on Windows, edit and copy:
# Edit: scripts/auto_setup_mecam.sh
scp .\scripts\auto_setup_mecam.sh pi@mecamdev6.local:~/
ssh pi@mecamdev6.local "bash ~/auto_setup_mecam.sh"
```

Key sections to modify:
- **Storage limits** (line ~215): Adjust % of SD card used
- **Framerate defaults** (line ~219): Set FPS per Pi model
- **Camera overlays** (line ~265): Add new camera types

## License

Script by MangiafestoElectronics LLC (Feb 2026)  
Part of ME_CAM v2.2.3 security camera system

---

**Need help?** Check the main [FRESH_SD_CARD_TUTORIAL_SIMPLE.md](FRESH_SD_CARD_TUTORIAL_SIMPLE.md) for manual setup steps or troubleshooting.
