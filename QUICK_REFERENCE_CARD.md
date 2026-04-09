# 🎯 ME_CAM Quick Reference Card
## Your System at a Glance - v2.1 Pi Zero Version

---

## 🔗 Access URLs

### Main Dashboard:
```
🔒 https://me_cam.com:8080
```

### Direct IP Access:
```
🔒 https://[YOUR-PI-IP]:8080
Example: https://192.168.1.100:8080
```

### Pages:
- **Dashboard:** `/` (home)
- **Motion Events:** `/motion-events`
- **Configuration:** `/config`
- **Logout:** `/logout`

---

## 🎛️ System Status

### Current Features:
✅ **HD Camera Streaming** - 640x480 @ 20 FPS  
✅ **Motion Detection** - Auto-recording with video  
✅ **SMS Alerts** - Phone notifications on motion  
✅ **HTTPS Encryption** - 256-bit SSL/TLS secure  
✅ **Battery Monitoring** - Runtime estimation  
✅ **Video Playback** - In-browser viewing  
✅ **Nanny Cam Mode** - Watch without recording  

---

## 📊 Dashboard Info

### System Info:
```
Security: 🔒 SECURE (HTTPS Encrypted)
Pi Model: Raspberry Pi Zero 2W
RAM: 512MB
Version: 2.1-LITE
```

### Battery Display:
```
Charge Level: XX%
Runtime (10Ah): XXh XXm
```

### Storage:
```
Used: X.X GB / Total: XX GB
Recordings: XXX files
```

---

## 🔧 Quick Configuration

### Enable SMS Notifications:
1. Go to: `https://me_cam.com:8080/config`
2. Scroll to **SMS Notifications**
3. Check ✅ **SMS Notifications Enabled**
4. Enter Twilio credentials:
   ```
   Account SID: ACxxxxx
   Auth Token: xxxxx
   Phone From: +1234567890
   Phone To: +1987654321
   ```
5. Check ✅ **Send motion alerts to emergency contact**
6. Click **Save Configuration**

### Adjust Motion Sensitivity:
```
Low (0.3)    → Many alerts
Medium (0.5) → Balanced (default)
High (0.8)   → Only strong motion
```

### Enable Nanny Cam Mode:
- Toggle switch on dashboard
- **ON** = Watch only (no recording)
- **OFF** = Normal mode (records motion)

---

## 📱 Motion Events

### View Events:
```
https://me_cam.com:8080/motion-events
```

### Features:
- **Video Button:** Play inline in browser
- **Save Button:** Download event as JSON
- **Delete Button:** Remove individual event
- **Clear All:** Remove all events

### Statistics Shown:
- **Total Events:** All recorded events
- **Today:** Events since midnight
- **Latest Event:** Time of last motion (accurate!)

---

## 🚨 SMS Alerts

### Alert Format:
```
🚨 ME Camera: Motion detected at [Location] - HH:MM:SS AM/PM
```

### SMS Providers Supported:
- **Twilio** (Recommended) - Easy setup, $0.0075/SMS
- **AWS SNS** - AWS users, $0.00645/SMS
- **Plivo** - International, $0.0055/SMS
- **Custom HTTP** - DIY solutions

### Rate Limiting:
```
Default: Max 1 SMS per 5 minutes
Adjustable in config (1-60 minutes)
```

---

## 🔐 Security Status

### Your System IS Secure:
✅ **256-bit SSL/TLS encryption**  
✅ **HTTPS on all pages**  
✅ **Password authentication**  
✅ **Secure session management**  
✅ **Encrypted video streaming**  

### Browser "Not Secure" Warning:
- **Misleading!** Connection IS encrypted
- Warning is about self-signed certificate only
- All data is secure and encrypted
- See `HTTPS_SETUP_COMPLETE_GUIDE.md` for details

---

## 🎥 Camera Features

### Live Streaming:
- **Resolution:** 640x480 (optimized for Pi Zero)
- **Frame Rate:** ~20 FPS
- **Format:** MJPEG over HTTPS
- **Latency:** <1 second

### Motion Detection:
- **Algorithm:** Frame difference analysis
- **Threshold:** Configurable (0-1.0)
- **Cooldown:** 100 frames (~5 seconds)
- **Recording:** 3-second clips or snapshots

### Video Storage:
- **Location:** `recordings/` folder
- **Format:** MP4 (H.264) or JPEG
- **Naming:** `motion_YYYYMMDD_HHMMSS.mp4`
- **Auto-cleanup:** Configurable (7 days default)

---

## 📁 Important Files

### Configuration:
```
hub_config.json          - Main config file
logs/mecam_lite.log      - System logs
logs/motion_events.json  - Motion history
logs/sms_sent.json       - SMS history
```

### Certificates:
```
certs/certificate.pem    - SSL certificate
certs/private_key.pem    - SSL private key
```

### Recordings:
```
recordings/              - Motion videos/images
```

---

## 🖥️ Command Line Reference

### Start Service:
```bash
cd ~/ME_CAM-DEV
python3 main_lite.py
```

### Check Logs:
```bash
tail -f logs/mecam_lite.log
tail -f logs/mecam_lite.log | grep MOTION
tail -f logs/mecam_lite.log | grep SMS
```

### Test Battery:
```bash
python3 -c "from src.core import BatteryMonitor; print(BatteryMonitor(True).get_status())"
```

### Test SMS:
```bash
python3 -c "from src.core import get_sms_notifier; get_sms_notifier().send_sms('+15551234567', 'Test')"
```

### View Recordings:
```bash
ls -lh recordings/
du -sh recordings/
```

### Clear Old Recordings:
```bash
find recordings/ -name "*.mp4" -mtime +7 -delete
find recordings/ -name "*.jpg" -mtime +7 -delete
```

---

## 🔄 System Maintenance

### Restart Service:
```bash
sudo systemctl restart mecam
# or
pkill -f main_lite.py && python3 main_lite.py &
```

### View System Status:
```bash
systemctl status mecam
```

### Update Code:
```bash
cd ~/ME_CAM-DEV
git pull
sudo systemctl restart mecam
```

### Backup Configuration:
```bash
cp hub_config.json hub_config.json.backup
tar -czf mecam_backup_$(date +%Y%m%d).tar.gz hub_config.json logs/ recordings/
```

---

## 💰 SMS Cost Estimates

### Twilio Pricing:
```
10 alerts/day  → 300/month = $2.25/month
30 alerts/day  → 900/month = $6.75/month
100 alerts/day → 3,000/month = $22.50/month
```

### Cost Control:
- Adjust `rate_limit_minutes` in config
- Increase motion threshold
- Enable only for specific hours
- Use nanny cam mode when not needed

---

## 📱 Mobile Access

### iPhone/Android:
1. Open browser
2. Go to `https://[PI-IP]:8080`
3. Tap **Advanced** → **Proceed**
4. Bookmark for easy access

### Add to Home Screen:
- **iOS:** Share → Add to Home Screen
- **Android:** Menu → Add to Home screen

---

## 🆘 Quick Troubleshooting

### Camera Not Working:
```bash
# Check camera
vcgencmd get_camera

# Restart camera
sudo systemctl restart mecam
```

### SMS Not Sending:
```bash
# Check config
cat hub_config.json | grep sms_enabled

# Check logs
tail -f logs/mecam_lite.log | grep SMS
```

### Can't Access Web Interface:
```bash
# Check if running
ps aux | grep main_lite

# Check port
sudo netstat -tulpn | grep 8080

# Restart service
sudo systemctl restart mecam
```

### Battery Shows 100% Always:
```bash
# Check uptime
uptime

# Battery estimate is based on uptime
# Will decrease as system runs longer
```

---

## 📚 Full Documentation

### Detailed Guides:
- **`FIXES_AND_IMPROVEMENTS_SUMMARY.md`** - Complete changelog
- **`HTTPS_SETUP_COMPLETE_GUIDE.md`** - SSL/TLS security
- **`SMS_NOTIFICATIONS_SETUP_GUIDE.md`** - SMS configuration
- **`README.md`** - General system info
- **`DEPLOYMENT_GUIDE.md`** - Installation guide

---

## 🎯 Default Login

```
Username: admin
Password: admin123
```

**⚠️ Change default password immediately!**

```bash
python3 -c "from src.core.user_auth import change_password; change_password('admin', 'NEW_PASSWORD')"
```

---

## 🌐 Network Configuration

### Local Access Only (Default):
```
Access: https://me_cam.com:8080 (local network)
Firewall: No external ports open
Security: Maximum (no internet exposure)
```

### Internet Access (Advanced):
1. Port forward 8080 on router
2. Get Let's Encrypt certificate
3. Use dynamic DNS (DuckDNS, No-IP)
4. Configure firewall rules

---

## 💡 Tips & Tricks

### Save Battery:
- Reduce motion sensitivity
- Use nanny cam mode when home
- Disable SMS when not needed

### Reduce False Alarms:
- Increase motion threshold (0.7-0.8)
- Adjust camera angle
- Cover LED lights in camera view

### Improve Performance:
- Clear old recordings regularly
- Use wired network instead of WiFi
- Reduce camera resolution if needed

### Better Security:
- Change default password
- Use strong WiFi password
- Keep system updated
- Enable auto-cleanup of recordings

---

## 📞 Quick Support Checklist

Before asking for help:
1. ✅ Check logs: `tail -f logs/mecam_lite.log`
2. ✅ Verify configuration: `cat hub_config.json`
3. ✅ Test connectivity: `ping me_cam.com`
4. ✅ Check service status: `systemctl status mecam`
5. ✅ Review documentation (see above)

---

## 🎉 System Highlights

### What Makes This Special:
- 🔒 **Fully Encrypted** - Bank-level 256-bit SSL
- 📱 **SMS Alerts** - Instant phone notifications
- 🎥 **HD Streaming** - Real-time camera feed
- 💾 **Auto Recording** - Motion-triggered video
- 🔋 **Battery Monitor** - Runtime estimation
- 📊 **Event Tracking** - Complete motion history
- 🌐 **Web Interface** - Access from anywhere
- 🚀 **Pi Zero Optimized** - Runs on 512MB RAM

---

**Access your camera now:** `https://me_cam.com:8080` 🚀

---

**Quick Ref Version:** 2.1-LITE  
**Last Updated:** January 20, 2026  
**Status:** ✅ All Systems Operational
