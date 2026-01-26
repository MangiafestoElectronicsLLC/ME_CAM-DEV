# 🔧 Critical Fixes for Camera, Motion Detection, WiFi & Notifications
**Date**: January 26, 2026  
**Status**: READY TO DEPLOY  
**Severity**: HIGH - Multiple blocking issues

---

## 🎯 Issues to Fix

### 1. Camera Upside Down 🔄
**Problem**: Image flipped vertically  
**Cause**: rpicam-jpeg orientation setting missing  
**Solution**: Add rotation parameter to rpicam command

### 2. Motion Detection Not Working 🚫
**Problem**: Events showing old dates, no new events today  
**Cause**: Motion detection logic disabled or broken  
**Solution**: Fix frame counter logic and add debug logging

### 3. Video Not Saving to Events 📹
**Problem**: Motion detected but no video saved  
**Cause**: save_motion_clip_buffered() failing silently  
**Solution**: Add error handling and fallback to snapshot

### 4. WiFi Status Not Shown 📶
**Problem**: Dashboard doesn't show WiFi connection status  
**Cause**: Missing API endpoint and UI element  
**Solution**: Add WiFi status API + dashboard widget

### 5. Offline Recording Not Implemented 🌐
**Problem**: Videos not saved when WiFi down  
**Cause**: No offline queue system  
**Solution**: Implement local queue + sync on reconnect

### 6. Notifications Not Sending 📱
**Problem**: SMS and email notifications fail silently  
**Cause**: API endpoints not configured, missing error handling  
**Solution**: Add notification queue + retry logic

### 7. No Events Detected Today 📅
**Problem**: Motion events from previous days but not today  
**Cause**: Timezone issue or motion detection disabled  
**Solution**: Fix event logging and timezone handling

---

## 🔧 Fixes to Apply

### Fix #1: Camera Orientation (rpicam_streamer.py)

Add rotation parameter:

```python
cmd = [
    self.rpicam_path,
    '--width', str(self.width),
    '--height', str(self.height),
    '--timelapse', str(1000 // self.fps),
    '-t', '0',
    '-o', '-',
    '--nopreview',
    '--quality', '85',
    '--rotation', '180',  # ← ADD THIS: Rotate 180° to fix upside-down
]
```

Options: `--rotation 0` (normal), `90` (left), `180` (upside-down), `270` (right)

---

### Fix #2: Motion Detection Logic (app_lite.py)

Fix the motion detection that was using wrong counter:

```python
# CURRENT BUGGY CODE:
if frame_count % 2 == 0:  # Skip every other frame for speed
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
else:
    # Skip motion detection this frame
    pass

# SHOULD BE:
if frame_count % 2 != 0:  # Check motion on ODD frames
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    # ... do motion detection
else:
    # Skip this frame
    pass
```

---

### Fix #3: Video Recording Error Handling (app_lite.py)

Add try-catch and fallback:

```python
if not nanny_cam and cfg.get('motion_record_enabled', True):
    logger.info(f"[MOTION] Motion detected")
    recording = True
    try:
        clip_file = save_motion_clip_buffered(camera, frame_buffer.copy(), duration_sec=5)
        if clip_file:
            video_path = clip_file
        else:
            # Fallback to snapshot if video fails
            video_path = save_motion_snapshot(frame)
            logger.warning("[MOTION] Video save failed, using snapshot")
    except Exception as e:
        logger.error(f"[MOTION] Recording error: {e}")
        video_path = save_motion_snapshot(frame)
```

---

### Fix #4: WiFi Status API (app_lite.py - NEW)

Add these API endpoints:

```python
@app.route("/api/network/wifi", methods=["GET"])
def api_wifi_status():
    """Get WiFi connection status"""
    try:
        import subprocess
        result = subprocess.run(
            ['iwconfig'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        output = result.stdout
        is_connected = 'ESSID:' in output and 'off/any' not in output
        
        # Extract SSID and signal strength
        ssid = "Not Connected"
        signal = "N/A"
        
        if 'ESSID:"' in output:
            ssid_start = output.find('ESSID:"') + 7
            ssid_end = output.find('"', ssid_start)
            ssid = output[ssid_start:ssid_end]
        
        if 'Signal level=' in output:
            sig_start = output.find('Signal level=') + 13
            sig_end = output.find(' ', sig_start)
            signal = output[sig_start:sig_end]
        
        return jsonify({
            'connected': is_connected,
            'ssid': ssid,
            'signal': signal,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"[NETWORK] WiFi status error: {e}")
        return jsonify({'connected': False, 'error': str(e)}), 500

@app.route("/api/network/wifi/update", methods=["POST"])
def api_wifi_update():
    """Update WiFi settings"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        ssid = data.get('ssid')
        password = data.get('password')
        
        if not ssid or not password:
            return jsonify({'error': 'SSID and password required'}), 400
        
        # Save to config
        cfg = get_config()
        cfg['wifi_ssid'] = ssid
        cfg['wifi_password'] = password
        save_config(cfg)
        
        logger.info(f"[NETWORK] WiFi settings updated: {ssid}")
        return jsonify({'ok': True, 'message': 'WiFi settings saved'})
    except Exception as e:
        logger.error(f"[NETWORK] WiFi update error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500
```

---

### Fix #5: Offline Recording Queue (app_lite.py - NEW)

Add to helpers:

```python
def log_offline_video(video_path, event_type="motion"):
    """Queue video for upload when WiFi reconnects"""
    try:
        queue_file = os.path.join(BASE_DIR, "offline_queue.json")
        queue = []
        
        if os.path.exists(queue_file):
            with open(queue_file, 'r') as f:
                queue = json.load(f)
        
        queue.append({
            'video_path': video_path,
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            'uploaded': False
        })
        
        with open(queue_file, 'w') as f:
            json.dump(queue, f)
        
        logger.info(f"[OFFLINE] Queued video for sync: {video_path}")
        return True
    except Exception as e:
        logger.error(f"[OFFLINE] Queue error: {e}")
        return False

def sync_offline_queue():
    """Upload queued videos when WiFi returns"""
    try:
        queue_file = os.path.join(BASE_DIR, "offline_queue.json")
        if not os.path.exists(queue_file):
            return
        
        with open(queue_file, 'r') as f:
            queue = json.load(f)
        
        for item in queue:
            if not item.get('uploaded'):
                video_path = os.path.join(BASE_DIR, "recordings", item['video_path'])
                if os.path.exists(video_path):
                    # Try to send notifications, save events, etc.
                    log_motion_event(
                        event_type=item['type'],
                        confidence=1.0,
                        details={'video_path': item['video_path'], 'synced_from_offline': True}
                    )
                    item['uploaded'] = True
        
        # Save updated queue
        with open(queue_file, 'w') as f:
            json.dump(queue, f)
        
        logger.success(f"[OFFLINE] Synced {len([i for i in queue if i['uploaded']])} queued videos")
    except Exception as e:
        logger.error(f"[OFFLINE] Sync error: {e}")
```

---

### Fix #6: Notification Queue System (app_lite.py - NEW)

```python
def queue_notification(phone, message, event_id=None):
    """Queue notification for delivery"""
    try:
        notification_queue_file = os.path.join(BASE_DIR, "notification_queue.json")
        queue = []
        
        if os.path.exists(notification_queue_file):
            with open(notification_queue_file, 'r') as f:
                queue = json.load(f)
        
        queue.append({
            'phone': phone,
            'message': message,
            'event_id': event_id,
            'timestamp': datetime.now().isoformat(),
            'sent': False,
            'attempts': 0
        })
        
        with open(notification_queue_file, 'w') as f:
            json.dump(queue, f)
        
        logger.info(f"[NOTIFY] Queued notification for {phone}")
        return True
    except Exception as e:
        logger.error(f"[NOTIFY] Queue error: {e}")
        return False

def send_queued_notifications():
    """Send all queued notifications"""
    try:
        notification_queue_file = os.path.join(BASE_DIR, "notification_queue.json")
        if not os.path.exists(notification_queue_file):
            return
        
        with open(notification_queue_file, 'r') as f:
            queue = json.load(f)
        
        cfg = get_config()
        sent_count = 0
        
        for item in queue:
            if not item.get('sent') and item.get('attempts', 0) < 3:
                try:
                    # Try to send SMS
                    if cfg.get('sms_enabled') and cfg.get('sms_api_url'):
                        import requests
                        response = requests.post(
                            cfg.get('sms_api_url'),
                            json={
                                'to': item['phone'],
                                'message': item['message'],
                                'from': cfg.get('device_name', 'ME_CAM')
                            },
                            headers={'Authorization': f"Bearer {cfg.get('sms_api_key', '')}"},
                            timeout=10
                        )
                        
                        if response.status_code in [200, 201]:
                            item['sent'] = True
                            logger.success(f"[NOTIFY] SMS sent to {item['phone']}")
                            sent_count += 1
                        else:
                            item['attempts'] += 1
                except Exception as e:
                    logger.warning(f"[NOTIFY] SMS send failed: {e}")
                    item['attempts'] += 1
        
        # Save updated queue
        with open(notification_queue_file, 'w') as f:
            json.dump(queue, f)
        
        if sent_count > 0:
            logger.info(f"[NOTIFY] Sent {sent_count} queued notifications")
    except Exception as e:
        logger.error(f"[NOTIFY] Send queued error: {e}")
```

---

### Fix #7: Timezone Fix (app_lite.py)

Ensure consistent timezone handling:

```python
from datetime import datetime, timedelta, timezone

# When logging events, use timezone-aware datetime
def log_motion_event(event_type="motion", confidence=1.0, details=None):
    """Log motion event with proper timezone"""
    try:
        # Use local timezone, not UTC
        timestamp = datetime.now().isoformat()  # Local time
        
        event = {
            'id': str(int(time.time() * 1000)),
            'timestamp': timestamp,
            'type': event_type,
            'confidence': confidence,
            'details': details or {}
        }
        
        events_path = os.path.join(BASE_DIR, "logs", "motion_events.json")
        os.makedirs(os.path.dirname(events_path), exist_ok=True)
        
        events = []
        if os.path.exists(events_path):
            with open(events_path, 'r') as f:
                events = json.load(f)
        
        events.append(event)
        
        with open(events_path, 'w') as f:
            json.dump(events, f, indent=2)
        
        logger.info(f"[MOTION] Event logged: {event_type} @ {timestamp}")
        return event
    except Exception as e:
        logger.error(f"[MOTION] Logging error: {e}")
        return None
```

---

## 📊 Deployment Order

1. ✅ Fix camera rotation (rpicam_streamer.py)
2. ✅ Fix motion detection logic (app_lite.py) 
3. ✅ Add video error handling (app_lite.py)
4. ✅ Add WiFi status API (app_lite.py)
5. ✅ Add offline queue (app_lite.py)
6. ✅ Add notification queue (app_lite.py)
7. ✅ Fix timezone (app_lite.py)
8. ✅ Update dashboard_lite.html for WiFi widget
9. ✅ Restart service

---

## 📱 Dashboard Updates Needed

Add WiFi status widget to [dashboard_lite.html](dashboard_lite.html):

```html
<div class="info-card">
    <h3>📶 WiFi Status</h3>
    <div id="wifi-status" style="font-size: 14px; line-height: 1.6;">
        <p style="color: #999;">Loading WiFi info...</p>
    </div>
</div>

<script>
// Load WiFi status on page load
function loadWiFiStatus() {
    fetch('/api/network/wifi')
        .then(r => r.json())
        .then(data => {
            let html = '';
            if (data.connected) {
                html = `<p><strong>Status:</strong> <span style="color: #4CAF50;">✅ Connected</span></p>
                        <p><strong>Network:</strong> ${data.ssid}</p>
                        <p><strong>Signal:</strong> ${data.signal}</p>
                        <a href="/config" style="color: #667eea; text-decoration: underline;">Edit WiFi Settings</a>`;
            } else {
                html = `<p><strong>Status:</strong> <span style="color: #f44336;">❌ Disconnected</span></p>
                        <p style="font-size: 12px; color: #999;">Recording continues offline</p>
                        <a href="/config" style="color: #667eea; text-decoration: underline;">Connect WiFi</a>`;
            }
            document.getElementById('wifi-status').innerHTML = html;
        })
        .catch(e => console.error('WiFi status error:', e));
}

// Load on page load
window.addEventListener('load', loadWiFiStatus);

// Refresh every 30 seconds
setInterval(loadWiFiStatus, 30000);
</script>
```

---

## ✅ Verification After Deployment

```bash
# 1. Check camera rotation
ssh pi@mecamdev2.local 'tail -5 ~/ME_CAM-DEV/logs/mecam_lite.log' | grep -i rotation

# 2. Check motion detection
ssh pi@mecamdev2.local 'grep -i "motion detected" ~/ME_CAM-DEV/logs/mecam_lite.log | tail -5'

# 3. Check WiFi API
curl http://mecamdev2.local:8080/api/network/wifi

# 4. Verify queue files created
ssh pi@mecamdev2.local 'ls -la ~/ME_CAM-DEV/offline_queue.json ~/ME_CAM-DEV/notification_queue.json'

# 5. Test motion by moving in front of camera
# Should see new event logged with today's date
```

