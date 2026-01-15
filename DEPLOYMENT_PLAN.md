# 🚀 PI ZERO DEPLOYMENT - QUICK START

## 📊 Project Comparison

| Feature | ME_CAM-main | ME_CAM-DEV (v2.0) |
|---------|------------|------------------|
| **FPS** | 1-2 FPS (libcamera-still) | 15-30 FPS (picamera2) + fallback |
| **Structure** | Flat root directory | Organized src/ subdirectories |
| **Motion Detection** | libcamera-still based | Fast (integrated) + libcamera fallback |
| **Camera Coordinator** | Basic | Advanced (prevents conflicts) |
| **Storage Management** | Manual | Automated cleanup + organization |
| **Performance** | Slower | Optimized for Pi Zero 2 W |
| **Status** | Production stable | Development (v2.0 features) |
| **Recommended For** | Reliability | Features + Speed |

---

## ✅ DEPLOYMENT STEPS FOR PI ZERO

### Step 1: SSH into Pi
```bash
ssh pi@10.2.1.47
# OR
ssh pi@raspberrypi.local
```

### Step 2: Clean Old Installation
```bash
sudo systemctl stop mecamera 2>/dev/null
sudo systemctl disable mecamera 2>/dev/null
sudo rm -f /etc/systemd/system/mecamera.service
sudo systemctl daemon-reload

rm -rf ~/ME_CAM-DEV
rm -rf ~/.cache/pip
sudo apt autoremove -y
sudo apt clean
```

### Step 3: Clone Latest Code
```bash
cd ~
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV
```

### Step 4: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 5: Install Dependencies
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**If NumPy/OpenCV Error:**
```bash
pip install "numpy<2"
pip uninstall opencv-python opencv-python-headless opencv-contrib-python -y
pip install opencv-python-headless
```

**If picamera2 fails (fallback to libcamera-still):**
```bash
# This is OK - code will use fallback automatically
pip install --no-cache-dir picamera2 --break-system-packages 2>&1 | tail -5
```

### Step 6: Run Setup Script
```bash
chmod +x setup.sh
./setup.sh
```

### Step 7: Test Manually (First Time)
```bash
python3 main.py
```
- Open browser: `http://10.2.1.47:8080` or `http://raspberrypi.local:8080`
- Complete first-run wizard
- Check that dashboard loads and camera shows feed

### Step 8: Enable Auto-Boot Service
```bash
sudo cp etc/systemd/system/mecamera.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mecamera
sudo systemctl start mecamera
sudo systemctl status mecamera
```

### Step 9: Verify Service Running
```bash
# Check status
sudo systemctl status mecamera

# View live logs
sudo journalctl -u mecamera.service -f
```

---

## 🐛 TROUBLESHOOTING

### Camera shows "no cameras available"
```bash
libcamera-still --list-cameras
sudo raspi-config  # Disable legacy camera if enabled
sudo reboot
```

### ModuleNotFoundError: No module named 'X'
```bash
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

### SSH keeps disconnecting
```bash
ssh -o TCPKeepAlive=yes pi@10.2.1.47
# OR use screen/tmux for long-running tasks
screen
ssh pi@10.2.1.47
```

### Dashboard not loading
- Check firewall: `sudo ufw allow 8080`
- Verify service: `sudo systemctl status mecamera`
- View errors: `sudo journalctl -u mecamera.service -n 50`

### Motion detection not working
- Ensure settings enable motion detection
- Check disk space: `df -h`
- View motion logs: `tail -f logs/mecam.log | grep MOTION`

---

## 📋 WHICH VERSION TO USE?

**Use ME_CAM-DEV (v2.0) if:**
- ✅ You want faster streaming (15-30 FPS)
- ✅ You want organized code structure
- ✅ You want new emergency features
- ✅ You're testing new features
- ⚠️ You can tolerate occasional issues

**Use ME_CAM-main if:**
- ✅ You need rock-solid stability
- ✅ You're in production (customer deployment)
- ✅ You can accept 1-2 FPS streaming
- ✅ You want proven, tested code

---

## 🔄 SWITCHING BETWEEN VERSIONS

```bash
# Currently deployed version
pwd  # Shows which branch you're on

# Switch to production (main)
git checkout main

# Switch to development (DEV)
git checkout DEV

# Update current branch
git pull origin <branch-name>

# Restart service
sudo systemctl restart mecamera
```

---

## ⚡ QUICK DEPLOY FROM PC

Save this to `QUICK_DEPLOY.ps1` and run from PowerShell:

```powershell
$PI = "pi@10.2.1.47"
ssh $PI "cd ~/ME_CAM-DEV && git pull origin DEV && source venv/bin/activate && pip install -r requirements.txt && sudo systemctl restart mecamera && sudo systemctl status mecamera"
```

Then check logs:
```powershell
ssh $PI "sudo journalctl -u mecamera.service -f"
```

---

**Status:** Ready for deployment ✅
**Last Updated:** January 14, 2026
