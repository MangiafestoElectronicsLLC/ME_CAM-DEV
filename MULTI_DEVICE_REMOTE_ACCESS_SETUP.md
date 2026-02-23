# ME_CAM Multi-Device Remote Access Setup
## Independent Accounts + Mobile Hotspot + Tailscale

**Version:** 2.3.0+  
**Date:** February 19, 2026  
**Use Case:** Each camera device with independent web interface, accessible remotely via Tailscale from any WiFi network

---

## 🎯 What This Enables

### ✅ Mobile Hotspot Support
- Connect Raspberry Pi via your phone's hotspot
- Works at home, work, or anywhere
- No WiFi router dependency

### ✅ Independent Device Access
- Each Pi has its own web interface (separate port or domain)
- Device 1: http://device1.tailscale.com or 100.100.100.1
- Device 2: http://device2.tailscale.com or 100.100.100.2
- Device 3: http://device3.tailscale.com or 100.100.100.3

### ✅ Multi-User Accounts
- Your account on Device 1
- Wife's account on Device 2
- Completely independent login systems
- No shared passwords or confusion

### ✅ Remote Access Anywhere
- Access Device 1 from your work WiFi
- Wife accesses Device 2 from her work WiFi
- Both access simultaneously
- Encrypted connection (Tailscale)
- No port forwarding needed

### ✅ Architecture Benefits
- Each device is independent
- Scales to 10+ devices easily
- No single point of failure
- Secure peer-to-peer connections
- Works on any internet connection

---

## 📋 Architecture Overview

```
Your Home Network:
├─ Device 1 (Pi Zero 2W) → Tailscale → 100.100.100.1
│  └─ Web Interface on port 8080
│  └─ User: you
│  └─ Password: your-secure-password
│
├─ Device 2 (Pi Zero 2W) → Tailscale → 100.100.100.2
│  └─ Web Interface on port 8080
│  └─ User: wife
│  └─ Password: wife-password
│
└─ Device 3 (Pi Zero 2W) → Tailscale → 100.100.100.3
   └─ Web Interface on port 8080
   └─ User: optional-user
   └─ Password: optional-password

Remote Access:
├─ Your Work (Different WiFi)
│  └─ Access Device 1 via: http://100.100.100.1:8080
│  └─ Login as: you
│
└─ Wife's Work (Different WiFi)
   └─ Access Device 2 via: http://100.100.100.2:8080
   └─ Login as: wife
```

---

## 🔧 Step 1: Mobile Hotspot Setup (All Devices)

### On Raspberry Pi via SSH

```bash
# 1. Edit WiFi configuration
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf

# Add this at the end (or replace existing network):
network={
    ssid="YOUR_HOTSPOT_NAME"
    psk="YOUR_HOTSPOT_PASSWORD"
    priority=1
}

# If you also want home WiFi as fallback:
network={
    ssid="YOUR_HOME_WIFI"
    psk="YOUR_HOME_WIFI_PASSWORD"
    priority=0
}
```

### Save and Test
```bash
# Save: Ctrl+O, Enter, Ctrl+X

# Restart WiFi
sudo systemctl restart wpa_supplicant

# Check connection
ip addr show wlan0
# Should show inet (IP address)

# Test internet
ping 8.8.8.8
```

### Make it Persistent
```bash
# Edit dhcpcd config to prefer certain networks
sudo nano /etc/dhcpcd.conf

# Add at end:
interface wlan0
static ip_address=192.168.X.100/24
static routers=192.168.X.1
```

---

## 🌐 Step 2: Install Tailscale on Each Pi

### Install Tailscale
```bash
# Download and install
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate (will give you a URL)
sudo tailscale up

# Follow the link in terminal to approve this device
```

### Check Tailscale Status
```bash
sudo tailscale status

# Output should show:
# 100.100.100.1    device1              me@example.com linux idle
# 100.100.100.2    device2              me@example.com linux idle
```

### Get Device's Tailscale IP
```bash
sudo tailscale ip -4

# Output: 100.100.100.1 (your device's Tailscale IP)
# Write this down!
```

### Optional: Enable Tailscale on Boot
```bash
# Make Tailscale autostart
sudo systemctl enable tailscaled
sudo tailscale up --auto
```

---

## 🔐 Step 3: Independent Accounts Per Device

Each Pi already has its own Flask app instance running on port 8080. Here's how to set up independent accounts:

### Device 1 Setup (Your Device)
```bash
# SSH into Device 1
ssh pi@100.100.100.1  # Via Tailscale
# or
ssh pi@mecamdev1.local  # Via mDNS (same network)

# Start the app
cd /path/to/ME_CAM-DEV
python3 web/app.py

# First run: Go to http://100.100.100.1:8080
# Create account with YOUR credentials
# Username: your-username
# Password: secure-password
```

### Device 2 Setup (Wife's Device)
```bash
# SSH into Device 2
ssh pi@100.100.100.2

# Start the app
cd /path/to/ME_CAM-DEV
python3 web/app.py

# First run: Go to http://100.100.100.2:8080
# Create account with WIFE'S credentials
# Username: wife-username
# Password: wife-password
```

### Device 3 Setup (Optional)
```bash
# Same pattern for additional devices
ssh pi@100.100.100.3
cd /path/to/ME_CAM-DEV
python3 web/app.py
# Create your own account
```

**Key Point:** Each device has completely independent user databases. No conflict!

---

## 🚀 Step 4: Remote Access from Anywhere

### From Your Work (Different WiFi)

#### Method 1: Via Tailscale IP
```bash
# Open browser (from any network)
http://100.100.100.1:8080

# Login with YOUR credentials
# Username: your-username
# Password: secure-password

# You see Device 1's camera feed
```

#### Method 2: Via Custom Domain (Optional)
```bash
# In Tailscale admin, set custom hostname
# Device 1: device1.your-tailnet.ts.net
# Device 2: device2.your-tailnet.ts.net

# Then access:
http://device1.your-tailnet.ts.net:8080
http://device2.your-tailnet.ts.net:8080
```

### From Wife's Work (Different WiFi)

#### Same Process - Different Device
```bash
# Open browser (from any network)
http://100.100.100.2:8080

# Login with WIFE'S credentials
# Username: wife-username
# Password: wife-password

# She sees Device 2's camera feed
# Completely independent from Device 1
```

### Key Advantages
- ✅ You see Device 1 from work WiFi
- ✅ Wife sees Device 2 from her work WiFi
- ✅ No shared WiFi needed
- ✅ No port forwarding/exposed ports
- ✅ Encrypted connection (Tailscale)
- ✅ Completely private

---

## 📱 Mobile Hotspot Connection Flow

```
Home Internet Down?
↓
Switch to Mobile Hotspot
↓
Raspberry Pi connects to hotspot
↓
Pi gets internet via hotspot
↓
Tailscale establishes connection
↓
You access from work via Tailscale
↓
Everything still works ✅
```

---

## 🔄 Step 5: Systemd Service for Auto-Start

### Make Each App Auto-Start on Boot

**On Device 1:**
```bash
# Create service file
sudo nano /etc/systemd/system/mecam-device1.service

# Paste:
[Unit]
Description=ME_CAM Device 1
After=network.target tailscaled.service
Wants=tailscaled.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ME_CAM-DEV
ExecStart=/usr/bin/python3 /home/pi/ME_CAM-DEV/web/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Save and enable:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable mecam-device1.service
sudo systemctl start mecam-device1.service

# Check status
sudo systemctl status mecam-device1.service
```

**Repeat for Device 2, Device 3, etc.** (change service names)

---

## 🎯 Multi-Device Management Script

Create this script to manage all your devices:

```bash
#!/bin/bash
# File: manage_devices.sh

DEVICES=(
    "100.100.100.1:device1"
    "100.100.100.2:device2"
    "100.100.100.3:device3"
)

case "$1" in
    status)
        for device in "${DEVICES[@]}"; do
            ip=$(echo $device | cut -d: -f1)
            name=$(echo $device | cut -d: -f2)
            echo "=== $name ($ip) ==="
            curl -s http://$ip:8080/api/status 2>/dev/null || echo "Offline"
        done
        ;;
    
    restart)
        for device in "${DEVICES[@]}"; do
            ip=$(echo $device | cut -d: -f1)
            name=$(echo $device | cut -d: -f2)
            echo "Restarting $name..."
            ssh pi@$ip "sudo systemctl restart mecam-device*.service"
        done
        ;;
    
    tailscale-status)
        tailscale status
        ;;
    
    *)
        echo "Usage: $0 {status|restart|tailscale-status}"
        ;;
esac
```

**Use it:**
```bash
chmod +x manage_devices.sh
./manage_devices.sh status      # Check all devices
./manage_devices.sh restart     # Restart all devices
./manage_devices.sh tailscale-status
```

---

## 🔐 Security Best Practices

### Per-Device Security

```python
# In web/app.py on each device
app.config.update(
    # Device-specific secret key (different on each Pi!)
    SECRET_KEY=os.urandom(32),
    
    # Session timeout (30 minutes of inactivity)
    PERMANENT_SESSION_LIFETIME=1800,
    
    # Secure cookies
    SESSION_COOKIE_SECURE=True,  # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,  # No JS access
    SESSION_COOKIE_SAMESITE='Strict',  # CSRF protection
)
```

### Tailscale Security
```bash
# Require authentication for Tailscale
sudo tailscale set --auth-key=tskey-YOUR_KEY_HERE

# Enable MagicDNS
sudo tailscale set --accept-dns=true

# Check ACLs in Tailscale admin console
# Ensure proper access policies
```

### User Account Security
- Strong passwords (12+ characters)
- Different password per device
- Change passwords regularly
- Enable HTTPS (if possible)

---

## 📊 Testing the Setup

### Test 1: Local Access (Same WiFi)
```bash
# From laptop on same WiFi as Pi
curl http://mecamdev1.local:8080/
# Should show login page
```

### Test 2: Mobile Hotspot Connection
```bash
# Switch home WiFi off
# Make sure Pi is on mobile hotspot
ping pi-ip-address  # Via Tailscale
# Should respond

# Access web interface
http://100.100.100.1:8080
# Should load normally
```

### Test 3: Tailscale Remote Access
```bash
# From different WiFi (work, coffee shop, etc)
# Install Tailscale on your laptop first

# Access each device
curl http://100.100.100.1:8080  # Device 1
curl http://100.100.100.2:8080  # Device 2
curl http://100.100.100.3:8080  # Device 3

# All should respond even though WiFi is different
```

### Test 4: Independent Logins
```bash
# Device 1
http://100.100.100.1:8080
Login as: you
# See your camera feed

# Device 2 (open in another tab/window)
http://100.100.100.2:8080
Login as: wife
# See wife's camera feed

# Both work simultaneously without conflict!
```

---

## 🛠️ Troubleshooting

### Can't Connect to Hotspot
```bash
# Check if hotspot is visible
iwlist wlan0 scanning | grep SSID

# Test connection
sudo wpa_cli -i wlan0 select_network 0
sudo wpa_cli -i wlan0 enable_network 0

# Check status
iwconfig wlan0
```

### Tailscale Not Connecting
```bash
# Check if running
sudo systemctl status tailscaled

# Restart
sudo systemctl restart tailscaled

# View auth URL
sudo tailscale up

# Check status
sudo tailscale status
```

### Can't Access Device Remotely
```bash
# 1. Verify Tailscale connection
sudo tailscale status

# 2. Check firewall (if any)
sudo iptables -L | grep 8080

# 3. Verify app is running
ps aux | grep app.py

# 4. Check logs
tail -f /var/log/syslog | grep tailscale
```

### Password Issues
```bash
# If locked out, SSH in directly
ssh pi@100.100.100.1

# Reset user database
rm ~/.mecam/users.db

# Restart app - will be first-run mode
sudo systemctl restart mecam-device1.service
```

---

## 📈 Scaling to Multiple Devices

### Adding Device 4, 5, 6, etc.

Each new device:

1. **Flash SD Card** with same process
2. **Set hostname** to device4, device5, etc.
3. **Configure hotspot** support
4. **Install Tailscale** and authenticate
5. **Start web app** on port 8080
6. **Create account** with unique credentials
7. **Update management script** with new Tailscale IP

That's it! Each device is completely independent.

---

## 📱 Access from Phone App

You can also install Tailscale on your phone:

### iOS
1. Download Tailscale from App Store
2. Sign in with same account
3. Open browser to: http://100.100.100.1:8080
4. See camera feed on your phone!

### Android
1. Download Tailscale from Play Store
2. Sign in with same account
3. Open browser to: http://100.100.100.1:8080
4. Full access from anywhere

---

## 🎯 Summary: What You Get

✅ **Mobile Hotspot Support**
- Connect Pis via phone hotspot
- No WiFi router dependency
- Works at home, work, anywhere

✅ **Independent Device Access**
- Each Pi = separate web interface
- Device 1, 2, 3 all different
- Separate Tailscale IPs (100.100.100.1, 2, 3)

✅ **Independent Accounts**
- Your account on Device 1
- Wife's account on Device 2
- No shared passwords
- No account conflicts

✅ **Remote Access from Anywhere**
- You access Device 1 from work
- Wife accesses Device 2 from her work
- Both work simultaneously
- Different WiFi networks

✅ **Encrypted & Secure**
- Tailscale provides encryption
- No port forwarding needed
- No exposed ports
- Private peer-to-peer connections

✅ **Scales Easily**
- Add Device 4, 5, 6 seamlessly
- Same architecture
- No configuration complexity
- All independent

---

## 🚀 Getting Started

### Week 1: Setup Tailscale
1. Install Tailscale on all Pis
2. Authenticate each device
3. Verify connectivity

### Week 2: Configure Hotspots
1. Add mobile hotspot to each Pi
2. Test hotspot connections
3. Verify Tailscale works over hotspot

### Week 3: Multi-Account Setup
1. Create independent accounts per device
2. Test logins per device
3. Verify account isolation

### Week 4: Remote Testing
1. Test from work WiFi
2. Wife tests from her location
3. Both access simultaneously
4. Verify all working

---

**Version:** 2.3.0+  
**Status:** Ready to Implement  
**Date:** February 19, 2026

You now have a completely independent, scalable, secure multi-device system! 🚀
