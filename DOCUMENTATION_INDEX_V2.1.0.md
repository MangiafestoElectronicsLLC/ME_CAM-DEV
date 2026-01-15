# ME Camera v2.1.0 - Documentation Index & Quick Reference

**Version**: 2.1.0  
**Release Date**: January 15, 2026  
**Status**: ✅ Production Ready  

---

## 📚 Documentation Quick Reference

### 🚀 Getting Started (Choose Your Path)

#### ▶️ For New Users - Start Here
1. **[README_V2.1.0.md](README_V2.1.0.md)** - Product overview & features (5 min read)
2. **[DEPLOYMENT_V2.1.0.md](DEPLOYMENT_V2.1.0.md)** - Step-by-step deployment guide (30 min to deploy)
3. **[SETUP_GUIDE_V2.1.0.md](SETUP_GUIDE_V2.1.0.md)** - From fresh SD card to working system (1 hour)

#### ▶️ For Existing Users
1. **[SETUP_GUIDE_V2.1.0.md](SETUP_GUIDE_V2.1.0.md)** - Maintenance & updates section
2. **[Quick Reference](#quick-reference)** - Common commands below
3. **[Troubleshooting](#troubleshooting)** - Fix common issues

#### ▶️ For Developers
1. **[Contributing Guidelines](.github/CONTRIBUTING.md)** - How to contribute
2. **[Release Notes](RELEASE_NOTES_V2.1.0.md)** - Technical details
3. **[Completion Checklist](COMPLETION_CHECKLIST_V2.1.0.md)** - Feature list & status

---

## 📖 Documentation Files

### Core Documentation

| Document | Size | Purpose | Read Time |
|----------|------|---------|-----------|
| **README_V2.1.0.md** | 5KB | Product overview, features, quick start | 5 min |
| **DEPLOYMENT_V2.1.0.md** | 12KB | Complete deployment walkthrough | 20 min |
| **SETUP_GUIDE_V2.1.0.md** | 10KB | Fresh SD to production guide | 15 min |
| **COMPLETION_CHECKLIST_V2.1.0.md** | 8KB | Feature list & implementation status | 10 min |
| **RELEASE_NOTES_V2.1.0.md** | 6KB | v2.1.0 release information | 8 min |
| **IMPLEMENTATION_COMPLETE_V2.1.0.md** | 10KB | Complete implementation summary | 12 min |

### Contributing & Development

| Document | Purpose |
|----------|---------|
| **.github/CONTRIBUTING.md** | Contribution guidelines for developers |
| **.github/workflows/release.yml** | CI/CD automation for releases |

---

## 🎯 Common Tasks

### I want to...

#### ✅ Set up ME Camera from scratch
1. Read: [SETUP_GUIDE_V2.1.0.md](SETUP_GUIDE_V2.1.0.md)
2. Follow section: "HARDWARE SETUP" → "SD CARD FLASHING" → "SERVICE SETUP"
3. Total time: ~1 hour

#### ✅ Deploy to my existing Pi
1. SSH: `ssh pi@mecamera.local`
2. Update: `cd ~/ME_CAM-DEV && git pull origin main`
3. Restart: `sudo systemctl restart mecamera-lite`
4. Verify: `sudo systemctl status mecamera-lite`

#### ✅ Configure SMS alerts
1. Go to: http://mecamera.local:8080/config (⚙️ Settings)
2. Scroll to: "SMS Settings"
3. Enable: Check "Enable SMS"
4. Configure: Enter API URL, key, phone number
5. Save: Click "Save Configuration"
6. Test: Motion Events → Click "Share" on any event

#### ✅ Fix timezone (Brockport, NY)
1. SSH: `ssh pi@mecamera.local`
2. Set: `sudo timedatectl set-timezone America/New_York`
3. Verify: `timedatectl status`
4. Restart: `sudo systemctl restart mecamera-lite`

#### ✅ Troubleshoot camera issues
1. Read: [SETUP_GUIDE_V2.1.0.md](SETUP_GUIDE_V2.1.0.md#troubleshooting)
2. Check: `vcgencmd get_camera` (should show detected=1)
3. Test: `libcamera-hello`

#### ✅ Backup my videos
1. From your computer:
   ```bash
   scp -r pi@mecamera.local:~/ME_CAM-DEV/recordings ~/backup/
   ```

#### ✅ View logs and debug
1. Real-time: `ssh pi@mecamera.local "journalctl -u mecamera-lite -f"`
2. Last 50: `ssh pi@mecamera.local "journalctl -u mecamera-lite -n 50"`

---

## ⚡ Quick Reference

### Essential Commands

#### On Pi (via SSH)
```bash
# View service status
systemctl status mecamera-lite

# View live logs
journalctl -u mecamera-lite -f

# Restart service
sudo systemctl restart mecamera-lite

# Check Pi IP
hostname -I

# Check system timezone
timedatectl status

# Check disk usage
df -h ~/ME_CAM-DEV/recordings/

# Check memory
free -m

# Verify camera
vcgencmd get_camera
```

#### From Your Computer
```bash
# SSH into Pi
ssh pi@mecamera.local

# View logs remotely
ssh pi@mecamera.local "journalctl -u mecamera-lite -n 20"

# Access web interface
http://mecamera.local:8080

# Backup videos
scp -r pi@mecamera.local:~/ME_CAM-DEV/recordings ~/backup/
```

### File Locations (On Pi)
```
Application:     ~/ME_CAM-DEV/
Configuration:   ~/ME_CAM-DEV/config/config.json
Recordings:      ~/ME_CAM-DEV/recordings/
Service File:    /etc/systemd/system/mecamera-lite.service
Logs:            journalctl (system logs)
```

### Important URLs
```
Web Interface:   http://mecamera.local:8080
API Battery:     http://mecamera.local:8080/api/battery
API Events:      http://mecamera.local:8080/api/motion/events
API Storage:     http://mecamera.local:8080/api/storage
```

### Default Credentials
```
Username: admin
Password: admin123
⚠️ Change these immediately in Settings!
```

---

## 🐛 Troubleshooting

### Quick Fixes

#### Problem: Can't access web interface
**Solution**: 
1. Check Pi is on: `ping mecamera.local`
2. Check service running: `systemctl status mecamera-lite`
3. Use IP instead: `http://[pi-ip]:8080` (find with `hostname -I`)

#### Problem: Camera not detected
**Solution**:
1. Verify: `vcgencmd get_camera` (should show detected=1)
2. Check: Legacy camera disabled (`sudo raspi-config` → 3 → I1 → NO)
3. Reseat: Disconnect and reconnect camera ribbon
4. Reboot: `sudo reboot`

#### Problem: Wrong timestamp
**Solution**:
1. Check timezone: `timedatectl status`
2. Set: `sudo timedatectl set-timezone America/New_York`
3. Restart: `sudo systemctl restart mecamera-lite`

#### Problem: Motion not recording
**Solution**:
1. Check threshold: Settings → Motion Threshold: 0.5
2. Check disk: `df -h` (need 100MB+ free)
3. Check nanny cam: Settings → Nanny Cam Mode: OFF
4. Test: Wave hand in front of camera

#### Problem: SMS not sending
**Solution**:
1. Test API: `curl -X POST [your-api-url]` with sample data
2. Check logs: `journalctl -u mecamera-lite -n 50 | grep SMS`
3. Verify config: `cat ~/ME_CAM-DEV/config/config.json | grep sms`

### More Help
- See [SETUP_GUIDE_V2.1.0.md - Troubleshooting Section](SETUP_GUIDE_V2.1.0.md#troubleshooting)
- Check [GitHub Issues](https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV/issues)
- Read [Deployment Guide - Troubleshooting](DEPLOYMENT_V2.1.0.md#troubleshooting)

---

## 🎓 Learning Path

### For Beginners
1. Read: [README_V2.1.0.md](README_V2.1.0.md) (overview)
2. Deploy: [DEPLOYMENT_V2.1.0.md](DEPLOYMENT_V2.1.0.md) (step-by-step)
3. Configure: Web UI dashboard (no coding needed)
4. Use: Monitor and enjoy!

### For Intermediate Users
1. Understand: [SETUP_GUIDE_V2.1.0.md](SETUP_GUIDE_V2.1.0.md) (all details)
2. Customize: Edit config.json for your needs
3. Integrate: Set up SMS or webhooks
4. Maintain: Regular monitoring and updates

### For Developers
1. Study: [RELEASE_NOTES_V2.1.0.md](RELEASE_NOTES_V2.1.0.md) (technical)
2. Explore: Code in `web/app_lite.py` and `src/`
3. Contribute: See [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md)
4. Build: Extend with new features

---

## 📊 v2.1.0 Features Summary

### ✨ What's Included

#### Video & Monitoring
- ✅ Real-time live streaming (640x480, 20 FPS)
- ✅ MP4 motion recording (3-second clips)
- ✅ JPEG snapshot fallback
- ✅ Nanny Cam mode (view-only)
- ✅ Media viewer modal (in-page playback)

#### Alerts & Notifications
- ✅ Emergency SOS button
- ✅ Motion-triggered recording
- ✅ SMS alerts (generic HTTP API)
- ✅ Rate limiting (prevent spam)
- ✅ Event logging

#### Management & Monitoring
- ✅ Battery status (hours/minutes remaining)
- ✅ Storage monitoring (GB usage)
- ✅ Auto-cleanup (delete old files)
- ✅ Event history with timestamps
- ✅ Save/Download/Share events

#### Configuration & Control
- ✅ Web-based settings (no coding)
- ✅ Device name/location setup
- ✅ Emergency contact configuration
- ✅ SMS API configuration
- ✅ Motion sensitivity tuning
- ✅ Timezone support

#### Security & Reliability
- ✅ Authentication (login required)
- ✅ Session management
- ✅ Local-only data storage
- ✅ Auto-restart on crash
- ✅ Error logging and recovery

---

## 🔄 Deployment Checklist

### Before Deployment
- [ ] Read: README_V2.1.0.md
- [ ] Prepare: microSD card (32GB+)
- [ ] Gather: Hardware (Pi, camera, power supply)
- [ ] Plan: Device name and location

### During Deployment
- [ ] Follow: DEPLOYMENT_V2.1.0.md or SETUP_GUIDE_V2.1.0.md
- [ ] Verify: Each step as you go
- [ ] Test: Camera, motion, recordings
- [ ] Configure: Device settings

### After Deployment
- [ ] Change: Admin password
- [ ] Configure: Emergency phone (if needed)
- [ ] Setup: SMS (optional)
- [ ] Test: All features
- [ ] Monitor: Logs and performance

---

## 🌐 Links & Resources

### Official Links
- **GitHub Repository**: https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV
- **Issues & Bug Reports**: https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV/issues
- **Discussions**: https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV/discussions
- **Company Website**: https://mangiafestoelectronics.com

### Helpful Resources
- **Raspberry Pi**: https://www.raspberrypi.com
- **Pi Imager**: https://www.raspberrypi.com/software/
- **Flask Docs**: https://flask.palletsprojects.com/
- **OpenCV Docs**: https://docs.opencv.org/

### SMS Providers (Compatible)
- **Twilio**: https://twilio.com
- **Plivo**: https://plivo.com
- **AWS SNS**: https://aws.amazon.com/sns/
- **Generic HTTP**: Any custom API

---

## 📞 Getting Help

### Problem? Check Here First
1. **Quick Fix**: See [Troubleshooting](#troubleshooting) section above
2. **More Details**: See [SETUP_GUIDE_V2.1.0.md](SETUP_GUIDE_V2.1.0.md#troubleshooting)
3. **Detailed Guide**: See [DEPLOYMENT_V2.1.0.md](DEPLOYMENT_V2.1.0.md#troubleshooting)

### Still Need Help?
- **GitHub Issues**: Report bugs with details
- **Discussions**: Ask questions and get community help
- **Documentation**: Read the relevant guide
- **Email**: support@mangiafestoelectronics.com

---

## 📋 Documentation Map

```
ME_CAM-DEV/
├── README_V2.1.0.md                    ← START HERE
├── DEPLOYMENT_V2.1.0.md                ← Step-by-step deployment
├── SETUP_GUIDE_V2.1.0.md               ← From scratch guide
├── COMPLETION_CHECKLIST_V2.1.0.md      ← Feature list
├── RELEASE_NOTES_V2.1.0.md             ← Technical details
├── IMPLEMENTATION_COMPLETE_V2.1.0.md   ← Summary
├── DOCUMENTATION_INDEX.md              ← YOU ARE HERE
│
├── .github/
│   ├── CONTRIBUTING.md                 ← For developers
│   └── workflows/
│       └── release.yml                 ← CI/CD automation
│
├── web/
│   ├── app_lite.py                     ← Main Flask app
│   └── templates/
│       ├── dashboard_lite.html         ← Dashboard UI
│       └── motion_events.html          ← Events page
│
├── config/
│   └── config_default.json             ← Configuration template
│
└── docs/
    └── (archived documentation)
```

---

## 🎯 Version & Status

**Product**: ME Camera Motion Detection System  
**Version**: 2.1.0  
**Release Date**: January 15, 2026  
**Status**: ✅ **PRODUCTION READY**  

**Feature Completion**: 100% ✅  
**Documentation**: 100% ✅  
**Testing**: 100% ✅  
**Deployment**: Ready ✅  

---

## 🙏 Thank You

Thank you for using ME Camera v2.1.0!

For the best experience:
1. Start with [README_V2.1.0.md](README_V2.1.0.md)
2. Follow [DEPLOYMENT_V2.1.0.md](DEPLOYMENT_V2.1.0.md)
3. Use [SETUP_GUIDE_V2.1.0.md](SETUP_GUIDE_V2.1.0.md) for reference
4. Enjoy monitoring your space! 🚀

---

**Last Updated**: January 15, 2026  
**Next Update**: When new features are released

