# ME_CAM v2.2.3 - Local Testing on Windows

## 🎯 Quick Start: Test on Your Windows Device

You don't need a Pi to test the core features! Here's how to verify everything works locally.

---

## ✅ Step 1: Verify Python & Dependencies

```powershell
cd C:\Users\nickp\Downloads\ME_CAM-DEV\ME_CAM-DEV

# Activate virtual environment
& .\.venv\Scripts\Activate.ps1

# Check Python
python --version
# Should show: Python 3.9+

# Check installed packages
pip list | grep -E "Flask|opencv|pillow"
# Should show: Flask, opencv-python, Pillow, etc.
```

---

## ✅ Step 2: Run Local Component Tests

```powershell
# Make sure you're in the right directory
cd C:\Users\nickp\Downloads\ME_CAM-DEV\ME_CAM-DEV

# Run the test suite
python test_v2.2.3.py
```

**Expected output:**
```
✓ Test 1: Hardware Detection
✓ Test 2: Motion Event Logger
✓ Test 3: Notification Queue
✓ Test 4: GitHub Updater
✓ Test 5: Flask API Endpoints
✓ Test 6: Configuration Files
✓ Test 7: UI Files
```

---

## ✅ Step 3: Start Local Flask Server

```powershell
# Start the Flask app
python main.py

# You should see output like:
# [2026-02-02] ME_CAM v2.2.3 Starting...
# WARNING in app.run_simple: This is a development server. Do not use it in production deployments.
#  * Running on http://127.0.0.1:8080
```

**Keep this terminal open!** (Don't press Ctrl+C yet)

---

## ✅ Step 4: Open Dashboard in Browser

**Open a NEW PowerShell/Terminal** (don't close the Flask one):

```powershell
# Open dashboard in browser
start http://localhost:8080
```

Or manually visit: `http://localhost:8080`

You should see:
- ✅ ME_CAM Dashboard v2.2.3
- ✅ System information (CPU, RAM)
- ✅ Storage percentage
- ✅ Live camera section (will show error on Windows - expected)
- ✅ Configuration page (clickable)

---

## ✅ Step 5: Test Dashboard Features

### Dashboard Page:
- [ ] Page loads without errors
- [ ] Settings sliders visible
- [ ] Motion sensitivity slider works
- [ ] Recording duration slider works

### Configuration Page:
- [ ] Open: Click "Configuration" link
- [ ] See all settings displayed
- [ ] Check: Device name, motion sensitivity, storage location

### Status Indicators:
- [ ] Check system info (CPU, RAM, Storage)
- [ ] Check version number (should show v2.2.3)
- [ ] Check motion count

---

## ✅ Step 6: Test API Endpoints

**In NEW PowerShell terminal:**

```powershell
# Test API endpoints
curl http://localhost:8080/api/status | ConvertFrom-Json | Format-List

# Expected: Returns JSON with system status
```

Or use Python:
```python
import requests

# Test endpoints
response = requests.get('http://localhost:8080/api/status')
print(response.json())
```

---

## 🧪 What You Can Test Locally

### ✅ Works on Windows:
- Flask web server
- Dashboard rendering
- Configuration page
- API endpoints
- Database operations
- Motion event logging (simulated)
- Settings/sliders
- Navigation between pages
- Template rendering

### ❌ Won't Work on Windows:
- Live camera stream (requires Pi hardware)
- Raspberry Pi detection (will show generic Pi model)
- Motion detection (requires camera)
- Some hardware-specific features

---

## 🎯 Testing Checklist

```
LOCAL TESTING CHECKLIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Component Tests:
  ☐ test_v2.2.3.py runs without errors
  ☐ All 7 component tests pass
  ☐ Hardware detection shows (even if generic)

Flask Server:
  ☐ Starts without errors
  ☐ Listens on port 8080
  ☐ No warnings about missing files

Dashboard:
  ☐ Loads at http://localhost:8080
  ☐ No 404 errors
  ☐ CSS/styling looks good
  ☐ All buttons clickable

Pages:
  ☐ Dashboard page loads
  ☐ Configuration page loads
  ☐ Navigation works (no dead links)
  ☐ Pages render in <1 second

API Endpoints:
  ☐ /api/status returns JSON
  ☐ /api/config returns JSON
  ☐ Other API endpoints respond

Color Fix Verification:
  ☐ thumbnail_gen.py has color conversion code
  ☐ Video codec optimizer created
  ☐ Deployment scripts ready

SUCCESS CRITERIA: All checks pass ✅
```

---

## 🐛 Troubleshooting Local Testing

### Issue: "ModuleNotFoundError: No module named 'cv2'"
```powershell
# Install OpenCV
pip install opencv-python
```

### Issue: "Flask app won't start"
```powershell
# Check if port 8080 is in use
netstat -ano | findstr :8080

# If in use, kill it
taskkill /PID <PID> /F

# Or use different port
# Edit: web/app.py
# Change: app.run(host='0.0.0.0', port=8080)
# To: app.run(host='0.0.0.0', port=8081)
```

### Issue: "Dashboard shows error"
```
Check:
1. Browser console (F12) for JavaScript errors
2. Flask terminal for Python errors
3. Verify all files exist: templates/dashboard_v2.2.3.html
```

### Issue: "Can't reach http://localhost:8080"
```powershell
# Check if Flask is actually running
netstat -ano | findstr :8080
# Should show Python process listening

# Or test with curl
curl http://localhost:8080
```

---

## 📊 What to Look For

### Dashboard Should Show:
```
┌─────────────────────────────────────────┐
│ ME_CAM Dashboard v2.2.3                 │
│                                         │
│ System Info:                            │
│ • Device: Raspberry Pi (generic)        │
│ • Memory: ~1024MB                       │
│ • CPU: Windows (simulated)              │
│ • FPS: N/A (no camera on Windows)       │
│ • Storage: C:\ drive info               │
│                                         │
│ Settings:                               │
│ • Motion Sensitivity: [slider]          │
│ • Recording Duration: [slider]          │
│                                         │
│ [Camera Stream Area - "Error" OK]       │
│ [Configuration] [Motion Events]         │
└─────────────────────────────────────────┘
```

---

## ✨ Next: Deploy to Pi

After local testing confirms everything works:

```bash
# From Windows, run the Pi deployment
.\deploy_to_pi_v2.2.3.sh mecamdev1.local

# Or use the fixed color fix deployment
.\deploy_color_fix.ps1 -PiIP 10.2.1.3 -PiUser pi
```

---

## 📝 Test Results Template

Copy this and fill it out:

```
LOCAL TESTING RESULTS - v2.2.3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Date: February 2, 2026
Device: Windows (Local)
Python Version: ___
Flask Version: ___

Component Tests: ☐ Pass ☐ Fail
Flask Start: ☐ Pass ☐ Fail
Dashboard Load: ☐ Pass ☐ Fail
Configuration Page: ☐ Pass ☐ Fail
API Endpoints: ☐ Pass ☐ Fail

Issues Found:
(none) or list them...

Overall: ☐ Ready ☐ Needs Fixes

Next Step:
☐ Deploy to Pi
☐ Fix issues first
```

---

## 🎯 Your Next Action

1. **Open terminal** in VS Code
2. **Activate venv:** `. .\.venv\Scripts\Activate.ps1`
3. **Run tests:** `python test_v2.2.3.py`
4. **Start server:** `python main.py`
5. **Open browser:** `http://localhost:8080`
6. **Verify:** Dashboard loads and looks good
7. **Check color fix:** `grep -n "COLOR_YUV2BGR" src/core/thumbnail_gen.py`

---

## ✅ All Set!

Everything is configured for local testing. Start with the component tests, then run the Flask app, then access the dashboard.

**Status: READY FOR LOCAL TESTING** ✅
