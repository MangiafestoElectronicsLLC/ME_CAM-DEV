from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response, send_file
from threading import Event
from loguru import logger
import os
from datetime import datetime
import time
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

# Import from organized structure
from src.core import (
    get_config, save_config, is_first_run, mark_first_run_complete,
    authenticate, create_user, user_exists, get_user,
    BatteryMonitor, extract_thumbnail, generate_setup_qr,
    log_motion_event, get_recent_events, get_event_statistics, export_events_csv
)
from src.camera import (
    camera_coordinator, LibcameraStreamer, is_libcamera_available,
    FastCameraStreamer, FastMotionDetector, PICAMERA2_AVAILABLE
)
from src.detection import motion_service, CameraWatchdog

# Check if fast streamer available
fast_streamer_available = PICAMERA2_AVAILABLE

# Explicitly set template/static folders inside the web package to avoid confusion
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.urandom(24)

# DISABLED: Camera pipeline conflicts with libcamera-still streaming
# watchdog = CameraWatchdog()
# watchdog.start()
watchdog = None  # Disabled to allow libcamera streaming

battery = BatteryMonitor(enabled=True)

# Initialize camera streamer - use fast streamer if available
cfg = get_config()
use_fast = cfg.get("camera", {}).get("use_fast_streamer", True)

camera_available = False
camera_streamer = None
fast_motion_detector = None

if fast_streamer_available and use_fast:
    try:
        # Initialize fast streamer (picamera2 - 15-30 FPS!)
        resolution = cfg.get('camera', {}).get('resolution', '640x480')
        width, height = map(int, resolution.split('x'))
        fps = cfg.get('camera', {}).get('stream_fps', 15)
        
        camera_streamer = FastCameraStreamer(width=width, height=height, fps=fps)
        if camera_streamer.start():
            camera_available = True
            logger.success(f"[CAMERA] Fast streamer initialized: {width}x{height} @ {fps} FPS")
            
            # Initialize fast motion detector
            fast_motion_detector = FastMotionDetector(camera_streamer, cfg)
            logger.info("[CAMERA] Fast motion detector ready")
        else:
            camera_streamer = None
    except Exception as e:
        logger.error(f"[CAMERA] Fast streamer initialization failed: {e}")
        camera_streamer = None

# PRIORITY 1: Try legacy camera first (for older Pi cameras with legacy stack)
if not camera_streamer:
    import subprocess
    try:
        result = subprocess.run(['vcgencmd', 'get_camera'], capture_output=True, text=True, timeout=2)
        if 'detected=1' in result.stdout:
            logger.info("[CAMERA] Legacy camera detected, attempting to use picamera...")
            
            class LegacyCameraStreamer:
                """Legacy camera streamer using picamera v1 - for older Raspberry Pi cameras"""
                def __init__(self):
                    import io
                    self.stream = io.BytesIO()
                    self.camera = None
                    self.running = False
                    
                def start(self):
                    try:
                        import picamera
                        import time
                        self.camera = picamera.PiCamera()
                        self.camera.resolution = (640, 480)
                        self.camera.framerate = 15
                        time.sleep(2)  # Camera warmup
                        self.running = True
                        logger.success("[CAMERA] Legacy camera started successfully")
                        return True
                    except Exception as e:
                        logger.error(f"[CAMERA] Failed to start legacy camera: {e}")
                        return False
                
                def get_jpeg_frame(self):
                    """Capture frame and return as JPEG"""
                    if not self.running or not self.camera:
                        return None
                    
                    try:
                        self.stream.seek(0)
                        self.stream.truncate()
                        self.camera.capture(self.stream, format='jpeg', use_video_port=True)
                        self.stream.seek(0)
                        return self.stream.read()
                    except Exception as e:
                        logger.debug(f"[CAMERA] Frame capture error: {e}")
                        return None
                
                def stop(self):
                    self.running = False
                    if self.camera:
                        self.camera.close()
            
            camera_streamer = LegacyCameraStreamer()
            if camera_streamer.start():
                camera_available = True
    except Exception as e:
        logger.debug(f"[CAMERA] Legacy camera check failed: {e}")

# PRIORITY 2: Try USB camera via OpenCV (for IMX7098 and other USB cameras)
if not camera_streamer:
    logger.info("[CAMERA] Attempting USB camera detection via OpenCV...")
    
    class USBCameraStreamer:
        """USB camera streamer using OpenCV - works with /dev/video* devices"""
        def __init__(self, camera_index=0):
            import cv2
            self.camera_index = camera_index
            self.cap = cv2.VideoCapture(camera_index)
            self.jpeg_data = None
            self.running = False
            
        def start(self):
            if not self.cap.isOpened():
                logger.warning(f"[CAMERA] Could not open /dev/video{self.camera_index}")
                return False
            
            # Set camera resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 15)
            
            self.running = True
            logger.success(f"[CAMERA] USB camera started on /dev/video{self.camera_index}")
            return True
            
        def get_jpeg_frame(self):
            """Capture frame and encode as JPEG"""
            if not self.running or not self.cap.isOpened():
                return None
            
            ret, frame = self.cap.read()
            if not ret or frame is None:
                return None
            
            import cv2
            ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            return jpeg.tobytes() if ret else None
        
        def stop(self):
            self.running = False
            self.cap.release()
    
    # Try to open USB camera (try /dev/video0-23)
    for video_index in range(24):
        try:
            import cv2
            cap = cv2.VideoCapture(f'/dev/video{video_index}')
            if cap.isOpened():
                cap.release()
                camera_streamer = USBCameraStreamer(camera_index=video_index)
                if camera_streamer.start():
                    camera_available = True
                    logger.success(f"[CAMERA] USB camera found and started on /dev/video{video_index}")
                    break
        except Exception as e:
            logger.debug(f"[CAMERA] /dev/video{video_index} check failed: {e}")
            continue

# Fallback to slow libcamera-still approach if USB camera not found
if not camera_streamer and is_libcamera_available():
    camera_streamer = LibcameraStreamer()
    camera_available = True
    logger.info("[CAMERA] Using libcamera-still fallback (slow - 1-2 FPS)")

# Final fallback: TEST MODE with dummy stream
if not camera_streamer:
    logger.warning("[CAMERA] No camera found - enabling TEST MODE with dummy video stream")
    
    class DummyStreamer:
        """Generates dummy MJPEG frames for testing without hardware"""
        def __init__(self):
            import io
            import struct
            self.frame_num = 0
            
            def get_jpeg_frame(self):
                """Generate a valid JPEG frame with test pattern"""
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    import io
                    
                    # Create test image (640x480 by default)
                    img = Image.new('RGB', (640, 480), color=(40, 40, 40))
                    draw = ImageDraw.Draw(img)
                    
                    # Draw test pattern
                    draw.text((50, 50), f"TEST MODE - Frame #{self.frame_num}", fill=(0, 255, 0))
                    draw.text((50, 100), "Camera Hardware Detection Failed", fill=(255, 100, 0))
                    draw.text((50, 150), "Troubleshooting Steps:", fill=(100, 200, 255))
                    draw.text((50, 200), "1. Verify camera cable connection", fill=(100, 200, 255))
                    draw.text((50, 250), "2. Check: libcamera-hello --list-cameras", fill=(100, 200, 255))
                    draw.text((50, 300), "3. Review /boot/config.txt camera settings", fill=(100, 200, 255))
                    draw.text((50, 350), "4. Dashboard features are fully functional", fill=(0, 255, 0))
                    
                    # Draw frame counter animation
                    for i in range(5):
                        x = 100 + (i * 80)
                        if i <= (self.frame_num % 5):
                            draw.rectangle([x, 400, x+60, 450], fill=(0, 255, 0))
                        else:
                            draw.rectangle([x, 400, x+60, 450], outline=(0, 255, 0))
                    
                    # Convert to JPEG
                    jpeg_io = io.BytesIO()
                    img.save(jpeg_io, format='JPEG', quality=70)
                    self.frame_num += 1
                    return jpeg_io.getvalue()
                except ImportError:
                    logger.warning("[DUMMY] PIL not available, returning minimal JPEG")
                    # Return a minimal valid JPEG as fallback
                    return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd6\xff\xd9'
        
        camera_streamer = DummyStreamer()
        camera_available = True
        logger.info("[CAMERA] TEST MODE: Using dummy video stream for dashboard testing")

# Helpers for recordings/storage info
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def _recordings_path(cfg):
    rec_dir = cfg.get("storage", {}).get("recordings_dir", "recordings")
    return os.path.join(BASE_DIR, rec_dir)

def get_recordings(cfg, limit=12):
    path = _recordings_path(cfg)
    thumb_dir = os.path.join(BASE_DIR, "web", "static", "thumbs")
    videos = []
    try:
        os.makedirs(thumb_dir, exist_ok=True)
        if os.path.isdir(path):
            for name in os.listdir(path):
                if name.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
                    full = os.path.join(path, name)
                    ts = os.path.getmtime(full)
                    # Try to extract thumbnail
                    thumb_path = extract_thumbnail(full, thumb_dir)
                    thumb_url = f"/static/thumbs/{os.path.basename(thumb_path)}" if thumb_path else None
                    videos.append({
                        "name": name,
                        "date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M"),
                        "thumb_url": thumb_url
                    })
        videos.sort(key=lambda v: v["date"], reverse=True)
    except Exception as e:
        logger.warning(f"[RECORDINGS] Failed to list recordings: {e}")
    return videos[:limit]

def get_storage_used_gb(cfg):
    paths = [
        _recordings_path(cfg),
        os.path.join(BASE_DIR, cfg.get("storage", {}).get("encrypted_dir", "recordings_encrypted"))
    ]
    total_bytes = 0
    try:
        for path in paths:
            if not os.path.isdir(path):
                continue
            for root, _, files in os.walk(path):
                for f in files:
                    try:
                        total_bytes += os.path.getsize(os.path.join(root, f))
                    except Exception:
                        pass
    except Exception as e:
        logger.warning(f"[STORAGE] Failed to compute size: {e}")
    return round(total_bytes / (1024 ** 3), 2)

def count_recent_events(cfg, hours=24):
    cutoff_ts = (datetime.now()).timestamp() - (hours * 3600)
    count = 0
    try:
        path = _recordings_path(cfg)
        if os.path.isdir(path):
            for name in os.listdir(path):
                if name.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
                    full = os.path.join(path, name)
                    if os.path.getmtime(full) >= cutoff_ts:
                        count += 1
        enc = os.path.join(BASE_DIR, cfg.get("storage", {}).get("encrypted_dir", "recordings_encrypted"))
        if os.path.isdir(enc):
            for name in os.listdir(enc):
                if name.lower().endswith((".enc",)):
                    full = os.path.join(enc, name)
                    if os.path.getmtime(full) >= cutoff_ts:
                        count += 1
    except Exception as e:
        logger.warning(f"[HISTORY] Failed to count recent events: {e}")
    return count

@app.before_request
def ensure_first_run_redirect():
    if request.path.startswith("/static"):
        return
    if is_first_run() and request.path not in ("/setup", "/setup/save"):
        return redirect(url_for("setup"))

@app.route("/setup", methods=["GET"])
def setup():
    cfg = get_config()
    
    # Generate QR code for setup
    qr_code = generate_setup_qr("raspberrypi")
    setup_url = f"http://raspberrypi.local:8080/setup"
    
    return render_template("first_run.html", config=cfg, qr_code=qr_code, setup_url=setup_url)

@app.route("/setup/save", methods=["POST"])
def setup_save():
    cfg = get_config()
    cfg["device_name"] = request.form.get("device_name", cfg["device_name"])
    cfg["pin_enabled"] = request.form.get("pin_enabled") == "on"
    cfg["pin_code"] = request.form.get("pin_code") or cfg["pin_code"]
    cfg["storage"]["retention_days"] = int(request.form.get("retention_days") or 7)
    cfg["storage"]["motion_only"] = request.form.get("motion_only") == "on"
    cfg["storage"]["encrypt"] = request.form.get("encrypt") == "on"
    cfg["detection"]["person_only"] = request.form.get("person_only") == "on"
    cfg["detection"]["sensitivity"] = float(request.form.get("sensitivity") or 0.6)
    cfg["emergency_phone"] = request.form.get("emergency_phone", "")
    save_config(cfg)
    mark_first_run_complete()
    logger.info("[SETUP] First run completed.")
    return redirect(url_for("index"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if authenticate(username, password):
            session["authenticated"] = True
            session["username"] = username
            logger.info(f"[AUTH] User {username} logged in")
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid username or password")
    
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        
        # Validation
        if not username or len(username) < 3:
            return render_template("register.html", error="Username must be at least 3 characters")
        
        if not password or len(password) < 6:
            return render_template("register.html", error="Password must be at least 6 characters")
        
        if password != password_confirm:
            return render_template("register.html", error="Passwords don't match")
        
        if user_exists(username):
            return render_template("register.html", error="Username already exists")
        
        # Create user
        if create_user(username, password):
            logger.info(f"[AUTH] New user registered: {username}")
            return render_template("register.html", success="Account created! Please login.")
        else:
            return render_template("register.html", error="Error creating account")
    
    return render_template("register.html")

def require_auth():
    return session.get("authenticated", False)

@app.route("/")
@app.route("/dashboard")
def index():
    if not require_auth():
        return redirect(url_for("login"))
    
    # Start motion detection service if not already running (with camera coordination)
    if motion_service and not motion_service.running:
        try:
            motion_service.start()
            logger.info("[DASHBOARD] Motion detection service started")
        except Exception as e:
            logger.warning(f"[DASHBOARD] Could not start motion service: {e}")
    
    username = session.get("username", "User")
    try:
        cfg = get_config()
        status = watchdog.status() if watchdog else {"active": True, "timestamp": time.time()}
        battery_status = battery.get_status()
        videos = get_recordings(cfg, limit=12)
        storage_used = get_storage_used_gb(cfg)
        history_count = count_recent_events(cfg, hours=24)
        
        # Get better battery percentage (100% if external power)
        battery_percent = battery_status.get("percent")
        if battery_percent is None and battery_status.get("external_power"):
            battery_percent = 100
        elif battery_percent is None:
            battery_percent = 80  # Default assumption
        
        return render_template("user_dashboard.html",
            username=username,
            device_name=cfg.get("device_name", "ME_CAM_1"),
            status=status,
            battery_percent=battery_percent,
            battery_external=battery_status.get("external_power"),
            battery_low=battery_status.get("is_low"),
            storage_used=storage_used,
            video_count=len(videos),
            videos=videos,
            history_count=history_count,
            emergency_phone=cfg.get("emergency_phone", "Not configured")
        )
    except Exception as e:
        logger.warning(f"[DASHBOARD] Fallback: {e}")
        return render_template("fallback.html", message="Camera unavailable")

@app.route("/user/profile")
def user_profile():
    if not require_auth():
        return redirect(url_for("login"))
    
    username = session.get("username")
    user = get_user(username)
    
    return render_template("user_profile.html", 
        username=username,
        user=user
    )

@app.route("/user/change-password", methods=["GET", "POST"])
def change_password():
    if not require_auth():
        return redirect(url_for("login"))
    
    username = session.get("username")
    
    if request.method == "POST":
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        new_password_confirm = request.form.get("new_password_confirm", "")
        
        if not authenticate(username, old_password):
            return render_template("change_password.html", error="Old password is incorrect")
        
        if len(new_password) < 6:
            return render_template("change_password.html", error="New password must be at least 6 characters")
        
        if new_password != new_password_confirm:
            return render_template("change_password.html", error="Passwords don't match")
        
        from user_auth import change_password as change_pwd
        if change_pwd(username, old_password, new_password):
            logger.info(f"[AUTH] Password changed for {username}")
            return render_template("change_password.html", success="Password changed successfully!")
        else:
            return render_template("change_password.html", error="Error changing password")
    
    return render_template("change_password.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/api/status")
def api_status():
    return jsonify(watchdog.status() if watchdog else {"active": False, "timestamp": time.time()})

@app.route("/api/trigger_emergency", methods=["POST"])
def trigger_emergency():
    """Enhanced emergency trigger with medical and security options"""
    try:
        from emergency_handler import emergency_handler
        
        cfg = get_config()
        emergency_mode = cfg.get('emergency_mode', 'manual')
        
        # Get emergency type from request (default to general)
        emergency_type = request.json.get('type', 'general') if request.is_json else 'general'
        
        logger.critical(f"[EMERGENCY] Emergency trigger activated - Type: {emergency_type}, Mode: {emergency_mode}")
        
        # Get latest recording for evidence
        latest_recording = emergency_handler.get_latest_recording()
        
        # Trigger appropriate emergency response
        if emergency_type == 'medical' or emergency_type == 'seizure':
            success = emergency_handler.trigger_medical_emergency(
                event_type='seizure',
                video_path=latest_recording
            )
            message = f"Medical emergency alert sent to {cfg.get('emergency_primary_contact', 'configured contact')}"
            
        elif emergency_type == 'security' or emergency_type == 'theft':
            success = emergency_handler.trigger_security_emergency(
                event_type='theft',
                video_path=latest_recording
            )
            message = f"Security alert sent to {cfg.get('owner_email', 'configured contacts')}"
            
        else:
            # General emergency (SOS button)
            success = emergency_handler.trigger_general_emergency(
                message="Emergency SOS button pressed"
            )
            message = f"Emergency alert sent to {cfg.get('emergency_primary_contact', cfg.get('emergency_phone', 'Not configured'))}"
        
        if success:
            return jsonify({
                "ok": True,
                "message": message,
                "emergency_type": emergency_type,
                "video_included": latest_recording is not None,
                "timestamp": time.time()
            })
        else:
            return jsonify({
                "ok": False,
                "error": "Failed to send emergency notification. Check email configuration.",
                "timestamp": time.time()
            }), 500
            
    except Exception as e:
        logger.error(f"[EMERGENCY] Error triggering emergency: {e}")
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500

@app.route("/config", methods=["GET", "POST"])
def settings():
    if not require_auth():
        return redirect(url_for("login"))
    
    try:
        cfg = get_config()
        
        if request.method == "POST":
            try:
                # Optional integrations
                cfg["wifi_enabled"] = request.form.get("wifi_enabled") == "on"
                cfg["bluetooth_enabled"] = request.form.get("bluetooth_enabled") == "on"
                
                # Emergency Contacts
                cfg["device_location"] = request.form.get("device_location", "")
                cfg["emergency_primary_contact"] = request.form.get("emergency_primary_contact", "")
                cfg["owner_email"] = request.form.get("owner_email", "")
                
                # Parse comma-separated security contacts
                security_contacts_str = request.form.get("security_contacts", "")
                cfg["security_contacts"] = [c.strip() for c in security_contacts_str.split(",") if c.strip()]
                
                cfg["emergency_mode"] = request.form.get("emergency_mode", "manual")
                
                # Backward compatibility
                cfg["emergency_phone"] = cfg["emergency_primary_contact"]
                
                # Camera settings
                if "camera" not in cfg:
                    cfg["camera"] = {}
                cfg["camera"]["resolution"] = request.form.get("camera_resolution", "640x480")
                cfg["camera"]["recording_resolution"] = request.form.get("recording_resolution", "1280x720")
                cfg["camera"]["recording_duration"] = int(request.form.get("recording_duration", 30))
                
                # Device name
                cfg["device_name"] = request.form.get("device_name", cfg.get("device_name", "ME_CAM_1"))
                
                # Detection settings
                if "detection" not in cfg:
                    cfg["detection"] = {}
                cfg["detection"]["sensitivity"] = float(request.form.get("motion_sensitivity", 0.6))
                
                # Storage settings
                if "storage" not in cfg:
                    cfg["storage"] = {}
                cfg["storage"]["motion_only"] = request.form.get("motion_recording_enabled") == "on"
                cfg["storage"]["retention_days"] = int(request.form.get("storage_retention_days", 7))
                cfg["storage"]["max_storage_gb"] = float(request.form.get("max_storage_gb", 10))
                cfg["storage"]["cleanup_when_full_percent"] = int(request.form.get("cleanup_threshold", 90))
                cfg["storage"]["keep_newest_files"] = request.form.get("keep_newest_files") == "on"
                cfg["storage"]["organize_by_date"] = request.form.get("organize_by_date") == "on"
                cfg["storage"]["thumbnail_generation"] = request.form.get("thumbnail_generation") == "on"
                
                # Camera/Performance settings
                if "camera" not in cfg:
                    cfg["camera"] = {}
                cfg["camera"]["use_fast_streamer"] = request.form.get("use_fast_streamer") == "on"
                cfg["camera"]["stream_fps"] = int(request.form.get("stream_fps", 15))
                cfg["camera"]["motion_check_interval"] = float(request.form.get("motion_check_interval", 0.2))
                
                # Email
                if "email" not in cfg:
                    cfg["email"] = {}
                cfg["email"]["enabled"] = request.form.get("email_enabled") == "on"
                cfg["email"]["smtp_server"] = request.form.get("smtp_server", "")
                cfg["email"]["smtp_port"] = int(request.form.get("smtp_port", 587)) if request.form.get("smtp_port") else 587
                cfg["email"]["username"] = request.form.get("email_username", "")
                cfg["email"]["password"] = request.form.get("email_password", "")
                cfg["email"]["from_address"] = request.form.get("email_from", "")
                cfg["email"]["to_address"] = request.form.get("email_to", "")
                
                # Google Drive
                if "google_drive" not in cfg:
                    cfg["google_drive"] = {}
                cfg["google_drive"]["enabled"] = request.form.get("gdrive_enabled") == "on"
                cfg["google_drive"]["folder_id"] = request.form.get("gdrive_folder_id", "")
                
                # Storage & Notifications
                if "notifications" not in cfg:
                    cfg["notifications"] = {}
                cfg["notifications"]["email_on_motion"] = cfg["email"]["enabled"]
                cfg["notifications"]["gdrive_on_motion"] = cfg["google_drive"]["enabled"]
                
                save_config(cfg)
                logger.info("[SETTINGS] Configuration updated successfully.")
                
                # Redirect to settings to show updated config
                return redirect(url_for("settings"))
            except Exception as e:
                logger.error(f"[SETTINGS] Error saving configuration: {e}")
                return render_template("config.html", config=cfg, error=f"Failed to save settings: {str(e)}")
        
        return render_template("config.html", config=cfg)
    except Exception as e:
        logger.error(f"[SETTINGS] Error loading settings page: {e}")
        return render_template("config.html", config={}, error=f"Failed to load settings: {str(e)}")

def gen_mjpeg():
    """Generate MJPEG frames from camera - OPTIMIZED for speed!"""
    import time
    
    if not camera_streamer:
        logger.warning("[STREAM] Camera streamer not available")
        yield b''
        return
    
    BOUNDARY = b'MJPEGBOUNDARY'
    frame_count = 0
    last_log_time = time.time()
    fps_counter = 0
    
    # Check if using fast streamer
    is_fast_streamer = hasattr(camera_streamer, 'get_jpeg_frame')
    
    # Optimize frame timing for minimal latency
    if is_fast_streamer:
        logger.info("[STREAM] Using FAST streaming mode (picamera2) - High FPS, Low Latency")
        target_delay = 0.016  # ~60 FPS for responsiveness
    else:
        logger.info("[STREAM] Using SLOW streaming mode (libcamera-still) - Fallback mode")
        target_delay = 0.5   # 2 FPS for slow mode
    
    last_frame_time = time.time()
    
    while True:
        try:
            # Calculate frame timing to minimize jitter
            time_since_last = time.time() - last_frame_time
            if time_since_last < target_delay:
                # Don't sleep too long, check in small increments
                time.sleep(min(0.002, target_delay - time_since_last))
                continue
            
            if is_fast_streamer:
                # FAST MODE: Get pre-captured frame (instant!)
                jpeg_data = camera_streamer.get_jpeg_frame()
            else:
                # SLOW MODE: Capture new frame via subprocess (500-1000ms)
                cfg = get_config()
                resolution = cfg.get('camera', {}).get('resolution', '640x480')
                width, height = map(int, resolution.split('x'))
                jpeg_data = camera_streamer.get_single_frame_jpeg(width, height)
            
            if jpeg_data and len(jpeg_data) > 100:  # Valid frame
                frame_count += 1
                fps_counter += 1
                
                # Send MJPEG boundary
                yield b'--' + BOUNDARY + b'\r\n'
                yield b'Content-Type: image/jpeg\r\n'
                yield b'Content-Length: ' + str(len(jpeg_data)).encode() + b'\r\n'
                yield b'X-Timestamp: ' + str(int(time.time() * 1000)).encode() + b'\r\n'
                yield b'X-Frame-Count: ' + str(frame_count).encode() + b'\r\n\r\n'
                yield jpeg_data
                yield b'\r\n'
                
                last_frame_time = time.time()
                
                # Log FPS every 5 seconds
                current_time = time.time()
                if current_time - last_log_time >= 5:
                    fps = fps_counter / (current_time - last_log_time)
                    logger.debug(f"[STREAM] FPS: {fps:.1f}, Mode: {'FAST' if is_fast_streamer else 'SLOW'}")
                    fps_counter = 0
                    last_log_time = current_time
            else:
                # No valid frame yet
                logger.debug("[STREAM] Waiting for frame...")
                time.sleep(0.1 if is_fast_streamer else 0.5)
                
        except Exception as e:
            logger.error(f"[STREAM] Frame generation error: {e}")
            time.sleep(1)

@app.route("/api/stream")
def stream():
    """MJPEG video stream endpoint."""
    if not require_auth():
        return redirect(url_for("login"))
    
    if not camera_available:
        return jsonify({"error": "Camera not available"}), 503
    
    return Response(gen_mjpeg(), mimetype='multipart/x-mixed-replace; boundary=MJPEGBOUNDARY')

@app.route("/api/recordings")
def api_recordings():
    """Get list of recordings with details."""
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        cfg = get_config()
        rec_path = _recordings_path(cfg)
        recordings = []
        
        if os.path.isdir(rec_path):
            for name in sorted(os.listdir(rec_path), reverse=True):
                if name.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
                    full_path = os.path.join(rec_path, name)
                    try:
                        size_mb = os.path.getsize(full_path) / (1024 * 1024)
                        ts = os.path.getmtime(full_path)
                        date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                        recordings.append({
                            "name": name,
                            "size_mb": round(size_mb, 2),
                            "date": date_str,
                            "timestamp": ts
                        })
                    except Exception as e:
                        logger.warning(f"[RECORDINGS] Error reading file {name}: {e}")
        
        return jsonify({
            "ok": True,
            "count": len(recordings),
            "storage_used_gb": get_storage_used_gb(cfg),
            "recordings": recordings
        })
    except Exception as e:
        logger.error(f"[RECORDINGS] Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/storage")
def api_storage():
    """Get storage information."""
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        cfg = get_config()
        rec_path = _recordings_path(cfg)
        total_bytes = 0
        file_count = 0
        
        if os.path.isdir(rec_path):
            for root, _, files in os.walk(rec_path):
                for f in files:
                    try:
                        total_bytes += os.path.getsize(os.path.join(root, f))
                        file_count += 1
                    except Exception:
                        pass
        
        # Get available space
        try:
            import shutil
            disk_usage = shutil.disk_usage(rec_path)
            available_gb = disk_usage.free / (1024 ** 3)
            total_gb = disk_usage.total / (1024 ** 3)
        except Exception:
            available_gb = 0
            total_gb = 0
        
        return jsonify({
            "ok": True,
            "used_gb": round(total_bytes / (1024 ** 3), 2),
            "available_gb": round(available_gb, 2),
            "total_gb": round(total_gb, 2),
            "file_count": file_count
        })
    except Exception as e:
        logger.error(f"[STORAGE] Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/download/<filename>")
def download_recording(filename):
    """Download a recording file."""
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        cfg = get_config()
        rec_path = _recordings_path(cfg)
        file_path = os.path.join(rec_path, filename)
        
        # Security: ensure file is in recordings directory
        if not os.path.abspath(file_path).startswith(os.path.abspath(rec_path)):
            return jsonify({"error": "Invalid file path"}), 400
        
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        logger.info(f"[DOWNLOAD] User downloading {filename}")
        return send_file(file_path, as_attachment=True, download_name=filename)
    except Exception as e:
        logger.error(f"[DOWNLOAD] Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/delete/<filename>", methods=["POST"])
def delete_recording(filename):
    """Delete a recording file."""
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        cfg = get_config()
        rec_path = _recordings_path(cfg)
        file_path = os.path.join(rec_path, filename)
        
        # Security: ensure file is in recordings directory
        if not os.path.abspath(file_path).startswith(os.path.abspath(rec_path)):
            return jsonify({"ok": False, "error": "Invalid file path"}), 400
        
        if not os.path.exists(file_path):
            return jsonify({"ok": False, "error": "File not found"}), 404
        
        os.remove(file_path)
        logger.info(f"[RECORDINGS] Deleted {filename}")
        
        return jsonify({"ok": True, "message": f"Deleted {filename}"})
    except Exception as e:
        logger.error(f"[DELETE] Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/clear-storage", methods=["POST"])
def clear_storage():
    """Delete all recordings (with confirmation)."""
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        cfg = get_config()
        rec_path = _recordings_path(cfg)
        deleted_count = 0
        
        if os.path.isdir(rec_path):
            for filename in os.listdir(rec_path):
                if filename.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
                    try:
                        os.remove(os.path.join(rec_path, filename))
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"[STORAGE] Failed to delete {filename}: {e}")
        
        logger.info(f"[STORAGE] Cleared {deleted_count} files")
        return jsonify({"ok": True, "deleted": deleted_count})
    except Exception as e:
        logger.error(f"[STORAGE] Clear error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/storage/stats")
def storage_stats():
    """Get detailed storage statistics"""
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        cfg = get_config()
        rec_path = _recordings_path(cfg)
        import shutil
        
        # Get disk usage
        disk = shutil.disk_usage(rec_path if os.path.exists(rec_path) else BASE_DIR)
        
        # Count files by type
        video_files = []
        total_video_bytes = 0
        
        if os.path.isdir(rec_path):
            for filename in os.listdir(rec_path):
                if filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                    filepath = os.path.join(rec_path, filename)
                    size = os.path.getsize(filepath)
                    mtime = os.path.getmtime(filepath)
                    total_video_bytes += size
                    video_files.append({
                        "name": filename,
                        "size_mb": round(size / (1024**2), 2),
                        "date": datetime.fromtimestamp(mtime).isoformat()
                    })
        
        # Sort by date descending
        video_files.sort(key=lambda x: x["date"], reverse=True)
        
        # Storage limits from config
        storage_cfg = cfg.get("storage", {})
        max_gb = storage_cfg.get("max_storage_gb", 10)
        cleanup_percent = storage_cfg.get("cleanup_when_full_percent", 90)
        
        used_gb = total_video_bytes / (1024**3)
        total_gb = disk.total / (1024**3)
        available_gb = disk.free / (1024**3)
        used_percent = (used_gb / max_gb * 100) if max_gb > 0 else 0
        
        return jsonify({
            "ok": True,
            "storage": {
                "used_gb": round(used_gb, 2),
                "available_gb": round(available_gb, 2),
                "total_gb": round(total_gb, 2),
                "used_percent": round(used_percent, 1),
                "max_gb": max_gb,
                "cleanup_threshold_percent": cleanup_percent
            },
            "files": {
                "count": len(video_files),
                "total_mb": round(total_video_bytes / (1024**2), 2),
                "list": video_files[:50]  # Limit to 50 most recent
            },
            "warnings": {
                "near_limit": used_percent > cleanup_percent,
                "message": f"Storage {used_percent:.1f}% full" if used_percent > cleanup_percent else None
            }
        })
    except Exception as e:
        logger.error(f"[STORAGE] Stats error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/storage/cleanup", methods=["POST"])
def storage_cleanup():
    """Clean up old recordings based on retention policy"""
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        cfg = get_config()
        storage_cfg = cfg.get("storage", {})
        rec_path = _recordings_path(cfg)
        
        retention_days = storage_cfg.get("retention_days", 7)
        keep_newest = storage_cfg.get("keep_newest_files", True)
        
        cutoff_time = time.time() - (retention_days * 24 * 3600)
        deleted_files = []
        kept_files = []
        
        if os.path.isdir(rec_path):
            files_with_mtime = []
            for filename in os.listdir(rec_path):
                if filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                    filepath = os.path.join(rec_path, filename)
                    mtime = os.path.getmtime(filepath)
                    files_with_mtime.append((filename, filepath, mtime))
            
            # Sort by modification time (oldest first)
            files_with_mtime.sort(key=lambda x: x[2])
            
            for filename, filepath, mtime in files_with_mtime:
                if mtime < cutoff_time:
                    try:
                        size = os.path.getsize(filepath)
                        os.remove(filepath)
                        deleted_files.append({
                            "name": filename,
                            "size_mb": round(size / (1024**2), 2),
                            "age_days": round((time.time() - mtime) / 86400, 1)
                        })
                        logger.info(f"[CLEANUP] Deleted old file: {filename}")
                    except Exception as e:
                        logger.error(f"[CLEANUP] Failed to delete {filename}: {e}")
                else:
                    kept_files.append(filename)
        
        return jsonify({
            "ok": True,
            "deleted_count": len(deleted_files),
            "kept_count": len(kept_files),
            "deleted_files": deleted_files,
            "retention_days": retention_days
        })
    except Exception as e:
        logger.error(f"[CLEANUP] Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/stream/quality", methods=["GET", "POST"])
def stream_quality():
    """Get or set stream quality"""
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        cfg = get_config()
        camera_cfg = cfg.get("camera", {})
        
        if request.method == "POST":
            quality = request.get_json().get("quality")
            if quality not in ["low", "standard", "high", "ultra"]:
                return jsonify({"error": "Invalid quality"}), 400
            
            camera_cfg["stream_quality"] = quality
            
            # Apply quality settings
            quality_options = camera_cfg.get("quality_options", {})
            if quality in quality_options:
                quality_cfg = quality_options[quality]
                camera_cfg["resolution"] = quality_cfg.get("resolution", "640x480")
                camera_cfg["stream_fps"] = quality_cfg.get("fps", 15)
            
            save_config(cfg)
            logger.info(f"[QUALITY] Stream quality changed to: {quality}")
            
            return jsonify({
                "ok": True,
                "quality": quality,
                "settings": camera_cfg.get("quality_options", {}).get(quality, {})
            })
        
        else:
            # GET - return available qualities and current setting
            return jsonify({
                "ok": True,
                "current": camera_cfg.get("stream_quality", "standard"),
                "available": camera_cfg.get("quality_options", {}),
                "resolution": camera_cfg.get("resolution"),
                "fps": camera_cfg.get("stream_fps")
            })
    except Exception as e:
        logger.error(f"[QUALITY] Error: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== MOTION EVENT LOGGING ENDPOINTS ====================

@app.route("/api/motion/events", methods=["GET"])
def api_motion_events():
    """Get recent motion events with filtering"""
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # Query parameters
        hours = int(request.args.get("hours", 24))
        event_type = request.args.get("type", None)
        limit = int(request.args.get("limit", 100))
        
        events = get_recent_events(hours=hours, event_type=event_type, limit=limit)
        
        return jsonify({
            "ok": True,
            "count": len(events),
            "hours": hours,
            "events": events
        })
    except Exception as e:
        logger.error(f"[MOTION_EVENTS] Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/motion/stats", methods=["GET"])
def api_motion_stats():
    """Get motion event statistics"""
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        hours = int(request.args.get("hours", 24))
        stats = get_event_statistics(hours=hours)
        
        return jsonify({
            "ok": True,
            "stats": stats
        })
    except Exception as e:
        logger.error(f"[MOTION_STATS] Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/motion/log", methods=["POST"])
def api_log_motion():
    """Log a motion event (called from motion detection service)"""
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        data = request.get_json()
        event_type = data.get("type", "motion")
        confidence = float(data.get("confidence", 0.0))
        details = data.get("details", {})
        
        event = log_motion_event(event_type=event_type, confidence=confidence, details=details)
        
        return jsonify({
            "ok": True,
            "event": event
        })
    except Exception as e:
        logger.error(f"[MOTION_LOG] Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/motion/export", methods=["GET"])
def api_export_motion():
    """Export motion events as CSV"""
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        hours = int(request.args.get("hours", 24))
        csv_file = f"motion_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        csv_path = os.path.join("logs", csv_file)
        
        from src.core import export_events_csv
        if export_events_csv(csv_path, hours=hours):
            return send_file(csv_path, as_attachment=True, download_name=csv_file)
        else:
            return jsonify({"ok": False, "error": "Export failed"}), 500
            
    except Exception as e:
        logger.error(f"[MOTION_EXPORT] Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

# ==================== MULTI-DEVICE ENDPOINTS ====================

@app.route("/api/devices", methods=["GET"])
def api_devices():
    """Get list of configured devices"""
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        cfg = get_config()
        devices_config = cfg.get("devices", [])
        
        # Format devices list with current status
        devices = []
        for device in devices_config:
            device_info = {
                "id": device.get("id", device.get("name", "")),
                "name": device.get("name", "Unknown Device"),
                "ip": device.get("ip", ""),
                "location": device.get("location", ""),
                "status": device.get("status", "unknown"),
                "battery": device.get("battery", None),
                "storage": device.get("storage", "0 GB"),
                "events_24h": device.get("events_24h", 0),
                "last_seen": device.get("last_seen", time.time()),
                "firmware": device.get("firmware", "Unknown")
            }
            devices.append(device_info)
        
        # Add current device as first one
        current_device = {
            "id": "current",
            "name": cfg.get("device_name", "ME_CAM_1"),
            "ip": "localhost",
            "location": cfg.get("device_location", "Not set"),
            "status": "online",
            "battery": battery.get_status().get("percent", 100) if battery else 100,
            "storage": f"{get_storage_used_gb(cfg):.2f} GB",
            "events_24h": count_recent_events(cfg, hours=24),
            "last_seen": time.time(),
            "firmware": "Latest"
        }
        
        # Insert current device at beginning
        devices.insert(0, current_device)
        
        return jsonify({
            "ok": True,
            "devices": devices
        })
    except Exception as e:
        logger.error(f"[DEVICES] Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/devices", methods=["POST"])
def api_add_device():
    """Add a new device to the network"""
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        data = request.get_json()
        device_id = data.get("id", "").strip()
        device_name = data.get("name", "Unknown").strip()
        device_location = data.get("location", "").strip()
        
        if not device_id:
            return jsonify({"ok": False, "error": "Device ID required"}), 400
        
        cfg = get_config()
        devices = cfg.get("devices", [])
        
        # Check if device already exists
        if any(d.get("id") == device_id for d in devices):
            return jsonify({"ok": False, "error": "Device already exists"}), 400
        
        new_device = {
            "id": device_id,
            "name": device_name,
            "ip": device_id,
            "location": device_location,
            "status": "pending",
            "battery": None,
            "storage": "0 GB",
            "events_24h": 0,
            "last_seen": time.time(),
            "firmware": "Unknown"
        }
        
        devices.append(new_device)
        cfg["devices"] = devices
        save_config(cfg)
        
        logger.info(f"[DEVICES] Added new device: {device_name} ({device_id})")
        
        return jsonify({
            "ok": True,
            "message": f"Device '{device_name}' added successfully",
            "device": new_device
        })
    except Exception as e:
        logger.error(f"[DEVICES] Error adding device: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/devices/<device_id>", methods=["DELETE"])
def api_remove_device(device_id):
    """Remove a device from the network"""
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        cfg = get_config()
        devices = cfg.get("devices", [])
        
        # Find and remove device
        devices = [d for d in devices if d.get("id") != device_id]
        cfg["devices"] = devices
        save_config(cfg)
        
        logger.info(f"[DEVICES] Removed device: {device_id}")
        
        return jsonify({
            "ok": True,
            "message": "Device removed successfully"
        })
    except Exception as e:
        logger.error(f"[DEVICES] Error removing device: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/multicam")
def multicam():
    """Multi-camera dashboard"""
    if not require_auth():
        return redirect(url_for("login"))
    
    try:
        cfg = get_config()
        devices = cfg.get("devices", [])
        
        return render_template("multicam.html", devices=devices)
    except Exception as e:
        logger.error(f"[MULTICAM] Error: {e}")
        return render_template("multicam.html", devices=[])

if __name__ == "__main__":
    # Run Flask app
    logger.info("[STARTUP] Starting ME Camera Dashboard...")
    app.run(host="0.0.0.0", port=8080, debug=False)

@app.route("/api/camera/stats")
def camera_stats():
    """Get camera performance statistics"""
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        stats = {
            "streaming_mode": "fast" if hasattr(camera_streamer, 'get_stats') else "slow",
            "camera_available": camera_available
        }
        
        # Get performance stats if using fast streamer
        if hasattr(camera_streamer, 'get_stats'):
            stats.update(camera_streamer.get_stats())
        
        return jsonify({"ok": True, "stats": stats})
    except Exception as e:
        logger.error(f"[CAMERA] Stats error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)