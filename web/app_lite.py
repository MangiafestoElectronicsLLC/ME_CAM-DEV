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

def create_lite_app(pi_model, camera_config):
    """Create lightweight Flask app with all features"""
    
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.secret_key = os.urandom(24)
    
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
    
    # Initialize camera
    camera = None
    if camera_config['mode'] in ['lite', 'fast']:
        try:
            from picamera2 import Picamera2
            camera = Picamera2()
            camera.configure(camera.create_preview_configuration(
                main={"size": (640, 480), "format": "RGB888"}
            ))
            camera.start()
            logger.success(f"[CAMERA] Camera initialized: 640x480")
        except Exception as e:
            logger.warning(f"[CAMERA] Camera init failed: {e}")
    
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

    def save_motion_clip(camera_obj, frame, duration_sec=3):
        """Save a short MP4 clip when motion is detected"""
        try:
            import cv2
            recordings_path = os.path.join(BASE_DIR, "recordings")
            os.makedirs(recordings_path, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"motion_{timestamp}.mp4"
            filepath = os.path.join(recordings_path, filename)

            # Prepare video writer (approx 20 FPS)
            height, width, _ = frame.shape
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(filepath, fourcc, 20.0, (width, height))

            # Write initial frame
            writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

            # Capture additional frames for duration_sec seconds
            frame_count = int(duration_sec * 20)
            for _ in range(frame_count):
                try:
                    next_frame = camera_obj.capture_array()
                    writer.write(cv2.cvtColor(next_frame, cv2.COLOR_RGB2BGR))
                except Exception as e:
                    logger.debug(f"[MOTION] Clip capture error: {e}")
                    break
                time.sleep(0.05)

            writer.release()
            logger.info(f"[MOTION] Saved clip: {filename}")
            return filename
        except Exception as e:
            logger.error(f"[MOTION] Save clip failed: {e}")
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
        """Delete a specific motion event"""
        try:
            events_path = os.path.join(BASE_DIR, "logs", "motion_events.json")
            if os.path.exists(events_path):
                with open(events_path, 'r') as f:
                    events = json.load(f)
                
                # Find and remove
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
            save_config(cfg)
            
            from src.core import create_user
            create_user('admin', 'admin123')
            
            mark_first_run_complete()
            return redirect(url_for('login'))
        
        return render_template('first_run.html', pi_model=pi_model)
    
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
            storage=storage
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
        """Live video stream"""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        if camera is None:
            return Response(generate_test_pattern(), mimetype='multipart/x-mixed-replace; boundary=frame')
        
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
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
        
        events = get_motion_events()
        return jsonify({'events': events, 'count': len(events)})
    
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
        """Clear all motion events"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            events_path = os.path.join(BASE_DIR, "logs", "motion_events.json")
            with open(events_path, 'w') as f:
                json.dump([], f)
            logger.info("[MOTION] All events cleared")
            return jsonify({'ok': True})
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
        
        while True:
            try:
                if camera is None:
                    break
                
                frame = camera.capture_array()
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                
                # Motion detection
                if motion_cooldown > 0:
                    motion_cooldown -= 1
                else:
                    if last_frame is not None:
                        diff = cv2.absdiff(last_frame, gray)
                        motion = np.mean(diff) > 5
                        
                        if motion:
                            cfg = get_config()
                            nanny_cam = cfg.get('nanny_cam_enabled', False)

                            if not nanny_cam and cfg.get('motion_record_enabled', True):
                                logger.debug("[MOTION] Motion detected")
                                try:
                                    # Save short clip (or snapshot fallback)
                                    clip_file = save_motion_clip(camera, frame, duration_sec=3)
                                    video_path = clip_file
                                    if not clip_file:
                                        # Fallback to snapshot if clip fails
                                        video_path = save_motion_snapshot(frame)

                                    log_motion_event(
                                        event_type="motion",
                                        confidence=1.0,
                                        details={
                                            "mode": "lite",
                                            "video_path": video_path
                                        }
                                    )
                                except Exception as e:
                                    logger.debug(f"[MOTION] Recording error: {e}")

                            motion_cooldown = 100
                
                last_frame = gray
                
                # Convert to JPEG
                img = Image.fromarray(frame)
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=85)
                jpeg_bytes = buf.getvalue()
                
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
    
    return app
