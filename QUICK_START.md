# Quick Start: Deploy ME_CAM Fixes

## TL;DR - Deploy in 5 Minutes

```powershell
# 1. Open PowerShell in workspace
cd c:\Users\nickp\Downloads\ME_CAM-DEV\ME_CAM-DEV

# 2. Run deployment
.\DEPLOY_MANUAL_JAN26.ps1

# 3. Wait for service to start (~10 seconds)

# 4. Check dashboard
# Open: http://mecamdev2.local:5000

# 5. Verify fixes
# ✓ Camera image should be upright
# ✓ WiFi status card appears (top right)
# ✓ Motion detection logs events
```

---

## What Gets Fixed

| Issue | Fix | File | Status |
|-------|-----|------|--------|
| 🎥 Camera Upside Down | Add `--rotation 180` | `src/camera/rpicam_streamer.py` | ✅ Ready |
| 🚨 Motion Not Detecting | Fix frame_count logic | `web/app_lite.py` | ✅ Ready |
| 📡 No WiFi Status | Add API endpoints | `web/app_lite.py` | ✅ Ready |
| 🎨 No WiFi Widget | Add dashboard card | `web/templates/dashboard_lite.html` | ✅ Ready |

---

## If App Crashes After Deploy

```bash
# Check what's wrong
ssh pi@mecamdev2.local
cd ~/ME_CAM-DEV

# Look at error
tail -50 logs/mecam_lite.log | grep ERROR

# Or run manually to see error
python3 main_lite.py
```

**Then refer to:** `EMERGENCY_FIX_APP_CRASH.md`

---

## Expected Results

### Before Fix
- Camera image: Upside down ❌
- Motion detection: Not working ❌  
- WiFi display: None ❌
- API endpoints: Missing ❌

### After Fix
- Camera image: Upright ✅
- Motion detection: Logs events ✅
- WiFi display: Shows status ✅
- API endpoints: Working ✅

---

## Deployment Files

| File | Purpose | Run From |
|------|---------|----------|
| `DEPLOY_MANUAL_JAN26.ps1` | Main deployment script | PowerShell |
| `FIXES_STATUS_JAN26.md` | Complete fix documentation | Browser/Editor |
| `EMERGENCY_FIX_APP_CRASH.md` | If app crashes | Reference |
| `SESSION_SUMMARY_JAN26.md` | Full session details | Reference |

---

## One-Line Test Commands

```bash
# Test camera stream
curl -s http://mecamdev2.local:5000/camera | head -c 100 | file -

# Test WiFi API
curl http://mecamdev2.local:5000/api/network/wifi | python3 -m json.tool

# Check motion events
ssh pi@mecamdev2.local "grep 'Motion detected' ~/ME_CAM-DEV/logs/mecam_lite.log | tail -5"

# Check service status
ssh pi@mecamdev2.local "systemctl status mecamera --no-pager | head -10"
```

---

## Rollback (if needed)

```bash
ssh pi@mecamdev2.local
cd ~/ME_CAM-DEV

# Find backup
ls -la backup_*

# Restore
cp backup_<TIMESTAMP>/app_lite.py.bak web/app_lite.py

# Restart
sudo systemctl restart mecamera
```

---

## Support

| Problem | Solution |
|---------|----------|
| App won't start | See `EMERGENCY_FIX_APP_CRASH.md` |
| Camera still upside down | Change `--rotation 180` to `--rotation 270` |
| WiFi widget doesn't show | Check browser console (F12) for errors |
| Motion not detecting | Check: `grep Motion logs/mecam_lite.log` |
| Device unreachable | Check: `ping mecamdev2.local` |

---

## Important Notes

⚠️ **Device will restart service** - Page will refresh automatically  
⚠️ **App may take 10-15 seconds to start** on Pi Zero 2W due to RAM  
⚠️ **Camera needs 5 seconds** to initialize after boot  
⚠️ **First motion event** may take 30+ seconds to process

---

## Files Modified in This Session

```
src/camera/rpicam_streamer.py
├─ Line 78: Added '--rotation', '180' parameter
└─ Line ~56: Fixed frame buffer cleanup

web/app_lite.py
├─ Lines 562-611: Added WiFi status API endpoints
├─ Line 1011: Fixed motion detection frame logic  
└─ Line ~50: Added VPN CORS headers

web/templates/dashboard_lite.html
├─ Line 195: Added WiFi status card HTML
└─ Lines 267-286: Added WiFi status JavaScript
```

---

## Success Checklist

After running deployment script:

- [ ] Script completes without errors
- [ ] Service status shows "Active: active (running)"
- [ ] Can access http://mecamdev2.local:5000
- [ ] Camera feed visible and upright
- [ ] WiFi status card appears on dashboard
- [ ] WiFi API responds: `curl http://mecamdev2.local:5000/api/network/wifi`
- [ ] Motion detection is logging: `grep Motion logs/mecam_lite.log`

---

## Next Steps (After Fixes Deployed)

1. **Test Everything Works**
   - Move in front of camera → Check if motion logged
   - Check WiFi status displays correctly
   - Verify camera image orientation

2. **Implement Offline Recording** (Design ready, code needed)
   - Records videos when WiFi down
   - Posts videos when WiFi reconnects
   - Edit: `web/app_lite.py` helpers section

3. **Implement Notification Queue** (Design ready, code needed)
   - Retry SMS/email notifications  
   - Retry up to 3 times
   - Edit: `web/app_lite.py` notification section

---

Created: Jan 26, 2026  
Device: Raspberry Pi Zero 2W (mecamdev2.local)  
App: ME_CAM v2.1 Lite Mode
