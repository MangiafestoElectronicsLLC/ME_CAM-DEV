# ME_CAM V3.0 - CUSTOMER QUICK START GUIDE

**For:** First-time users and homeowners  
**Version:** 3.0.0 | **Time to Setup:** 15 minutes  
**Last Updated:** March 19, 2026

---

## 🎉 WELCOME TO ME_CAM

Your ME_CAM device is a **professional-grade home security camera system** that works completely locally—no cloud subscriptions, no data breaches, full privacy.

This guide will get you up and running in **15 minutes**.

---

## 📋 WHAT YOU RECEIVED

- ✅ Raspberry Pi with ME_CAM software (pre-installed)
- ✅ Pre-configured for your WiFi and password
- ✅ Ready to use out of the box
- ✅ All security features enabled

---

## 🚀 5-MINUTE QUICK START

### Step 1: Power On (1 minute)

1. Plug the USB-C power adapter into your camera
2. Wait **60 seconds** for the device to boot
3. Look for the green LED to stop blinking (steady on)

### Step 2: Access the Dashboard (1 minute)

Open a web browser on your phone, tablet, or computer:

**Option A: Using the device hostname**
```
http://YOUR_DEVICE_HOSTNAME:8080
```
(Your technician gave you the hostname, e.g., `mecamdev1`)

**Option B: Using the IP address**
```
http://192.168.X.X:8080
```
(Or whatever IP your technician provided)

### Step 3: View Your Camera (1 minute)

1. Enter the password your technician provided
2. Click **"Live Stream"** 
3. **You're watching your camera in real-time!**

---

## 📊 DASHBOARD FEATURES

### Live Video
- **Real-time feed** from your camera
- **Record clips** manually or automatically
- **Save snapshots** to your device
- **Night vision** (if IR camera)

### Battery Status
Shows:
- **Current charge %** (e.g., "85%")
- **Power source** (Wall Power / USB Adapter / Battery Pack)
- **Estimated runtime** (e.g., "11 hours")
- **Power mode** (Normal/Medium/Low/Critical)

### Motion Detection
- **Automatic motion recording** with timestamps
- **Video clips** saved locally (encrypted)
- **Export quick video summaries** from today
- **Motion alerts** (if enabled)

### Settings Panel
- **Change password** for security
- **WiFi reconect** if needed
- **Camera brightness/contrast** adjustments
- **Video quality settings** (auto-scales for power)
- **Recording preferences**

---

## 🔋 POWER & BATTERY GUIDE

### Understanding Power Modes

Your camera **automatically adjusts** video quality based on remaining battery:

| Battery | Mode | Quality | FPS | Runtime |
|---------|------|---------|-----|---------|
| 🔴 <10% | Critical | 40% | 15 | ~2 hours |
| 🟠 10-25% | Low | 50% | 20 | ~4 hours |
| 🟡 25-50% | Medium | 70% | 30 | ~7 hours |
| 🟢 50%+ | Normal | 85% | 40 | ~11 hours |

> **What does this mean?** As your battery drains, the camera automatically reduces quality to save power. This extends runtime by 30-50%!

### Charging Tips

**Wall Power** (Best)
- Plug in permanently for 24/7 recording
- No power limitations, full quality
- Green power LED indicator

**External Battery Pack** (Good)
- Supports 8-12 hours of operation
- Portable for outdoor placement
- Use 10,000 mAh or larger

**USB Adapter** (Emergency)
- Works with any USB-C charger
- Great for travel or testing
- Slower charge than wall power

---

## 🔒 SECURITY & PRIVACY

### Your Data is Local
- ✅ All video **stays on the device**
- ✅ **No cloud** servers
- ✅ **No subscription** fees
- ✅ **You control** everything

### Security Features Enabled
- 🔐 **HTTPS encryption** for all connections
- 🔐 **AES-256 encryption** for video at rest
- 🔐 **Strong password protection**
- 🔐 **Rate limiting** against brute-force attacks

### Change Your Password

1. Open dashboard → **Settings**
2. Click **"Change Password"**
3. Enter current password, then new password (8+ characters)
4. Click **"Save"**

**Important:** Use a strong password with:
- Uppercase letters (A-Z)
- Lowercase letters (a-z)  
- Numbers (0-9)
- Special characters (!@#$%)

---

## 📱 MOBILE ACCESS

### View on Your Phone

**From same WiFi network:**
```
http://YOUR_HOSTNAME:8080
```

**From outside your home (Optional Setup):**
Requires manual port forwarding or VPN setup. Contact support if you need help.

## ⚙️ COMMON SETTINGS

### Change Video Quality

1. Open dashboard → **Settings**
2. **Video Quality:** Auto (recommended) / 480p / 720p / 1080p
3. **Frame Rate:** Auto / 15fps / 30fps / 60fps
4. Click **"Save"**

> **Tip:** "Auto" mode uses the intelligent power-saving system

### Enable/Disable Motion Recording

1. Open **Settings** → **Recording**
2. Toggle **"Motion Detection"** on/off
3. Set **"Sensitivity"** (Low / Medium / High)
4. Click **"Save"**

### View Recorded Clips

1. Click **"Video Library"** 
2. Choose date and time range
3. Clips appear automatically (organized by motion events)
4. Click clip to play or download

---

## 🆘 QUICK TROUBLESHOOTING

### Camera shows "No Signal"

**Try this:**
1. Check power cable is plugged in
2. Confirm green LED is on
3. Try reloading the page (refresh browser)
4. Wait 30 seconds and try again

**Still not working?**
```
Your camera may need a restart. Contact support.
```

### Can't access dashboard

**Try this:**
1. Check device is powered on (green LED)
2. Confirm WiFi is working (other devices connected?)
3. Check device hostname is correct (ask technician)
4. Try using IP address instead of hostname
5. Refresh browser (Ctrl+R or Cmd+R)

**Still stuck?**
```
Clear your browser cache:
- Chrome: Ctrl+Shift+Delete (Settings → Privacy)
- Safari: Preferences → Privacy → Manage Website Data
Then reload page.
```

### Video is very pixelated

**Normal reasons:**
- Low internet/WiFi speed
- Device on battery (power-saving mode enabled)
- Low light conditions

**To improve:**
1. Move closer to WiFi router
2. Plug into wall power
3. Check WiFi signal strength (Settings → Network)
4. Increase video quality in Settings

### Device appears offline

**Check:**
1. Is WiFi router on?
2. Is camera powered on? (Check LED)
3. Is camera connected to your WiFi? (Ask technician)

**To reconnect:**
1. Power off camera (unplug for 10 seconds)
2. Power back on (wait 60 seconds for boot)
3. Check LED turns green

---

## 📞 GETTING HELP

### Error Messages

| Message | Meaning | Fix |
|---------|---------|-----|
| "Connection Refused" | Device offline | Power on / check WiFi |
| "Authentication Failed" | Wrong password | Check CAPS LOCK / reset password |
| "Timeout Error" | Device not responding | Restart camera / wait 2 min |
| "Encryption Error" | Security issue | Contact support |

### Before Contacting Support

Provide:
1. Device hostname (e.g., `mecamdev1`)
2. What were you doing when error occurred?
3. Any error messages shown?
4. Screenshot of error (if possible)

### Contact Information

**Support Email:** [your-email@domain.com]  
**Support Phone:** [your-phone-number]  
**GitHub Issues:** https://github.com/YOUR_USERNAME/ME_CAM/issues  
**Response Time:** 24-48 hours

---

## 💡 PRO TIPS

### Tip 1: Place Camera Strategically
- **Wide view:** Front door, driveway, backyard
- **Close-up:** Package area, window
- **Multiple angles:** Use multiple cameras (add more devices)

### Tip 2: Power Management
- **Wall power:** Best for 24/7 coverage
- **Battery:** Good for portable/outdoor use
- **Check battery:** Monitor dashboard daily

### Tip 3: Storage Management
- **Video clips:** Keep auto-recorded clips (local storage)
- **Manual exports:** Download important clips regularly
- **Manage disk space:** Older clips auto-delete (30-day default)

### Tip 4: Security
- **Change default password** first thing
- **Use strong password** (uppercase, numbers, special chars)
- **Keep WiFi secure** (WPA3 recommended)
- **Monitor access logs** (in Settings)

---

## 📚 FEATURES EXPLAINED

### What is "Power-Saving Mode"?

Your camera automatically adjusts quality based on battery level. Less battery = lower quality = longer runtime.

**Example:**
- Normal (80% battery): 85% quality, 11 hours runtime
- Low (15% battery): 50% quality, 4 hours runtime
- Critical (5% battery): 40% quality, 2 hours runtime

This means you get **longer battery life** automatically!

### What is "Local Storage"?

Videos are saved **on the device itself**—not in the cloud.

**Benefits:**
- ✅ No monthly fees
- ✅ Complete privacy
- ✅ Works without internet
- ✅ Video never leaves your home

**Note:** Device has 32GB-64GB storage (typical 7-30 days of video)

### What is "HTTPS Encryption"?

Secure connection (like banking websites). Your password and video stream are **encrypted in transit**.

🔒 **Secure:** `https://mecamdev1.local:8443`  
⚠️ **Basic:** `http://mecamdev1.local:8080`

> **Note:** HTTPS shows a "security warning" because the certificate is self-signed (this is normal and secure)

---

## 🔄 KEEPING YOUR CAMERA UPDATED

### Automatic Updates (Recommended)

Your device checks for updates automatically. Updates include:
- Security patches
- Performance improvements
- New features

To enable auto-updates:
1. Open **Settings** → **System**
2. Toggle **"Auto Update"** ON
3. Updates install at **3 AM** (when camera is less active)

---

## 🎓 LEARNING MORE

### Full Documentation
Visit: https://github.com/YOUR_USERNAME/ME_CAM

### Video Tutorials
- Setup Guide: [YouTube link]
- Feature Overview: [YouTube link]
- Troubleshooting: [YouTube link]

### Community Forum
- Ask questions: [Community link]
- Share setups: [Forum link]
- Report bugs: [GitHub issues link]

---

## ⭐ TELL US WHAT YOU THINK

We'd love your feedback!

- **Loving ME_CAM?** Give us a ⭐ on GitHub
- **Found a bug?** Report it in Issues
- **Have an idea?** Submit a feature request
- **Want to help?** Contribute code on GitHub

---

## 🙏 THANK YOU

Thank you for choosing ME_CAM! We're committed to providing you with a professional, private, and open-source security camera system.

**Enjoy worry-free local video surveillance!**

---

**Version:** 3.0.0  
**Updated:** March 19, 2026  
**License:** Open Source (MIT)

For latest documentation, visit: https://github.com/YOUR_USERNAME/ME_CAM
