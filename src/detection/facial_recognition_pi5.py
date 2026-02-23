"""
Pi 5 Optimized Facial Recognition Module
=========================================
Uses face_recognition library (dlib) for high-accuracy face identification
Optimized for Pi 5's 8GB+ RAM and quad-core CPU (2.4GHz)

Features:
- Real-time face detection and recognition
- Whitelist/blacklist management
- Face encoding storage and matching
- JSON database of known faces
- Async face processing for non-blocking video streams
"""

import os
import json
import threading
import time
import numpy as np
from datetime import datetime
from pathlib import Path
from loguru import logger
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import pickle

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    logger.warning("[FACE] face_recognition not installed")

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


class FacialRecognitionPi5:
    """Pi 5 optimized facial recognition system"""
    
    def __init__(self, base_dir: str = ".", enabled: bool = True):
        self.base_dir = base_dir
        self.enabled = enabled and FACE_RECOGNITION_AVAILABLE
        
        # Create face database directories
        self.faces_dir = os.path.join(base_dir, "faces")
        self.whitelist_dir = os.path.join(self.faces_dir, "whitelist")
        self.blacklist_dir = os.path.join(self.faces_dir, "blacklist")
        self.unknown_dir = os.path.join(self.faces_dir, "unknown")
        self.encodings_dir = os.path.join(self.faces_dir, "encodings")
        
        for d in [self.whitelist_dir, self.blacklist_dir, self.unknown_dir, self.encodings_dir]:
            os.makedirs(d, exist_ok=True)
        
        # In-memory face databases (loaded on init)
        self.whitelist_encodings: Dict[str, List] = {}  # {person_name: [encoding, ...]}
        self.blacklist_encodings: Dict[str, List] = {}
        self.known_faces_db = os.path.join(self.encodings_dir, "known_faces.json")
        self.blacklist_db = os.path.join(self.encodings_dir, "blacklist.json")
        
        # Recognition thresholds (tuned for Pi 5)
        self.recognition_threshold = 0.6  # Lower = more strict (0.0-1.0)
        self.detection_confidence = 0.99  # Confidence for face detection
        
        # Recognition cache for performance
        self.face_cache = {}  # {person_name: last_seen_timestamp}
        self.unknown_faces_count = 0
        self.total_faces_seen = 0
        
        # Threading
        self.processing_lock = threading.Lock()
        self.cache_lock = threading.Lock()
        
        if self.enabled:
            self._load_databases()
            logger.success("[FACE] Facial recognition initialized (Pi 5 optimized)")
        else:
            logger.warning("[FACE] Facial recognition disabled or unavailable")
    
    def _load_databases(self):
        """Load whitelist and blacklist from storage on init"""
        try:
            # Load whitelist
            if os.path.exists(self.known_faces_db):
                with open(self.known_faces_db, 'r') as f:
                    data = json.load(f)
                    # Reconstruct encodings from JSON (lists -> numpy arrays later)
                    self.whitelist_encodings = data.get('whitelist', {})
                    logger.info(f"[FACE] Loaded {len(self.whitelist_encodings)} whitelisted persons")
            
            # Also load from actual image files (for backwards compatibility)
            self._index_whitelist_images()
            
            # Load blacklist
            if os.path.exists(self.blacklist_db):
                with open(self.blacklist_db, 'r') as f:
                    data = json.load(f)
                    self.blacklist_encodings = data.get('blacklist', {})
                    logger.info(f"[FACE] Loaded {len(self.blacklist_encodings)} blacklisted persons")
            
            self._index_blacklist_images()
            
        except Exception as e:
            logger.error(f"[FACE] Database load error: {e}")
    
    def _index_whitelist_images(self):
        """Index all whitelist images and compute encodings (Pi 5 can handle this)"""
        try:
            if not os.path.exists(self.whitelist_dir):
                return
            
            for person_name in os.listdir(self.whitelist_dir):
                person_path = os.path.join(self.whitelist_dir, person_name)
                if not os.path.isdir(person_path):
                    continue
                
                if person_name in self.whitelist_encodings:
                    continue  # Already indexed
                
                encodings = []
                image_count = 0
                
                for image_file in os.listdir(person_path):
                    if not image_file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        continue
                    
                    try:
                        image_path = os.path.join(person_path, image_file)
                        image = face_recognition.load_image_file(image_path)
                        face_encodings = face_recognition.face_encodings(image)
                        
                        if face_encodings:
                            for encoding in face_encodings:
                                encodings.append(encoding.tolist())  # Convert to list for JSON
                            image_count += 1
                            logger.debug(f"[FACE] Indexed {person_name}/{image_file}: {len(face_encodings)} face(s)")
                    except Exception as e:
                        logger.warning(f"[FACE] Failed to process {person_name}/{image_file}: {e}")
                
                if encodings:
                    self.whitelist_encodings[person_name] = encodings
                    logger.info(f"[FACE] Indexed {person_name}: {image_count} images, {len(encodings)} faces")
        
        except Exception as e:
            logger.error(f"[FACE] Whitelist indexing error: {e}")
    
    def _index_blacklist_images(self):
        """Index all blacklist images"""
        try:
            if not os.path.exists(self.blacklist_dir):
                return
            
            for person_name in os.listdir(self.blacklist_dir):
                person_path = os.path.join(self.blacklist_dir, person_name)
                if not os.path.isdir(person_path):
                    continue
                
                if person_name in self.blacklist_encodings:
                    continue
                
                encodings = []
                for image_file in os.listdir(person_path):
                    if not image_file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        continue
                    
                    try:
                        image_path = os.path.join(person_path, image_file)
                        image = face_recognition.load_image_file(image_path)
                        face_encodings = face_recognition.face_encodings(image)
                        
                        if face_encodings:
                            for encoding in face_encodings:
                                encodings.append(encoding.tolist())
                    except Exception as e:
                        logger.warning(f"[FACE] Failed to process blacklist {person_name}/{image_file}: {e}")
                
                if encodings:
                    self.blacklist_encodings[person_name] = encodings
                    logger.info(f"[FACE] Blacklist indexed {person_name}: {len(encodings)} faces")
        
        except Exception as e:
            logger.error(f"[FACE] Blacklist indexing error: {e}")
    
    def save_databases(self):
        """Save whitelist and blacklist to JSON files"""
        try:
            with open(self.known_faces_db, 'w') as f:
                json.dump({'whitelist': self.whitelist_encodings}, f)
            
            with open(self.blacklist_db, 'w') as f:
                json.dump({'blacklist': self.blacklist_encodings}, f)
            
            logger.debug("[FACE] Databases saved")
        except Exception as e:
            logger.error(f"[FACE] Database save error: {e}")
    
    def detect_faces_in_frame(self, frame_rgb) -> List[Dict]:
        """
        Detect all faces in frame
        Returns list of face dicts with locations and sizes
        """
        if not self.enabled or frame_rgb is None:
            return []
        
        try:
            # Use HOG-based detection for Pi 5 (much faster than CNN)
            # Pi 5's CPU is fast enough for HOG at good quality
            face_locations = face_recognition.face_locations(frame_rgb, model='hog', number_of_times_to_upsample=0)
            
            faces = []
            for (top, right, bottom, left) in face_locations:
                width = right - left
                height = bottom - top
                faces.append({
                    'location': (top, right, bottom, left),
                    'top': top,
                    'right': right,
                    'bottom': bottom,
                    'left': left,
                    'width': width,
                    'height': height,
                    'center_x': left + width // 2,
                    'center_y': top + height // 2
                })
            
            if faces:
                logger.debug(f"[FACE] Detected {len(faces)} face(s) in frame")
            
            return faces
        
        except Exception as e:
            logger.error(f"[FACE] Detection error: {e}")
            return []
    
    def recognize_face(self, frame_rgb, face_location: Tuple) -> Dict:
        """
        Recognize a single face in the frame
        Returns: {
            'recognized': bool,
            'name': str or None,
            'confidence': float 0.0-1.0,
            'is_whitelisted': bool,
            'is_blacklisted': bool,
            'match_type': 'whitelist'|'blacklist'|'unknown'
        }
        """
        if not self.enabled or frame_rgb is None:
            return {'recognized': False, 'name': None, 'confidence': 0.0, 'match_type': 'unknown'}
        
        try:
            # Get encoding for this face
            face_encodings = face_recognition.face_encodings(frame_rgb, [face_location])
            if not face_encodings:
                return {'recognized': False, 'name': None, 'confidence': 0.0, 'match_type': 'unknown'}
            
            face_encoding = face_encodings[0]
            
            # Check blacklist FIRST (security)
            for blacklist_person, blacklist_encodings in self.blacklist_encodings.items():
                # Convert stored encodings back to numpy arrays
                bl_encodings = [np.array(enc) for enc in blacklist_encodings]
                distances = face_recognition.face_distance(bl_encodings, face_encoding)
                
                min_distance = np.min(distances)
                if min_distance < self.recognition_threshold:
                    confidence = 1.0 - min_distance
                    logger.warning(f"[FACE] BLACKLISTED: {blacklist_person} (confidence: {confidence:.2f})")
                    
                    with self.cache_lock:
                        self.face_cache[f"BLACKLIST_{blacklist_person}"] = time.time()
                    
                    return {
                        'recognized': True,
                        'name': blacklist_person,
                        'confidence': confidence,
                        'is_blacklisted': True,
                        'is_whitelisted': False,
                        'match_type': 'blacklist'
                    }
            
            # Check whitelist
            best_match = None
            best_distance = self.recognition_threshold
            
            for whitelist_person, whitelist_encodings in self.whitelist_encodings.items():
                # Convert stored encodings back to numpy arrays
                wl_encodings = [np.array(enc) for enc in whitelist_encodings]
                distances = face_recognition.face_distance(wl_encodings, face_encoding)
                
                min_distance = np.min(distances)
                if min_distance < best_distance:
                    best_distance = min_distance
                    best_match = whitelist_person
            
            if best_match:
                confidence = 1.0 - best_distance
                logger.success(f"[FACE] Recognized: {best_match} (confidence: {confidence:.2f})")
                
                with self.cache_lock:
                    self.face_cache[best_match] = time.time()
                
                return {
                    'recognized': True,
                    'name': best_match,
                    'confidence': confidence,
                    'is_whitelisted': True,
                    'is_blacklisted': False,
                    'match_type': 'whitelist'
                }
            
            # Unknown face
            logger.info(f"[FACE] Unknown face detected (closest match distance: {best_distance:.2f})")
            
            with self.cache_lock:
                self.unknown_faces_count += 1
            
            return {
                'recognized': False,
                'name': None,
                'confidence': 0.0,
                'is_whitelisted': False,
                'is_blacklisted': False,
                'match_type': 'unknown'
            }
        
        except Exception as e:
            logger.error(f"[FACE] Recognition error: {e}")
            return {'recognized': False, 'name': None, 'confidence': 0.0, 'match_type': 'unknown'}
    
    def add_person_to_whitelist(self, person_name: str, image_path: str) -> bool:
        """Add a person to whitelist from an image file"""
        try:
            if not person_name or not image_path or not os.path.exists(image_path):
                return False
            
            # Load and encode the image
            image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image)
            
            if not face_encodings:
                logger.warning(f"[FACE] No face detected in {image_path}")
                return False
            
            # Create person directory
            person_dir = os.path.join(self.whitelist_dir, person_name)
            os.makedirs(person_dir, exist_ok=True)
            
            # Copy image to whitelist directory
            filename = os.path.basename(image_path)
            dest_path = os.path.join(person_dir, filename)
            
            import shutil
            shutil.copy2(image_path, dest_path)
            
            # Store encoding
            if person_name not in self.whitelist_encodings:
                self.whitelist_encodings[person_name] = []
            
            for encoding in face_encodings:
                self.whitelist_encodings[person_name].append(encoding.tolist())
            
            self.save_databases()
            logger.success(f"[FACE] Added {person_name} to whitelist ({len(face_encodings)} face(s))")
            
            return True
        
        except Exception as e:
            logger.error(f"[FACE] Failed to add {person_name}: {e}")
            return False
    
    def add_person_to_blacklist(self, person_name: str, image_path: str) -> bool:
        """Add a person to blacklist from an image file"""
        try:
            if not person_name or not image_path or not os.path.exists(image_path):
                return False
            
            image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image)
            
            if not face_encodings:
                logger.warning(f"[FACE] No face detected in {image_path}")
                return False
            
            # Create person directory
            person_dir = os.path.join(self.blacklist_dir, person_name)
            os.makedirs(person_dir, exist_ok=True)
            
            # Copy image
            filename = os.path.basename(image_path)
            dest_path = os.path.join(person_dir, filename)
            
            import shutil
            shutil.copy2(image_path, dest_path)
            
            # Store encoding
            if person_name not in self.blacklist_encodings:
                self.blacklist_encodings[person_name] = []
            
            for encoding in face_encodings:
                self.blacklist_encodings[person_name].append(encoding.tolist())
            
            self.save_databases()
            logger.warning(f"[FACE] Added {person_name} to BLACKLIST ({len(face_encodings)} face(s))")
            
            return True
        
        except Exception as e:
            logger.error(f"[FACE] Failed to blacklist {person_name}: {e}")
            return False
    
    def remove_person_from_whitelist(self, person_name: str) -> bool:
        """Remove a person from whitelist"""
        try:
            if person_name in self.whitelist_encodings:
                del self.whitelist_encodings[person_name]
            
            person_dir = os.path.join(self.whitelist_dir, person_name)
            if os.path.exists(person_dir):
                import shutil
                shutil.rmtree(person_dir)
            
            self.save_databases()
            logger.info(f"[FACE] Removed {person_name} from whitelist")
            return True
        except Exception as e:
            logger.error(f"[FACE] Failed to remove {person_name}: {e}")
            return False
    
    def get_whitelist(self) -> List[str]:
        """Get list of whitelisted persons"""
        return list(self.whitelist_encodings.keys())
    
    def get_blacklist(self) -> List[str]:
        """Get list of blacklisted persons"""
        return list(self.blacklist_encodings.keys())
    
    def get_statistics(self) -> Dict:
        """Get recognition statistics"""
        with self.cache_lock:
            whitelist_count = len(self.whitelist_encodings)
            blacklist_count = len(self.blacklist_encodings)
            unknown_count = self.unknown_faces_count
            total_count = self.total_faces_seen
        
        return {
            'enabled': self.enabled,
            'whitelist_persons': whitelist_count,
            'blacklist_persons': blacklist_count,
            'unknown_faces_detected': unknown_count,
            'total_faces_processed': total_count,
            'recognition_threshold': self.recognition_threshold,
            'detection_confidence': self.detection_confidence
        }


def create_facial_recognition(base_dir: str = ".", enabled: bool = True) -> Optional[FacialRecognitionPi5]:
    """Factory function to create facial recognition instance"""
    if not FACE_RECOGNITION_AVAILABLE:
        logger.warning("[FACE] face_recognition library not installed")
        return None
    
    return FacialRecognitionPi5(base_dir=base_dir, enabled=enabled)
