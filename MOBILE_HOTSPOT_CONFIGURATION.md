# Mobile Hotspot Configuration Guide for Raspberry Pi

**Purpose:** Connect your Raspberry Pi camera devices to your phone's mobile hotspot  
**Works with:** iPhone, Android, any hotspot  
**Time:** 15 minutes per device

---

## 🔧 Quick Setup (5 Steps)

### Step 1: Enable Hotspot on Your Phone

**iPhone:**
1. Settings → Personal Hotspot
2. Toggle "Allow Others to Connect"
3. Set WiFi password (copy this)
4. Note the network name (SSID)

**Android:**
1. Settings → Mobile Hotspot & Tethering
2. Toggle "Mobile Hotspot"
3. Tap settings to see name/password
4. Note the network name (SSID)

### Step 2: Connect Pi to Hotspot

```bash
# SSH into your Raspberry Pi
ssh pi@mecamdev1.local

# Edit WiFi config
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
```

### Step 3: Add Hotspot Network

At the **end** of the file, add:

```
network={
    ssid="YOUR_HOTSPOT_NAME"
    psk="YOUR_HOTSPOT_PASSWORD"
    priority=1
}
```

**Example:**
```
network={
    ssid="Nick's iPhone"
    psk="SecurePassword123"
    priority=1
}
```

### Step 4: Save and Reconnect

```bash
# Save: Ctrl+O, Enter, Ctrl+X

# Restart WiFi
sudo systemctl restart wpa_supplicant

# Wait 5 seconds, then check
ip addr show wlan0

# Should show: inet 192.168.X.X (you got an IP!)
```

### Step 5: Verify Connection

```bash
# Test internet connection
ping 8.8.8.8

# If you see replies, you're connected! ✅
```

---

## 📊 Multiple Networks Setup

Want your Pi to switch between home WiFi AND hotspot automatically?

### Add Both Networks (Home First, Hotspot Backup)

```bash
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf

# Add both networks:
network={
    ssid="Home WiFi Name"
    psk="Home WiFi Password"
    priority=10
}

network={
    ssid="Your iPhone"
    psk="Hotspot Password"
    priority=1
}
```

**How it works:**
- Pi tries network with priority=10 first (home WiFi)
- If not available, tries priority=1 (hotspot)
- Automatically switches if network is lost

---

## 🛠️ Troubleshooting

### Problem: Can't See Hotspot Network

**Solution:**
```bash
# Scan for available networks
iwlist wlan0 scanning | grep SSID

# If hotspot doesn't appear:
# 1. Check phone hotspot is ON
# 2. Check phone hotspot name (it might be hidden)
# 3. Restart hotspot
# 4. Restart Pi WiFi
```

### Problem: Wrong Password

**Fix:**
```bash
# Edit config again
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf

# Check the password matches exactly (case-sensitive!)
# Save and restart WiFi
sudo systemctl restart wpa_supplicant
```

### Problem: No Internet Through Hotspot

**Check:**
```bash
# 1. Is phone hotspot enabled?
#    (Look for arrow icon at top of phone)

# 2. Check if Pi has IP address
ip addr show wlan0
# Should show: inet 192.168.X.X

# 3. Check if phone hotspot is sharing internet
#    (On iPhone, it shows "Connected Devices")

# 4. Try restarting phone hotspot
```

### Problem: Slow Connection

**Solutions:**
```bash
# Check WiFi signal strength
iwconfig wlan0 | grep "Signal level"

# If weak signal:
# 1. Move Pi closer to phone
# 2. Move phone closer to window (better reception)
# 3. Check for interference (microwave, other WiFi)

# Test internet speed
speedtest-cli
# Should be close to your phone's normal speed
```

---

## 🔋 Power Considerations

When using mobile hotspot:
- Phone's battery drains faster
- Keep phone plugged in if possible
- Disable hotspot when not needed
- Pi will work fine, but depends on phone power

---

## 🌍 Using Hotspot with Tailscale

Once both are set up:

```
Phone Hotspot
    ↓
Raspberry Pi connects
    ↓
Pi gets internet via hotspot
    ↓
Tailscale connects
    ↓
You can access from anywhere! 🎉
```

**The beautiful part:** You access Device 1 from work, Wife accesses Device 2 from her work - both via the hotspot connection! The hotspot is just how the Pis get internet.

---

## 📱 Switching Networks Manually

If you want to manually switch networks:

```bash
# List available networks
sudo wpa_cli -i wlan0 list_networks

# Switch to specific network
sudo wpa_cli -i wlan0 select_network 0  # Home WiFi
sudo wpa_cli -i wlan0 select_network 1  # Hotspot

# Or disable/enable
sudo wpa_cli -i wlan0 disable_network 0
sudo wpa_cli -i wlan0 enable_network 1
```

---

## 🚀 Advanced: Static IP via Hotspot

If you want consistent IP on hotspot:

```bash
# Edit DHCP config
sudo nano /etc/dhcpcd.conf

# Add at end:
interface wlan0
static ip_address=192.168.137.100/24
static routers=192.168.137.1
static domain_name_servers=8.8.8.8 8.8.4.4
```

**Note:** IP range may vary. Common hotspot IPs:
- iPhone: 192.168.1.x
- Android: 192.168.0.x or 192.168.137.x

---

## 💡 Pro Tips

### Tip 1: Hotspot Name
Use a descriptive name you'll recognize:
- "Nick's iPhone" (better than default)
- "Household WiFi" (for family hotspot)

### Tip 2: Hotspot Password
Make it strong but easy to type:
- ✅ "SecurePass123" (good)
- ❌ "P@ssw0rd!#$%^&*()" (too complex)

### Tip 3: Keep Consistent
Don't change hotspot password often - it breaks Pi connection

### Tip 4: Monitor Phone Battery
When hotspotting:
- Phone battery drains ~15-20% per hour
- Keep plugged in when possible
- Disable when cameras aren't needed

### Tip 5: Data Usage
Hotspot data usage (approximate):
- 1 hour of HD stream: ~500MB-1GB
- 24/7 on 480p: ~10-15GB per day
- Monitor if you have limited data plan

---

## 🎯 Complete Setup Example

**Scenario:** You have Device 1 (living room) and Device 2 (bedroom)

### Device 1 Config:
```
network={
    ssid="Home WiFi"
    psk="HomePass123"
    priority=10
}

network={
    ssid="Nick's iPhone"
    psk="HotspotPass456"
    priority=1
}
```

### Device 2 Config:
```
network={
    ssid="Home WiFi"
    psk="HomePass123"
    priority=10
}

network={
    ssid="Nick's iPhone"
    psk="HotspotPass456"
    priority=1
}
```

### Result:
- Both devices prefer home WiFi
- If home WiFi down, both use phone hotspot
- Both still accessible via Tailscale
- You can access both from work! ✅

---

## 🔐 Security Note

### Hotspot Security
- ✅ Hotspot password is encrypted (WPA2)
- ✅ Data between phone and Pi is secure
- ✅ But your phone is the intermediary
- ✅ On phone's battery, so be aware

### Recommendation
- Use strong hotspot password (12+ chars)
- Don't share hotspot with untrusted people
- Change password if someone unauthorized joins
- Monitor connected devices in phone hotspot settings

---

## 📋 Verification Checklist

- [ ] Phone hotspot enabled and tested
- [ ] Pi can see hotspot network
- [ ] Pi connects to hotspot
- [ ] Pi gets IP address (192.168.x.x)
- [ ] Internet working (ping 8.8.8.8)
- [ ] Can SSH into Pi via hotspot IP
- [ ] Web interface loads via hotspot
- [ ] Tailscale connects over hotspot
- [ ] Remote access works (from other network)
- [ ] Both devices work simultaneously

---

## 🆘 Getting Help

### Common Issues

| Issue | Fix |
|-------|-----|
| Can't see hotspot | Restart phone hotspot, move closer |
| Wrong password error | Double-check exact password match |
| No internet | Check phone is connected to cellular |
| Slow speed | Move Pi closer, check signal strength |
| Keeps disconnecting | Update Pi WiFi drivers or move antenna |

### Debug Command
```bash
# See detailed WiFi info
sudo wpa_cli -i wlan0 status

# Show WiFi events
sudo journalctl -u wpa_supplicant -f

# Check signal strength
iwconfig wlan0 | grep "Signal level"
```

---

## 📚 Related Guides

- **Multi-Device Remote Access:** MULTI_DEVICE_REMOTE_ACCESS_SETUP.md
- **Tailscale Setup:** See MULTI_DEVICE_REMOTE_ACCESS_SETUP.md (Step 2)
- **General Setup:** FRESH_SD_CARD_TUTORIAL_SIMPLE.md

---

**Time to Complete:** 15 minutes per device  
**Difficulty:** Easy  
**Requirements:** Raspberry Pi, Phone with hotspot, WiFi dongle  

**You're ready to use mobile hotspot as backup internet!** 🚀
