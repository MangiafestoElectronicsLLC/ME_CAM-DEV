# ME_CAM v2.1 - Customer Setup & User Manual

**Version:** 2.1-LITE  
**Date:** January 2026  
**Device:** Raspberry Pi Zero 2W  
**Support:** support@mangiafesto-electronics.com

---

## Table of Contents

1. [Quick Start (5 minutes)](#quick-start)
2. [Initial Setup](#initial-setup)
3. [Accessing via Web Browser](#accessing-your-camera)
4. [Mobile & Tablet Access](#mobile--tablet-access)
5. [Configuration Guide](#configuration-guide)
6. [Features Overview](#features-overview)
7. [Troubleshooting](#troubleshooting)
8. [Security & Safety](#security--safety)

---

## Quick Start

### What You Need
- **ME_CAM Device** (pre-configured Pi Zero 2W)
- **Power Supply** (USB-C, included)
- **WiFi or Ethernet** (for network connection)
- **Computer, Phone, or Tablet** (to view camera)

### Setup in 3 Steps

**Step 1: Power On**
- Connect USB-C power cable to the ME_CAM device
- Wait 30 seconds for system to boot (green LED will blink)

**Step 2: Connect to Network**
- Device automatically connects to your WiFi (if previously configured) or Ethernet

**Step 3: Access Web Interface**
- Open web browser on your PC, phone, or tablet
- Go to: **`http://10.2.1.7:8080`** (or your device IP)
- Login with credentials provided

✅ **Done!** Your camera feed should appear within 10 seconds.

---

## Initial Setup

### First-Time Configuration

If this is your first time using ME_CAM:

1. **Power on the device** (USB-C cable)
2. **Wait 1 minute** for full boot
3. **Open browser** → `http://10.2.1.7:8080`
4. **Click "Setup"** or **"Configuration"**
5. **Fill in:**
   - Device Name (e.g., "Front Door Camera")
   - Location (e.g., "Kitchen")
   - Emergency Phone Number (optional)
   - Storage Cleanup (how many days to keep videos)
6. **Click "Save & Continue"**

### Finding Your Device IP Address

If you don't know your device IP:

**Option A - Use Hostname (Easiest):**
```
http://mecamdev3.local:8080
```

**Option B - Find IP on Your Router:**
1. Open router admin page (usually `192.168.1.1`)
2. Look for "Connected Devices" or "DHCP Clients"
3. Find device named "MECAMDEV3" or "raspberrypi"
4. Note its IP address
5. Use in browser: `http://[IP-ADDRESS]:8080`

**Option C - Use Ethernet Connection:**
- Plug Ethernet cable into device (if available)
- Device gets automatic IP from router
- Check router DHCP list for new device

---

## Accessing Your Camera

### On Desktop/Laptop

1. **Open any web browser** (Chrome, Firefox, Safari, Edge)
2. **Type in address bar:**
   ```
   http://10.2.1.7:8080
   ```
   (or your device's actual IP)

3. **Press Enter**
4. **Login** with your credentials
5. **Click "Dashboard"** to view live camera

### On Mobile Phone/Tablet

See "Mobile & Tablet Access" section below.

### Bookmarking for Quick Access

**To save your camera link:**

**Chrome/Firefox (Android & iPhone):**
1. Open `http://10.2.1.7:8080` in browser
2. Tap the **three-line menu** (⋮) in top-right
3. Tap **"Add to Home Screen"** or **"Create Shortcut"**
4. Choose name and confirm
5. Device appears as app icon on home screen

**Safari (iPhone/iPad):**
1. Open `http://10.2.1.7:8080`
2. Tap **Share button** (↗️ or ⬆️)
3. Tap **"Add to Home Screen"**
4. Choose name and tap **"Add"**

---

## Mobile & Tablet Access

### Phone (iPhone/Android)

ME_CAM works perfectly on phones! The interface automatically adapts:

**On Mobile:**
- ✅ Full-size camera feed
- ✅ All controls (Pan, Zoom if supported)
- ✅ Motion alerts
- ✅ Settings & configuration
- ✅ Battery & storage status

**Tips for Mobile:**
- Rotate phone to **landscape** for larger camera view
- Tap camera feed to **fullscreen**
- Use **browser bookmarks** for quick access
- Create **home screen shortcut** (see "Bookmarking" above)

### Tablet (iPad/Android Tablet)

**Best experience!** Tablets show the full desktop layout:

- Large camera feed
- Side panel with status
- All controls easily accessible
- Perfect for mounting on wall

**iPad Recommendation:**
- Use **Safari** for best performance
- Enable **landscape mode** for side-by-side layout
- Create home screen app shortcut for instant access

### Offline Mobile Access (Local Network Only)

✅ **Your phone must be on the same WiFi network as the camera**

- No internet required
- Ultra-fast response time
- Secure (stays on your local network)

---

## Configuration Guide

### Basic Settings

**Device Name:**
- Used to identify your camera
- Example: "Kitchen", "Front Door", "Garage"
- Visible in browser title and interface

**Device Location:**
- Where the camera is placed
- Used for organizing multiple devices

**Emergency Phone:**
- Phone number for SMS alerts (if enabled)
- Used only if motion detected & SMS configured

### Storage Settings

**Keep Videos For (Days):**
- How long to store recorded videos
- Default: **7 days**
- Older videos automatically deleted
- Adjust based on your storage needs:
  - **3 days** = save space
  - **7 days** = balanced
  - **14 days** = keep longer history
  - **30+ days** = maximum retention

### Motion Detection

**Motion Recording:**
- ✅ **ON** = record when motion detected
- ⚫ **OFF** = never record

**Motion Threshold:**
- **Low (0.1)** = very sensitive, records often
- **Medium (0.5)** = balanced (recommended)
- **High (0.9)** = only major motion triggers

### Nanny Cam Mode

- ⚫ **OFF** = normal mode (recording enabled)
- ✅ **ON** = view-only mode (no recording)

---

## Features Overview

### Live Camera Feed

**View:**
- Real-time video stream from camera
- Updates continuously
- Click to fullscreen (phones: landscape mode)

**Recording:**
- Automatic when motion detected
- Manual recording available in settings
- Videos saved to local storage

### Battery Status

**Shows:**
- Current charge level (%)
- Runtime remaining (hours:minutes)
- Charge status (charging/discharging)

**Green bar** = healthy battery  
**Yellow bar** = medium charge  
**Red bar** = low battery (plug in soon!)

### Storage Information

**Displays:**
- **Used Space** = videos currently stored
- **Free Space** = available storage
- **Total Space** = SD card size

**When storage is full:**
- Oldest videos automatically deleted
- New recordings saved
- No action needed

### System Information

**Shows:**
- Device model (e.g., "Raspberry Pi Zero 2W")
- RAM memory (512MB)
- Software version (2.1-LITE)
- Security status

### Motion Events

**Last 24 Hours:**
- Count of motion detection events
- Timestamps of recordings
- Video clips available to view/download

---

## Troubleshooting

### Camera Not Loading

**Problem:** Black screen, "Camera Unavailable"

**Solutions:**
1. **Wait 10 seconds** - first boot takes time
2. **Refresh browser** (F5 or Ctrl+R)
3. **Check camera lens** - clean with soft cloth
4. **Reboot device:**
   - Unplug power cable
   - Wait 10 seconds
   - Plug back in
   - Wait 1 minute for boot

### Can't Connect to Device

**Problem:** "Cannot reach server" or connection timeout

**Solutions:**
1. **Verify IP address:**
   - Check router for device connected devices
   - Use IP found in DHCP list
2. **Check WiFi:**
   - Phone/computer must be on **same network** as camera
   - Look for green light on device (connected)
3. **Restart router:**
   - Power off router
   - Wait 30 seconds
   - Power back on
   - Wait 1 minute
4. **Use Ethernet (if available):**
   - Plug network cable into device
   - Direct connection bypasses WiFi issues

### Slow Performance / Buffering

**Problem:** Video feed stutters or loads slowly

**Solutions:**
1. **Check WiFi signal:**
   - Move camera/router closer
   - Reduce obstacles between devices
2. **Reduce video quality:**
   - Go to Settings → Video Quality
   - Lower resolution (360p instead of 720p)
3. **Close other apps:**
   - Don't stream on multiple devices simultaneously
4. **Restart device:**
   - Unplug and re-plug power

### Login Issues

**Problem:** Can't login, forgotten password

**Solutions:**
1. **Default credentials:**
   - Username: `admin`
   - Password: `admin123`
2. **Reset to defaults:**
   - Power off device
   - Press and hold reset button (if available)
   - Power on
   - Wait 1 minute
   - Try default credentials
3. **Contact support:** support@mangiafesto-electronics.com

### No Motion Detected

**Problem:** Motion detection not working

**Solutions:**
1. **Check if enabled:**
   - Go to Settings → Motion Detection
   - Ensure "Motion Recording" is ✅ ON
2. **Adjust threshold:**
   - Try lower threshold (more sensitive)
   - Test by moving in front of camera
3. **Check lighting:**
   - Motion works best in well-lit areas
   - Very dark rooms may not detect
4. **Restart:**
   - Unplug and re-plug device

### Storage Full

**Problem:** Can't record new videos

**Solutions:**
1. **Videos auto-delete:**
   - Old videos automatically removed based on retention setting
   - Wait a few minutes
2. **Speed up deletion:**
   - Go to Settings → Storage
   - Lower "Keep Videos For" to 3 days
   - Old videos will delete faster
3. **Check storage:**
   - View Storage section on dashboard
   - If 100% full, restart device

---

## Security & Safety

### Important Security Notes

✅ **DO:**
- Change default password immediately (Settings → Change Password)
- Keep device on your private network
- Update firmware when notified
- Use HTTPS when available
- Keep default login credentials private

❌ **DON'T:**
- Share your IP address publicly
- Use weak/simple passwords
- Leave default credentials unchanged
- Expose camera to direct rain/weather
- Disable security features

### Privacy Considerations

- **Local storage only** - videos not uploaded to cloud (unless you configure it)
- **Encrypted connection** - option available in settings
- **No tracking** - we don't monitor your camera feeds
- **Full control** - you decide what's recorded and when

### Physical Safety

- **Placement:**
  - Mount out of reach of children
  - Avoid direct sunlight for lens
  - Protect from rain/humidity
  - Ensure proper ventilation

- **Power:**
  - Use provided power supply only
  - Don't modify cables
  - Keep power adapter dry

- **Network:**
  - Connect to your personal WiFi only
  - Don't share WiFi password with untrusted parties

---

## Warranty & Support

### Limited Warranty

Your ME_CAM device includes:
- **1 Year** hardware warranty
- **Coverage:** Manufacturing defects
- **Not covered:** Physical damage, water damage, misuse

### Technical Support

**Email:** support@mangiafesto-electronics.com  
**Response time:** 24-48 hours  
**Include:**
- Device serial number
- Problem description
- What you've tried already
- Screenshots/photos if helpful

### Common Support Questions

**Q: Can I view multiple cameras?**
A: Yes, with setup instructions provided. See "Multi-Device Setup" guide.

**Q: Is there a mobile app?**
A: Not needed! The web interface works perfectly on all phones/tablets.

**Q: Can I use this without WiFi?**
A: Yes, via Ethernet cable connection (if available).

**Q: What if I forget my password?**
A: Contact support or perform factory reset (press reset button 5+ seconds).

**Q: Can I backup my videos?**
A: Yes, download from "Events" page or configure cloud backup.

---

## Advanced: Multi-Device Setup

If you have multiple ME_CAM devices:

1. **Set unique names** for each device
2. **Note each IP address:**
   - Device 1: `http://10.2.1.7:8080`
   - Device 2: `http://10.2.1.8:8080` (example)
3. **Create bookmarks** for each in your browser
4. **Switch between them** using tabs

---

## Quick Reference Card

**Cut and keep this for quick reference!**

```
═══════════════════════════════════════════
        ME_CAM QUICK REFERENCE
═══════════════════════════════════════════

📱 WEB ACCESS:
   http://10.2.1.7:8080
   (or your device IP)

🔑 DEFAULT LOGIN:
   Username: admin
   Password: admin123

⚙️ FIRST TIME:
   1. Power on device
   2. Open browser to IP
   3. Click Setup
   4. Configure settings

📱 MOBILE:
   Same URL works on phone!
   Tap camera feed to fullscreen
   Rotate to landscape for best view

🔋 BATTERY:
   Green = good
   Yellow = okay
   Red = charge soon

💾 STORAGE:
   Auto-deletes old videos
   Based on retention setting

🔄 RESTART DEVICE:
   Unplug 10 sec, plug back in
   Wait 1 minute to boot

📧 SUPPORT:
   support@mangiafesto-electronics.com

═══════════════════════════════════════════
```

---

## Feedback & Updates

We're constantly improving ME_CAM!

**Have feedback?** Let us know at support@mangiafesto-electronics.com

**New features coming:**
- Enhanced motion detection
- Cloud backup integration
- Multi-camera unified dashboard
- Advanced alerts & notifications

**Stay updated:** Check this manual periodically for updates.

---

**Last Updated:** January 25, 2026  
**Document Version:** 2.1.0  
© 2026 Mangiafesto Electronics LLC. All rights reserved.
