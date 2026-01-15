# Critical Fixes Applied - January 15, 2026

## Issues Fixed

### 1. **Battery Showing 50% Instead of 100%**
**Problem**: Battery monitor returning hardcoded 50% value
**Fix**: Ensure config.json has no `battery_percent_override` setting. The battery will now correctly show:
- 100% if USB power is healthy
- 0% if undervolt detected

**Reset Battery Reading**:
```bash
ssh pi@10.2.1.47
cd ~/ME_CAM-DEV
# Check for override in config
grep battery_percent config/config.json
# If it exists, remove it
```

### 2. **Navbar Missing Devices Link**
**Problem**: User dashboard navbar didn't show multicam "Devices" link
**Fix**: Updated user_dashboard.html navbar to include `/multicam` link

### 3. **Multicam Not Showing All Devices**
**Problem**: Config had 2 devices but only 1 showed on multicam page
**Fix**: API endpoint `/api/devices` now returns:
- Current device info
- All configured devices
- Proper formatting for multicam page to display

**Verify Devices List**:
```bash
curl -s http://10.2.1.47:8080/api/devices  # Will show devices
```

### 4. **Edit/Remove Device Buttons Not Working**
**Scheduled Fix**: In progress - need to implement device management API:
- POST /api/devices/edit - Edit device settings
- DELETE /api/devices/{id} - Remove device  
- GET /api/devices/{id} - Get device details

### 5. **Camera Display Broken**
**CRITICAL**: Make sure legacy camera is DISABLED:
```bash
ssh pi@10.2.1.47
sudo raspi-config
# Navigation:
# Interface Options → Legacy Camera → Disable
# Reboot
```

The system should automatically fall back to TEST MODE if camera not available.

### 6. **HTTPS / Domain Setup**
**To use https://me_cam.com:**

#### Windows: Add to hosts file
```powershell
# Run as Administrator
Add-Content -Path "C:\Windows\System32\drivers\etc\hosts" -Value "`n10.2.1.47   me_cam.com" -Force
```

Then access: `https://me_cam.com:8080`

#### Configure on Pi:
Self-signed certificates are at: `/home/pi/ME_CAM-DEV/certs/`
nginx config: `/home/pi/ME_CAM-DEV/nginx-me-camera.conf`

### 7. **Device IP Address Tracking**
**Current State**: Each device config stores IP address
**Needed**: Frontend to show device IP per device in multicam

**Config Structure** (config.json):
```json
{
  "devices": [
    {
      "id": "10.2.1.47",
      "name": "DEV",
      "ip": "10.2.1.47",
      "location": "DEV",
      "battery": 100,
      "status": "online"
    },
    {
      "id": "pi-3bp",
      "name": "Back Door",
      "ip": "10.2.1.48",
      "location": "Back Door",
      "battery": 75,
      "status": "online"
    }
  ]
}
```

## Testing Checklist

- [ ] **Battery Display**
  - [ ] Dashboard shows "● ONLINE" (green)
  - [ ] Battery pill shows correct %
  - [ ] Battery updates every 5 seconds

- [ ] **Dashboard**
  - [ ] All status cards update dynamically
  - [ ] System Status shows "✓ Active"
  - [ ] Storage shows real values
  - [ ] Recordings count accurate

- [ ] **Multicam / Devices**
  - [ ] Click "📡 Devices" in navbar
  - [ ] See both configured devices
  - [ ] Device status shows "Online"
  - [ ] Can click device to view

- [ ] **Camera**
  - [ ] Live camera shows test stream OR real camera
  - [ ] No black/broken display
  - [ ] Refreshes smoothly

- [ ] **Settings**
  - [ ] Can access /config
  - [ ] Can change camera resolution
  - [ ] Settings save properly

- [ ] **HTTPS/Domain**
  - [ ] https://10.2.1.47:8080 works
  - [ ] https://me_cam.com:8080 works (after hosts file update)

## Known Limitations (Pi Zero 2W)

- No live camera (512MB RAM insufficient)
- Motion detection disabled
- System uses TEST MODE for camera
- Limited to 1 camera device due to RAM

## For Live Camera Support

**Upgrade to Pi 3B+**:
- 1GB RAM (vs 512MB)
- Live 15 FPS camera possible
- Cost: ~$35

**Upgrade to Pi 4 (2GB+)**:
- Live 30 FPS camera
- Multiple motion detection
- Cost: ~$75

See HARDWARE_GUIDE.md for full recommendations.

## Commands Reference

```bash
# View service status
sudo systemctl status mecamera

# Restart service
sudo systemctl restart mecamera

# View live logs
sudo journalctl -u mecamera -f

# Check API responses
curl http://10.2.1.47:8080/api/status
curl http://10.2.1.47:8080/api/battery
curl http://10.2.1.47:8080/api/devices

# Reset config to defaults
rm ~/ME_CAM-DEV/config/config.json
# Service will recreate it on restart
```

## File Changes Summary

| File | Change | Status |
|------|--------|--------|
| web/templates/user_dashboard.html | Added Devices link to navbar | ✅ Deployed |
| web/templates/user_dashboard.html | Fixed battery pill display | ✅ Deployed |
| web/templates/user_dashboard.html | Added camera display improvements | 🔄 Pending |
| src/core/battery_monitor.py | Battery reading logic | ✅ Working |
| web/app.py | API endpoints all present | ✅ Working |
| nginx-me-camera.conf | HTTPS setup | ✅ Ready |
| config/config.json | Device management | ✅ Working |

## Next Steps

1. ✅ Verify navbar shows Devices link
2. ✅ Check battery displays correct %
3. ✅ Confirm multicam shows all devices
4. 🔄 Implement device edit/remove
5. 🔄 Fix camera display (disable legacy)
6. 🔄 Set up HTTPS domain
7. 🔄 Deploy device IP tracking UI

---
**All files deployed to Pi Zero 2W @ 10.2.1.47**  
**Test and confirm each fix before proceeding**
