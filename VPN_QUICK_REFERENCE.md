# 🌐 VPN Quick Reference - ME_CAM Access Guide
**Print this page or save to your phone!**

---

## ✅ VPN Access URLs

| Location | URL | VPN Needed |
|----------|-----|-----------|
| Home WiFi | `https://me_cam.com:8080` | ❌ No |
| Mobile Hotspot | `https://me_cam.com:8080` | ✅ Yes |
| Public WiFi | `https://me_cam.com:8080` | ✅ Yes |
| Work/School | `https://me_cam.com:8080` | ✅ Yes |
| IP Address | `https://192.168.1.XX:8080` | Optional |

---

## 🚀 Quick Start (3 Steps)

### Step 1: Connect VPN
- Open your VPN app
- Choose a server
- Connect

### Step 2: Open Browser
- Open Safari, Chrome, or Firefox
- Go to: `https://me_cam.com:8080`

### Step 3: Login & Enjoy
- Username: admin
- Password: admin123 (or your custom password)
- View camera feed
- Check motion events

---

## 📱 Mobile Setup

### iPhone (iOS)
1. Open VPN app → Connect
2. Open Safari
3. Visit: `https://me_cam.com:8080`
4. Tap "Continue" on security warning

### Android
1. Open VPN app → Connect
2. Open Chrome
3. Visit: `https://me_cam.com:8080`
4. Tap "Advanced" → "Proceed anyway"

### Web App Installation (iOS)
1. Open Safari at `https://me_cam.com:8080`
2. Tap Share → "Add to Home Screen"
3. Tap "Add"
4. Now you have an app icon!

---

## 🔒 Security Reminder

✅ **Always use:** `https://` (not http://)  
✅ **Always enable:** VPN on public WiFi  
✅ **Always login:** Even over VPN  
✅ **Never share:** Your password

---

## 🐛 Troubleshooting

### "Can't connect"
→ Check VPN is enabled  
→ Try different VPN server location  
→ Restart VPN app

### "Certificate warning"
→ This is normal (self-signed cert)  
→ Tap "Advanced" → "Proceed"  
→ Or use IP if available

### "Page won't load"
→ Try: Force refresh (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)  
→ Clear browser cache  
→ Try different browser

### "Slow speed"
→ VPN reduces speed slightly (normal)  
→ Try closer VPN server  
→ Switch from WiFi to mobile hotspot

---

## 🎯 Access Points

**Best for:** Home  
→ `https://me_cam.com:8080`  
(fastest, local network)

**Best for:** Away from home  
→ `https://me_cam.com:8080` + VPN  
(secure, works everywhere)

**Best for:** Debugging  
→ SSH tunnel (see Advanced section)

---

## 💡 Pro Tips

**Tip 1**: Bookmark `https://me_cam.com:8080` in all browsers

**Tip 2**: Use iOS "Add to Home Screen" for app-like access

**Tip 3**: Check logs if you forget password:
```bash
ssh pi@mecamdev2.local 'grep -i auth logs/mecam_lite.log'
```

**Tip 4**: Multiple VPN providers = better redundancy

**Tip 5**: Wake device with ping if it sleeps:
```bash
ping -c 5 mecamdev2.local
```

---

## 📞 Support Commands

**Check if device is online:**
```bash
ping mecamdev2.local
```

**Check if service is running:**
```bash
ssh pi@mecamdev2.local 'sudo systemctl status mecamera'
```

**View recent logs:**
```bash
ssh pi@mecamdev2.local 'tail -30 logs/mecam_lite.log'
```

**Restart service:**
```bash
ssh pi@mecamdev2.local 'sudo systemctl restart mecamera'
```

---

## 🎉 Features Over VPN

✅ Live camera streaming  
✅ Motion detection & alerts  
✅ Video playback  
✅ Configuration changes  
✅ Emergency alerts  
✅ Storage management  

---

**Last Updated**: January 26, 2026  
**VPN Support**: ✅ Enabled  
**SSL/TLS**: ✅ Enabled  
**CORS Headers**: ✅ Enabled  

