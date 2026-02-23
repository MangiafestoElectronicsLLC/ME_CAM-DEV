# Facial Recognition Integration - Code Snippets for app_lite.py

**Copy-paste these exact code blocks into your `web/app_lite.py` file**

---

## 📍 Location 1: Add Import (Around Line 50)

**Find this section:**
```python
try:
    from src.detection.tflite_detector import SmartMotionDetector, DetectionTracker
    AI_DETECTION_AVAILABLE = True
    logger.info("[V3] AI detection module loaded successfully")
except ImportError as e:
    AI_DETECTION_AVAILABLE = False
    logger.warning(f"[V3] AI detection not available: {e}")
```

**Add after it:**
```python
# Facial Recognition for Pi 5
try:
    from src.detection.facial_recognition_pi5 import create_facial_recognition
    FACIAL_RECOGNITION_AVAILABLE = True
    logger.info("[FACIAL] Pi 5 facial recognition module loaded")
except ImportError as e:
    FACIAL_RECOGNITION_AVAILABLE = False
    logger.warning(f"[FACIAL] Facial recognition not available: {e}")
```

---

## 📍 Location 2: Initialize in create_lite_app() (Around Line 140)

**Find this:**
```python
def create_lite_app(pi_model, camera_config):
    """Create lightweight Flask app with all features"""
    
    app = Flask(__name__, template_folder='templates', static_folder='static')
    cfg = get_config()
    security = _ensure_security_cfg(cfg)
    app.secret_key = security.get("secret_key")
```

**Add after the Flask app initialization and battery monitor:**
```python
    # Initialize facial recognition for Pi 5
    facial_recognition = None
    if FACIAL_RECOGNITION_AVAILABLE:
        try:
            pi_ram = pi_model.get('ram_mb', 1024)
            if pi_ram >= 4096:  # Requires 4GB+ RAM (Pi 5 has 8GB)
                cfg_fresh = get_config()
                facial_recognition = create_facial_recognition(
                    base_dir=BASE_DIR,
                    enabled=cfg_fresh.get('facial_recognition_enabled', True)
                )
                if facial_recognition:
                    logger.success(f"[FACIAL] Pi 5 facial recognition initialized (RAM: {pi_ram}MB)")
                else:
                    logger.warning("[FACIAL] Facial recognition disabled in config")
            else:
                logger.info(f"[FACIAL] Skipped (requires 4GB+ RAM, found {pi_ram}MB)")
        except Exception as e:
            logger.error(f"[FACIAL] Initialization failed: {e}")
            facial_recognition = None
```

---

## 📍 Location 3: Motion Detection Integration (Around Line 2150)

**Find the motion detection section in `generate_frames()` that looks like:**
```python
                    motion = (
                        max_diff > 75 and            # more sensitive contrast detection
                        motion_percent > 1.2 and     # lower threshold for faster detection
                        edge_motion > 1000 and       # slightly more permissive edges
                        mean_diff > 15 and
                    )

                    if motion and not nanny_cam_enabled:
                        logger.info(f"[MOTION] Motion detected...")
```

**Replace the `if motion and not nanny_cam_enabled:` block with:**
```python
                    if motion and not nanny_cam_enabled:
                        logger.info(f"[MOTION] Motion detected: {motion_ratio*100:.1f}% pixels")
                        
                        # Extract face recognition data if available
                        face_recognition_data = None
                        if facial_recognition and facial_recognition.enabled:
                            try:
                                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                faces = facial_recognition.detect_faces_in_frame(frame_rgb)
                                
                                if faces:
                                    face_results = []
                                    for face in faces:
                                        face_location = face['location']
                                        result = facial_recognition.recognize_face(frame_rgb, face_location)
                                        face_results.append(result)
                                    
                                    # Summarize face data
                                    recognized_count = len([f for f in face_results if f['recognized']])
                                    unknown_count = len([f for f in face_results if not f['recognized']])
                                    blacklisted_count = len([f for f in face_results if f.get('is_blacklisted')])
                                    recognized_names = [f['name'] for f in face_results if f['recognized'] and f['name']]
                                    
                                    face_recognition_data = {
                                        'total_faces_detected': len(faces),
                                        'recognized_count': recognized_count,
                                        'unknown_count': unknown_count,
                                        'blacklisted_count': blacklisted_count,
                                        'recognized_names': recognized_names,
                                        'event_type': 'motion_with_faces'
                                    }
                                    
                                    # Log based on recognition results
                                    if blacklisted_count > 0:
                                        logger.critical(f"🚨 SECURITY ALERT: Blacklisted person detected in motion event")
                                        logger.warning(f"[MOTION] {face_recognition_data}")
                                    elif recognized_count > 0:
                                        logger.success(f"[MOTION] Recognized person(s): {recognized_names}")
                                    else:
                                        logger.warning(f"[MOTION] Unknown person detected")
                            
                            except Exception as e:
                                logger.debug(f"[FACIAL] Motion frame processing error: {e}")
                        
                        # Log motion event with face data included
                        event_details = {
                            'threshold': motion_threshold,
                            'motion_ratio': motion_ratio,
                            'motion_percent': motion_percent,
                            'max_diff': max_diff,
                            'mean_diff': mean_diff,
                        }
                        
                        if face_recognition_data:
                            event_details['face_recognition'] = face_recognition_data
                        
                        event_data = log_motion_event(
                            event_type='motion_detected',
                            confidence=motion_ratio,
                            details=event_details
                        )
```

---

## 📍 Location 4: Add API Routes (Around Line 2600, before `def generate_frames()`)

**Add these 6 new route handlers:**

```python
    # ============= FACIAL RECOGNITION API ROUTES =============
    
    @app.route("/api/face/whitelist", methods=["GET"])
    def api_face_whitelist_get():
        """Get all whitelisted persons"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        if not facial_recognition or not facial_recognition.enabled:
            return jsonify({'whitelist': [], 'enabled': False, 'count': 0}), 200
        
        try:
            whitelist = facial_recognition.get_whitelist()
            return jsonify({
                'whitelist': whitelist,
                'enabled': True,
                'count': len(whitelist)
            })
        except Exception as e:
            logger.error(f"[FACIAL] Whitelist get error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route("/api/face/whitelist", methods=["POST"])
    def api_face_whitelist_add():
        """Add person to whitelist"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        if not facial_recognition or not facial_recognition.enabled:
            return jsonify({'error': 'Facial recognition disabled'}), 403
        
        try:
            person_name = request.form.get('name', '').strip()
            image_file = request.files.get('image')
            
            if not person_name:
                return jsonify({'error': 'Person name required'}), 400
            
            if not image_file:
                return jsonify({'error': 'Image file required'}), 400
            
            # Save temporary image
            temp_dir = os.path.join(BASE_DIR, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, f"{int(time.time())}_{person_name}.jpg")
            image_file.save(temp_path)
            
            # Add to whitelist
            if facial_recognition.add_person_to_whitelist(person_name, temp_path):
                os.remove(temp_path)
                logger.info(f"[FACIAL] Added {person_name} to whitelist via API")
                
                return jsonify({
                    'ok': True,
                    'message': f'✓ Added {person_name} to whitelist',
                    'whitelist': facial_recognition.get_whitelist()
                })
            else:
                os.remove(temp_path)
                return jsonify({'error': 'No face detected in image'}), 400
        
        except Exception as e:
            logger.error(f"[FACIAL] Add person error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route("/api/face/whitelist/<person_name>", methods=["DELETE"])
    def api_face_whitelist_delete(person_name):
        """Remove person from whitelist"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        if not facial_recognition or not facial_recognition.enabled:
            return jsonify({'error': 'Facial recognition disabled'}), 403
        
        try:
            person_name = person_name.strip()
            
            if facial_recognition.remove_person_from_whitelist(person_name):
                logger.info(f"[FACIAL] Removed {person_name} from whitelist")
                return jsonify({
                    'ok': True,
                    'message': f'✓ Removed {person_name}',
                    'whitelist': facial_recognition.get_whitelist()
                })
            else:
                return jsonify({'error': 'Person not found'}), 404
        
        except Exception as e:
            logger.error(f"[FACIAL] Remove person error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route("/api/face/blacklist", methods=["GET"])
    def api_face_blacklist_get():
        """Get all blacklisted persons"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        if not facial_recognition or not facial_recognition.enabled:
            return jsonify({'blacklist': [], 'enabled': False, 'count': 0}), 200
        
        try:
            blacklist = facial_recognition.get_blacklist()
            return jsonify({
                'blacklist': blacklist,
                'enabled': True,
                'count': len(blacklist)
            })
        except Exception as e:
            logger.error(f"[FACIAL] Blacklist get error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route("/api/face/blacklist", methods=["POST"])
    def api_face_blacklist_add():
        """Add person to blacklist (THREAT)"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        if not facial_recognition or not facial_recognition.enabled:
            return jsonify({'error': 'Facial recognition disabled'}), 403
        
        try:
            person_name = request.form.get('name', '').strip()
            image_file = request.files.get('image')
            
            if not person_name:
                return jsonify({'error': 'Person name required'}), 400
            
            if not image_file:
                return jsonify({'error': 'Image file required'}), 400
            
            # Save temporary image
            temp_dir = os.path.join(BASE_DIR, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, f"{int(time.time())}_{person_name}.jpg")
            image_file.save(temp_path)
            
            # Add to blacklist
            if facial_recognition.add_person_to_blacklist(person_name, temp_path):
                os.remove(temp_path)
                logger.warning(f"[FACIAL] 🚨 Added {person_name} to BLACKLIST via API")
                
                return jsonify({
                    'ok': True,
                    'message': f'🚨 Added {person_name} to BLACKLIST - emergency alerts enabled',
                    'blacklist': facial_recognition.get_blacklist()
                })
            else:
                os.remove(temp_path)
                return jsonify({'error': 'No face detected in image'}), 400
        
        except Exception as e:
            logger.error(f"[FACIAL] Blacklist add error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route("/api/face/statistics", methods=["GET"])
    def api_face_statistics():
        """Get facial recognition statistics"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        if not facial_recognition or not facial_recognition.enabled:
            return jsonify({
                'enabled': False,
                'message': 'Facial recognition not enabled'
            }), 200
        
        try:
            stats = facial_recognition.get_statistics()
            stats['timestamp'] = datetime.utcnow().isoformat()
            return jsonify(stats)
        except Exception as e:
            logger.error(f"[FACIAL] Statistics error: {e}")
            return jsonify({'error': str(e)}), 500
```

---

## 🔍 Testing the Integration

### Test 1: Verify Import Works

```bash
ssh pi@mecamera.local
cd ~/ME_CAM-DEV && source venv/bin/activate

python3 -c "
from web.app_lite import FACIAL_RECOGNITION_AVAILABLE
print(f'Facial Recognition Available: {FACIAL_RECOGNITION_AVAILABLE}')
"
```

Expected output: `Facial Recognition Available: True`

### Test 2: Check API

```bash
# After app is running
curl -X GET http://mecamera.local:8080/api/face/statistics

# Should return JSON like:
{
  "enabled": true,
  "whitelist_persons": 0,
  "blacklist_persons": 0,
  "unknown_faces_detected": 0,
  "total_faces_processed": 0,
  "recognition_threshold": 0.6,
  "detection_confidence": 0.99,
  "timestamp": "2026-02-19T..."
}
```

### Test 3: Live Test

1. SSH to Pi and put a photo in the whitelist:
   ```bash
   mkdir -p ~/ME_CAM-DEV/faces/whitelist/TestPerson
   cp /path/to/your/photo.jpg ~/ME_CAM-DEV/faces/whitelist/TestPerson/
   ```

2. Restart the app:
   ```bash
   sudo systemctl restart mecam
   ```

3. Check that it loaded:
   ```bash
   curl http://mecamera.local:8080/api/face/whitelist
   # Should show: {"whitelist": ["TestPerson"], "enabled": true, "count": 1}
   ```

4. Walk in front of camera, check motion events for face data

---

## ⚙️ Configuration (Add to config.json)

```json
{
  "facial_recognition_enabled": true,
  "facial_recognition_confidence": 0.6,
  "face_detection_in_motion": true,
  "log_unknown_faces": true
}
```

---

## 📌 Important Notes

1. **Don't forget the import!** It goes near the top with other imports
2. **Initialization must be after `app = Flask(...)`**
3. **Motion detection block is in the `generate_frames()` function** (around line 2100-2150)
4. **API routes go before `generate_frames()` definition**
5. **Test each section as you add it**

---

## 🐛 Common Mistakes

❌ **Mistake 1**: Putting code in wrong location
✅ **Fix**: Follow the "📍 Location" markers exactly

❌ **Mistake 2**: Indentation errors
✅ **Fix**: Use spaces (4-space indentation in Python)

❌ **Mistake 3**: Missing imports
✅ **Fix**: Add the facial recognition import from Location 1

❌ **Mistake 4**: Forgetting to install face_recognition
✅ **Fix**: Run `pip install face-recognition` on Pi

---

## 📊 Code Organization Summary

| What | Where | Lines |
|------|-------|-------|
| Imports | ~Line 50 | 5 lines |
| Initialization | ~Line 140 | 15 lines |
| Motion Integration | ~Line 2150 | 40 lines |
| API Routes | ~Line 2600 | 150 lines |
| **Total additions** | - | **~210 lines** |

---

## ✨ After Integration

Your lite app will have:
- ✅ Real-time face detection
- ✅ Known person recognition
- ✅ Threat/blacklist detection
- ✅ Motion events with face data
- ✅ Web API for management
- ✅ Statistics tracking

All while maintaining the lightweight profile of the lite app! 🚀

---

**Version**: 2.3.0  
**Status**: ✅ Copy-Paste Ready  
**Date**: February 19, 2026

