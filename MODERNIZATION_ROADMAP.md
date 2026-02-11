# ME_CAM Modernization Roadmap 2026

**Objective:** Transform ME_CAM from a local-network camera system into a production-grade security platform that competes with Ring, Nest, and Arlo while maintaining the lightweight footprint for Pi Zero 2W.

**Status:** v2.2.3 → v3.0 (Professional Release)

---

## Executive Summary

Current state: ME_CAM is a solid **local-network camera system** with:
- ✅ MJPEG streaming (works on local WiFi)
- ✅ Motion detection (basic pixel-change detection)
- ✅ Event recording (stores to local SD card)
- ✅ Lightweight design (150MB RAM on Pi Zero 2W)

**The Gap:** Users must be on the same local network (10.2.1.x IP range) to access their camera. This is the #1 barrier to adoption vs competitors.

**The Solution:** Enable **remote access without port forwarding** + **smart AI detection** + **cloud-aware storage** while keeping the lightweight edge-processing design.

---

## Phase 1: Remote Access (CRITICAL - Weeks 1-2)

### 1.1 Implement WebRTC (Immediate Low-Latency Remote Video)

**Why:** MJPEG over HTTPS still relies on local IP discovery. WebRTC handles NAT traversal automatically.

**Files to Create:**
- `src/streaming/webrtc_peer.py` - STUN/TURN server integration
- `web/templates/webrtc_viewer.html` - Browser-based peer connection
- `src/utils/ice_candidates.py` - ICE candidate gathering

**Implementation:**

```python
# src/streaming/webrtc_peer.py
from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer
from loguru import logger

class WebRTCStreamer:
    def __init__(self, stun_servers=None, turn_servers=None):
        """Initialize WebRTC with STUN/TURN for NAT traversal"""
        self.config = RTCConfiguration(
            iceServers=[
                RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
                RTCIceServer(urls=["stun:stun1.l.google.com:19302"]),
            ] + (turn_servers or [])
        )
        self.pc = RTCPeerConnection(configuration=self.config)
        self.logger = logger.bind(name="WebRTC")
    
    async def create_offer(self):
        """Create SDP offer for client"""
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        return self.pc.localDescription
    
    async def set_remote_description(self, answer):
        """Accept client's SDP answer"""
        await self.pc.setRemoteDescription(answer)
```

**Integration Points:**
- Modify `web/app_lite.py` to add `/webrtc/offer` and `/webrtc/answer` endpoints
- Update `requirements.txt` to add: `aiortc>=1.5.0`
- Create signaling mechanism for SDP exchange

**Expected Outcome:**
- Users can access camera from cellular data
- Latency ~200-400ms (vs 50-100ms local MJPEG)
- Works with NAT/firewalls automatically

---

### 1.2 Implement Tailscale VPN Tunnel (Zero-Configuration Remote Access)

**Why:** WebRTC works for video, but full system access needs a VPN tunnel. Tailscale is simpler than port forwarding.

**Files to Create:**
- `setup_scripts/tailscale_setup.sh` - One-click Tailscale install
- `src/networking/tailscale_helper.py` - Check Tailscale status
- `web/templates/remote_access.html` - UI showing Tailscale URL

**Implementation:**

```bash
#!/bin/bash
# setup_scripts/tailscale_setup.sh

echo "Installing Tailscale..."
curl -fsSL https://tailscale.com/install.sh | sh

echo "Starting Tailscale..."
sudo tailscale up --accept-routes --advertise-exit-node

# Get Tailscale IP
TAILSCALE_IP=$(tailscale ip -4)
echo "Tailscale IP: $TAILSCALE_IP"
echo "Access your camera at: http://$TAILSCALE_IP:8080"
```

**Integration:**
- Add dashboard widget showing "Remote Access URL"
- Auto-detect and display Tailscale IP if connected
- Fall back to MJPEG if no tunnel available

**Expected Outcome:**
- One command setup: `curl -fsSL https://me-cam.sh | bash`
- Users get persistent URL like `100.64.1.50` (Tailscale IP)
- Works from anywhere without exposing home network

---

### 1.3 Cloudflare Tunnel Alternative (No Tailscale Account Required)

**Files to Create:**
- `setup_scripts/cloudflare_tunnel_setup.sh`
- `src/networking/cloudflare_helper.py`

**Implementation:**

```bash
#!/bin/bash
# setup_scripts/cloudflare_tunnel_setup.sh

echo "Installing Cloudflare Tunnel..."
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm -O /tmp/cloudflared
chmod +x /tmp/cloudflared
sudo mv /tmp/cloudflared /usr/local/bin/

echo "Login to Cloudflare..."
cloudflared tunnel login

echo "Creating tunnel for ME_CAM..."
cloudflared tunnel create me-cam-$HOSTNAME
cloudflared tunnel route dns me-cam-$HOSTNAME mycamera.me-cam.com

# Create config
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml << EOF
tunnel: me-cam-$HOSTNAME
credentials-file: /home/pi/.cloudflared/$(cloudflared tunnel info me-cam-$HOSTNAME --token | jq -r '.TunnelID').json

ingress:
  - hostname: mycamera.me-cam.com
    service: http://localhost:8080
  - service: http_status:404
EOF

sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

**Integration:**
- Detect if Cloudflare tunnel is configured
- Show public URL in dashboard (e.g., `https://mycamera-[device-id].me-cam.com`)
- Option to auto-register custom domain

**Expected Outcome:**
- Public HTTPS URL: `https://mycamera-abc123.me-cam.com`
- No port forwarding needed
- Works from anywhere globally

---

## Phase 2: Smart AI Detection (Weeks 3-4)

### 2.1 Edge AI with TensorFlow Lite

**Why:** Current motion detection triggers on shadows/pets. TensorFlow Lite on Pi Zero 2W can distinguish:
- Person detected → Alert user
- Pet detected → Log silently
- Unknown object → Alert with snapshot

**Files to Create:**
- `src/detection/tflite_detector.py` - TensorFlow Lite person/object detection
- `src/detection/smart_motion_filter.py` - Intelligent alert logic
- `models/mobilenet_ssd_v2_coco.tflite` - Download from TensorFlow Hub

**Installation:**

```bash
pip install tflite-runtime==2.11.0

# Download model (13MB)
wget https://storage.googleapis.com/download.tensorflow.org/models/tflite/coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.zip
unzip coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.zip -d models/
```

**Implementation:**

```python
# src/detection/tflite_detector.py
import tflite_runtime.interpreter as tflite
import numpy as np
from loguru import logger

class TFLiteDetector:
    def __init__(self, model_path, threshold=0.5):
        self.interpreter = tflite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.threshold = threshold
        self.logger = logger.bind(name="TFLite")
    
    def detect_objects(self, frame: np.ndarray) -> dict:
        """Run inference on frame, return detected objects"""
        input_details = self.interpreter.get_input_details()
        output_details = self.interpreter.get_output_details()
        
        # Resize frame to model input size
        input_shape = input_details[0]['shape']
        resized = cv2.resize(frame, (input_shape[2], input_shape[1]))
        resized = np.expand_dims(resized, axis=0).astype(np.uint8)
        
        self.interpreter.set_tensor(input_details[0]['index'], resized)
        self.interpreter.invoke()
        
        # Parse outputs
        detections = self.interpreter.get_tensor(output_details[0]['index'])
        classes = self.interpreter.get_tensor(output_details[1]['index'])
        scores = self.interpreter.get_tensor(output_details[2]['index'])
        
        results = {
            'person': [],
            'pet': [],
            'vehicle': [],
            'unknown': []
        }
        
        for i, score in enumerate(scores[0]):
            if score > self.threshold:
                class_id = int(classes[0][i])
                class_name = self._get_class_name(class_id)
                results[class_name].append({
                    'confidence': float(score),
                    'class': class_name,
                    'box': detections[0][i].tolist()
                })
        
        return results
    
    def _get_class_name(self, class_id: int) -> str:
        """Map COCO class IDs to categories"""
        coco_names = {1: 'person', 16: 'dog', 17: 'cat', 2: 'vehicle'}
        return coco_names.get(class_id, 'unknown')
```

**Integration Points:**
- Replace motion detection with dual-layer:
  1. Fast pixel-change detection (trigger frame grab)
  2. TensorFlow inference on frame (decide alert)
- Log detection results: `{"timestamp": "2026-02-04T12:34:56Z", "detected": ["person", "dog"], "confidence": 0.89}`
- Store detection metadata with video clips

**Memory Management:**
- TensorFlow Lite is ~50MB RAM vs 400MB for full TensorFlow
- Model quantization reduces to 4-13MB
- Run inference every 2-5 seconds (not every frame)

**Expected Outcome:**
- "Person detected at front door" vs generic "Motion detected"
- Significantly fewer false alerts from pets/shadows
- Premium feature comparable to Nest/Arlo

---

### 2.2 Rich Push Notifications with Snapshots

**Files to Create:**
- `src/notifications/push_notifier.py` - FCM integration
- `src/notifications/snapshot_handler.py` - Capture + compress snapshot
- `web/templates/notification_settings.html` - FCM token management

**Implementation:**

```python
# src/notifications/push_notifier.py
import firebase_admin
from firebase_admin import credentials, messaging
from loguru import logger
from PIL import Image
import io
import base64

class PushNotifier:
    def __init__(self, credentials_path: str):
        firebase_admin.initialize_app(
            credentials.Certificate(credentials_path)
        )
        self.logger = logger.bind(name="Push")
    
    async def send_alert(self, token: str, title: str, 
                        body: str, snapshot_path: str = None):
        """Send push notification with optional snapshot"""
        
        # Build notification
        message_dict = {
            'notification': {
                'title': title,
                'body': body,
                'clickAction': 'https://camera.me-cam.com/events'
            },
            'android': {
                'priority': 'high',
                'notification': {
                    'sound': 'default'
                }
            },
            'apns': {
                'headers': {
                    'apns-priority': '10'
                }
            }
        }
        
        # Attach snapshot if available
        if snapshot_path and os.path.exists(snapshot_path):
            with Image.open(snapshot_path) as img:
                # Compress to ~50KB for notification
                img.thumbnail((320, 240))
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=75)
                snapshot_b64 = base64.b64encode(buffer.getvalue()).decode()
                
                message_dict['webpush'] = {
                    'data': {'snapshot': snapshot_b64}
                }
        
        message = messaging.Message(**message_dict, token=token)
        response = messaging.send(message)
        self.logger.success(f"Push sent: {response}")
```

**Integration:**
- Add Firebase config to `config/firebase_config.json`
- Create mobile app (React Native/Flutter) that registers FCM token
- On motion alert: capture snapshot, send push + snapshot
- Deep link to event details in app

**Expected Outcome:**
- User gets push: "Person detected at 2:34 PM" with snapshot
- No need to open browser to see what triggered alert
- Same UX as Ring/Nest apps

---

## Phase 3: Cloud Storage & Events (Weeks 5-6)

### 3.1 Event-Based Cloud Backup

**Files to Create:**
- `src/cloud/s3_uploader.py` - AWS S3 integration
- `src/cloud/gcs_uploader.py` - Google Cloud Storage integration
- `config/cloud_config.json` - Cloud credentials template

**Implementation:**

```python
# src/cloud/s3_uploader.py
import boto3
from loguru import logger
import asyncio
from datetime import datetime

class S3EventUploader:
    def __init__(self, bucket: str, region: str, 
                 access_key: str, secret_key: str):
        self.s3 = boto3.client(
            's3',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        self.bucket = bucket
        self.logger = logger.bind(name="S3")
    
    async def upload_event(self, video_path: str, 
                          event_metadata: dict) -> str:
        """Upload event clip to S3, return cloud URL"""
        
        timestamp = datetime.utcnow().isoformat()
        device_id = event_metadata.get('device_id', 'unknown')
        detection_type = event_metadata.get('detection', 'motion')
        
        # S3 path: /me-cam/device-id/events/2026/02/04/12-34-56.mp4
        s3_key = (
            f"me-cam/{device_id}/events/"
            f"{timestamp[:10].replace('-', '/')}/{timestamp[11:19].replace(':', '-')}.mp4"
        )
        
        try:
            # Upload with metadata
            self.s3.upload_file(
                video_path, self.bucket, s3_key,
                ExtraArgs={
                    'Metadata': {
                        'device-id': device_id,
                        'detection': detection_type,
                        'timestamp': timestamp,
                        'confidence': str(event_metadata.get('confidence', '0'))
                    },
                    'ContentType': 'video/mp4'
                }
            )
            
            url = f"https://{self.bucket}.s3.amazonaws.com/{s3_key}"
            self.logger.success(f"Event uploaded: {s3_key}")
            return url
            
        except Exception as e:
            self.logger.error(f"S3 upload failed: {e}")
            return None
    
    async def list_events(self, device_id: str, 
                         days: int = 7) -> list:
        """List recent events for device"""
        from datetime import timedelta
        
        prefix = f"me-cam/{device_id}/events/"
        paginator = self.s3.get_paginator('list_objects_v2')
        
        events = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get('Contents', []):
                events.append({
                    'key': obj['Key'],
                    'timestamp': obj['LastModified'],
                    'size': obj['Size'],
                    'url': f"https://{self.bucket}.s3.amazonaws.com/{obj['Key']}"
                })
        
        return sorted(events, key=lambda x: x['timestamp'], reverse=True)
```

**Integration:**
- On motion alert with person detected: upload to S3 (async)
- Keep 7 days of clips on local storage
- Archive older clips to S3
- Provide S3 URL in event list UI

**Cost Model:**
- AWS S3: ~$0.023 per GB/month
- 10 events/day @ 30 sec each = ~15GB/month = $0.35/month per camera
- **Customer subscription:** $9.99/month for unlimited cloud storage (vs Ring's $10/month)

**Expected Outcome:**
- Camera stolen? Events still in cloud
- 30-day event archive available
- "Cloud Backup Active" badge on dashboard

---

### 3.2 Visual Event Timeline UI

**Files to Create:**
- `web/templates/events_timeline.html` - Timeline view
- `web/static/js/timeline.js` - Interactive timeline
- `src/api/events_api.py` - Timeline API endpoints

**Implementation:**

```html
<!-- web/templates/events_timeline.html -->
<div id="timeline-container">
  <div class="timeline-header">
    <h2>📅 Events Timeline</h2>
    <div class="timeline-filters">
      <input type="date" id="filter-date" />
      <select id="filter-type">
        <option value="">All Events</option>
        <option value="person">Person Detected</option>
        <option value="motion">Motion Only</option>
      </select>
    </div>
  </div>
  
  <div class="timeline-scroll">
    <div id="timeline-items"></div>
  </div>
</div>

<script>
// Load timeline events
async function loadTimeline(date) {
  const response = await fetch(`/api/events/timeline?date=${date}`);
  const events = await response.json();
  
  const timeline = document.getElementById('timeline-items');
  timeline.innerHTML = events.map(e => `
    <div class="timeline-item" data-id="${e.id}">
      <div class="timeline-time">${e.timestamp}</div>
      <div class="timeline-thumbnail">
        <img src="${e.snapshot_url}" alt="${e.detection}" />
        <span class="timeline-badge">${e.detection}</span>
      </div>
      <div class="timeline-details">
        <p>${e.detection} detected (${e.confidence}%)</p>
        <a href="${e.video_url}" download>Download Video</a>
      </div>
    </div>
  `).join('');
}

loadTimeline(new Date().toISOString().split('T')[0]);
</script>
```

**API Endpoints:**
- `GET /api/events/timeline?date=2026-02-04` → List events with thumbnails
- `GET /api/events/:id/video` → Stream event video
- `GET /api/events/:id/snapshot` → Get snapshot image

**Expected Outcome:**
- Similar to Nest/Blink timeline UI
- Scroll through day's events with thumbnails
- Click to view full video
- Filter by detection type

---

## Phase 4: Hardware Optimization (Week 7)

### 4.1 Optimized `/boot/firmware/config.txt` for Pi Zero 2W

**Create:**
- `setup_scripts/optimize_pi_zero.sh` - Auto-apply optimal settings

**Implementation:**

```bash
#!/bin/bash
# setup_scripts/optimize_pi_zero.sh

sudo tee /boot/firmware/config.txt > /dev/null << EOF
# ME_CAM Optimized Pi Zero 2W Configuration
# ==========================================

[all]

# Disable unnecessary services
dtparam=audio=off
dtparam=bt=off
dtparam=spi=off
dtparam=i2c_arm=off

# GPU Memory: Allocate 256MB for hardware encoding
gpu_mem=256

# Camera configuration (Arducam V3)
camera_auto_detect=0
dtoverlay=imx708
dtparam=i2c_vc=on

# Overclock GPU for video encoding (safe)
gpu_freq=500

# CPU overclock (optional, for motion detection)
arm_freq=1200
# arm_boost=1  # Uncomment for aggressive boost

# Disable desktop/X11 (we're headless)
disable_splash=1

# Enable SSH
dtparam=ssh=on

# Enable hardware watchdog
dtparam=watchdog=on

# Reduce power consumption
undervolting=0  # Safe default
EOF

echo "✅ Pi Zero 2W optimization applied"
echo "Reboot required: sudo reboot"
```

**Expected Improvements:**
- H.264 encoding uses GPU (frees CPU for detection)
- 256MB GPU memory = smooth 30FPS @ 640x480
- Disabling unused services = +50MB free RAM
- Total available RAM: ~250MB (up from ~150MB)

### 4.2 H.264 Hardware Encoder Configuration

**Files to Create:**
- `src/camera/h264_encoder.py` - Hardware-accelerated H.264 encoding

**Implementation:**

```python
# src/camera/h264_encoder.py
import subprocess
from loguru import logger

class H264Encoder:
    def __init__(self, width=640, height=480, fps=30, bitrate=1500):
        """Initialize H.264 hardware encoder"""
        self.width = width
        self.height = height
        self.fps = fps
        self.bitrate = bitrate
        self.logger = logger.bind(name="H264")
    
    def capture_stream(self):
        """Start h264 encoding stream using GPU"""
        cmd = [
            'libcamera-vid',
            '--width', str(self.width),
            '--height', str(self.height),
            '--framerate', str(self.fps),
            '--bitrate', str(self.bitrate * 1000),  # Convert to kbps
            '--codec', 'h264',
            '--inline',  # Include SPS/PPS in stream
            '--listen',
            '--output', 'tcp://127.0.0.1:5555'
        ]
        
        self.logger.info(f"Starting H.264 stream: {self.width}x{self.height} @ {self.fps}FPS")
        self.process = subprocess.Popen(cmd)
        return self.process
```

**Benefits:**
- GPU encodes video (uses <5% CPU)
- CPU free for motion detection/AI inference
- Smoother playback, lower latency
- Battery life improvement on mobile clients

---

## Phase 5: UI/UX Enhancements (Week 8)

### 5.1 Privacy Zone Drawing Feature

**Files to Create:**
- `web/templates/privacy_zones.html` - Zone editor
- `web/static/js/canvas-draw.js` - Polygon drawing
- `src/detection/privacy_zone_mask.py` - Zone masking

**Implementation:**

```python
# src/detection/privacy_zone_mask.py
import cv2
import numpy as np
from typing import List, Tuple

class PrivacyZoneMask:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.zones = []  # List of polygon points
        self.mask = np.ones((height, width), dtype=np.uint8)
    
    def add_zone(self, polygon: List[Tuple[int, int]], name: str):
        """Add privacy zone (polygon of points)"""
        points = np.array(polygon, dtype=np.int32)
        self.zones.append({'name': name, 'points': points})
        
        # Update mask: set zone to 0 (masked)
        cv2.fillPoly(self.mask, [points], 0)
    
    def apply_mask(self, frame: np.ndarray) -> np.ndarray:
        """Apply privacy zones to frame"""
        # Blur masked areas
        blurred = cv2.GaussianBlur(frame, (51, 51), 0)
        
        # Blend: masked areas use blur, others use original
        self.mask_3ch = cv2.cvtColor(self.mask, cv2.COLOR_GRAY2BGR)
        masked_frame = np.where(
            self.mask_3ch == 1, 
            frame, 
            blurred
        )
        
        return masked_frame.astype(np.uint8)
    
    def apply_to_detection(self, detections: dict) -> dict:
        """Filter detections outside privacy zones"""
        filtered = detections.copy()
        
        for zone in self.zones:
            for detection_type in ['person', 'pet', 'vehicle']:
                filtered[detection_type] = [
                    d for d in detections[detection_type]
                    if not self._in_zone(d['box'], zone['points'])
                ]
        
        return filtered
    
    def _in_zone(self, bbox, polygon) -> bool:
        """Check if bounding box overlaps privacy zone"""
        x1, y1, x2, y2 = bbox
        pts = polygon.reshape((-1, 2))
        return cv2.pointPolygonTest(pts, ((x1+x2)/2, (y1+y2)/2), False) >= 0
```

**UI Implementation:**

```html
<!-- web/templates/privacy_zones.html -->
<div class="privacy-zone-editor">
  <h2>🔒 Privacy Zones</h2>
  <p>Draw areas to blur/exclude from detection</p>
  
  <div class="canvas-container">
    <img id="camera-snapshot" src="/api/latest-snapshot" alt="Camera feed" />
    <canvas id="zone-canvas" style="position: absolute; top: 0; left: 0;"></canvas>
  </div>
  
  <div class="zone-controls">
    <button onclick="startDrawing('blur')">🟨 Blur Zone</button>
    <button onclick="startDrawing('exclude')">🚫 Exclude Zone</button>
    <button onclick="saveZones()">💾 Save Zones</button>
    <button onclick="clearZones()">🗑️ Clear All</button>
  </div>
  
  <div id="zones-list"></div>
</div>

<script>
const canvas = document.getElementById('zone-canvas');
const ctx = canvas.getContext('2d');
let isDrawing = false;
let currentZone = [];

canvas.addEventListener('mousedown', (e) => {
  isDrawing = true;
  const rect = canvas.getBoundingClientRect();
  currentZone.push([e.clientX - rect.left, e.clientY - rect.top]);
});

canvas.addEventListener('mousemove', (e) => {
  if (!isDrawing) return;
  // Draw preview line
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = 'rgba(255, 255, 0, 0.5)';
  // Draw polygon preview...
});

async function saveZones() {
  await fetch('/api/privacy-zones', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({zones: currentZone})
  });
}
</script>
```

**Integration:**
- Load privacy zones on startup
- Apply mask to stream before display
- Filter detections by zone
- Persist zones in `config/privacy_zones.json`

**Expected Outcome:**
- Users blur keypad/neighbor's window
- Exclude low-traffic zones from alerts
- Premium feature in Nest/Arlo

---

### 5.2 Multi-Camera Grid View

**Files to Create:**
- `web/templates/grid_view.html` - Grid layout
- `web/static/css/grid.css` - Responsive grid styling
- `src/api/multicam_api.py` - Multi-camera API

**Implementation:**

```html
<!-- web/templates/grid_view.html -->
<div class="cameras-grid">
  <h2>📹 Multiple Cameras</h2>
  
  <div class="grid-controls">
    <button onclick="setGridLayout(1)">1x1</button>
    <button onclick="setGridLayout(2)">2x2</button>
    <button onclick="setGridLayout(3)">3x3</button>
    <select id="sort-by">
      <option>Recent Activity</option>
      <option>Device Name</option>
    </select>
  </div>
  
  <div class="camera-grid" id="camera-grid"></div>
</div>

<script>
async function loadCameras() {
  const response = await fetch('/api/cameras/list');
  const cameras = await response.json();
  
  const grid = document.getElementById('camera-grid');
  grid.innerHTML = cameras.map(cam => `
    <div class="camera-card">
      <div class="camera-feed">
        <img src="/api/cameras/${cam.id}/snapshot" alt="${cam.name}" />
        <div class="camera-status ${cam.online ? 'online' : 'offline'}"></div>
      </div>
      <div class="camera-info">
        <h3>${cam.name}</h3>
        <p>${cam.location}</p>
        <div class="camera-stats">
          <span>🎬 ${cam.events_today} events</span>
          <span>📡 ${cam.online ? 'Online' : 'Offline'}</span>
        </div>
        <a href="/camera/${cam.id}" class="view-btn">View Details</a>
      </div>
    </div>
  `).join('');
}

// Load on page load
loadCameras();
```

**CSS for responsive grid:**

```css
/* web/static/css/grid.css */
.camera-grid {
  display: grid;
  gap: 1rem;
  margin-top: 1rem;
}

.camera-grid.grid-1x1 { grid-template-columns: 1fr; }
.camera-grid.grid-2x2 { grid-template-columns: repeat(2, 1fr); }
.camera-grid.grid-3x3 { grid-template-columns: repeat(3, 1fr); }

.camera-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.2s;
}

.camera-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}

.camera-feed {
  position: relative;
  aspect-ratio: 16/9;
  background: #000;
  overflow: hidden;
}

.camera-feed img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.camera-status {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #ccc;
}

.camera-status.online {
  background: #4caf50;
  box-shadow: 0 0 8px #4caf50;
}

@media (max-width: 768px) {
  .camera-grid.grid-2x2 { grid-template-columns: 1fr; }
  .camera-grid.grid-3x3 { grid-template-columns: repeat(2, 1fr); }
}
```

**Integration:**
- Detect multiple `mecamdev*` devices on network
- Show grid of live feeds
- Click camera to expand for details
- Sync across browser tabs (WebSocket)

**Expected Outcome:**
- Monitor 2-4 cameras on one screen
- Instantly see which cameras are online
- Quick access to specific camera feeds

---

## Phase 6: Deployment & Documentation (Week 9)

### 6.1 Unified Installation Script

**File:** `install.sh`

```bash
#!/bin/bash
# ME_CAM v3.0 Installation Script
# One command to rule them all

set -e

echo "╔════════════════════════════════════════╗"
echo "║  ME_CAM v3.0 Professional Installation ║"
echo "║    Raspberry Pi Zero 2W + Arducam V3   ║"
echo "╚════════════════════════════════════════╝"

# 1. System updates
echo "[1/8] Updating system..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install dependencies
echo "[2/8] Installing dependencies..."
sudo apt-get install -y \
    python3-pip python3-venv \
    libcamera-apps python3-opencv \
    libraspberrypi-dev \
    git curl wget

# 3. Clone repo
echo "[3/8] Cloning ME_CAM repository..."
cd ~
git clone https://github.com/MangiafestoElectronicsLLC/ME_CAM.git
cd ME_CAM

# 4. Create venv
echo "[4/8] Creating Python environment..."
python3 -m venv venv --system-site-packages
source venv/bin/activate

# 5. Install Python packages
echo "[5/8] Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt
pip install aiortc>=1.5.0 tflite-runtime boto3

# 6. Download ML models
echo "[6/8] Downloading ML models (50MB)..."
mkdir -p models
wget -q https://storage.googleapis.com/download.tensorflow.org/models/tflite/coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.zip -O /tmp/model.zip
unzip -q /tmp/model.zip -d models/

# 7. Optimize hardware
echo "[7/8] Optimizing Pi Zero 2W..."
bash setup_scripts/optimize_pi_zero.sh

# 8. Install service
echo "[8/8] Installing systemd service..."
sudo tee /etc/systemd/system/mecamera.service > /dev/null << 'SERVICEEOF'
[Unit]
Description=ME_CAM Security Camera v3.0
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ME_CAM
Environment="PATH=/home/pi/ME_CAM/venv/bin:/usr/bin:/bin"
ExecStart=/home/pi/ME_CAM/venv/bin/python3 /home/pi/ME_CAM/main_lite.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICEEOF

sudo systemctl daemon-reload
sudo systemctl enable mecamera
sudo systemctl start mecamera

echo ""
echo "╔════════════════════════════════════════╗"
echo "║      ✅ ME_CAM Installation Complete!  ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "📱 Local Dashboard: http://$(hostname -I | awk '{print $1}'):8080"
echo ""
echo "🌐 Enable Remote Access:"
echo "   Option 1: curl -fsSL https://tailscale.com/install.sh | sh"
echo "   Option 2: bash setup_scripts/cloudflare_tunnel_setup.sh"
echo ""
echo "🚀 Next steps:"
echo "   1. Configure WiFi: http://$(hostname -I | awk '{print $1}'):8080/config"
echo "   2. Set up cloud backup: Dashboard → Settings → Cloud"
echo "   3. Enable notifications: Dashboard → Settings → Alerts"
echo ""
echo "📖 Documentation: https://github.com/MangiafestoElectronicsLLC/ME_CAM"

sudo reboot
```

### 6.2 Comprehensive README

Update `README.md` with:
- Architecture diagram (local processing + cloud sync)
- Feature comparison table (vs Ring/Nest/Arlo)
- Quick start (3 steps)
- Troubleshooting guide
- Performance benchmarks

---

## Implementation Schedule

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1-2  | Remote Access | WebRTC + Tailscale tunneling |
| 3-4  | AI Detection | TensorFlow Lite + Push notifications |
| 5-6  | Cloud Storage | S3 backup + Event timeline UI |
| 7    | Hardware | Pi Zero optimization + H.264 encoder |
| 8    | UI/UX | Privacy zones + Multi-camera grid |
| 9    | Deploy | Unified installer + Docs + Release |

---

## Success Metrics

✅ **Adoption:** User can set up in <10 minutes without technical knowledge  
✅ **Remote Access:** Works from cellular data without port forwarding  
✅ **AI Accuracy:** <5% false alerts (vs 30% for basic motion detection)  
✅ **Performance:** 30FPS @ 640x480 on Pi Zero 2W  
✅ **Privacy:** All video processing happens locally (no cloud processing)  
✅ **Reliability:** 99.9% uptime, auto-recovery from crashes  

---

## Competitive Positioning

| Feature | ME_CAM | Ring | Nest | Arlo |
|---------|--------|------|------|------|
| Local Processing | ✅ Yes | ❌ Cloud-only | ✅ Yes | ✅ Yes |
| Zero Subscription | ✅ Yes | ❌ $10/mo | ❌ $12/mo | ❌ $3/mo |
| DIY Installation | ✅ Yes | ❌ Pro install | ✅ Yes | ✅ Yes |
| Person Detection | ✅ v3.0 | ✅ Yes | ✅ Yes | ✅ Yes |
| Multi-Camera Grid | ✅ v3.0 | ✅ Yes | ✅ Yes | ✅ Yes |
| Privacy Zones | ✅ v3.0 | ❌ No | ❌ No | ❌ No |
| Open Source | ✅ Yes | ❌ No | ❌ No | ❌ No |
| Pi Zero Compatible | ✅ Yes | ❌ No | ❌ No | ❌ No |
| RTSP Export | ✅ Yes | ❌ No | ❌ No | ❌ No |

---

## Conclusion

ME_CAM v3.0 transforms from "local network camera" to "production security platform" while maintaining:
- **Edge-first design:** Processing happens locally
- **Privacy-first:** No cloud surveillance
- **Hardware-optimized:** Works flawlessly on Pi Zero 2W
- **Open source:** Community improvements

**Target Market:** Developers, makers, and privacy-conscious users who want Ring-quality features without the subscription model.

---

**Created:** February 4, 2026  
**Status:** Ready for implementation  
**Priority:** Phase 1 (Remote Access) → Launch MVP → Expand features
