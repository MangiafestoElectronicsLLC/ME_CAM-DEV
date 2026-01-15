# ME CAMERA v2.1 - QUICK START GUIDE

## 60-Second Setup

```bash
# 1. Flash SD card with Bullseye OS (use Raspberry Pi Imager)
# 2. SSH into Pi
ssh pi@mecamera.local

# 3. Update system and disable legacy camera (REQUIRED!)
sudo apt update && sudo apt upgrade -y
sudo raspi-config  # → Interfacing → Camera → NO, I2C → YES → Reboot

# 4. Clone and setup
cd ~
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Configure
cp config/config_default.json config/config.json
nano config/config.json  # Edit device name if desired

# 6. Install service and start
sudo cp etc/systemd/system/mecamera.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mecamera
sudo systemctl start mecamera

# 7. Access dashboard
# Open: http://mecamera.local:8080
# Login: admin / admin123
```

**Done! Dashboard should show ● ONLINE status**

---

## What Just Happened

✅ System installed and running  
✅ Web dashboard accessible  
✅ API endpoints operational  
✅ Service enabled for auto-boot  
✅ Battery monitoring available  
✅ Motion detection ready  
✅ Multi-device support configured  

---

## Common Tasks

### Check Service Status
```bash
sudo systemctl status mecamera
# Should show: Active (running)
```

### View Live Logs
```bash
sudo journalctl -u mecamera -f
# Press Ctrl+C to exit
```

### Test API
```bash
curl http://127.0.0.1:8080/api/status
# Response: {"active": true, "timestamp": 1234567890.123}
```

### Restart Service
```bash
sudo systemctl restart mecamera
```

### Change Dashboard Password
1. Open web interface: http://mecamera.local:8080
2. Log in with admin/admin123
3. Go to Settings → Profile
4. Change password

### Add Another Camera
```bash
# Set up second Pi (repeat steps 1-6)
# Then edit first Pi's config:
nano config/config.json

# Add to "remote_devices" array:
{
  "device_id": "camera-garage",
  "name": "Garage Camera",
  "hostname": "camera-garage.local",
  "ip_address": "192.168.1.105",
  "port": 8080,
  "enabled": true
}

# Restart first Pi
sudo systemctl restart mecamera
# Navigate to "📡 Devices" page to see both cameras
```

---

## Troubleshooting

### Dashboard shows "OFFLINE"
```bash
# Check if service is running
sudo systemctl status mecamera

# If not running, restart it
sudo systemctl restart mecamera

# Check logs for errors
sudo journalctl -u mecamera -n 50
```

### Can't connect to dashboard
```bash
# Find Pi's IP address
hostname -I

# Try connecting to IP directly
# http://[IP-ADDRESS]:8080

# Or use hostname
# http://mecamera.local:8080
```

### Battery shows 0%
```bash
# Verify battery enabled in config
grep "enable_battery" config/config.json

# Unplug power to reset battery counter
# Then plug back in
```

### Camera shows "Hardware Detection Failed"
```bash
# Check available memory
free -m

# If you see only 50MB free (Pi Zero 2W), this is expected!
# See: PI_ZERO_2W_CAMERA_EXPLANATION.md
```

---

## Important Notes

### Pi Zero 2W Camera Display
❌ **Will NOT display camera** - Only 512MB RAM, camera needs 250MB+ buffer  
✅ **WILL record videos** - Stored to SD card  
✅ **WILL detect motion** - Records on movement  
✅ **WILL show in dashboard** - But camera section displays error message  

**This is correct behavior, not a bug. See PI_ZERO_2W_CAMERA_EXPLANATION.md**

### Legacy Camera Support
⚠️ **MUST disable legacy camera** (step 3 above)  
- If you skip this, camera won't work on Pi 3B+/4/5
- Go to raspi-config → Interfacing → Camera → NO
- Then reboot

### HTTPS Domain Access
To access via https://me_cam.com:
1. Open C:\Windows\System32\drivers\etc\hosts (Windows)
   Or /etc/hosts (Mac/Linux)
2. Add line: [PI-IP] me_cam.com
3. Access: https://me_cam.com:8080
4. Accept self-signed certificate warning (normal)

---

## Features Included in v2.1

### Dashboard
- Real-time status display (updates every 5 seconds)
- Battery monitoring with accurate percentage
- Storage usage tracking
- Recording count display
- Live camera stream (or TEST MODE)

### Multi-Device
- Control multiple cameras from one dashboard
- Each device shows its own status
- Individual device pages with detailed info
- Unified battery and storage monitoring

### Recording & Detection
- Automatic video recording on motion
- Event history with timestamps
- Storage quota management
- Motion sensitivity adjustment

### Security
- User authentication (admin account)
- HTTPS/SSL support (self-signed certs)
- Domain access with local hostnames
- User settings and profile management

### API
- RESTful endpoints for integration
- JSON responses for all data
- Device discovery API
- Motion event queries

---

## File Structure

```
ME_CAM-DEV/
├── web/
│   ├── app.py                 # Flask application
│   ├── templates/             # HTML pages
│   │   └── user_dashboard.html # Main dashboard (FIXED in v2.1)
│   ├── static/                # CSS, JavaScript
│   └── api/                   # REST endpoints
├── src/
│   ├── camera/               # Camera control
│   ├── detection/            # Motion detection
│   └── utils/                # System utilities
├── config/
│   ├── config.json           # Your configuration (YOU EDIT THIS)
│   └── config_default.json   # Template (don't edit)
├── certs/                    # SSL certificates
├── main.py                   # Entry point
├── notes.txt                 # Complete setup guide (UPDATED v2.1)
├── requirements.txt          # Python dependencies
└── [other files...]
```

---

## Documentation

### For Setup
👉 **START HERE:** [notes.txt](notes.txt) - Complete step-by-step installation guide

### For Detailed Info
- [GITHUB_V2.1_RELEASE.md](GITHUB_V2.1_RELEASE.md) - Release notes and changes
- [PI_ZERO_2W_CAMERA_EXPLANATION.md](PI_ZERO_2W_CAMERA_EXPLANATION.md) - Camera limitation explanation
- [CRITICAL_FIXES_JAN15.md](CRITICAL_FIXES_JAN15.md) - Details of fixes applied
- [config/config_default.json](config/config_default.json) - Configuration reference

### For Troubleshooting
See **PART 8: TROUBLESHOOTING** in notes.txt

### For API Integration
See **API Endpoints** section in GITHUB_V2.1_RELEASE.md

---

## Support

- **Questions?** See documentation above
- **Found a bug?** Report on GitHub Issues
- **Want to contribute?** Create a pull request
- **Setup help?** Follow notes.txt step-by-step

---

## Version Information

**Current:** v2.1 (Production Ready)  
**Released:** January 15, 2026  
**Python:** 3.9+  
**OS:** Raspberry Pi OS Bullseye  
**Status:** ✅ Stable, tested, production-ready  

---

## Next Steps

1. ✅ Complete the 60-second setup above
2. ✅ Access dashboard at http://mecamera.local:8080
3. ✅ Verify status shows ● ONLINE
4. ✅ Check logs: `sudo journalctl -u mecamera -f`
5. ✅ Configure device name in settings
6. ✅ (Optional) Set up HTTPS domain access
7. ✅ (Optional) Add second camera for multi-device

---

**ME CAMERA v2.1 - PRODUCTION READY & FULLY DOCUMENTED**

Deploy with confidence. Monitor with certainty.
