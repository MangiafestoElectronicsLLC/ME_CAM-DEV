# ME_CAM v2.0 - Developer Quick Reference

## 🎯 Quick Start Commands

### Deploy to Pi Zero 2W
```bash
# SSH to Pi
ssh pi@me-cam-1.local

# Download deployment script
curl -O https://raw.githubusercontent.com/YOUR_REPO/ME_CAM-DEV/main/scripts/deploy_pi_zero.sh

# Deploy (one command!)
sudo bash deploy_pi_zero.sh

# Verify service
sudo systemctl status mecamera
```

### Local Development
```bash
# Clone repo
git clone <repo-url>
cd ME_CAM-DEV

# Setup Python environment
python3 -m venv --system-site-packages venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run locally
python3 main.py

# Access: http://localhost:8080
```

---

## 📚 Project Structure

```
ME_CAM-DEV/
├── main.py                    # Entry point
├── web/
│   ├── app.py                # Flask app + all API routes
│   ├── templates/
│   │   ├── dashboard.html     # Main UI (enhanced)
│   │   ├── multicam.html      # Multi-device dashboard
│   │   └── config.html        # Settings page
│   └── static/
│       └── style.css          # Styling
│
├── src/
│   ├── core/
│   │   ├── motion_logger.py   # Motion event logging ✨ NEW
│   │   ├── secure_encryption.py # E2E encryption ✨ NEW
│   │   ├── config_manager.py  # Configuration
│   │   ├── user_auth.py       # Authentication
│   │   └── battery_monitor.py # Battery status
│   │
│   ├── camera/
│   │   ├── fast_camera_streamer.py # High-speed streaming
│   │   ├── camera_pipeline.py
│   │   └── libcamera_streamer.py
│   │
│   └── detection/
│       ├── motion_service.py  # Motion detection
│       ├── ai_person_detector.py
│       └── watchdog.py
│
├── config/
│   ├── config.json            # User config
│   └── config_default.json    # Default config
│
├── recordings/                # Video storage (local)
├── logs/
│   ├── mecam.log             # Application logs
│   └── motion_events.json    # Motion event log
│
└── docs/
    ├── DEPLOYMENT_GUIDE.md   # Complete setup guide ✨ NEW
    └── IMPLEMENTATION_SUMMARY.md # Feature list ✨ NEW
```

---

## 🔌 Key API Endpoints

### Motion Events (NEW)
```bash
# Get recent motion events
curl http://localhost:8080/api/motion/events?hours=24

# Get statistics
curl http://localhost:8080/api/motion/stats

# Log a motion event
curl -X POST http://localhost:8080/api/motion/log \
  -H "Content-Type: application/json" \
  -d '{"type": "person", "confidence": 0.87}'

# Export as CSV
curl http://localhost:8080/api/motion/export
```

### Stream Quality (NEW)
```bash
# Get current quality
curl http://localhost:8080/api/stream/quality

# Set quality
curl -X POST http://localhost:8080/api/stream/quality \
  -H "Content-Type: application/json" \
  -d '{"quality": "high"}'
```

### Existing Endpoints
```bash
# Get storage info
curl http://localhost:8080/api/storage

# List recordings
curl http://localhost:8080/api/recordings

# Download video
curl http://localhost:8080/api/download/motion_20240114_120000.mp4

# Get device list
curl http://localhost:8080/api/devices
```

---

## 🛠️ Configuration

### Default Config Path
```
config/config.json
```

### Key Settings
```json
{
  "device_name": "ME_CAM_1",
  "camera": {
    "stream_quality": "standard",
    "resolution": "640x480",
    "stream_fps": 15
  },
  "storage": {
    "retention_days": 7,
    "max_storage_gb": 10,
    "encrypt": true
  },
  "detection": {
    "sensitivity": 0.6
  }
}
```

### Programmatic Access
```python
from src.core import get_config, save_config

# Get config
cfg = get_config()
print(cfg['camera']['resolution'])

# Update config
cfg['camera']['stream_quality'] = 'high'
save_config(cfg)
```

---

## 🔐 Encryption Usage

### Basic Usage
```python
from src.core import get_encryption

enc = get_encryption()

# Encrypt/decrypt files
enc.encrypt_file("video.mp4")
enc.decrypt_file("video.mp4.enc")

# Encrypt/decrypt JSON
encrypted_json = enc.encrypt_json({"sensitive": "data"})
data = enc.decrypt_json(encrypted_json)
```

### With Password
```python
enc = get_encryption(password="my_secure_password")
# Uses PBKDF2 with 100,000 iterations
```

---

## 📝 Motion Logging

### Log Events
```python
from src.core import log_motion_event

# Log motion detection
log_motion_event(
    event_type="motion",
    confidence=0.75,
    details={"duration": 3, "area": "center"}
)

# Log person detection
log_motion_event(
    event_type="person",
    confidence=0.92,
    details={"count": 1, "location": "porch"}
)
```

### Retrieve Events
```python
from src.core import get_recent_events, get_event_statistics

# Get recent events
events = get_recent_events(hours=24, event_type="person", limit=100)

# Get statistics
stats = get_event_statistics(hours=24)
print(f"Total events: {stats['total']}")
print(f"Events by type: {stats['by_type']}")
```

---

## 🚀 Deployment Checklist

### Before Deploying
- [ ] Test locally: `python3 main.py`
- [ ] Verify motion logging works
- [ ] Test all API endpoints
- [ ] Check encryption functions
- [ ] Verify dashboard UI on mobile

### Pi Zero Deployment
```bash
# 1. Flash SD card with Raspberry Pi OS Lite

# 2. SSH to Pi
ssh pi@me-cam-1.local

# 3. Run deployment script
curl -O https://raw.githubusercontent.com/YOUR_REPO/ME_CAM-DEV/main/scripts/deploy_pi_zero.sh
sudo bash deploy_pi_zero.sh

# 4. Access dashboard
# Open: http://me-cam-1.local:8080

# 5. Complete first-run setup
# - Create admin user
# - Configure camera
# - Set emergency contacts
# - Enable encryption
```

### Post-Deployment
- [ ] Verify streaming works
- [ ] Test motion detection
- [ ] Check logs: `sudo journalctl -u mecamera -f`
- [ ] Test emergency alert
- [ ] Backup encryption key

---

## 🐛 Debugging

### View Logs
```bash
# Real-time logs
sudo journalctl -u mecamera -f

# Last 50 lines
sudo journalctl -u mecamera -n 50

# By date
sudo journalctl -u mecamera --since "2024-01-14"
```

### Restart Service
```bash
# Restart
sudo systemctl restart mecamera

# Stop
sudo systemctl stop mecamera

# Start
sudo systemctl start mecamera

# Check status
sudo systemctl status mecamera
```

### Debug Motion Logging
```bash
# Check motion events file
cat logs/motion_events.json | python3 -m json.tool | head -20

# Export and analyze
curl http://localhost:8080/api/motion/export > events.csv
```

### Check Camera
```bash
# Camera detected?
vcgencmd get_camera

# Test streaming
curl http://localhost:8080/api/stream --max-time 2 | file -
```

---

## 📦 Dependencies

### System
```
python3, pip, ffmpeg, libcamera, git
```

### Python
```
flask==2.3.0
werkzeug==2.3.0
cryptography==41.0.0
loguru==0.7.2
qrcode==7.4.2
Pillow==10.0.0
```

### Optional
```
google-auth-oauthlib  # Google Drive
twilio                # SMS alerts
requests             # HTTP calls
```

---

## 🎯 Common Tasks

### Add New Configuration Option
```python
# 1. Update config_default.json
{
  "my_setting": "default_value"
}

# 2. Access in code
cfg = get_config()
value = cfg.get("my_setting", "default")

# 3. Update in settings form (config.html)
<input name="my_setting" value="{{ config.my_setting }}">

# 4. Save in settings route (app.py)
cfg["my_setting"] = request.form.get("my_setting", "default")
save_config(cfg)
```

### Add New API Endpoint
```python
# In web/app.py
@app.route("/api/my-endpoint", methods=["GET", "POST"])
def my_endpoint():
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # Your code here
        return jsonify({"ok": True, "data": "..."})
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
```

### Update Dashboard
```javascript
// In dashboard.html JavaScript
fetch('/api/my-endpoint')
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            // Update UI
            document.getElementById('element').innerHTML = data.data;
        }
    })
    .catch(e => console.error('Error:', e));
```

---

## 📊 Performance Optimization

### For Pi Zero
```json
{
  "camera": {
    "stream_quality": "low",     // 320x240 @ 10fps
    "stream_fps": 10,
    "resolution": "320x240"
  },
  "detection": {
    "sensitivity": 0.7,          // Less sensitive = faster
    "motion_check_interval": 0.5 // Check every 500ms
  }
}
```

### For Pi 4+
```json
{
  "camera": {
    "stream_quality": "high",    // 1280x720 @ 25fps
    "stream_fps": 25,
    "resolution": "1280x720"
  },
  "detection": {
    "sensitivity": 0.5,
    "motion_check_interval": 0.2
  }
}
```

---

## 🔄 Updates & Maintenance

### Update Application
```bash
cd ~/ME_CAM-DEV
git pull origin main
sudo systemctl restart mecamera
```

### Backup Configuration
```bash
# Backup config and encryption key
tar czf ~/mecamera_backup.tar.gz \
  config/config.json \
  config/.encryption_key \
  logs/motion_events.json
```

### Log Rotation
```bash
# Already configured via:
# /etc/logrotate.d/mecamera

# Manual rotation
sudo logrotate /etc/logrotate.d/mecamera
```

---

## 📚 Additional Resources

- [Complete Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Feature Summary](IMPLEMENTATION_SUMMARY.md)
- [Configuration Reference](docs/CONFIG.md)
- [Troubleshooting Guide](docs/TROUBLESHOOT.md)

---

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit PR with description

---

**Made with ❤️ for privacy-conscious users** 🔐
