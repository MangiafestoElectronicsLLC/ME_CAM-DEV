# 🚀 Deployment Guide - Transfer v2.1.2 to Pi Zero

This guide shows you how to transfer the v2.1.2 updates to your Raspberry Pi Zero for testing before committing to GitHub.

---

## 🎯 Quick Start (Recommended)

### Windows Users:
```powershell
# From ME_CAM-DEV directory
.\deploy_v2.1.2_updates.ps1
```

### Linux/Mac Users:
```bash
# From ME_CAM-DEV directory
chmod +x deploy_v2.1.2_updates.sh
./deploy_v2.1.2_updates.sh
```

The script will:
1. ✅ Create backup on Pi
2. ✅ Transfer updated files
3. ✅ Verify transfer
4. ✅ Restart service
5. ✅ Show testing instructions

---

## 📋 Prerequisites

### 1. SSH Access to Pi
Make sure you can SSH to your Pi:
```bash
ssh pi@192.168.1.100
# (replace with your Pi's IP)
```

### 2. OpenSSH Installed (Windows)
**Windows users need OpenSSH client:**
- Go to: Settings → Apps → Optional Features
- Click "Add a feature"
- Search for "OpenSSH Client"
- Install it
- Restart PowerShell

### 3. Know Your Pi's IP Address
Find your Pi's IP:
```bash
# On Pi:
hostname -I

# Or from router's connected devices list
```

---

## 🛠️ Manual Deployment (Alternative)

If you prefer manual transfer:

### Step 1: Create Backup on Pi
```bash
ssh pi@YOUR_PI_IP

# Create backup directory
BACKUP_DIR=~/ME_CAM-DEV/backup_v2.1.1_$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup files
cd ~/ME_CAM-DEV
cp src/core/battery_monitor.py $BACKUP_DIR/
cp web/app_lite.py $BACKUP_DIR/
cp web/templates/dashboard_lite.html $BACKUP_DIR/
cp web/templates/motion_events.html $BACKUP_DIR/

echo "Backup created: $BACKUP_DIR"
```

### Step 2: Transfer Files from Windows
```powershell
# From ME_CAM-DEV directory on Windows

# Transfer Python files
scp src\core\battery_monitor.py pi@YOUR_PI_IP:~/ME_CAM-DEV/src/core/
scp web\app_lite.py pi@YOUR_PI_IP:~/ME_CAM-DEV/web/

# Transfer HTML templates
scp web\templates\dashboard_lite.html pi@YOUR_PI_IP:~/ME_CAM-DEV/web/templates/
scp web\templates\motion_events.html pi@YOUR_PI_IP:~/ME_CAM-DEV/web/templates/

# Transfer documentation
scp FIXES_AND_IMPROVEMENTS_SUMMARY.md pi@YOUR_PI_IP:~/ME_CAM-DEV/
scp HTTPS_SETUP_COMPLETE_GUIDE.md pi@YOUR_PI_IP:~/ME_CAM-DEV/
scp SMS_NOTIFICATIONS_SETUP_GUIDE.md pi@YOUR_PI_IP:~/ME_CAM-DEV/
scp QUICK_REFERENCE_CARD.md pi@YOUR_PI_IP:~/ME_CAM-DEV/
scp TESTING_AND_DEPLOYMENT_GUIDE.md pi@YOUR_PI_IP:~/ME_CAM-DEV/
```

### Step 3: Restart Service on Pi
```bash
ssh pi@YOUR_PI_IP

# Stop service
sudo systemctl stop mecam
# Or if no service:
pkill -f main_lite.py

# Start service
sudo systemctl start mecam
# Or if no service:
cd ~/ME_CAM-DEV
nohup python3 main_lite.py > logs/startup.log 2>&1 &

# Check status
systemctl status mecam
# Or:
tail -f ~/ME_CAM-DEV/logs/mecam_lite.log
```

---

## ✅ Verify Deployment

### 1. Check Service is Running
```bash
ssh pi@YOUR_PI_IP

# Check if running
systemctl status mecam
# Or:
ps aux | grep main_lite
```

### 2. Check Web Interface
```
Open browser: https://YOUR_PI_IP:8080
```

You should see:
- ✅ "🔒 Pi Zero Version v2.1-LITE" in header
- ✅ Green security badge
- ✅ Battery percentage (not fixed at 100%)
- ✅ "Security: 🔒 SECURE" in System Info

### 3. Check Motion Events
```
Go to: https://YOUR_PI_IP:8080/motion-events
```

- ✅ Latest time shows correct time
- ✅ Video button plays inline
- ✅ Statistics accurate

### 4. Check Logs
```bash
ssh pi@YOUR_PI_IP
tail -50 ~/ME_CAM-DEV/logs/mecam_lite.log
```

Look for:
```
[HTTPS] Running with SSL/TLS (https://me_cam.com:8080)
✓ All systems operational
```

---

## 🧪 Testing Checklist

After deployment, test these features:

### Battery Monitoring:
- [ ] Dashboard shows battery percentage
- [ ] Runtime shows hours and minutes
- [ ] Battery changes over time (not stuck at 100%)

Test:
```bash
ssh pi@YOUR_PI_IP
python3 << EOF
from src.core import BatteryMonitor
battery = BatteryMonitor(enabled=True)
status = battery.get_status()
print(f"Battery: {status['percent']}%")
print(f"Runtime: {status['runtime_hours']}h {status['runtime_minutes']}m")
EOF
```

### Video Playback:
- [ ] Trigger motion (wave at camera)
- [ ] Go to motion events page
- [ ] Click "Video" button
- [ ] Video plays in browser modal

### SMS Notifications:
- [ ] Configure SMS in settings
- [ ] Trigger motion
- [ ] Receive text within 30 seconds

### UI/UX:
- [ ] Header shows "Pi Zero Version"
- [ ] Green 🔒 badges visible
- [ ] Footer shows "SECURE CONNECTION"
- [ ] No "LITE MODE" warnings

### Motion Statistics:
- [ ] Latest time matches last event
- [ ] Today count accurate
- [ ] Total count correct

---

## 🔄 Rollback (If Issues)

If something breaks, restore from backup:

```bash
ssh pi@YOUR_PI_IP

# List backups
ls -lt ~/ME_CAM-DEV/backup_v2.1.1_*

# Find most recent backup
BACKUP_DIR=$(ls -td ~/ME_CAM-DEV/backup_v2.1.1_* | head -1)
echo "Restoring from: $BACKUP_DIR"

# Restore files
cd ~/ME_CAM-DEV
cp $BACKUP_DIR/battery_monitor.py src/core/
cp $BACKUP_DIR/app_lite.py web/
cp $BACKUP_DIR/dashboard_lite.html web/templates/
cp $BACKUP_DIR/motion_events.html web/templates/

# Restart service
sudo systemctl restart mecam
# Or:
pkill -f main_lite.py
cd ~/ME_CAM-DEV
python3 main_lite.py &

echo "Rollback complete"
```

---

## 📝 What Gets Transferred

### Core Files (4 files):
1. **`src/core/battery_monitor.py`**
   - Enhanced battery calculation
   - Runtime estimation
   - Uptime-based percentage

2. **`web/app_lite.py`**
   - SMS notification integration
   - Motion statistics API
   - Accurate timestamp handling

3. **`web/templates/dashboard_lite.html`**
   - UI branding (Pi Zero Version)
   - Security indicators
   - Professional styling

4. **`web/templates/motion_events.html`**
   - Inline video playback
   - Latest time fix
   - Enhanced statistics

### Documentation (5 files):
- `FIXES_AND_IMPROVEMENTS_SUMMARY.md`
- `HTTPS_SETUP_COMPLETE_GUIDE.md`
- `SMS_NOTIFICATIONS_SETUP_GUIDE.md`
- `QUICK_REFERENCE_CARD.md`
- `TESTING_AND_DEPLOYMENT_GUIDE.md`

---

## 🐛 Troubleshooting

### Connection Refused
```bash
# Check Pi is on network
ping YOUR_PI_IP

# Check SSH is enabled
# On Pi: sudo raspi-config → Interface Options → SSH → Enable
```

### Permission Denied
```bash
# Add SSH key (avoid password prompts)
ssh-copy-id pi@YOUR_PI_IP

# Or use password when prompted
```

### Service Won't Start
```bash
ssh pi@YOUR_PI_IP

# Check for errors
tail -100 ~/ME_CAM-DEV/logs/mecam_lite.log

# Try manual start
cd ~/ME_CAM-DEV
python3 main_lite.py

# Look for error messages
```

### Files Not Found
```bash
# Verify files exist on Pi
ssh pi@YOUR_PI_IP
ls -lh ~/ME_CAM-DEV/src/core/battery_monitor.py
ls -lh ~/ME_CAM-DEV/web/app_lite.py
ls -lh ~/ME_CAM-DEV/web/templates/*.html
```

---

## 📊 Deployment Status Checklist

Use this to track your deployment:

```
Pre-Deployment:
[ ] SSH access to Pi verified
[ ] Pi IP address known: __________
[ ] OpenSSH installed (Windows)
[ ] Files backed up locally

Deployment:
[ ] Backup created on Pi
[ ] battery_monitor.py transferred
[ ] app_lite.py transferred
[ ] dashboard_lite.html transferred
[ ] motion_events.html transferred
[ ] Documentation transferred
[ ] Files verified on Pi
[ ] Service restarted

Post-Deployment:
[ ] Web interface accessible
[ ] Battery shows accurate %
[ ] Videos play inline
[ ] UI shows "Pi Zero Version"
[ ] SMS configured (optional)
[ ] Motion statistics accurate
[ ] Logs show no errors

Testing:
[ ] Battery monitoring tested
[ ] Video playback tested
[ ] SMS notifications tested (optional)
[ ] UI/UX verified
[ ] Motion time accuracy verified
[ ] All features working

Status: [ ] SUCCESS [ ] ISSUES

Notes:
_________________________________
_________________________________
```

---

## 🎉 After Successful Testing

Once you've verified everything works:

### 1. Document Test Results
```bash
# On Windows
cd ME_CAM-DEV
echo "Tested on: $(Get-Date)" >> TEST_RESULTS.txt
echo "Pi IP: YOUR_PI_IP" >> TEST_RESULTS.txt
echo "Status: All features working ✓" >> TEST_RESULTS.txt
```

### 2. Prepare for GitHub
```bash
# Check what changed
git status

# Review changes
git diff src/core/battery_monitor.py
git diff web/app_lite.py
# etc.

# Stage changes
git add src/core/battery_monitor.py
git add web/app_lite.py
git add web/templates/dashboard_lite.html
git add web/templates/motion_events.html
git add *.md

# Commit
git commit -m "v2.1.2: Enhanced battery monitoring, SMS alerts, video playback, UI improvements"
```

### 3. Create Release Tag
```bash
git tag -a v2.1.2 -m "Release v2.1.2 - Battery monitoring, SMS, video playback fixes"
git push origin main
git push origin v2.1.2
```

---

## 📞 Support

If deployment fails:

1. **Check logs:**
   ```bash
   ssh pi@YOUR_PI_IP
   tail -100 ~/ME_CAM-DEV/logs/mecam_lite.log
   ```

2. **Rollback (see section above)**

3. **Re-run deployment script**

4. **Manual transfer (see alternative method)**

---

## ✨ Summary

**Automated Deployment (Recommended):**
```powershell
# Windows
.\deploy_v2.1.2_updates.ps1

# Linux/Mac
./deploy_v2.1.2_updates.sh
```

**Manual Deployment:**
```bash
# 1. Backup on Pi
# 2. SCP files from Windows
# 3. Restart service
# 4. Test
```

**Testing:**
```
https://YOUR_PI_IP:8080
→ Verify all 6 fixes working
```

**Commit to GitHub:**
```bash
git add .
git commit -m "v2.1.2 updates"
git push
```

---

**Deployment ready! Transfer the updates and test before GitHub commit. 🚀**
