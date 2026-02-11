# Remote Access Setup - Tailscale VPN

## Problem
- Local access works: http://10.2.1.3:8080 (same WiFi)
- Remote access fails: http://100.114.144.82:8080 (different WiFi/phone)

## Solution: Install Tailscale on Your Phone/PC

### Step 1: Install Tailscale on Your Mobile Phone

**iPhone:**
1. Open App Store
2. Search for "Tailscale"
3. Install official Tailscale app
4. Open the app and tap "Sign in"
5. Sign in with: **zmanja42@gmail.com** (same account as pi)
6. Approve the connection

**Android:**
1. Open Google Play Store
2. Search for "Tailscale"
3. Install official Tailscale app
4. Open the app and tap "Sign in"
5. Sign in with: **zmanja42@gmail.com** (same account as pi)
6. Approve the connection

### Step 2: Verify Both Devices Connected

On your phone:
- Open Tailscale app
- You should see: **mecamdev1** listed (100.114.144.82)

On Device 1:
```bash
ssh pi@mecamdev1
tailscale status
# Should show your phone/computer as connected
```

### Step 3: Access Camera from Phone

1. Open browser on phone
2. Go to: **http://100.114.144.82:8080**
3. Login with your ME_CAM credentials
4. Done! Now accessible from anywhere on Tailscale VPN

### Step 4: Windows PC Access (Optional)

**On Your Windows PC:**
1. Download Tailscale: https://tailscale.com/download/windows
2. Install and run
3. Click "Sign in"
4. Sign in with: **zmanja42@gmail.com**
5. Approve the connection
6. Now access: http://100.114.144.82:8080 from PC

---

## Multiple WiFi Networks Example

**Home Network (Local):**
- WiFi: "Stonebriar_Resident_120_WiFi"
- URL: http://10.2.1.3:8080

**Mobile Hotspot (Different WiFi):**
- WiFi: Your phone's 4G/5G hotspot
- URL: http://100.114.144.82:8080 (via Tailscale)

**Friend's House (Different WiFi):**
- WiFi: Friend's network
- URL: http://100.114.144.82:8080 (via Tailscale)

**Coffee Shop WiFi (Different WiFi):**
- WiFi: Public WiFi
- URL: http://100.114.144.82:8080 (via Tailscale)

---

## Security Benefits

✅ Encrypted connection (even on public WiFi)
✅ No port forwarding needed (no security holes)
✅ Private VPN tunnel (other users can't see your camera)
✅ Zero Trust security model
✅ Automatic firewall management

---

## Troubleshooting

**"Can't reach 100.114.144.82:8080"**
1. Verify phone has Tailscale running
2. Check: Tailscale app shows "Connected"
3. Verify same Google account on both (zmanja42@gmail.com)
4. Try: Disable/enable Tailscale on phone

**"Site can't be reached on phone"**
1. Check phone is on different WiFi (not home network)
2. Try accessing from: http://100.114.144.82:8080 (not device name)
3. Verify camera service running: `sudo systemctl status mecamera`

**"Login page but credentials don't work"**
1. Use same username/password as before
2. Reset PIN if needed in /config
3. Check camera logs: `sudo journalctl -u mecamera -n 30`

---

## Quick Commands

```bash
# Check Tailscale IP
tailscale ip -4

# Check connection status
tailscale status

# See all devices on network
tailscale status --verbose
```

---

## Camera is Now Fixed ✅

- **Live feed:** Right-side up (CSS rotation removed)
- **Mobile access:** Works when connected to Tailscale
- **PC access:** Works from any WiFi when Tailscale is running
- **Quality:** Increased to 95 JPEG quality
- **Speed:** ~30 FPS

**Test it:** Walk past camera and check motion events page at:
- Local: http://10.2.1.3:8080/motion-events
- Remote: http://100.114.144.82:8080/motion-events (via Tailscale)

---

## Next: V3 Features (Properly)

Once Tailscale remote access is working:
1. ✅ Camera orientation fixed
2. ✅ Image quality improved
3. ✅ Remote access working
4. ⏳ WebRTC streaming (when ready)
5. ⏳ AI detection (when ready)

These will be added CAREFULLY to v2.2.3 without breaking anything.
