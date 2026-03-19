# D7/D8 Fleet Deployment Status

## Configuration Status
✓ **generate_config.py**: Both D7 and D8 profiles already defined
  - D7: Pi 5 (1280x720, 60fps, h264)
  - D8: Pi Zero 2W (640x480, 40fps, mjpeg)

✓ **check_all_devices.ps1**: D7 and D8 device definitions present
  - D7: mecamdev7.local (10.2.1.7) - pass: Kiducdi1234567
  - D8: mecamdev8.local (10.2.1.8) - pass: Kidcudi12345678

✓ **activate_devices_poshssh.ps1**: D7 and D8 host mappings in place

## Current Status of Devices (as of last check)
- D1-D4: Production-ready
- D5: Requires SD card reflash (null-byte corruption in main.py)
- D6: Fixed (ffmpeg + espeak-ng installed)
- D7: Awaiting verification
- D8: Awaiting verification

## To Deploy to D7 and D8

### Option 1: Auto-Deploy (Recommended)
If devices are online and network connectivity is verified:
```powershell
cd C:\Users\nickp\Downloads\ME_CAM-DEV\ME_CAM-DEV
powershell -NoProfile -ExecutionPolicy Bypass -File activate_devices_poshssh.ps1
```

### Option 2: Check Device Status First
```powershell
cd C:\Users\nickp\Downloads\ME_CAM-DEV\ME_CAM-DEV
powershell -NoProfile -ExecutionPolicy Bypass -File check_all_devices.ps1
```

### Option 3: Manual SSH Deployment (if automated fails)
```powershell
# D7 SSH
ssh pi@mecamdev7.local  # password: Kiducdi1234567
cd ~/ME_CAM-DEV
git pull origin main
python3 scripts/generate_config.py --profile device7 --force

# D8 SSH  
ssh pi@mecamdev8.local  # password: Kidcudi12345678
cd ~/ME_CAM-DEV
git pull origin main
python3 scripts/generate_config.py --profile device8 --force
```

## Deployment Verification Commands
Once deployed, verify status on each device:
```bash
# Check git status
git log -1 --oneline

# Check config
cat config/config.json | jq .device_name,.device_id,.framerate

# Check service status
systemctl status mecamera
curl http://localhost:8080/api/health
```

## Notes
- D7 is high-spec (Pi 5) - suitable for network hub/coordinator roles
- D8 is standard spec (Pi Zero 2W) - same baseline as D1-D4, D5, D6
- Network credentials stored in check_all_devices.ps1
- SSH connections use Posh-SSH module
