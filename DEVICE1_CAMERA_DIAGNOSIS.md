# Device 1 (mecamdev1) - Camera Hardware Diagnosis

## Issue Summary
**Camera Display is Black - Hardware Not Detected**

The device shows "Camera streaming active" but displays black screen. Root cause: **The camera module is not being detected by the Raspberry Pi bootloader**.

## Diagnostic Results

### 1. Firmware Camera Detection
```bash
$ sudo vcgencmd get_camera
supported=0 detected=0, libcamera interfaces=0
```
- `detected=0` = **Camera not recognized by bootloader**
- `libcamera interfaces=0` = **No libcamera interfaces available**

### 2. Software Status (All Working)
- ✅ rpicam-jpeg binary installed and functional
- ✅ Motion detection code deployed and running
- ✅ Flask web server running on port 8080
- ✅ Network connectivity stable (-52 dBm WiFi signal)
- ✅ Service starts cleanly

### 3. Root Cause
When rpicam-jpeg (or any libcamera app) tries to capture frames, it exits immediately with **code 255 ("no cameras available")** - this is because libcamera cannot find the camera module at the hardware level.

## Configuration Status
```
/boot/firmware/config.txt:
- camera_auto_detect=1   ✓ (enabled - should auto-detect)
- arm_64bit=1            ✓
- enable_uart=1          ✓
```

## Likely Hardware Issues

1. **Camera Ribbon Cable**
   - Not seated properly in the camera socket
   - Disconnected or loose connection
   - Bent or damaged pins

2. **Camera Module**
   - Defective/failed module
   - Bent ribbon connector
   - Physical damage

3. **Raspberry Pi Connector**
   - Damaged CSI connector on Pi
   - Bent pins in socket
   - Connection corrosion

4. **Firmware/EEPROM**
   - Camera EEPROM not readable
   - Camera ID not recognized

## What We've Tried
- ✅ Updated rpicam capture timeout (100ms → 500ms)
- ✅ Added exposure/brightness/AWB settings  
- ✅ Increased subprocess timeout (1.0s → 1.5s)
- ✅ Removed motion_service conflict with streaming
- ✅ Rebooted device
- ✅ Verified config.txt settings
- ❌ Still: No camera detection at firmware level

## Next Steps (Hardware)

### Option 1: Physical Inspection & Reseating
1. **Power off the device completely**
2. **Remove camera ribbon cable** from the CSI connector on the Pi
3. **Inspect for:**
   - Visible damage or corrosion
   - Bent pins/connectors
   - Dust or debris in connector
4. **Reseat the ribbon:**
   - Push the black clip/lever away from you
   - Fully insert the ribbon cable (shiny side DOWN)
   - Push the black clip/lever back toward you until it clicks
5. **Power on and test:**
   ```bash
   sudo vcgencmd get_camera
   # Should show: supported=1 detected=1, libcamera interfaces=1
   ```

### Option 2: Try Different Camera Module
If camera reseating doesn't work, swap the camera module with a known-working one to verify if the hardware module is defective.

### Option 3: Force Camera Overlay (If Reseating Works)
If vcgencmd shows `detected=1` after reseating, add to `/boot/firmware/config.txt`:
```ini
camera_auto_detect=0
dtoverlay=ov5647
```
Then reboot.

## Software Status - Ready When Hardware Fixed
When camera is detected by hardware:
- **Camera stream**: Will show live video at 640×480 @ 30 FPS
- **Motion detection**: Will automatically detect motion and save video clips to `~/ME_CAM-DEV/recordings/`
- **Delayed event posting**: Yesterday's events posting today is normal (feature to review older motion events)
- **FPS optimization**: Already tuned for Pi Zero 2W (30 FPS, 0.35 motion threshold, disabled encryption/thumbnails)

## Related Files Modified (v2.2.3+)
- `main_lite.py` - Disabled background motion service (no resource conflict)
- `src/camera/rpicam_streamer.py` - Added exposure/brightness, increased timeouts
- `src/detection/libcamera_motion_detector.py` - Changed to rpicam-still (available binary)

## Support Contact
Camera hardware issues require physical inspection. If camera is seated properly and still not detected after reboot, the camera module may be defective.
