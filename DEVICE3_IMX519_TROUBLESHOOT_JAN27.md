# Device 3 IMX519 Camera Fix - Troubleshooting Summary

## Current Status
- **Device**: Raspberry Pi Zero 2W (MECAMDEV3)
- **IP**: 10.2.1.47 / mecamdev3.local
- **Issue**: IMX519 camera not detected (error -5: I/O error)
- **Root Cause**: Camera appears on I2C bus 10 at address **0x0a** but driver expects **0x1a**
- **Last Action**: Applied config fix and triggered reboot

---

## What We Discovered

### I2C Bus Scan Results
```
$ sudo i2cdetect -y 10
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:                         -- -- -- -- UU -- -- -- 
```

**Key Finding**: "UU" at 0x0a means the device is there but at wrong address for the driver.

### Kernel Error
```
imx519 10-001a: failed to read chip id 519, with error -5
imx519 10-001a: probe with driver imx519 failed with error -5
```

Error -5 = I/O error (device not responding to I2C at expected address)

---

## Solution Applied

Updated `/boot/firmware/config.txt` with:

```ini
# IMX519 Camera Configuration (Fixed Jan 27)
# Camera detected at I2C 0x0a on CSI bus
dtoverlay=imx519,cam0
dtparam=i2c_arm=on
dtparam=i2c_arm_baudrate=400000
```

Then reboot was triggered. **Device may still be coming back online.**

---

## Next Steps - Choose One:

### **Option 1: Wait and Check Again (Device Still Booting)**
```powershell
# Wait 2 minutes from the reboot command, then:
ssh pi@10.2.1.47 "vcgencmd get_camera && rpicam-hello --list-cameras"
```

**Success indicators:**
- `vcgencmd get_camera` returns `supported=1 detected=1`
- `rpicam-hello --list-cameras` shows IMX519 module

### **Option 2: Manual Physical Reseat (If Config Didn't Work)**

If device comes back online but camera still shows `detected=0`:

```bash
# SSH into device
ssh pi@10.2.1.47

# 1. Power down
sudo shutdown -h now

# 2. Unplug power for 15 seconds

# 3. Check camera cable at BOTH ENDS:
#    - Pi Zero CSI: Lift black tab, remove, inspect, reseat firmly
#    - Camera module: Ensure ribbon fully inserted with contacts facing PCB

# 4. Plug power back in

# 5. Wait 30 seconds and test:
vcgencmd get_camera
rpicam-hello --list-cameras
```

### **Option 3: Alternative IMX519 Address Configuration**

If device comes back but still not detected, try:

```bash
ssh pi@10.2.1.47 "sudo nano /boot/firmware/config.txt"
```

Replace the IMX519 section with ONE of these alternatives:

**Try A (I2C address 0x10):**
```ini
dtoverlay=imx519,cam0,addr=0x10
```

**Try B (GPIO 18 for CSI address):**
```ini
dtoverlay=imx519,cam0,gpio=18
```

**Try C (No address spec - auto-detect):**
```ini
dtoverlay=imx519
dtparam=i2c_arm=on
```

Then save and reboot:
```bash
sudo reboot
```

---

## Testing Commands

Once device is back online:

```bash
# Check camera detection
vcgencmd get_camera
# Expected: supported=1 detected=1

# List cameras
rpicam-hello --list-cameras
# Expected: Shows IMX519 [4656x3496]

# View kernel messages
dmesg | grep -i imx519 | tail -5
# Expected: "sensor driver probed successfully"

# Quick camera test
rpicam-hello -t 5000
# Should show 5-second camera preview

# Restart application
cd ~/ME_CAM-DEV
source venv/bin/activate
pkill -f 'python main_lite.py'
python main_lite.py
# Should show camera feed at http://10.2.1.47:8080
```

---

## If All Config Changes Fail

**This indicates a hardware issue:**

1. **Bad camera module** - IMX519 may be defective
2. **Bad ribbon cable** - Cable may not be seating properly
3. **Bad CSI port** - Raspberry Pi CSI port may be damaged
4. **Bad I2C address** - Camera module shipped with non-standard address

**Next steps:**
- Try swapping camera with Device 1 or 2 (if available)
- Try different camera ribbon cable (if available)
- Consider RMA/replacement of IMX519 module

---

## Important Files

**Config Backup:**
```bash
# Show backup
ssh pi@10.2.1.47 "ls -la /boot/firmware/config.txt*"

# Restore if needed
ssh pi@10.2.1.47 "sudo cp /boot/firmware/config.txt.backup /boot/firmware/config.txt"
```

**Fix Script Location:**
```bash
ssh pi@10.2.1.47 "ls ~/fix_imx519.sh"
```

---

## Expected Timeline

- **Right now**: Device may still be booting (took ~90 seconds)
- **In 5 minutes**: Device should be fully online and responsive
- **After camera fixed**: Application should auto-detect and display camera feed

---

**Status**: ⏳ Waiting for device to come back online after reboot. Check back in 2-3 minutes and run:

```powershell
ssh pi@10.2.1.47 "vcgencmd get_camera"
```
