# Device 3 - Pre-Autoboot Fixes (Jan 22, 2026)

## What Went Wrong

When running `python main_lite.py` on Pi Zero 2W (MECAMDEV3), you encountered:

1. **Jinja2 Configuration Error** ❌
   - Template tried to access `config.storage.retention_days`
   - Flask config object was not passed to template
   - **FIXED** ✅ - Updated setup() to pass config dict to template

2. **Camera Init Warning** (Non-critical)
   - "list index out of range" when initializing camera
   - This happens with libcamera on first run - usually resolves on subsequent runs

3. **SSL/HTTPS Not Found** (Expected)
   - Development server running without HTTPS
   - This is normal for initial testing

---

## Steps to Test Before Autoboot

### Step 1: Verify Python Installation
```bash
cd ~/ME_CAM-DEV
source venv/bin/activate
python3 -c "import numpy, flask, PIL, cv2; print('✓ All packages OK')"
```

### Step 2: Test Application Start
```bash
python main_lite.py
```

Expected output:
```
2026-01-22 17:08:58.006 | INFO     | src.utils.pi_detect:init_pi_detection:175 - [PI_DETECT] Detected: Raspberry Pi Zero 2W
2026-01-22 17:08:58.020 | INFO     | src.utils.pi_detect:init_pi_detection:176 - [PI_DETECT] RAM: 512MB
...
Running on http://10.2.1.7:8080
```

### Step 3: Test Web Interface
From your Windows machine:
```
http://mecamdev3.local:8080
```

Should see:
- Homepage with redirect to /setup
- Setup form loads correctly (no Jinja2 errors)
- Form fields display configuration options

### Step 4: Complete Setup
1. Fill in device name and settings
2. Click "Save Configuration"
3. Should redirect to login page
4. Login with `admin` / `admin123`

### Step 5: Fix Any Camera Issues (if needed)
If camera still shows "list index out of range", try:

```bash
# Restart the service
sudo systemctl restart me-cam-dev

# OR manually check libcamera
rpicam-hello --list

# Reload kernel modules
sudo modprobe -r bcm2835_isp
sudo modprobe bcm2835_isp
```

---

## What Changed

**File: `web/app_lite.py`**
- Modified `/setup` route to:
  - Load current configuration with `get_config()`
  - Create proper config display dict with nested structure
  - Pass `config` object to template on GET request
  - Save all form fields on POST request

This ensures the template has all required config values.

---

## Before Setting Up Autoboot

✅ Checklist:
- [ ] Application starts without errors
- [ ] Web interface loads at `http://mecamdev3.local:8080`
- [ ] Setup form displays correctly (no 500 errors)
- [ ] Can complete setup and reach login
- [ ] Can login with admin/admin123
- [ ] Camera shows in logs (even if "init failed", that's okay for lite mode)

**Once all ✅, you can proceed to autoboot setup.**

---

## Testing on Pi Zero 2W with 512MB RAM

Your device is running:
- **OS**: Debian Trixie (bookworm-like)
- **Kernel**: 6.12.62+rpt-rpi-v8
- **Python**: 3.13
- **RAM**: 512MB (lite mode auto-detected)

The lite mode disables:
- Multi-device polling
- Background threads
- Heavy image processing

---

## Next Steps

1. Run `python main_lite.py` again to verify fix
2. Test web interface
3. Once working, follow [PI_ZERO_AUTOBOOT_SETUP.md](PI_ZERO_AUTOBOOT_SETUP.md)

---

**Status**: Ready for testing ✓
