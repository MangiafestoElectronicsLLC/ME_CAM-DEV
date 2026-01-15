# ME CAMERA - IMMEDIATE ACTION REQUIRED

## Your Current Issues & How to Fix Them

### Issue #1: Battery Showing 50% Instead of 100% ✅
**FIXED** - But you must verify:
1. Go to http://10.2.1.47:8080/dashboard
2. Look at top right - battery should now show "🔋 100%"  
3. Should update every 5 seconds
4. If still wrong, check config has no `battery_percent_override`

### Issue #2: Navbar Missing Devices Link ✅  
**FIXED** - Your navbar should now show:
```
📹 DEV  |  Dashboard  |  📡 Devices  |  ⚙️ Settings  |  👤 Profile  |  Logout
```
Click "📡 Devices" to see multicam page

### Issue #3: Multicam Only Shows 1 Device ⚠️ NEEDS YOUR ACTION
The API shows 2 devices but the page only displays 1.

**Temporary Fix**: Refresh browser (Ctrl+F5)

**Permanent Fix**: Check your config.json - make sure BOTH devices have correct format:
```json
"devices": [
  {"id": "current", "name": "DEV", "ip": "10.2.1.47", "battery": 100},
  {"id": "pi-3bp", "name": "Back Door", "ip": "10.2.1.48", "battery": 75}
]
```

### Issue #4: Edit/Remove Device Buttons Don't Work ⚠️ KNOWN LIMITATION
These features are template placeholders but backend API works.

**Current**: Can add devices via "➕ Add Device" button
**Needed**: Implement edit/remove UI (scheduled for next phase)

### Issue #5: Camera Display Broken - THIS IS CRITICAL ⚠️ URGENT
**Root Cause**: Legacy camera might not be disabled

**MUST DO THIS:**
```bash
ssh pi@10.2.1.47
sudo raspi-config
# Choose: Interface Options → Legacy Camera → Disable
# Reboot when prompted
```

After reboot, camera should either:
- ✅ Show live stream (if hardware working)
- ✅ Show TEST MODE demo (if camera not detected)
- ❌ Show black screen (problem - needs fixing)

### Issue #6: HTTPS / me_cam.com Access
**Current State**: HTTP only on port 8080

**To Enable HTTPS:**
1. Windows (as Admin):
   ```powershell
   Add-Content -Path "C:\Windows\System32\drivers\etc\hosts" -Value "`n10.2.1.47   me_cam.com" -Force
   ```
2. Then access: `https://me_cam.com:8080`
3. Click through certificate warning (self-signed is normal)

**Why the warning?** Self-signed cert is intentional for local development. 
Remove warning by installing cert on your computer (optional).

### Issue #7: Device IP Address Per Device
**Current**: Config stores IP but not displayed in UI

**Example Config**:
```json
{
  "id": "10.2.1.48",
  "name": "Back Door",
  "ip": "10.2.1.48",  ← This is stored
  "location": "Back Door",
  "battery": 75,
  "status": "online"
}
```

**To Display in UI**: Click on device card in multicam page - should show location + IP

---

## Quick Test Checklist (Do These Now)

```bash
# 1. Can you see the navbar with "📡 Devices" link?
#    Answer: YES / NO

# 2. Does battery show "🔋 100%" in top right?
#    Answer: YES / NO  

# 3. Can you see 2 devices when you click Devices?
#    Answer: YES / NO / ONLY SHOWS 1

# 4. Does the camera display show something (test image or real feed)?
#    Answer: YES / NO / BLACK SCREEN

# 5. Can you add a new device?
#    Answer: YES / NO

# 6. Can you click Edit on a device?
#    Answer: YES / NO / BUTTON DOES NOTHING
```

---

## If Camera Still Broken After Raspi-Config

**Emergency Test:**
```bash
ssh pi@10.2.1.47
# Check if legacy camera is REALLY disabled:
cat /boot/firmware/config.txt | grep camera
# Should NOT show: start_x=1

# Test camera detection:
libcamera-hello --list-cameras
# Should show: Camera 0 : imx708 [... (working)
# OR: No cameras found (device not detected - needs troubleshooting)
```

---

## Your Battery Issue Explanation

**Pi Zero 2W doesn't have a battery HAT**. The battery monitor uses:
- `vcgencmd get_throttled` command
- Checks for undervolt condition
- Returns: 100% (healthy power), 0% (underwolt detected)

If showing 50%, there's a config override. To clear it:
```bash
ssh pi@10.2.1.47
cd ~/ME_CAM-DEV
sed -i '/battery_percent_override/d' config/config.json
sudo systemctl restart mecamera
```

---

## Multi-Device Setup Example

If you have **2 Raspberry Pi cameras**:

**Pi Zero 2W (Primary - 10.2.1.47)**:
```
- Name: DEV
- IP: 10.2.1.47
- Status: ONLINE
- Camera: TEST MODE (RAM limitation)
- Battery: 100% (USB Power)
```

**Pi 3B+ (Secondary - 10.2.1.48)**:
```
- Name: Back Door  
- IP: 10.2.1.48
- Status: ONLINE
- Camera: LIVE STREAM (1GB RAM available)
- Battery: ~75% (if USB powered)
```

**To Add Second Device**:
1. Click "➕ Add Device" on multicam page
2. Enter IP: `10.2.1.48`
3. Enter Name: `Back Door`
4. Enter Location: `Back Door`
5. Click "Add Device"
6. Refresh page - should now show both

---

## File Changes Made Today

| File | Change | Status |
|------|--------|--------|
| user_dashboard.html | Added "📡 Devices" navbar link | ✅ Live |
| user_dashboard.html | Fixed battery pill display (ID-based) | ✅ Live |
| battery_monitor.py | Correct calculation (no changes needed) | ✅ Working |
| api/devices | Returns all devices | ✅ Working |
| nginx-me-camera.conf | HTTPS ready | ✅ Ready |

---

## Next Phase (Not Urgent)

1. **Edit Device Button**: Implement in multicam.html
2. **Remove Device Button**: Implement delete function  
3. **Device Status Polling**: Auto-refresh device list
4. **IP Per Device Display**: Show IP address on device cards
5. **Certificate Installation**: Remove HTTPS warning

---

## Need Help? Check These Files

- **Setup**: See SETUP_GUIDE.md
- **Troubleshooting**: See notes.txt  
- **Hardware**: See HARDWARE_GUIDE.md
- **All Fixes**: See CRITICAL_FIXES_JAN15.md

---

**Service Running**: ✅ ACTIVE at 10.2.1.47:8080  
**Last Deploy**: January 15, 2026 14:41:39 GMT  
**Status**: AWAITING YOUR ACTION ON CAMERA LEGACY CONFIG

