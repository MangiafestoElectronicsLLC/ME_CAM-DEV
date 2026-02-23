# Tailscale Multi-User & Multi-Device Guide

**Purpose:** Securely access your cameras from anywhere with different accounts  
**Scenario:** You access Device 1, Wife accesses Device 2, both from different locations  
**Security:** End-to-end encrypted, no port forwarding needed

---

## 🎯 Understanding Tailscale

### What is Tailscale?
- **VPN service** that connects your devices securely
- **Encrypted** - All traffic encrypted end-to-end
- **Private IPs** - Gives each device a 100.x.x.x address
- **No port forwarding** - Works through firewalls
- **Free tier** - Up to 100 devices, perfect for home use

### How It Works for Cameras
```
Your Pi → Internet → Tailscale → Your Laptop
         (Encrypted connection)
```

---

## 📋 Prerequisites

1. **Tailscale Account** (free at tailscale.com)
2. **Each Raspberry Pi** needs Tailscale installed
3. **Working Internet** on each Pi
4. **Your Tailscale Account** (free works fine)

---

## ⚙️ Step 1: Install Tailscale on Raspberry Pi

### On Each Pi (Device 1, 2, 3, etc.)

```bash
# SSH into the Pi
ssh pi@mecamdev1.local

# Download and install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Verify installation
tailscale version
# Should show version number like: 1.54.0
```

### Authenticate Tailscale

```bash
# Start Tailscale and get auth URL
sudo tailscale up

# Output will show something like:
# To authenticate, visit:
#    https://login.tailscale.com/a/XXXXX

# Open that URL in your browser
# Follow prompts to authenticate
# Device will automatically connect
```

### Check Connection

```bash
# View Tailscale status
sudo tailscale status

# Output should show something like:
# 100.100.100.1    device1    you@gmail.com  linux   idle

# Get just the IP
sudo tailscale ip -4
# Output: 100.100.100.1
```

---

## 👤 Step 2: Multi-User Account Setup

### Device 1 (Your Camera)

```bash
# SSH into Device 1
ssh pi@100.100.100.1  # Via Tailscale IP

# Start the Flask app
python3 /path/to/ME_CAM-DEV/web/app.py

# Open browser: http://100.100.100.1:8080
# Create YOUR account:
#   Username: your-username
#   Password: your-secure-password
```

### Device 2 (Wife's Camera)

```bash
# SSH into Device 2
ssh pi@100.100.100.2

# Start the Flask app
python3 /path/to/ME_CAM-DEV/web/app.py

# Open browser: http://100.100.100.2:8080
# Create WIFE'S account:
#   Username: wife-username
#   Password: her-secure-password
```

### Device 3 (Optional - Shared Camera)

```bash
# SSH into Device 3
ssh pi@100.100.100.3

# Start Flask app
python3 /path/to/ME_CAM-DEV/web/app.py

# Open browser: http://100.100.100.3:8080
# Create shared account:
#   Username: shared
#   Password: shared-password
```

**Key Point:** Each device has independent user database. No conflicts!

---

## 🌐 Step 3: Access from Anywhere

### You Access Device 1 from Your Work

```bash
# Completely different WiFi network (work)
# Open browser: http://100.100.100.1:8080

# Login with YOUR credentials:
#   Username: your-username
#   Password: your-password

# You see your camera feed! ✅
```

### Wife Accesses Device 2 from Her Work

```bash
# Her completely different WiFi network
# Open browser: http://100.100.100.2:8080

# Login with HER credentials:
#   Username: wife-username
#   Password: her-password

# She sees her camera feed! ✅
```

### Both Access Simultaneously (Different WiFi)

- You're on work WiFi accessing Device 1
- Wife is on her work WiFi accessing Device 2
- Both work at the same time
- No conflicts, no shared passwords
- **Everything encrypted via Tailscale**

---

## 🔒 Security Best Practices

### 1. Strong Passwords Per Device

```
Device 1 (Your account):
  Username: your-username
  Password: Tr0picalM0nkey!Secure123

Device 2 (Wife's account):
  Username: wife-username
  Password: SunsetBeach#Paradise456

Device 3 (Shared):
  Username: shared
  Password: CameraAccess$789!
```

### 2. Different Password Per Device
- Don't reuse same password across devices
- If one compromised, others still safe

### 3. Enable Tailscale Security Features

```bash
# On your Tailscale admin console:
# https://login.tailscale.com/admin/machines

# 1. Enable "Require approval for new devices"
# 2. Set access control rules (ACLs)
# 3. Review "Connected devices" regularly
# 4. Disable access for unused devices
```

### 4. Firewall Settings (Extra Security)

```bash
# On each Pi, restrict web server to Tailscale network only
# Edit web/app.py:
# app.run(host='100.100.100.1', port=8080)  # Only Tailscale IP

# This prevents direct local access via router
```

---

## 📱 Step 4: Install Tailscale on Phone (Optional)

Access cameras from your phone!

### iPhone
1. Download "Tailscale" from App Store
2. Open app → Sign in
3. Use same Tailscale account
4. Open Safari → http://100.100.100.1:8080
5. Instantly access camera feed!

### Android
1. Download "Tailscale" from Play Store
2. Open app → Sign in
3. Use same Tailscale account
4. Open Chrome → http://100.100.100.1:8080
5. Full camera access!

---

## 🛰️ Advanced: Custom DNS Names

Instead of remembering IPs, use custom names:

### In Tailscale Admin Console

1. Go to https://login.tailscale.com/admin
2. Under "DNS" section
3. Add custom names:

```
100.100.100.1  → my-living-room
100.100.100.2  → wifes-bedroom
100.100.100.3  → front-porch
```

### Then Access via Name

```bash
# Instead of: http://100.100.100.1:8080
# Use: http://my-living-room:8080

# Instead of: http://100.100.100.2:8080
# Use: http://wifes-bedroom:8080
```

Much easier to remember!

---

## 📊 Real-World Scenario

### Situation: Wife is at Work, You're at Work

```
Wife at Work:
├─ WiFi: CompanyWiFi
├─ Opens: http://100.100.100.2:8080 (via Tailscale)
├─ Logs in: wife-username / wife-password
└─ Sees: Her bedroom camera feed

You at Work:
├─ WiFi: DifferentWiFi
├─ Opens: http://100.100.100.1:8080 (via Tailscale)
├─ Logs in: your-username / your-password
└─ Sees: Your living room camera feed

Security:
✅ Different WiFi networks
✅ Different login credentials
✅ Encrypted Tailscale connection
✅ No port forwarding needed
✅ No exposed servers
```

---

## 🔄 Step 5: Autostart Everything

Make cameras auto-start on boot:

### Systemd Service on Each Pi

**Device 1 (/etc/systemd/system/mecam-device1.service):**
```ini
[Unit]
Description=ME_CAM Device 1
After=network.target tailscaled.service
Wants=tailscaled.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ME_CAM-DEV
ExecStart=/usr/bin/python3 web/app.py
Restart=always

[Install]
WantedBy=multi-user.service
```

**Enable:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable mecam-device1.service
sudo systemctl start mecam-device1.service

# Check status
sudo systemctl status mecam-device1.service
```

Now everything starts automatically on boot!

---

## 🧪 Testing Multi-User Access

### Test Setup

```
Device 1 (Your camera):
  Tailscale IP: 100.100.100.1
  Your Account: you / password1
  Port: 8080
  URL: http://100.100.100.1:8080

Device 2 (Wife's camera):
  Tailscale IP: 100.100.100.2
  Wife's Account: wife / password2
  Port: 8080
  URL: http://100.100.100.2:8080
```

### Test 1: Same Location, Different Accounts

```bash
# Test 1a: You log in
http://100.100.100.1:8080
Login: you / password1
Result: See Device 1 ✅

# Test 1b: In another tab, wife logs in
http://100.100.100.2:8080
Login: wife / password2
Result: See Device 2 ✅

# Both work in same browser simultaneously!
```

### Test 2: Different WiFi Networks

```bash
# Your work WiFi:
http://100.100.100.1:8080
# Should work ✅

# Wife's work WiFi:
http://100.100.100.2:8080
# Should work ✅

# Both access simultaneously from different WiFi!
```

### Test 3: Mobile Phone Access

```bash
# Install Tailscale on phone
# Sign in to same account

# Open browser: http://100.100.100.1:8080
# Should work on cellular data! ✅

# Full camera access from phone
```

---

## 📝 Troubleshooting

### Problem: Can't Connect to Tailscale IP

```bash
# Check if Tailscale is running
sudo tailscale status

# If not connected, run:
sudo tailscale up

# Check the auth URL and follow it
```

### Problem: Device Not Showing in Tailscale

```bash
# Check if Tailscale service is running
sudo systemctl status tailscaled

# Restart it
sudo systemctl restart tailscaled

# Check status
sudo tailscale status
```

### Problem: Can Access Device 1 but Not Device 2

```bash
# Each device needs independent Tailscale setup
# Verify Device 2:
ssh pi@100.100.100.2
sudo tailscale status
# Should show different Tailscale IP

# Check if web app is running on Device 2
ps aux | grep app.py
```

### Problem: Wife Can't Log Into Device 2

```bash
# Each device has independent user database
# Wife needs separate account on Device 2

# On Device 2, create her account:
http://100.100.100.2:8080
# Should show first-run setup
# Create: wife / password2
```

### Problem: Forgot Password

```bash
# SSH into the device
ssh pi@100.100.100.1

# Reset the app (nuclear option)
rm -rf ~/.mecam/users.db

# Restart app
sudo systemctl restart mecam-device1.service

# Go to http://100.100.100.1:8080
# Will be first-run mode again
# Create new account
```

---

## 🎓 Understanding the Architecture

### Before Tailscale
```
Your WiFi ← → Device 1
           ← → Device 2
Wife's WiFi: Can't access (different network)
```

### After Tailscale
```
Your WiFi → Tailscale VPN → Device 1, 2, 3
Wife's WiFi → Tailscale VPN → Device 1, 2, 3
Mobile Data → Tailscale VPN → Device 1, 2, 3

All encrypted, all independent accounts!
```

---

## 📈 Scaling to More Devices

### Add Device 4, 5, 6, etc.

Same process for each:

1. Install Tailscale
2. Authenticate
3. Get Tailscale IP (100.100.100.4)
4. Start web app on port 8080
5. Create your accounts
6. Access via http://100.100.100.4:8080

Scales infinitely!

---

## 💡 Pro Tips

### Tip 1: Custom Hostnames
Use easy names instead of IPs:
```
my-living-room:8080
wifes-bedroom:8080
front-porch:8080
```

### Tip 2: Share Access
Want wife to also see Device 1?
Create second account on Device 1:
```
Device 1:
  Account 1: you / password1
  Account 2: wife / password_for_device1
```

### Tip 3: Monitor Bandwidth
Cameras use data. On mobile hotspot:
- Monitor data usage
- Disable streaming when not needed
- Use lower quality if on limited data

### Tip 4: Bookmarks
Save URLs for quick access:
- http://my-living-room:8080
- http://wifes-bedroom:8080
- http://front-porch:8080

---

## 🔐 Security Summary

✅ **Encryption:** End-to-end via Tailscale  
✅ **Authentication:** Per-device accounts  
✅ **No Port Forwarding:** Works through firewalls  
✅ **No Exposed Services:** Only Tailscale clients can access  
✅ **Different Credentials:** Each device/user unique  
✅ **Remote Access:** Secure from anywhere  

---

## 🎉 What You Get

✅ Each camera = independent web interface  
✅ You access Device 1 from anywhere  
✅ Wife accesses Device 2 from anywhere  
✅ Different WiFi networks (no shared WiFi needed)  
✅ Separate login credentials (no password sharing)  
✅ Encrypted connections (Tailscale)  
✅ Works on mobile hotspot  
✅ Works on any internet connection  
✅ Scales to unlimited devices  

---

## 📞 Support

For Tailscale issues: https://tailscale.com/kb/  
For ME_CAM issues: See DEVELOPER_QUICK_REFERENCE.md

---

**Ready to set up?**
1. Create free Tailscale account (tailscale.com)
2. Follow steps above for each Pi
3. Create independent accounts
4. Test from different WiFi networks
5. Enjoy unlimited remote access! 🚀

---

**Version:** 2.3.0+  
**Status:** Production Ready  
**Date:** February 19, 2026
