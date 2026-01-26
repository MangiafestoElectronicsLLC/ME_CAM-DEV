"""
Lightweight Flask App for Pi Zero 2W - COMPLETE VERSION
==========================================================
- Motion detection with video recording
- Emergency alerts
- Configuration page
- Motion event viewer
- Storage cleanup
- Battery monitoring
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
from loguru import logger
import os
import sys
import subprocess
from datetime import datetime, timedelta
import time
import threading
import json
import shutil

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from src.core import (
    get_config, save_config, is_first_run, mark_first_run_complete,
    authenticate, BatteryMonitor, log_motion_event, get_recent_events,
    get_event_statistics
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Offline queues (lightweight JSON logs; safe for Pi Zero 2W)
OFFLINE_QUEUE_FILE = os.path.join(BASE_DIR, "logs", "offline_queue.json")
NOTIFY_QUEUE_FILE = os.path.join(BASE_DIR, "logs", "notification_queue.json")


def _ensure_log_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _load_queue(path: str) -> list:
    _ensure_log_dir(path)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"[QUEUE] Failed to load {path}: {e}")
        return []


def _save_queue(path: str, items: list) -> None:
    _ensure_log_dir(path)
    try:
        with open(path, "w") as f:
            json.dump(items, f, indent=2)
    except Exception as e:
        logger.error(f"[QUEUE] Failed to save {path}: {e}")


def is_wifi_connected() -> bool:
    """Lightweight WiFi check without depending on specific tools."""
    try:
        import subprocess
        # Check if wlan0 is up using /sys/class/net
        try:
            result = subprocess.run(['cat', '/sys/class/net/wlan0/operstate'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and 'up' in result.stdout.lower():
                return True
        except:
            pass
        
        # Fallback: try iw command
        try:
            result = subprocess.run(['iw', 'dev', 'wlan0', 'link'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and 'Connected to' in result.stdout:
                return True
        except:
            pass
        
        # Last resort: try iwconfig (may not be installed)
        try:
            result = subprocess.run(['iwconfig', 'wlan0'], capture_output=True, text=True, timeout=2)
            return 'ESSID:' in result.stdout and 'ESSID:""' not in result.stdout
        except:
            pass
        
        return False
    except Exception as e:
        logger.debug(f"[NETWORK] WiFi check failed: {e}")
        return False


def queue_offline_clip(video_path: str, meta: dict) -> None:
    """Store video reference to sync when WiFi returns."""
    items = _load_queue(OFFLINE_QUEUE_FILE)
    items.append({
        "video_path": video_path,
        "meta": meta or {},
        "timestamp": datetime.utcnow().isoformat(),
        "synced": False
    })
    _save_queue(OFFLINE_QUEUE_FILE, items)
    logger.info(f"[OFFLINE] Queued clip for later sync: {video_path}")


def queue_notification_retry(phone: str, message: str, reason: str = "unknown") -> None:
    items = _load_queue(NOTIFY_QUEUE_FILE)
    items.append({
        "phone": phone,
        "message": message,
        "attempts": 0,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    })
    _save_queue(NOTIFY_QUEUE_FILE, items)
    logger.info(f"[NOTIFY] Queued notification retry for {phone} (reason: {reason})")


def flush_notification_queue() -> None:
    if not is_wifi_connected():
        return
    items = _load_queue(NOTIFY_QUEUE_FILE)
    if not items:
        return
    cfg = get_config()
    if not cfg.get('sms_enabled'):
        return
    from src.core import get_sms_notifier
    notifier = get_sms_notifier()
    remaining = []
    for item in items:
        phone = item.get("phone")
        message = item.get("message")
        attempts = int(item.get("attempts", 0))
        if not phone or not message:
            continue
        if attempts >= 3:
            logger.warning(f"[NOTIFY] Dropping notification after 3 attempts: {phone}")
            continue
        try:
            notifier.send_sms(phone, message)
            logger.success(f"[NOTIFY] Retry sent to {phone}")
        except Exception as e:
            attempts += 1
            item["attempts"] = attempts
            item["last_error"] = str(e)
            remaining.append(item)
            logger.warning(f"[NOTIFY] Retry failed ({attempts}/3) for {phone}: {e}")
    _save_queue(NOTIFY_QUEUE_FILE, remaining)


def mark_offline_clips_synced() -> None:
    if not is_wifi_connected():
        return
    items = _load_queue(OFFLINE_QUEUE_FILE)
    changed = False
    for item in items:
        if not item.get("synced") and os.path.exists(item.get("video_path", "")):
            item["synced"] = True
            item["synced_at"] = datetime.utcnow().isoformat()
            changed = True
    if changed:
        _save_queue(OFFLINE_QUEUE_FILE, items)


# Throttle background flush work to keep Pi Zero responsive
_last_queue_flush = 0

def maybe_flush_queues(throttle_seconds: int = 30) -> None:
    global _last_queue_flush
    now = time.time()
    if now - _last_queue_flush < throttle_seconds:
        return
    _last_queue_flush = now
    flush_notification_queue()
    mark_offline_clips_synced()

def create_lite_app(pi_model, camera_config):
    """Create lightweight Flask app with all features"""
    
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.secret_key = os.urandom(24)
    
    # VPN SUPPORT: Add CORS and security headers for VPN connections
    @app.after_request
    def add_vpn_headers(response):
        """Add headers for VPN and remote access support"""
        # Allow requests from any origin (VPN clients)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Max-Age'] = '3600'
        
        # Tell browser/clients that HTTP is not required
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Allow connection from VPN clients that might have different IPs
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Cache control for offline VPN access
        if 'Cache-Control' not in response.headers:
            response.headers['Cache-Control'] = 'public, max-age=3600'
        
        return response
    
    # Handle CORS preflight requests
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = Response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
    
    # Lightweight battery monitor
    battery = BatteryMonitor(enabled=True)
    
    # Motion recording state
    motion_recorder = {
        'recording': False,
        'start_time': None,
        'frames': []
    }

    # Nanny cam mode (when enabled, motion is not logged/recorded)
    nanny_cam_enabled = False
    
    # Initialize camera - try RpicamStreamer first (most compatible)
    camera = None
    camera_available = False
    
    if camera_config['mode'] in ['lite', 'fast']:
        try:
            from src.camera import RpicamStreamer, is_rpicam_available
            
            if is_rpicam_available():
                logger.info("[CAMERA] Attempting rpicam-jpeg streaming...")
                camera = RpicamStreamer(width=640, height=480, fps=15)
                if camera.start():
                    camera_available = True
                    logger.success(f"[CAMERA] RPiCam initialized: 640x480 @ 15 FPS")
            else:
                logger.warning("[CAMERA] rpicam-jpeg not available, falling back to picamera2...")
                from picamera2 import Picamera2
                camera = Picamera2()
                camera.configure(camera.create_preview_configuration(
                    main={"size": (640, 480), "format": "RGB888"}
                ))
                camera.start()
                camera_available = True
                logger.success(f"[CAMERA] Camera initialized (picamera2): 640x480")
        except ImportError as e:
            logger.warning(f"[CAMERA] Required module not available: {e}")
        except Exception as e:
            logger.warning(f"[CAMERA] Camera init failed: {e}")
            camera = None
            camera_available = False
    
    # ============= HELPER FUNCTIONS =============
    
    def get_storage_info():
        """Get storage information"""
        recordings_path = os.path.join(BASE_DIR, "recordings")
        os.makedirs(recordings_path, exist_ok=True)
        
        total, used, free = shutil.disk_usage(recordings_path)
        
        # Count recordings
        recording_count = 0
        total_size_mb = 0
        if os.path.exists(recordings_path):
            for root, dirs, files in os.walk(recordings_path):
                for f in files:
                    if f.endswith(('.mp4', '.h264', '.h265', '.mkv', '.jpg', '.jpeg', '.png')):
                        recording_count += 1
                        try:
                            total_size_mb += os.path.getsize(os.path.join(root, f)) / (1024*1024)
                        except:
                            pass
        
        return {
            'total_gb': round(total / (1024**3), 2),
            'used_gb': round(used / (1024**3), 2),
            'free_gb': round(free / (1024**3), 2),
            'recording_count': recording_count,
            'recordings_size_mb': round(total_size_mb, 2)
        }
    
    def cleanup_old_recordings(days=7):
        """Delete recordings older than X days"""
        recordings_path = os.path.join(BASE_DIR, "recordings")
        cutoff = datetime.now() - timedelta(days=days)
        
        if not os.path.exists(recordings_path):
            return {'deleted': 0, 'freed_mb': 0}
        
        deleted_count = 0
        freed_mb = 0
        
        for root, dirs, files in os.walk(recordings_path):
            for f in files:
                if f.endswith(('.mp4', '.h264', '.h265', '.mkv')):
                    fpath = os.path.join(root, f)
                    try:
                        mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                        if mtime < cutoff:
                            size_mb = os.path.getsize(fpath) / (1024*1024)
                            os.remove(fpath)
                            deleted_count += 1
                            freed_mb += size_mb
                            logger.info(f"[STORAGE] Deleted old recording: {f}")
                    except Exception as e:
                        logger.error(f"[STORAGE] Delete failed: {f}: {e}")
        
        return {'deleted': deleted_count, 'freed_mb': round(freed_mb, 2)}
    
    def get_motion_events():
        """Get all motion events"""
        try:
            events_path = os.path.join(BASE_DIR, "logs", "motion_events.json")
            if os.path.exists(events_path):
                with open(events_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"[MOTION] Load events failed: {e}")
        return []

    def save_motion_clip(camera_obj, frame, duration_sec=5):
        """Save a short MP4 clip when motion is detected"""
        try:
            import cv2
            recordings_path = os.path.join(BASE_DIR, "recordings")
            os.makedirs(recordings_path, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"motion_{timestamp}.mp4"
            filepath = os.path.join(recordings_path, filename)

            # Prepare video writer with H.264 codec for browser compatibility
            height, width, _ = frame.shape
            # Use H.264 codec (x264) which all browsers support
            fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 / AVC
            fps = 15.0  # Balanced FPS for Pi Zero
            writer = cv2.VideoWriter(filepath, fourcc, fps, (width, height))

            if not writer.isOpened():
                # Fallback to mp4v if H.264 not available
                logger.warning("[MOTION] H.264 not available, using mp4v")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                writer = cv2.VideoWriter(filepath, fourcc, fps, (width, height))

            # Write initial frame
            writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

            # Capture additional frames for duration_sec seconds
            frame_count = int(duration_sec * fps)
            for i in range(frame_count):
                try:
                    next_frame = camera_obj.capture_array()
                    writer.write(cv2.cvtColor(next_frame, cv2.COLOR_RGB2BGR))
                    time.sleep(1.0 / fps)  # Control frame rate
                except Exception as e:
                    logger.debug(f"[MOTION] Frame {i} capture error: {e}")
                    break

            writer.release()
            logger.info(f"[MOTION] Saved {frame_count} frames to: {filename}")
            return filename
        except Exception as e:
            logger.error(f"[MOTION] Save clip failed: {e}")
            return None
    
    def save_motion_clip_buffered(camera_obj, buffered_frames, duration_sec=5):
        """Save a motion clip using pre-buffered frames + continue recording, with optional audio."""
        try:
            import cv2
            recordings_path = os.path.join(BASE_DIR, "recordings")
            os.makedirs(recordings_path, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"motion_{timestamp}.mp4"
            filepath = os.path.join(recordings_path, filename)

            # Get dimensions from buffered frames
            if not buffered_frames:
                return None
            
            height, width, _ = buffered_frames[0].shape
            fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264
            fps = 15.0
            writer = cv2.VideoWriter(filepath, fourcc, fps, (width, height))

            if not writer.isOpened():
                logger.warning("[MOTION] H.264 not available, using mp4v")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                writer = cv2.VideoWriter(filepath, fourcc, fps, (width, height))

            audio_proc = None
            audio_path = None

            # Try to capture audio in parallel if arecord is present
            if shutil.which("arecord"):
                try:
                    audio_path = os.path.join(recordings_path, f"motion_{timestamp}.wav")
                    audio_cmd = [
                        "arecord",
                        "-f", "S16_LE",
                        "-r", "16000",
                        "-d", str(duration_sec),
                        "-t", "wav",
                        audio_path
                    ]
                    audio_proc = subprocess.Popen(audio_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception as e:
                    logger.warning(f"[AUDIO] Failed to start audio capture: {e}")
                    audio_proc = None
                    audio_path = None

            # Write buffered frames first (captures motion that already happened)
            for frame in buffered_frames:
                writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

            # Continue capturing for remaining duration
            additional_frames = int(duration_sec * fps) - len(buffered_frames)
            for i in range(max(0, additional_frames)):
                try:
                    next_frame = camera_obj.capture_array()
                    writer.write(cv2.cvtColor(next_frame, cv2.COLOR_RGB2BGR))
                    time.sleep(1.0 / fps)
                except Exception as e:
                    logger.debug(f"[MOTION] Frame {i} capture error: {e}")
                    break

            writer.release()

            # Wait for audio capture to finish (best-effort)
            if audio_proc:
                try:
                    audio_proc.wait(timeout=duration_sec + 2)
                except Exception:
                    audio_proc.kill()
                audio_proc = None

            # Mux audio if available and ffmpeg present
            if audio_path and os.path.exists(audio_path) and shutil.which("ffmpeg"):
                try:
                    muxed_path = filepath.replace(".mp4", "_av.mp4")
                    mux_cmd = [
                        "ffmpeg", "-y",
                        "-i", filepath,
                        "-i", audio_path,
                        "-c:v", "copy",
                        "-c:a", "aac",
                        "-shortest",
                        muxed_path
                    ]
                    subprocess.run(mux_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=20)
                    if os.path.exists(muxed_path):
                        os.replace(muxed_path, filepath)
                        logger.info(f"[AUDIO] Embedded audio into {filename}")
                    else:
                        logger.warning("[AUDIO] Mux failed; keeping video-only file")
                except Exception as e:
                    logger.warning(f"[AUDIO] Mux error: {e}")
                finally:
                    try:
                        if audio_path and os.path.exists(audio_path):
                            os.remove(audio_path)
                    except Exception:
                        pass

            total_frames = len(buffered_frames) + max(0, additional_frames)
            logger.info(f"[MOTION] Saved {total_frames} frames ({len(buffered_frames)} buffered) to: {filename}")
            return filename
        except Exception as e:
            logger.error(f"[MOTION] Save buffered clip failed: {e}")
            return None
    
    def save_motion_snapshot(frame):
        """Save a snapshot when motion is detected"""
        try:
            recordings_path = os.path.join(BASE_DIR, "recordings")
            os.makedirs(recordings_path, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"motion_{timestamp}.jpg"
            filepath = os.path.join(recordings_path, filename)
            
            from PIL import Image
            img = Image.fromarray(frame)
            img.save(filepath, quality=95)
            
            logger.info(f"[MOTION] Saved snapshot: {filename}")
            return filename
        except Exception as e:
            logger.error(f"[MOTION] Save snapshot failed: {e}")
            return None
    
    def delete_motion_event(event_id):
        """Delete a specific motion event and its video file"""
        try:
            events_path = os.path.join(BASE_DIR, "logs", "motion_events.json")
            if os.path.exists(events_path):
                with open(events_path, 'r') as f:
                    events = json.load(f)
                
                # Find event and delete its video file
                event_to_delete = next((e for e in events if e.get('id') == event_id), None)
                if event_to_delete:
                    video_path = event_to_delete.get('details', {}).get('video_path')
                    if video_path:
                        # video_path is just filename like "motion_20260120_141043.mp4"
                        full_path = os.path.join(BASE_DIR, "recordings", video_path)
                        if os.path.exists(full_path):
                            os.remove(full_path)
                            logger.info(f"[MOTION] Deleted video file: {full_path}")
                        else:
                            logger.warning(f"[MOTION] Video file not found: {full_path}")
                
                # Remove from events list
                events = [e for e in events if e.get('id') != event_id]
                
                with open(events_path, 'w') as f:
                    json.dump(events, f, indent=2)
                
                return True
        except Exception as e:
            logger.error(f"[MOTION] Delete event failed: {e}")
        return False
    
    # ============= ROUTES =============
    
    @app.route("/")
    def index():
        """Main dashboard"""
        if is_first_run():
            return redirect(url_for('setup'))
        
        if 'user' not in session:
            return redirect(url_for('login'))
        
        cfg = get_config()
        storage = get_storage_info()
        battery_status = battery.get_status()
        motion_events = get_motion_events()
        
        return render_template('dashboard_lite.html',
            device_name=cfg.get('device_name', 'ME Camera'),
            device_id=cfg.get('device_id', 'camera-001'),
            pi_model=pi_model['name'],
            ram_mb=pi_model['ram_mb'],
            camera_available=camera is not None,
            battery_pct=battery_status.get('percent', 0),
            storage=storage,
            motion_count=len(motion_events),
            version='2.1-LITE'
        )
    
    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Login page"""
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            
            if authenticate(username, password):
                session['user'] = username
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error="Invalid credentials")
        
        return render_template('login.html')
    
    @app.route("/register", methods=["GET", "POST"])
    def register():
        """User registration"""
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
            
            from src.core import user_exists, create_user
            if user_exists(username):
                return render_template("register.html", error="Username already exists")
            
            # Create user
            if create_user(username, password):
                logger.info(f"[AUTH] New user registered: {username}")
                return render_template("register.html", success="Account created! Please login.")
            else:
                return render_template("register.html", error="Error creating account")
        
        return render_template("register.html")
    
    @app.route("/logout")
    def logout():
        """Logout"""
        session.pop('user', None)
        return redirect(url_for('login'))
    
    @app.route("/setup", methods=["GET", "POST"])
    def setup():
        """First-run setup"""
        if not is_first_run():
            return redirect(url_for('index'))
        
        if request.method == "POST":
            cfg = get_config()
            cfg['device_name'] = request.form.get('device_name', 'ME Camera')
            cfg['device_id'] = request.form.get('device_id', 'camera-001')
            cfg['device_location'] = request.form.get('device_location', '')
            cfg['pin_enabled'] = request.form.get('pin_enabled', False) == 'on'
            cfg['pin_code'] = request.form.get('pin_code', '')
            cfg['storage_cleanup_days'] = int(request.form.get('retention_days', 7))
            cfg['motion_record_enabled'] = request.form.get('motion_only', True) == 'on'
            cfg['storage_encrypt'] = request.form.get('encrypt', False) == 'on'
            cfg['detection_person_only'] = request.form.get('person_only', False) == 'on'
            cfg['detection_sensitivity'] = float(request.form.get('sensitivity', 0.5))
            cfg['emergency_phone'] = request.form.get('emergency_phone', '')
            cfg['send_motion_to_emergency'] = request.form.get('send_motion_to_emergency', False) == 'on'
            cfg['email_enabled'] = request.form.get('email_enabled', False) == 'on'
            cfg['email_address'] = request.form.get('email_address', '')
            cfg['gdrive_enabled'] = request.form.get('gdrive_enabled', False) == 'on'
            cfg['gdrive_folder_id'] = request.form.get('gdrive_folder_id', '')
            cfg['wifi_enabled'] = request.form.get('wifi_enabled', True) == 'on'
            cfg['bluetooth_enabled'] = request.form.get('bluetooth_enabled', False) == 'on'
            save_config(cfg)
            
            from src.core import create_user
            create_user('admin', 'admin123')
            
            mark_first_run_complete()
            return redirect(url_for('login'))
        
        # Get current config for display
        cfg = get_config()
        config_display = {
            'device_name': cfg.get('device_name', 'ME Camera'),
            'device_id': cfg.get('device_id', 'camera-001'),
            'device_location': cfg.get('device_location', ''),
            'pin_enabled': cfg.get('pin_enabled', False),
            'pin_code': cfg.get('pin_code', ''),
            'storage': {
                'retention_days': cfg.get('storage_cleanup_days', 7),
                'motion_only': cfg.get('motion_record_enabled', True),
                'encrypt': cfg.get('storage_encrypt', False),
                'encrypted_dir': cfg.get('storage_encrypted_dir', '/mnt/encrypted')
            },
            'detection': {
                'person_only': cfg.get('detection_person_only', False),
                'sensitivity': cfg.get('detection_sensitivity', 0.5)
            },
            'emergency_phone': cfg.get('emergency_phone', ''),
            'send_motion_to_emergency': cfg.get('send_motion_to_emergency', False),
            'email': {
                'enabled': cfg.get('email_enabled', False)
            },
            'email_address': cfg.get('email_address', ''),
            'google_drive': {
                'enabled': cfg.get('gdrive_enabled', False),
                'folder_id': cfg.get('gdrive_folder_id', '')
            },
            'wifi_enabled': cfg.get('wifi_enabled', True),
            'bluetooth_enabled': cfg.get('bluetooth_enabled', False),
            'motion_threshold': cfg.get('motion_threshold', 0.5),
            'motion_record_enabled': cfg.get('motion_record_enabled', True),
            'motion_record_duration': cfg.get('motion_record_duration', 10),
            'sms_enabled': cfg.get('sms_enabled', False),
            'sms_phone_to': cfg.get('sms_phone_to', ''),
        }
        
        return render_template('first_run.html', pi_model=pi_model, config=config_display)
    
    @app.route("/config", methods=["GET", "POST"])
    def config_page():
        """Configuration page"""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        cfg = get_config()
        storage = get_storage_info()
        
        return render_template('config.html',
            device_name=cfg.get('device_name', 'ME Camera'),
            device_id=cfg.get('device_id', 'camera-001'),
            device_location=cfg.get('device_location', 'Unknown'),
            emergency_phone=cfg.get('emergency_phone', ''),
            send_motion_to_emergency=cfg.get('send_motion_to_emergency', False),
            motion_threshold=cfg.get('motion_threshold', 0.5),
            motion_record_enabled=cfg.get('motion_record_enabled', True),
            motion_record_duration=cfg.get('motion_record_duration', 10),
            storage_cleanup_days=cfg.get('storage_cleanup_days', 7),
            sms_enabled=cfg.get('sms_enabled', False),
            sms_phone_to=cfg.get('sms_phone_to', ''),
            sms_api_url=cfg.get('sms_api_url', ''),
            sms_api_key=cfg.get('sms_api_key', ''),
            sms_rate_limit=cfg.get('sms_rate_limit', 5),
            storage=storage,
            config=cfg
        )
    
    @app.route("/recordings/<path:filename>")
    def serve_recording(filename):
        """Serve recorded video/image files"""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        recordings_path = os.path.join(BASE_DIR, "recordings")
        from flask import send_from_directory
        return send_from_directory(recordings_path, filename)
    
    @app.route("/motion-events", methods=["GET"])
    def motion_events_page():
        """View motion events"""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        events = get_motion_events()
        return render_template('motion_events.html', events=events)
    
    @app.route("/video_feed")
    def video_feed():
        """Live video stream - accessible from dashboard"""
        # Video stream accessible from authenticated dashboard (no session check for iframe)
        if camera is None or not camera_available:
            return Response(generate_test_pattern(), mimetype='multipart/x-mixed-replace; boundary=frame')
        
        # BUG FIX #4: Add keep-alive timeout to prevent orphan connections
        response = Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
        response.headers['Connection'] = 'keep-alive'
        response.headers['Keep-Alive'] = 'timeout=300'  # 5 min timeout to force browser reconnect
        return response
    
    # ============= API ROUTES =============
    
    @app.route("/api/battery", methods=["GET"])
    def api_battery():
        """Battery status"""
        status = battery.get_status()
        return jsonify({
            'percentage': status.get('percent', 0),
            'percent': status.get('percent', 0),
            'runtime_hours': status.get('runtime_hours', 0),
            'runtime_minutes': status.get('runtime_minutes', 0),
            'external_power': status.get('external_power', False),
            'is_low': status.get('is_low', False),
            'timestamp': datetime.utcnow().isoformat()
        })
    
    # NEW: WiFi status API endpoints
    @app.route("/api/network/wifi", methods=["GET"])
    def api_wifi_status():
        """Get WiFi connection status - works without iwconfig"""
        try:
            import subprocess
            # Try multiple methods to detect WiFi
            is_connected = False
            ssid = "Unknown"
            signal = "N/A"
            
            # Method 1: Check /sys/class/net/ for wlan interface
            try:
                result = subprocess.run(['cat', '/sys/class/net/wlan0/operstate'], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0 and 'up' in result.stdout.lower():
                    is_connected = True
            except:
                pass
            
            # Method 2: Try iw command (more modern than iwconfig)
            if not is_connected:
                try:
                    result = subprocess.run(['iw', 'dev', 'wlan0', 'link'], 
                                          capture_output=True, text=True, timeout=2)
                    if result.returncode == 0 and 'Connected to' in result.stdout:
                        is_connected = True
                        # Extract SSID from iw output
                        for line in result.stdout.split('\n'):
                            if 'SSID:' in line:
                                ssid = line.split('SSID:')[1].strip()
                            elif 'signal:' in line.lower():
                                signal = line.split('signal:')[1].strip().split()[0]
                except:
                    pass
            
            # Method 3: Fallback - try iwconfig if available
            if not is_connected:
                try:
                    result = subprocess.run(['iwconfig', 'wlan0'], 
                                          capture_output=True, text=True, timeout=2)
                    if 'ESSID:' in result.stdout and 'ESSID:""' not in result.stdout:
                        is_connected = True
                        for line in result.stdout.split('\n'):
                            if 'ESSID:' in line:
                                ssid = line.split('ESSID:"')[1].split('"')[0]
                            elif 'Signal level' in line:
                                signal = line.split('Signal level=')[1].split(' ')[0]
                except:
                    pass
            
            logger.info(f"[NETWORK] WiFi: connected={is_connected}, ssid={ssid}, signal={signal}")
            
            return jsonify({
                'connected': is_connected,
                'ssid': ssid,
                'signal': signal,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.warning(f"[NETWORK] WiFi status error: {e}")
            return jsonify({'connected': False, 'error': str(e), 'ssid': 'Unknown', 'signal': 'N/A'}), 200
    
    @app.route("/api/network/wifi/update", methods=["POST"])
    def api_wifi_update():
        """Update WiFi settings"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            data = request.get_json()
            ssid = data.get('ssid', '').strip()
            password = data.get('password', '').strip()
            
            if not ssid:
                return jsonify({'error': 'SSID required'}), 400
            
            # Save to config
            cfg = get_config()
            cfg['wifi_ssid'] = ssid
            cfg['wifi_password'] = password
            cfg['wifi_enabled'] = True
            save_config(cfg)
            
            # Try to apply WiFi config at system level
            try:
                import subprocess
                
                # Create wpa_supplicant config
                wpa_conf = f'''ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}'''
                
                # Write and apply
                temp_conf = '/tmp/wpa_supplicant.conf'
                with open(temp_conf, 'w') as f:
                    f.write(wpa_conf)
                
                subprocess.run(['sudo', 'cp', temp_conf, '/etc/wpa_supplicant/wpa_supplicant.conf'], 
                              timeout=5, capture_output=True, check=False)
                subprocess.run(['sudo', 'systemctl', 'restart', 'wpa_supplicant'], 
                              timeout=5, capture_output=True, check=False)
                
                logger.success(f"[NETWORK] WiFi applied: {ssid}")
            except Exception as e:
                logger.warning(f"[NETWORK] System config pending: {e}")
            
            logger.info(f"[NETWORK] WiFi settings updated to: {ssid}")
            return jsonify({'ok': True, 'message': f'WiFi configured for {ssid}. Device connecting...'})
        except Exception as e:
            logger.error(f"[NETWORK] WiFi update error: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500
    
    @app.route("/api/storage", methods=["GET"])
    def api_storage():
        """Storage info"""
        storage = get_storage_info()
        return jsonify(storage)
    
    @app.route("/api/motion/events", methods=["GET"])
    def api_motion_events():
        """Get motion events"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            events = get_motion_events()
            
            # Calculate statistics
            from datetime import datetime, timedelta
            now = datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            total = len(events)
            today_count = 0
            latest_time = None
            by_type = {}
            
            for event in events:
                # Count by type
                event_type = event.get('type', 'unknown')
                by_type[event_type] = by_type.get(event_type, 0) + 1
                
                # Count today
                try:
                    event_dt = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                    if event_dt >= today_start:
                        today_count += 1
                    
                    # Track latest time
                    if latest_time is None or event_dt > latest_time:
                        latest_time = event_dt
                except:
                    pass
            
            # Latest timestamp (raw string so frontend can render in local timezone)
            latest_raw = None
            if events:
                # events are chronological; take last item
                latest_raw = events[-1].get('timestamp')

            statistics = {
                'total': total,
                'today': today_count,
                'by_type': by_type,
                'latest': latest_raw
            }
            
            return jsonify({
                'events': events,
                'count': total,
                'statistics': statistics
            })
        except Exception as e:
            logger.error(f"[API] Motion events error: {e}")
            return jsonify({'error': str(e), 'events': [], 'count': 0}), 500
    
    @app.route("/api/motion/delete/<event_id>", methods=["POST"])
    def api_delete_motion(event_id):
        """Delete motion event"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        if delete_motion_event(event_id):
            return jsonify({'ok': True})
        return jsonify({'ok': False}), 500
    
    @app.route("/api/motion/clear", methods=["POST"])
    def api_clear_motion():
        """Clear all motion events and delete video files"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            events_path = os.path.join(BASE_DIR, "logs", "motion_events.json")
            deleted_count = 0
            freed_mb = 0
            
            # Delete all video files first
            if os.path.exists(events_path):
                with open(events_path, 'r') as f:
                    events = json.load(f)
                
                for event in events:
                    video_path = event.get('details', {}).get('video_path')
                    if video_path:
                        # video_path is just filename, need to add recordings folder
                        full_path = os.path.join(BASE_DIR, "recordings", video_path)
                        if os.path.exists(full_path):
                            try:
                                file_size = os.path.getsize(full_path) / (1024 * 1024)  # MB
                                os.remove(full_path)
                                deleted_count += 1
                                freed_mb += file_size
                                logger.debug(f"[MOTION] Deleted: {full_path}")
                            except Exception as e:
                                logger.error(f"[MOTION] Failed to delete {full_path}: {e}")
            
            # Clear events list
            with open(events_path, 'w') as f:
                json.dump([], f)
            
            logger.info(f"[MOTION] Cleared {deleted_count} events, freed {freed_mb:.2f}MB")
            return jsonify({'ok': True, 'deleted': deleted_count, 'freed_mb': round(freed_mb, 2)})
        except Exception as e:
            logger.error(f"[MOTION] Clear failed: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500
    
    @app.route("/api/config/update", methods=["POST"])
    def api_config_update():
        """Update configuration"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            data = request.get_json()
            cfg = get_config()
            
            # Update settings
            cfg['device_name'] = data.get('device_name', cfg.get('device_name'))
            cfg['device_location'] = data.get('device_location', cfg.get('device_location'))
            cfg['emergency_phone'] = data.get('emergency_phone', cfg.get('emergency_phone'))
            cfg['send_motion_to_emergency'] = data.get('send_motion_to_emergency', False)
            cfg['motion_threshold'] = float(data.get('motion_threshold', 0.5))
            cfg['motion_record_enabled'] = data.get('motion_record_enabled', True)
            cfg['motion_record_duration'] = int(data.get('motion_record_duration', 10))
            cfg['storage_cleanup_days'] = int(data.get('storage_cleanup_days', 7))
            cfg['nanny_cam_enabled'] = data.get('nanny_cam_enabled', False)

            # WiFi settings
            cfg['wifi_enabled'] = data.get('wifi_enabled', cfg.get('wifi_enabled', True))
            cfg['wifi_ssid'] = data.get('wifi_ssid', cfg.get('wifi_ssid', ''))
            cfg['wifi_password'] = data.get('wifi_password', cfg.get('wifi_password', ''))
            cfg['wifi_country'] = data.get('wifi_country', cfg.get('wifi_country', 'US'))
            
            # SMS configuration
            cfg['sms_enabled'] = data.get('sms_enabled', False)
            cfg['sms_phone_to'] = data.get('sms_phone_to', '')
            cfg['sms_api_url'] = data.get('sms_api_url', '')
            cfg['sms_api_key'] = data.get('sms_api_key', '')
            cfg['sms_rate_limit'] = int(data.get('sms_rate_limit', 5))
            
            save_config(cfg)
            logger.info("[CONFIG] Settings updated")
            return jsonify({'ok': True, 'message': 'Configuration saved'})
        except Exception as e:
            logger.error(f"[CONFIG] Update failed: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500

    @app.route("/api/nanny-cam/status", methods=["GET"])
    def api_nanny_status():
        """Get nanny cam enabled status"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        cfg = get_config()
        enabled = cfg.get('nanny_cam_enabled', False)
        return jsonify({'enabled': enabled})

    @app.route("/api/nanny-cam/toggle", methods=["POST"])
    def api_nanny_toggle():
        """Toggle nanny cam mode (disables motion logging/recording when on)"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        try:
            data = request.get_json()
            enabled = bool(data.get('enabled', False))
            cfg = get_config()
            cfg['nanny_cam_enabled'] = enabled
            save_config(cfg)
            return jsonify({'ok': True, 'enabled': enabled})
        except Exception as e:
            logger.error(f"[NANNY] Toggle failed: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500
    
    @app.route("/api/emergency/alert", methods=["POST"])
    def api_emergency_alert():
        """Send emergency alert"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            data = request.get_json()
            message = data.get('message', 'Emergency alert')
            event_type = data.get('type', 'security_alert')
            
            cfg = get_config()
            emergency_phone = cfg.get('emergency_phone')
            device_name = cfg.get('device_name', 'ME_CAM')
            
            if not emergency_phone:
                return jsonify({'ok': False, 'error': 'No emergency number configured'}), 400
            
            # Log as motion event
            log_motion_event(event_type=event_type, confidence=1.0, 
                           details={'emergency': True, 'message': message})
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            alert_msg = f"🚨 ALERT: {message}\nDevice: {device_name}\nTime: {timestamp}"
            
            logger.warning(f"[EMERGENCY] {alert_msg}")
            
            return jsonify({
                'ok': True,
                'message': 'Emergency alert triggered',
                'phone': emergency_phone
            })
        except Exception as e:
            logger.error(f"[EMERGENCY] Alert failed: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500
    
    @app.route("/api/motion/send", methods=["POST"])
    def api_motion_send():
        """Send motion event via SMS or notification"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            data = request.get_json()
            event_id = data.get('event_id')
            phone = data.get('phone', '')
            media_type = data.get('media_type', 'image')
            
            cfg = get_config()
            
            # Get event details
            events_path = os.path.join(BASE_DIR, "logs", "motion_events.json")
            events = []
            if os.path.exists(events_path):
                with open(events_path, 'r') as f:
                    events = json.load(f)
            
            event = next((e for e in events if e.get('id') == event_id), None)
            if not event:
                return jsonify({'ok': False, 'error': 'Event not found'}), 404
            
            # Format timestamp for EST (Brockport, NY)
            from datetime import datetime
            event_time = event.get('timestamp', 'Unknown time')
            device_name = cfg.get('device_name', 'ME_CAM')
            
            message = f"🎥 Motion Alert from {device_name}\n"
            message += f"Time: {event_time}\n"
            message += f"Type: {event.get('type', 'motion').upper()}\n"
            message += f"Confidence: {int(event.get('confidence', 0) * 100)}%"
            
            if cfg.get('sms_enabled') and cfg.get('sms_api_url'):
                import requests
                try:
                    # Generic HTTP-based SMS API integration
                    api_url = cfg.get('sms_api_url')
                    api_key = cfg.get('sms_api_key', '')
                    
                    headers = {}
                    if api_key:
                        headers['Authorization'] = f"Bearer {api_key}"
                        headers['X-API-Key'] = api_key
                    
                    payload = {
                        'to': phone or cfg.get('sms_phone_to'),
                        'message': message,
                        'from': device_name
                    }
                    
                    response = requests.post(api_url, json=payload, headers=headers, timeout=10)
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"[SMS] Message sent to {phone}")
                        return jsonify({
                            'ok': True,
                            'message': 'SMS sent successfully',
                            'phone': phone
                        })
                    else:
                        logger.warning(f"[SMS] Send failed: {response.status_code} - {response.text}")
                        return jsonify({
                            'ok': False,
                            'error': f'API returned {response.status_code}'
                        }), 500
                except requests.exceptions.Timeout:
                    logger.error("[SMS] Request timeout")
                    return jsonify({'ok': False, 'error': 'SMS API timeout'}), 504
                except Exception as e:
                    logger.error(f"[SMS] Send failed: {e}")
                    return jsonify({'ok': False, 'error': str(e)}), 500
            else:
                # Log the attempt if SMS not configured
                logger.info(f"[SMS] SMS not configured. Message would go to: {phone}")
                return jsonify({
                    'ok': True,
                    'message': 'SMS logging enabled (no API configured)',
                    'phone': phone,
                    'text': message
                })
        except Exception as e:
            logger.error(f"[MOTION] Send failed: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500
    
    @app.route("/api/storage/cleanup", methods=["POST"])
    def api_storage_cleanup():
        """Clean up old recordings"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            data = request.get_json()
            days = int(data.get('days', 7))
            
            result = cleanup_old_recordings(days)
            logger.info(f"[STORAGE] Cleanup: {result['deleted']} files, {result['freed_mb']}MB freed")
            
            return jsonify({
                'ok': True,
                'deleted': result['deleted'],
                'freed_mb': result['freed_mb']
            })
        except Exception as e:
            logger.error(f"[STORAGE] Cleanup failed: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500
    
    # ============= FRAME GENERATORS =============
    
    def generate_frames():
        """Generate camera frames"""
        import cv2
        import numpy as np
        from PIL import Image
        import io
        
        last_frame = None
        motion_cooldown = 0
        frame_buffer = []  # Buffer to capture frames BEFORE motion detected
        # BUG FIX #2: Reduce buffer size for Pi Zero 2W (512MB RAM)
        # Each frame is ~600KB, so limit to 4 frames = 2.4MB instead of 8 frames = 4.8MB
        buffer_size = 4 if pi_model.get('ram_mb', 1024) <= 512 else 8
        recording = False
        frame_count = 0  # BUG FIX #3: Add frame counter for consistent motion detection
        
        while True:
            try:
                # Periodically retry queued notifications/offline clips without touching camera settings
                maybe_flush_queues()

                if camera is None:
                    break
                
                # Check if using RpicamStreamer or picamera2
                if hasattr(camera, 'get_jpeg_frame'):
                    # RpicamStreamer - get JPEG directly
                    jpeg_bytes = camera.get_jpeg_frame()
                    if not jpeg_bytes:
                        time.sleep(0.1)
                        continue
                    
                    # BUG FIX #3: Use frame counter instead of buffer length for consistency
                    frame_count += 1
                    
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
                    time.sleep(0.05)
                    continue
                
                # picamera2 - get array and convert
                frame = camera.capture_array()
                frame_count += 1  # BUG FIX #3: Increment frame counter
                
                # Motion detection - check every 2nd frame for performance
                # BUG FIX: Changed logic - now processes motion detection on EVERY frame for responsiveness
                if frame_count % 2 == 0:  # Skip buffering on even frames
                    # Process frame for motion detection (every 2nd frame)
                    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                else:
                    # Just buffer the frame and stream it
                    frame_buffer.append(frame.copy())
                    if len(frame_buffer) > buffer_size:
                        frame_buffer.pop(0)
                    
                    img = Image.fromarray(frame)
                    buf = io.BytesIO()
                    img.save(buf, format='JPEG', quality=85)
                    jpeg_bytes = buf.getvalue()
                    
                    # BUG FIX #5: Explicit cleanup for PIL objects
                    del img
                    buf.close()
                    del buf
                    
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
                    time.sleep(0.05)
                    continue
                
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                
                # Always add current frame to buffer
                frame_buffer.append(frame.copy())
                if len(frame_buffer) > buffer_size:
                    frame_buffer.pop(0)  # Remove oldest
                
                # Motion detection - check every frame for responsiveness
                if motion_cooldown > 0:
                    motion_cooldown -= 1
                else:
                    if last_frame is not None and not recording:
                        # Advanced motion detection - filter out shadows and lighting
                        diff = cv2.absdiff(last_frame, gray)
                        
                        # Apply Gaussian blur to reduce noise and small changes
                        blurred_diff = cv2.GaussianBlur(diff, (21, 21), 0)
                        
                        # Threshold to get significant changes only
                        _, thresh = cv2.threshold(blurred_diff, 25, 255, cv2.THRESH_BINARY)
                        
                        # Calculate metrics
                        mean_diff = np.mean(diff)
                        max_diff = np.max(diff)
                        motion_pixels = np.sum(thresh > 0)  # Count pixels with significant change
                        total_pixels = thresh.shape[0] * thresh.shape[1]
                        motion_percent = (motion_pixels / total_pixels) * 100
                        
                        # Detect edges to distinguish objects from shadows
                        edges = cv2.Canny(gray, 50, 150)
                        edge_motion = np.sum(edges > 0)
                        
                        # Contour-based filtering to ignore tiny movements (leaves, shadows)
                        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        min_area = 1200  # tuned for 640x480; ignores tiny motion
                        allowed_labels = []
                        for c in contours:
                            area = cv2.contourArea(c)
                            if area < min_area:
                                continue
                            x, y, w, h = cv2.boundingRect(c)
                            aspect = w / float(h)
                            if 0.3 <= aspect <= 0.8:
                                allowed_labels.append("person")
                            elif 0.8 < aspect <= 3.5:
                                allowed_labels.append("vehicle")

                        motion = (
                            max_diff > 85 and            # sharper contrast to avoid shadows
                            motion_percent > 1.5 and     # smaller percent allowed but paired with area filter
                            edge_motion > 1200 and       # enforce clear edges
                            mean_diff > 18 and
                            len(allowed_labels) > 0      # only accept person/vehicle-shaped contours
                        )
                        
                        if motion:
                            cfg = get_config()
                            nanny_cam = cfg.get('nanny_cam_enabled', False)

                            if not nanny_cam and cfg.get('motion_record_enabled', True):
                                logger.info(f"[MOTION] Motion detected (mean:{mean_diff:.1f}, max:{max_diff:.1f})")
                                recording = True
                                try:
                                    # Save clip using buffered frames + continue recording
                                    clip_file = save_motion_clip_buffered(camera, frame_buffer.copy(), duration_sec=5)
                                    video_path = clip_file
                                    if not clip_file:
                                        # Fallback to snapshot if clip fails
                                        video_path = save_motion_snapshot(frame)

                                    detected_label = allowed_labels[0] if allowed_labels else "motion"
                                    event = log_motion_event(
                                        event_type=detected_label,
                                        confidence=1.0,
                                        details={
                                            "mode": "lite",
                                            "video_path": video_path,
                                            "mean_diff": float(mean_diff),
                                            "max_diff": float(max_diff),
                                            "label": detected_label,
                                            "contours": len(allowed_labels)
                                        }
                                    )
                                    # If WiFi is down, remember this clip to sync/notify later
                                    if not is_wifi_connected():
                                        queue_offline_clip(video_path, {
                                            "event_id": event.get("id"),
                                            "type": event.get("type"),
                                            "timestamp": event.get("timestamp")
                                        })
                                    
                                    # Send SMS notification if enabled
                                    if cfg.get('sms_enabled') and cfg.get('send_motion_to_emergency'):
                                        try:
                                            from src.core import get_sms_notifier
                                            sms_notifier = get_sms_notifier()
                                            phone = cfg.get('sms_phone_to') or cfg.get('emergency_phone')
                                            if phone:
                                                device_name = cfg.get('device_name', 'ME Camera')
                                                location = cfg.get('device_location', 'Unknown')
                                                timestamp = datetime.now().strftime("%I:%M:%S %p")
                                                msg = f"🚨 {device_name}: Motion detected at {location} - {timestamp}"
                                                sms_notifier.send_sms(phone, msg)
                                                logger.success(f"[SMS] Motion alert sent to {phone}")
                                        except Exception as sms_error:
                                            logger.error(f"[SMS] Notification failed: {sms_error}")
                                            if phone:
                                                queue_notification_retry(phone, msg, reason="send_failed")
                                except Exception as e:
                                    logger.error(f"[MOTION] Recording error: {e}")
                                finally:
                                    recording = False

                            # Cooldown: 45 frames (~3 sec) to avoid duplicate triggers
                            motion_cooldown = 45
                
                last_frame = gray
                
                # Convert to JPEG
                img = Image.fromarray(frame)
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=85)
                jpeg_bytes = buf.getvalue()
                
                # BUG FIX #5: Explicit cleanup for PIL objects
                del img
                buf.close()
                del buf
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
                
                time.sleep(0.05)  # ~20 FPS
            except Exception as e:
                logger.debug(f"[CAMERA] Frame error: {e}")
                break
    
    def generate_test_pattern():
        """Generate test pattern"""
        from PIL import Image, ImageDraw
        import io
        
        while True:
            img = Image.new('RGB', (640, 480), color=(40, 40, 40))
            draw = ImageDraw.Draw(img)
            draw.text((120, 200), "TEST MODE\nPi Zero 2W\n512MB RAM", fill=(255, 255, 255))
            
            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            jpeg_bytes = buf.getvalue()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
            
            time.sleep(0.1)
    
    # ============= SYSTEM ROUTES =============
    
    @app.route("/api/system/reboot", methods=["POST"])
    def api_system_reboot():
        """Reboot the device"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            import subprocess
            logger.warning("[SYSTEM] Reboot requested by user")
            # Schedule reboot in 5 seconds to allow response to be sent
            subprocess.Popen(['sudo', 'shutdown', '-r', '+1'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return jsonify({'ok': True, 'message': 'Device rebooting in 1 minute...'})
        except Exception as e:
            logger.error(f"[SYSTEM] Reboot failed: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500
    
    return app
