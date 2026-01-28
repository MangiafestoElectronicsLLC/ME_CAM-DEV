# Device 3 Recovery Checklist - Jan 27, 2026

## Status
- ⏳ Device is offline after reboot command
- Last known IP: **10.2.1.47**
- Hostname: **mecamdev3.local**

---

## What to Do Now (In Order)

### **Step 1: Wait and Monitor (5-10 minutes)**

The device was rebooting to apply config changes. It may take:
- 2-3 minutes to boot
- 2-3 minutes to establish network connection
- 1-2 minutes for SSH daemon to start

**Check status:**
```powershell
ssh pi@10.2.1.47 "vcgencmd get_camera"
# Should return: supported=1 detected=1
```

If successful → **Go to Step 4 (Test Camera)**

---

### **Step 2: Device Not Responding After 10 Minutes?**

**Check if device is on network:**

**Option A: From Windows (easiest)**
- Check your router's connected devices list
- Look for "MECAMDEV3" or "pi"
- Note the IP address if it changed

**Option B: ARP scan (if available)**
```powershell
arp -a | findstr "pi"
```

**Option C: Find by hostname**
```powershell
nslookup mecamdev3.local
# Look for IP in response
```

---

### **Step 3: Physical Check Required**

If still offline, the device may have a power or boot issue:

1. **Check power LED**
   - Is the red power LED on?
   - Is green activity LED blinking?

2. **Check HDMI/Display**
   - If you can see the display, check for boot messages
   - Look for kernel panic or errors

3. **If stuck at black screen:**
   - The config change might have caused a boot issue
   - We can revert the config

**To revert config (without SSH):**

If you have physical access to the Pi:
1. Remove the SD card
2. Insert into another computer with SD card reader
3. Edit `/boot/firmware/config.txt` on the card
4. Remove these lines:
   ```ini
   # IMX519 Camera Configuration (Fixed Jan 27)
   # Camera detected at I2C 0x0a on CSI bus
   dtoverlay=imx519,cam0
   dtparam=i2c_arm=on
   dtparam=i2c_arm_baudrate=400000
   ```
5. Restore the backup:
   ```
   Copy content from config.txt.backup back to config.txt
   ```
6. Reinsert SD card into Pi Zero 2W
7. Power on again

---

### **Step 4: Test Camera (Once Device Responds)**

```bash
# SSH into device
ssh pi@10.2.1.47

# Check camera detection
vcgencmd get_camera
# Expected: supported=1 detected=1

# List cameras
rpicam-hello --list-cameras
# Should show IMX519 details

# Check kernel messages
dmesg | grep imx519 | tail -3
# Should show success message
```

**If camera now detected:**
✅ The fix worked! Proceed to Step 5

**If camera still shows detected=0:**
❌ The I2C address issue persists. Try Step 5

---

### **Step 5: If Camera Still Not Detected**

Try alternate I2C configurations:

```bash
ssh pi@10.2.1.47
sudo nano /boot/firmware/config.txt
```

Find this section:
```ini
# IMX519 Camera Configuration (Fixed Jan 27)
dtoverlay=imx519,cam0
dtparam=i2c_arm=on
dtparam=i2c_arm_baudrate=400000
```

Replace with **ONE** of these:

**Option A (Try I2C speed change):**
```ini
dtoverlay=imx519
dtparam=i2c_arm=on
dtparam=i2c_arm_baudrate=100000
```

**Option B (Try legacy format):**
```ini
dtoverlay=imx519
start_x=1
gpu_mem=256
```

**Option C (Minimal config):**
```ini
camera_auto_detect=1
dtoverlay=imx519
```

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

Reboot:
```bash
sudo reboot
```

Test again after reboot:
```bash
vcgencmd get_camera
rpicam-hello --list-cameras
```

---

### **Step 6: Application Testing**

Once camera is detected:

```bash
cd ~/ME_CAM-DEV
source venv/bin/activate

# Kill any existing process
pkill -f 'python main_lite.py'

# Start the app
python main_lite.py
```

**Then access from Windows browser:**
```
http://10.2.1.47:8080
or
http://mecamdev3.local:8080
```

You should see the camera feed!

---

## Diagnostic Commands

These will help identify the issue if camera still won't work:

```bash
# Check I2C communication
sudo i2cdetect -y 10
# Look for "1a" or "0a" in the output

# Read full error messages
dmesg | grep -i imx519

# Check camera module is loaded
lsmod | grep imx519

# Check CSI interface
cat /proc/device-tree/soc/i2c0mux/i2c@1/imx519@1a/status 2>/dev/null

# Test libcamera directly
libcamera-hello --list-properties
```

---

## Important Contact Points

**Files changed:**
- `/boot/firmware/config.txt` - Camera configuration
- `/boot/firmware/config.txt.backup_*` - Backup (auto-created)

**Application:**
- Location: `~/ME_CAM-DEV`
- Main file: `main_lite.py`
- Web port: 8080

**Device info:**
- OS: Debian Trixie/Bookworm
- Kernel: 6.12.62+rpt-rpi-v8
- Python: 3.13
- RAM: 512MB (lite mode enabled)

---

## Timeline

| Time | Event |
|------|-------|
| ~12:30 PM | Config updated, reboot triggered |
| 12:31-12:35 PM | Device booting/restarting |
| 12:35+ PM | Should be back online and testable |

**If offline at:** 
- **12:35 PM**: Still booting (wait 5 more minutes)
- **12:40 PM**: Check network/power
- **12:50 PM**: Likely hung boot, need physical intervention

---

## Quick Commands to Try

```powershell
# Try multiple times (network may need time to come up)
for ($i=1; $i -le 5; $i++) { 
    Write-Host "Attempt $i..."
    ssh pi@10.2.1.47 "vcgencmd get_camera" -ErrorAction SilentlyContinue
    if ($?) { break }
    Start-Sleep -Seconds 10
}
```

---

**Last Updated**: Jan 27, 2026 12:32 PM  
**Status**: Device rebooting, waiting for network response

