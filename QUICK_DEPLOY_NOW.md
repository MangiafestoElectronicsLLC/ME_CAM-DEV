# ME_CAM-DEV - Get Your Pi Zero 2W Running

## Quick Deploy (Current Project)

Your ME_CAM-DEV has a complete working system with:
- Fast streaming (15-30 FPS with picamera2)
- Motion detection with AI person recognition
- Emergency alerts (SMS, email)
- Storage management
- Web dashboard

### Deploy Now

```bash
cd c:\Users\nickp\Downloads\ME_CAM-DEV\ME_CAM-DEV
bash DEPLOY_PI.sh 10.2.1.47 pi
```

**Time:** 10-15 minutes
**Result:** Dashboard at http://10.2.1.47:8080

### What It Does

1. ✓ Tests connection to Pi
2. ✓ Stops existing service
3. ✓ Backs up old installation
4. ✓ Transfers all your code
5. ✓ Sets up Python virtual environment
6. ✓ Installs dependencies (handles NumPy compatibility)
7. ✓ Runs setup script
8. ✓ Installs systemd service

### After Deployment

**Access Dashboard:**
```
http://10.2.1.47:8080
PIN: 1234 (change in dashboard)
```

**Check Service Status:**
```bash
ssh pi@10.2.1.47 'sudo systemctl status mecamera'
```

**View Live Logs:**
```bash
ssh pi@10.2.1.47 'tail -f ~/ME_CAM-DEV/logs/mecam.log'
```

**Restart Service:**
```bash
ssh pi@10.2.1.47 'sudo systemctl restart mecamera'
```

### Your Current Features

From your [web/app.py](web/app.py):
- Flask web server (1354 lines)
- Fast camera streaming (picamera2)
- Motion detection service
- Battery monitoring
- User authentication
- Storage management
- Emergency alerts
- Configuration system

From your [main.py](main.py):
- Service orchestration
- Logging setup (loguru)
- Motion service integration

### Troubleshooting

**If camera not working:**
```bash
ssh pi@10.2.1.47
vcgencmd get_camera
# Should show: supported=1 detected=1
```

**If dependencies fail:**
```bash
ssh pi@10.2.1.47
cd ~/ME_CAM-DEV
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**If port 8080 in use:**
```bash
# Edit main.py line ~30:
app.run(host="0.0.0.0", port=8081, debug=False)
```

### Your Project Structure

```
ME_CAM-DEV/
├── main.py                    # Entry point
├── web/
│   └── app.py                 # Flask app (1354 lines)
├── src/
│   ├── camera/                # Camera streaming
│   ├── core/                  # Config, auth, monitoring
│   ├── detection/             # Motion detection
│   ├── utils/                 # Utilities
│   └── web/                   # Web components
├── requirements.txt           # Dependencies
├── deploy_pi_zero.sh         # Original deploy script
├── DEPLOY_PI.sh              # New simplified deploy
└── setup.sh                   # Setup script
```

### Next Steps

1. **Deploy:** Run `bash DEPLOY_PI.sh 10.2.1.47 pi`
2. **Test:** Open http://10.2.1.47:8080
3. **Configure:** Change PIN, adjust motion settings
4. **Monitor:** Watch logs for any issues

### Backup/Recovery

Your old installation is backed up at:
```
~/ME_CAM-DEV.backup.[timestamp]
```

To restore:
```bash
ssh pi@10.2.1.47
sudo systemctl stop mecamera
rm -rf ~/ME_CAM-DEV
mv ~/ME_CAM-DEV.backup.[timestamp] ~/ME_CAM-DEV
sudo systemctl start mecamera
```

---

**Ready to Deploy?** Run the command above and your Pi will be running in ~15 minutes!
