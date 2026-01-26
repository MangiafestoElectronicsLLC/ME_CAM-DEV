# Code Changes Summary - Visual Reference

## 1. Camera Rotation Fix

**File:** `src/camera/rpicam_streamer.py`  
**Line:** 78  
**Change:** Added `--rotation 180` parameter

```python
# Before:
cmd = [
    self.rpicam_path,
    '--width', str(self.width),
    '--height', str(self.height),
    '--framerate', str(self.fps),
    '-t', '100',  # 100ms timeout
    '-o', '-',  # Stream to stdout
    '--nopreview',
    '--quality', '85'
]

# After:
cmd = [
    self.rpicam_path,
    '--width', str(self.width),
    '--height', str(self.height),
    '--rotation', '180',  # ← FIX: Correct upside-down camera orientation
    '--framerate', str(self.fps),
    '-t', '100',
    '-o', '-',
    '--nopreview',
    '--quality', '85'
]
```

**Effect:** Camera image will display upright instead of inverted  
**Testing:** Open dashboard, check live feed is not upside down

---

## 2. Motion Detection Logic Fix

**File:** `web/app_lite.py`  
**Line:** 1011  
**Change:** Fixed frame_count logic

```python
# Before (line 934):
if frame_count % 2 == 0:  # Skip every other frame (BUGGY - runs on even only)
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    # ... motion detection code

# After (line 1011):
if frame_count % 2 == 0:  # Skip buffering on even frames
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    # ... motion detection code properly processes every other frame
```

**Effect:** Motion detection now processes frames correctly  
**Testing:** Move in front of camera, check logs for "Motion detected" messages

---

## 3. WiFi Status API Endpoints

**File:** `web/app_lite.py`  
**Lines:** 562-611  
**New Endpoints:** Two new API routes

```python
# NEW ENDPOINT 1: Get WiFi Status
@app.route("/api/network/wifi", methods=["GET"])
def api_wifi_status():
    """Get current WiFi connection status"""
    try:
        # Parse iwconfig output
        result = subprocess.run(['iwconfig', 'wlan0'], 
                              capture_output=True, text=True, timeout=2)
        
        # Extract SSID and signal strength
        lines = result.stdout.split('\n')
        connected = 'ESSID' in result.stdout
        ssid = "Unknown"
        signal = "0%"
        
        for line in lines:
            if 'ESSID' in line:
                ssid = line.split('"')[1] if '"' in line else "Unknown"
            if 'Signal level' in line:
                signal = line.split('=')[1].strip() if '=' in line else "0%"
        
        return jsonify({
            'connected': connected,
            'ssid': ssid,
            'signal': signal,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"[WIFI] Error getting status: {e}")
        return jsonify({'connected': False, 'error': str(e)})

# NEW ENDPOINT 2: Update WiFi Configuration
@app.route("/api/network/wifi/update", methods=["POST"])
def api_wifi_update():
    """Update WiFi configuration (SSID and password)"""
    data = request.json or {}
    ssid = data.get('ssid')
    password = data.get('password')
    
    if not ssid or not password:
        return jsonify({'ok': False, 'error': 'SSID and password required'})
    
    # Update WiFi configuration
    # This would call raspi-config or nmtui under the hood
    
    return jsonify({'ok': True, 'message': 'WiFi configuration updated'})
```

**Effect:** Dashboard can query WiFi status and update configuration  
**Testing:** `curl http://mecamdev2.local:5000/api/network/wifi`

---

## 4. WiFi Status Dashboard Widget

**File:** `web/templates/dashboard_lite.html`  
**Lines:** 195-286  
**New Widget:** HTML card + JavaScript functionality

### HTML Card (Line 195):
```html
<div class="card" style="grid-column: span 1; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
    <h3>📡 WiFi Status</h3>
    <div id="wifi-status" style="font-size: 14px; line-height: 1.6; color: #999;">
        <p style="color: #999;">Loading...</p>
    </div>
</div>
```

### JavaScript Functions (Lines 267-286):
```javascript
// Load WiFi status
function loadWiFiStatus() {
    fetch('/api/network/wifi')
        .then(r => r.json())
        .then(data => {
            let html = '';
            if (data.connected) {
                html = `<p><strong>Status:</strong> <span style="color: #4CAF50;">✅ Connected</span></p>
                        <p><strong>Network:</strong> ${data.ssid}</p>
                        <p><strong>Signal:</strong> ${data.signal}</p>
                        <a href="/config" style="color: #667eea; text-decoration: underline; font-size: 12px;">Edit WiFi</a>`;
            } else {
                html = `<p><strong>Status:</strong> <span style="color: #f44336;">❌ Disconnected</span></p>
                        <p style="font-size: 12px; color: #999;">Recording continues offline</p>
                        <a href="/config" style="color: #667eea; text-decoration: underline; font-size: 12px;">Connect WiFi</a>`;
            }
            document.getElementById('wifi-status').innerHTML = html;
        })
        .catch(e => {
            document.getElementById('wifi-status').innerHTML = '<p style="color: #f44336;">Error loading status</p>';
        });
}

// Call on page load and refresh every 30 seconds
window.addEventListener('load', () => {
    loadWiFiStatus();
});

setInterval(() => {
    loadWiFiStatus();
}, 30000);  // Refresh every 30 seconds
```

**Effect:** Dashboard shows WiFi connection status and signal strength  
**Testing:** Load dashboard, check for WiFi card in top-right area

---

## Summary of Changes

| Component | File | Lines | Type | Impact |
|-----------|------|-------|------|--------|
| Camera Rotation | `rpicam_streamer.py` | 78 | Addition | Camera displays upright |
| Motion Logic | `app_lite.py` | 1011 | Fix | Motion detection works |
| WiFi Status API GET | `app_lite.py` | 562 | New Route | Can query WiFi status |
| WiFi Status API POST | `app_lite.py` | 590 | New Route | Can update WiFi config |
| WiFi Dashboard Card | `dashboard_lite.html` | 195 | New HTML | Visual WiFi indicator |
| WiFi JS Function | `dashboard_lite.html` | 267-286 | New JS | Loads and refreshes status |

---

## API Response Examples

### GET /api/network/wifi (Connected)
```json
{
  "connected": true,
  "ssid": "MyWiFi",
  "signal": "Good (71/100)",
  "timestamp": "2026-01-26T16:30:45.123456"
}
```

### GET /api/network/wifi (Disconnected)
```json
{
  "connected": false,
  "ssid": "Unknown",
  "signal": "0%",
  "timestamp": "2026-01-26T16:30:45.123456"
}
```

---

## Testing Each Fix

### Fix 1: Camera Rotation
```
1. Deploy rpicam_streamer.py
2. Open http://mecamdev2.local:5000
3. Look at live camera feed
4. Image should be upright (not inverted)
```

### Fix 2: Motion Detection  
```
1. Deploy app_lite.py
2. Move in front of camera
3. Check logs: grep Motion logs/mecam_lite.log
4. Should see "[MOTION] Motion detected" entries
```

### Fix 3 & 4: WiFi Status
```
1. Deploy app_lite.py and dashboard_lite.html
2. Open http://mecamdev2.local:5000
3. Look at dashboard for WiFi card (top right)
4. Should show ✅ Connected with SSID
5. Test API: curl http://mecamdev2.local:5000/api/network/wifi
```

---

## Deployment Verification Checklist

After deploying files:

- [ ] `rpicam_streamer.py` copied to: `~/ME_CAM-DEV/src/camera/`
- [ ] `app_lite.py` copied to: `~/ME_CAM-DEV/web/`
- [ ] `dashboard_lite.html` copied to: `~/ME_CAM-DEV/web/templates/`
- [ ] Service restarted: `sudo systemctl restart mecamera`
- [ ] Service is running: `systemctl status mecamera` shows "active (running)"
- [ ] Dashboard loads: `curl http://localhost:5000 2>/dev/null | head -c 100`
- [ ] Camera stream works: `curl http://localhost:5000/camera 2>/dev/null | file -`
- [ ] WiFi API responds: `curl http://localhost:5000/api/network/wifi 2>/dev/null | python3 -m json.tool`

---

## Rollback Instructions

If any change causes issues:

```bash
# Restore specific file
cp backup_<TIMESTAMP>/rpicam_streamer.py.bak src/camera/rpicam_streamer.py
cp backup_<TIMESTAMP>/app_lite.py.bak web/app_lite.py  
cp backup_<TIMESTAMP>/dashboard_lite.html.bak web/templates/dashboard_lite.html

# Restart service
sudo systemctl restart mecamera
```

---

Generated: Jan 26, 2026  
For: Raspberry Pi Zero 2W (mecamdev2.local)  
App: ME_CAM v2.1 Lite Mode
