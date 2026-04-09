# Update Guide for ME_CAM Devices 1 & 2

## Device 1 & 2 Update Instructions

### Quick Update (Recommended)

SSH into each device and run:

```bash
cd ~/ME_CAM-DEV
git pull origin main
source venv/bin/activate

# Restart the app
pkill -f 'python main_lite.py'
python main_lite.py &
```

### What's New in Latest Update

**Fixed Issues:**
- ✅ First-run setup form now renders without Jinja2 errors
- ✅ Complete config dictionary with all required nested structures
- ✅ Form save functionality working correctly
- ✅ POST handler properly stores all configuration fields

**New Fields Supported:**
- PIN protection (pin_enabled, pin_code)
- Storage encryption settings
- Detection sensitivity settings
- Email & Google Drive backup configuration
- Network settings (WiFi/Bluetooth toggles)

**Files Updated:**
- `web/app_lite.py` - Setup route now handles full config

---

## Device 3 Camera Issue - ESD Tape Solution

### The Problem
- IMX519 camera not being detected
- Error: `imx519 10-001a: failed to read chip id 519, with error -5`
- Your Pi Zero 2W connector came without a clamp
- Currently using ESD tape to secure ribbon cable

### Why This Might Not Work
1. **ESD Tape too thick** - Creates poor electrical contact
2. **Tape not conductive enough** - May isolate contacts
3. **Tape absorbs moisture** - Causes intermittent connection
4. **Pressure not uniform** - Bad contact at some pins

### Better Solution: 3D Print Camera Holder

Since you have a 3D printed chassis, you can modify or print a camera holder that:
- Secures the ribbon cable without tape
- Applies uniform pressure to the connector
- Allows proper pin contact

**Option 1: Print a Simple Clip**
- Search Thingiverse for "Pi Zero CSI camera clip"
- Print in PLA or PETG
- Replaces the missing connector clamp

**Option 2: Modify Chassis**
- Add a clip mechanism inside your existing chassis
- Secures ribbon cable by friction/retention
- No tape or external parts needed

### Temporary Fix: Improve Tape Contact

If printing isn't immediately possible:

```bash
# On device 3:
ssh pi@MECAMDEV3

# Check current camera status
vcgencmd get_camera

# Reseat cable more firmly:
# 1. Power off: sudo shutdown -h now
# 2. Wait 30 seconds
# 3. Remove old ESD tape carefully
# 4. Reconnect ribbon cable fully into CSI port
# 5. Apply new, thinner tape or use thermal tape (more conductive)
# 6. Power on and test
```

### Proper Camera Connector Clamp Options

**Where to Buy:**
- Amazon: "Pi Zero CSI Camera Connector" (~$5)
- Adafruit: CSI/DSI ribbon connector clamp
- Raspberry Pi Shop official connectors

**Part Numbers:**
- Official Pi Foundation camera connector clamp

**Cost:** ~$2-5 per unit

---

## Device Comparison Matrix

| Device | Model | Camera | Status | Issue |
|--------|-------|--------|--------|-------|
| Device 1 | Pi Zero 2W | Unknown | Working | Needs update |
| Device 2 | Pi Zero 2W | Unknown | Working Well | Updated |
| Device 3 | Pi Zero 2W | IMX519 | Failed | Cable not detected + DIY tape solution |

---

## Action Plan

### Immediate (Today)

**Device 1:**
```bash
ssh pi@<device1-ip>
cd ~/ME_CAM-DEV
git pull origin main
pkill -f 'python main_lite.py'
python main_lite.py &
```

**Device 3 - Camera Testing:**
```bash
# Test current connection
vcgencmd get_camera

# If still detected=0, try different tape/clip solution
# If detected=1, run:
rpicam-hello -t 5000  # Should show preview
```

### Short Term (This Week)

1. Order or 3D print a proper CSI camera connector clamp
2. Replace ESD tape with proper solution
3. Test IMX519 detection again

### Long Term

- All 3 devices running latest code
- All 3 devices with working cameras
- Ready for autoboot setup

---

## Device 3 Debugging Checklist

- [ ] Reseated ribbon cable at Pi end
- [ ] Reseated ribbon cable at camera end  
- [ ] Verified cable orientation (contacts toward PCB)
- [ ] Removed old tape carefully
- [ ] Applied new tape/clip solution
- [ ] Ran `vcgencmd get_camera` - shows `detected=1`
- [ ] Ran `rpicam-hello --list-cameras` - shows IMX519
- [ ] Ran `rpicam-hello -t 5000` - saw camera preview
- [ ] Started ME_CAM app
- [ ] Saw live camera feed in web dashboard

---

## File Update Status

**Latest commit:** e631661
**Date:** Jan 25, 2026
**Changes:** Complete config dictionary for first_run.html template

All devices should pull this version for the setup form fixes.
