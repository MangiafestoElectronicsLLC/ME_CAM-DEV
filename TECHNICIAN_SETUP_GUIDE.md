# ME_CAM V3.0 - TECHNICIAN SETUP GUIDE

**For:** Production technicians, field installation teams, and deployment specialists  
**Time Required:** 30-45 minutes per device  
**Version:** 3.0.0 | **Updated:** March 19, 2026

---

## 🎯 WHAT YOU'RE BUILDING

A Raspberry Pi-based security camera system with:
- ✅ Local video surveillance (no cloud dependency)
- ✅ HTTPS encrypted connections
- ✅ AES-256 video encryption
- ✅ Intelligent power-saving (extends battery 30-50%)
- ✅ Responsive mobile UI with dark mode
- ✅ Open-source, customizable, production-ready

**Output:** Fully operational ME_CAM device ready for customer deployment

---

## 📋 PRE-INSTALLATION REQUIREMENTS

### Hardware Needed
- [ ] Raspberry Pi 3B+ or 4B (recommended: 4B)
- [ ] microSD card (32GB minimum, 64GB recommended)
- [ ] USB-C power adapter (5V/3A minimum)
- [ ] Pi camera ribbon cable + IMX519 camera module
- [ ] Optional: USB microphone, external battery pack (10K mAh)
- [ ] SD card reader for flashing

### Software on Your Workstation
- [ ] Raspberry Pi Imager (download from raspberrypi.com)
- [ ] SSH client (built-in on Mac/Linux, PuTTY on Windows)
- [ ] Text editor (for config files)
- [ ] Internet connection (for downloading software)

### Credentials Setup (BEFORE YOU START)
1. Create a **secure password** for the `pi` user (8+ characters, mixed case/numbers/special chars)
2. Prepare WiFi credentials (SSID and password)
3. Plan hostname: `mecamdevX` (replace X with device number, e.g., `mecamdev1`, `mecamdev2`)

---

## 🔧 STEP 1: FLASH RASPBERRY PI OS (5 minutes)

### 1.1 - Insert SD Card and Open Raspberry Pi Imager

1. Insert microSD card into your workstation
2. Open **Raspberry Pi Imager**
3. Click **"Choose Device"** → Select your Pi model (e.g., Raspberry Pi 4B)

### 1.2 - Select Operating System

1. Click **"Choose OS"**
2. Select **"Raspberry Pi OS (64-bit)"** (Full version, not Lite)
3. Click **"Choose Storage"** → Select your microSD card

### 1.3 - Configure Advanced Settings (IMPORTANT)

Click **"Next"** → **"Edit Settings"** when prompted:

- **Hostname:** Enter `mecamdevX` (e.g., `mecamdev1`)
- **Username:** `pi`
- **Password:** Enter your secure password (e.g., `MySecure123!`)
- **WiFi SSID:** Your network name
- **WiFi Password:** Your network password
- **Wireless LAN country:** Your country code
- **Locale:** Your timezone and locale
- **Enable SSH:** ✅ Check this box
- **SSH using password authentication:** ✅ Keep enabled

### 1.4 - Write Image to Card

1. Click **"Write"**
2. Confirm warning (this will erase the card)
3. Wait for completion (3-5 minutes)
4. Eject SD card when done

---

## 🔌 STEP 2: INITIAL BOOT AND NETWORK SETUP (5 minutes)

### 2.1 - Hardware Assembly

1. Insert flashed SD card into Raspberry Pi
2. Connect camera ribbon cable (gently insert into CSI port)
3. Connect USB microphone (if available)
4. Connect USB-C power adapter
5. **Wait 2 minutes** for first boot (system auto-expands filesystem)

### 2.2 - Find Device on Network

Open terminal/command prompt on your workstation:

```bash
# Try to SSH into the device using hostname
ssh pi@mecamdevX.local
# Replace X with your device number
# Example: ssh pi@mecamdev1.local

# When prompted: "Are you sure you want to continue?"
# Type: yes

# Enter password when prompted (the one you set in Imager)
```

**✅ Success:** You see the prompt `pi@mecamdevX:~$`

**❌ Problem:** Can't find device?
```bash
# Try using the IP address instead
# First, find your Pi's IP
ping mecamdevX.local -c 4

# Or check your router's DHCP client list
# Then SSH to IP: ssh pi@192.168.X.X
```

---

## 📥 STEP 3: CLONE ME_CAM REPOSITORY (5 minutes)

Once SSH'd into the device:

```bash
# Update system first
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv git ffmpeg libatlas-base-dev

# Clone ME_CAM repository
cd ~
git clone https://github.com/YOUR_USERNAME/ME_CAM.git
cd ME_CAM

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

> **Note:** Replace `YOUR_USERNAME` with your actual GitHub username

---

## ⚙️ STEP 4: CONFIGURATION (5 minutes)

### 4.1 - Create Device Configuration

```bash
# Copy template configuration
cp config.template.json config.json
```

### 4.2 - Edit Configuration

```bash
# Open config editor (using nano - simple text editor)
nano config.json
```

Make these changes (use arrow keys to navigate):

```json
{
  "device_name": "ME_CAM Device 1",      // Change number to your device
  "hostname": "mecamdevX",               // Must match hostname from Step 1
  "port": 8080,                          // Can change if needed
  "pi_user": "pi",                       // Keep as is
  "avg_current_draw_ma": 600,           // Battery drain rate (mA)
  "power_saving_enabled": true,          // Enable power optimization
  "https_enabled": true,                 // Enable HTTPS for security
  "encryption_enabled": false,           // Enable after testing
  "security_headers_enabled": true,      // Recommended for production
  "firmware_version": "3.0.0"
}
```

**How to save in nano:**
1. Press `Ctrl + X`
2. Press `Y` (yes to save)
3. Press `Enter` (confirm filename)

---

## 🧪 STEP 5: VERIFY INSTALLATION (10 minutes)

### 5.1 - Test Camera Detection

```bash
# Make sure you're still in the venv
source ~/ME_CAM/venv/bin/activate

# Test camera
python3 -c "from picamera2 import Picamera2; print('✅ Camera detected')" 2>&1 || echo "❌ Camera not found - check ribbon cable"
```

### 5.2 - Start the Application

```bash
# Navigate to application directory
cd ~/ME_CAM/web

# Start Flask application
python3 app_lite.py
```

**Expected output:**
```
Running on http://0.0.0.0:8080
Press CTRL+C to quit
```

### 5.3 - Test Dashboard (In New Terminal Window)

Open a **NEW** terminal/SSH session (don't close the app_lite.py one):

```bash
# From your workstation browser OR
# From another SSH session on the Pi, test the dashboard

# Option 1: Browser on workstation
# Open: http://mecamdevX.local:8080
# Or use IP: http://192.168.X.X:8080

# Option 2: From Pi terminal, test with curl
curl http://localhost:8080/dashboard
```

**✅ Success:** Dashboard loads with video feed, battery status, and settings

**❌ Problems?**
```bash
# Check if port 8080 is listening
sudo netstat -tlnp | grep 8080

# View application logs
tail -50 ~/ME_CAM/logs/app.log

# Restart application (from app_lite.py terminal, press Ctrl+C, then restart)
```

---

## 🔒 STEP 6: PRODUCTION SECURITY SETUP (10 minutes)

### 6.1 - Generate HTTPS Certificates

```bash
# Stop the app if it's running (Ctrl+C in app_lite.py terminal)

# Generate self-signed certificates (valid 5 years)
cd ~/ME_CAM
python3 setup_https.py mecamdevX

# Verify certificates created
ls -la certs/
```

**Expected output:**
```
certificate.crt  (readable)
private.key      (read-only, restricted permissions)
```

### 6.2 - Update Configuration for HTTPS

```bash
# Edit config to enable HTTPS
nano config.json

# Change: "https_enabled": true
# And set: "port": 8443 (or keep as 8080 if no HTTPS yet)
```

### 6.3 - Start Application with HTTPS

```bash
# From ~/ME_CAM/web directory
python3 app_lite.py
```

Test with HTTPS:
```bash
# In new terminal
curl -k https://mecamdevX.local:8443/api/battery
# The -k flag tells curl to ignore self-signed certificate warnings
```

---

## 🔋 STEP 7: BATTERY AND POWER TESTING (5 minutes)

### 7.1 - Test Battery Monitoring

```bash
# In new SSH session
curl http://mecamdevX.local:8080/api/battery | python3 -m json.tool
```

**Expected response:**
```json
{
  "percent": 85,
  "power_source": "wall_adapter",
  "display_text": "Wall Power (85%)",
  "runtime_hours": 11,
  "power_mode": "normal"
}
```

### 7.2 - Test Power-Saving Modes

```python
# Test power mode calculation
python3 << 'EOF'
from src.core.power_saver import PowerSaver

ps = PowerSaver()

# Test at different battery levels
for battery in [5, 15, 35, 60, 90]:
    mode = ps.get_power_mode_for_battery(battery, False)
    print(f"Battery {battery}% → Mode: {mode}")

# Expected:
# Battery 5% → Mode: critical
# Battery 15% → Mode: low
# Battery 35% → Mode: medium
# Battery 60% → Mode: normal
# Battery 90% → Mode: normal
EOF
```

---

## ✅ DEPLOYMENT CHECKLIST

Before handing off to customer, verify all items:

### Hardware
- [ ] Camera ribbon cable secured and not pinched
- [ ] Power adapter provides stable 5V
- [ ] Device stays on without disconnecting for 5 minutes
- [ ] All cables properly seated

### Network
- [ ] Device connects to WiFi automatically after reboot
- [ ] Device has stable IP on network (check hostname)
- [ ] SSH access works: `ssh pi@mecamdevX.local`

### Software
- [ ] Dashboard loads at `http://mecamdevX.local:8080`
- [ ] Video feed displays camera output
- [ ] Battery API returns correct data
- [ ] Power mode switches work (check API response)
- [ ] No error messages in logs

### Security
- [ ] HTTPS certificates generated (`ls certs/`)
- [ ] Security headers present in HTTP responses
- [ ] Rate limiting active (test `/api/` endpoints)

### Operations
- [ ] Application auto-starts on reboot (set up systemd service)
- [ ] Logs save to `~/ME_CAM/logs/app.log`
- [ ] User knows their password
- [ ] Customer gets printed copy of hostname/IP/password

---

## 📖 AUTOSTART SETUP (Optional but Recommended)

To make the app auto-start on reboot:

```bash
# Create systemd service file
sudo nano /etc/systemd/system/mecam.service
```

Paste this content:

```ini
[Unit]
Description=ME_CAM Video Surveillance System
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ME_CAM/web
ExecStart=/home/pi/ME_CAM/venv/bin/python3 app_lite.py
Restart=always
RestartSec=10
StandardOutput=append:/home/pi/ME_CAM/logs/app.log
StandardError=append:/home/pi/ME_CAM/logs/app.log

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mecam
sudo systemctl start mecam

# Verify it's running
sudo systemctl status mecam
```

---

## 🆘 TROUBLESHOOTING

### Problem: "Camera not detected"
```bash
# Check ribbon cable is properly seated
# Test with libcamera
libcamera-hello

# Lists available cameras
libcamera-hello --list-cameras
```

### Problem: "Connection timeout when SSH"
```bash
# Check device is on same network
ping mecamdevX.local

# Try using IP instead
# Check your router's DHCP table for the Pi's IP
```

### Problem: "Dashboard shows 'Connection Error'"
```bash
# Check if Flask app is running on Pi
ps aux | grep app_lite.py

# Check port is listening
netstat -tlnp | grep 8080

# Restart app
pkill -f app_lite.py
cd ~/ME_CAM/web && python3 app_lite.py &
```

### Problem: "Authentication failed on SSH"
```bash
# Verify you're using correct password (set in Imager)
# Try resetting password:
sudo passwd pi
# Enter new password twice
```

---

## 📞 SUPPORT CHECKLIST

When handing off to customer, provide:

- [ ] Device hostname: `mecamdevX`
- [ ] Device IP address: `192.168.X.X`
- [ ] Default password: `[YOUR SECURE PASSWORD]`
- [ ] WiFi network name (if different from provided)
- [ ] Support phone number or email
- [ ] Quick start guide (next document)
- [ ] Warranty information

---

## 🚀 NEXT STEPS

Device is now ready for customer use! 

**For customers:** See the separate "USER_QUICK_START.md" guide
**For developers:** See the "DEVELOPER_SETUP.md" guide in the repo

---

**Questions?** Check the [ME_CAM GitHub Issues](https://github.com/YOUR_USERNAME/ME_CAM/issues) or contact support.
