# 🎯 GET YOUR PI ZERO RUNNING - QUICK GUIDE

## 📊 Project Comparison Summary

| Aspect | ME_CAM-main | ME_CAM-DEV (v2.0) |
|--------|-----------|-------------------|
| **Streaming Speed** | 1-2 FPS | 15-30 FPS (with fallback) |
| **Code Structure** | Simple/Flat | Organized (src/ subdirs) |
| **Features** | Core only | All v2.0 features |
| **Status** | Production stable | Development/Testing |
| **Recommendation** | Proven & tested | More features & speed |

**→ Use ME_CAM-DEV (v2.0) for your Pi Zero** ✅

---

## 🚀 DEPLOYMENT (Choose One Method)

### **Option A: Automated PowerShell Script (Windows)**

Open PowerShell in the repo folder and run:
```powershell
.\deploy_pi_zero.ps1 -IP "10.2.1.47" -Username "pi"
```

This will automatically:
- Clean old installation
- Clone latest code
- Install all dependencies
- Run setup script
- Enable auto-boot
- Start the service

**Wait 10-15 minutes for dependencies to install.**

### **Option B: Bash Script (SSH from PC or Pi)**

```bash
chmod +x deploy_pi_zero.sh
./deploy_pi_zero.sh pi 10.2.1.47
```

### **Option C: Manual Steps (Most Control)**

```bash
# 1. SSH to Pi
ssh pi@10.2.1.47

# 2. Clean old install
sudo systemctl stop mecamera 2>/dev/null
sudo systemctl disable mecamera 2>/dev/null
sudo rm -f /etc/systemd/system/mecamera.service
sudo systemctl daemon-reload
rm -rf ~/ME_CAM-DEV
sudo apt autoremove -y

# 3. Clone & setup
cd ~
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV.git
cd ME_CAM-DEV
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Handle NumPy/OpenCV issue (if needed)
pip install "numpy<2"
pip uninstall opencv-python opencv-python-headless opencv-contrib-python -y
pip install opencv-python-headless

# 5. Setup
chmod +x setup.sh
./setup.sh

# 6. Enable auto-boot
sudo cp etc/systemd/system/mecamera.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mecamera
sudo systemctl start mecamera

# 7. Verify
sudo systemctl status mecamera
```

---

## ✅ Verify Deployment

After deployment, SSH to Pi and run:

```bash
ssh pi@10.2.1.47

# Check service
sudo systemctl status mecamera

# View logs
sudo journalctl -u mecamera.service -f

# Get IP address
hostname -I
```

---

## 🌐 Access Dashboard

Open browser to:
- **`http://raspberrypi.local:8080`** (recommended)
- **`http://10.2.1.47:8080`** (if hostname doesn't resolve)

You should see:
- ✅ Live camera feed
- ✅ System status
- ✅ Storage info
- ✅ Motion detection status

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| **ModuleNotFoundError** | `source venv/bin/activate && pip install -r requirements.txt` |
| **Camera shows "no cameras"** | `libcamera-still --list-cameras` and reboot |
| **NumPy/OpenCV error** | `pip install "numpy<2"` then reinstall opencv |
| **SSH disconnects** | Use `-o TCPKeepAlive=yes` flag |
| **Dashboard won't load** | Check firewall: `sudo ufw allow 8080` |
| **Service won't start** | View logs: `sudo journalctl -u mecamera.service -n 50` |

---

## 📋 Files Created for Your Convenience

These scripts are now in your repo:
- **`deploy_pi_zero.ps1`** - PowerShell deployment script
- **`deploy_pi_zero.sh`** - Bash deployment script  
- **`DEPLOYMENT_PLAN.md`** - Full reference guide

---

## ⏱️ Expected Timeline

| Step | Time |
|------|------|
| Clean & clone | 2-3 min |
| Virtual env | 1 min |
| Dependencies | **7-10 min** (longest part) |
| Setup script | 1 min |
| Service setup | 1 min |
| **Total** | **12-16 min** |

---

**Status:** 🟢 Ready to Deploy
**Last Updated:** Jan 14, 2026
