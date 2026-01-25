# Device 3 Camera Not Detected - Fix Guide

## Problem
Device 3 shows "TEST MODE - Camera Unavailable" while devices 1 and 2 have working camera feeds.

**Diagnosis:** `vcgencmd get_camera` returns:
```
supported=0 detected=0, libcamera interfaces=0
```

This is a **hardware connection issue**, not a software bug.

---

## Physical Checks (Do These First!)

### 1. **Power Off the Pi**
```bash
ssh pi@mecamdev3.local
sudo shutdown -h now
```
Wait 10 seconds, then unplug power.

### 2. **Check Camera Cable Connection**

**At the Pi Zero 2W end:**
- [ ] Remove the camera ribbon cable from the Pi
- [ ] Check for:
  - Bent pins in the CSI connector
  - Damaged/torn ribbon cable
  - Cable inserted upside down (contacts should face toward the board)
  - Cable fully seated (should click into place)
- [ ] Reconnect the cable:
  - Lift the black plastic tab on the CSI port
  - Insert cable with contacts facing the PCB
  - Push tab down to lock

**At the Camera Module end:**
- [ ] Check camera end of ribbon cable
- [ ] Ensure it's fully seated
- [ ] No tears or damage in the ribbon

### 3. **Compare with Working Devices**

If you have physical access to device 2 (working):
- Compare how the cable is inserted
- Check orientation
- Check cable routing (not pinched or twisted)

### 4. **Try Different Cable**

If you have a spare camera ribbon cable, try replacing it. Ribbon cables can fail even if they look fine.

### 5. **Try Different Camera Module**

If possible, swap the camera module from device 2 to device 3 to rule out a bad camera.

---

## Software Verification (After Physical Checks)

### 1. **Power On and Test**
```bash
# Power on the Pi, SSH in
ssh pi@mecamdev3.local

# Check camera detection
vcgencmd get_camera
# Should show: supported=1 detected=1

# List cameras
rpicam-hello --list-cameras
# Should show camera details
```

### 2. **Test Camera**
```bash
# Quick test (5 second preview)
rpicam-hello -t 5000
```

### 3. **Restart the App**
```bash
cd ~/ME_CAM-DEV
source venv/bin/activate
pkill -f 'python main_lite.py'
python main_lite.py
```

---

## If Still Not Working

### Enable Legacy Camera Support (Last Resort)

Edit `/boot/firmware/config.txt`:
```bash
sudo nano /boot/firmware/config.txt
```

Change:
```ini
camera_auto_detect=1
```

To:
```ini
camera_auto_detect=1
start_x=1
gpu_mem=128
```

Save and reboot:
```bash
sudo reboot
```

---

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `detected=0` | Cable not connected | Reseat cable |
| `detected=0` | Cable upside down | Flip cable 180° |
| `detected=0` | Bad ribbon cable | Replace cable |
| `detected=0` | Bad camera module | Replace camera |
| `detected=0` | CSI port damaged | RMA/replace Pi |
| Camera works after reboot, then stops | Power supply issue | Use better power supply (5V/3A) |

---

## Expected Output When Working

```bash
pi@mecamdev3:~ $ vcgencmd get_camera
supported=1 detected=1, libcamera interfaces=1

pi@mecamdev3:~ $ rpicam-hello --list-cameras
Available cameras
-----------------
0 : imx219 [3280x2464] (/base/soc/i2c0mux/i2c@1/imx219@10)
    Modes: 'SRGGB10_CSI2P' : 640x480 [206.65 fps]
                              1640x1232 [41.85 fps]
                              1920x1080 [47.57 fps]
                              3280x2464 [21.19 fps]
```

---

## Comparison: Device 2 vs Device 3

**Device 2 (Working):**
- Camera feed visible
- 22 recordings
- "Live Camera Feed" shows image

**Device 3 (Not Working):**
- "TEST MODE - Camera Unavailable"
- Black screen
- 0 recordings
- App shows warning: "Camera init failed: list index out of range"

**Root Cause:** Physical hardware - camera not detected by the Pi at all.

---

**Next Step:** Power off device 3 and check the camera cable connection first.
