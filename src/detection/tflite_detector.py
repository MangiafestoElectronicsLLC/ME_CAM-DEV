"""
TensorFlow Lite Edge AI Detection for ME_CAM
=============================================
Run object detection locally on Pi Zero 2W to distinguish:
  - Person detected → Send alert
  - Pet detected → Log silently  
  - Vehicle detected → Alert if driveway
  - Motion only → Ignore

Replaces generic motion detection with smart AI detection.
Runs inference every 2-5 seconds (not every frame for performance).

Model: MobileNet SSD v2 COCO (4-13MB, ~100ms inference on Pi Zero)
"""

import numpy as np
import cv2
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import os
from loguru import logger
import time
import asyncio
from collections import deque

# TensorFlow Lite runtime (lightweight)
try:
    import tflite_runtime.interpreter as tflite
    TFLITE_AVAILABLE = True
except ImportError:
    TFLITE_AVAILABLE = False
    logger.warning("[TFLite] tflite-runtime not installed: pip install tflite-runtime")


class TFLiteDetector:
    """
    Run TensorFlow Lite object detection on frames.
    
    Usage:
        detector = TFLiteDetector('models/model.tflite')
        detections = detector.detect(frame)
        print(detections)  # {'person': [{'confidence': 0.95, ...}], ...}
    """
    
    # COCO class index mapping
    COCO_CLASSES = {
        1: ('person', 'high'),        # High priority alert
        2: ('bicycle', 'medium'),
        3: ('car', 'medium'),
        4: ('motorbike', 'medium'),
        5: ('aeroplane', 'low'),
        6: ('bus', 'medium'),
        7: ('train', 'low'),
        8: ('truck', 'medium'),
        15: ('cat', 'low'),            # Low priority alert
        16: ('dog', 'low'),
        17: ('horse', 'low'),
        18: ('sheep', 'low'),
        19: ('cow', 'low'),
    }
    
    def __init__(self, model_path: str, confidence_threshold: float = 0.5):
        """
        Initialize TensorFlow Lite detector.
        
        Args:
            model_path: Path to .tflite model file
            confidence_threshold: Minimum confidence to report detection (0-1)
        """
        if not TFLITE_AVAILABLE:
            raise RuntimeError("tflite-runtime not installed")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        self.logger = logger.bind(name="TFLite")
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        
        # Load model
        self.interpreter = tflite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        
        # Get input/output details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        self.input_shape = self.input_details[0]['shape']
        self.input_dtype = self.input_details[0]['dtype']
        
        self.logger.success(f"[INIT] Model loaded: {Path(model_path).name}")
        self.logger.debug(f"[INPUT] Shape: {self.input_shape}, Dtype: {self.input_dtype}")
        
        # Stats
        self.inference_times = deque(maxlen=10)
        self.detections_history = deque(maxlen=30)
    
    def detect(self, frame: np.ndarray) -> Dict[str, List[Dict]]:
        """
        Run inference on frame.
        
        Args:
            frame: OpenCV image (BGR, uint8)
        
        Returns:
            {
                'person': [{'confidence': 0.95, 'box': [x1, y1, x2, y2], ...}],
                'pet': [...],
                'vehicle': [...],
                'other': [...]
            }
        """
        start_time = time.time()
        
        # Preprocess: resize to model input size
        input_height, input_width = self.input_shape[1], self.input_shape[2]
        resized = cv2.resize(frame, (input_width, input_height))
        
        # Normalize if model expects float (most modern models do)
        if self.input_dtype == np.float32:
            input_data = np.expand_dims(resized.astype(np.float32) / 255.0, axis=0)
        else:
            input_data = np.expand_dims(resized.astype(np.uint8), axis=0)
        
        # Run inference
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        
        # Parse outputs (SSD Mobilenet outputs)
        detections = self.interpreter.get_tensor(self.output_details[0]['index'])
        classes = self.interpreter.get_tensor(self.output_details[1]['index'])
        scores = self.interpreter.get_tensor(self.output_details[2]['index'])
        
        # Group by class
        results = {
            'person': [],
            'pet': [],
            'vehicle': [],
            'other': []
        }
        
        # Process detections
        for i in range(len(scores[0])):
            score = scores[0][i]
            
            if score < self.confidence_threshold:
                continue
            
            class_id = int(classes[0][i])
            box = detections[0][i]  # [y1, x1, y2, x2] normalized
            
            # Get class name and priority
            class_info = self.COCO_CLASSES.get(class_id)
            if class_info:
                class_name, priority = class_info
            else:
                class_name, priority = f"class_{class_id}", "low"
            
            # Categorize
            if class_name == 'person':
                category = 'person'
            elif class_name in ['cat', 'dog', 'horse', 'sheep', 'cow']:
                category = 'pet'
            elif class_name in ['car', 'bicycle', 'truck', 'bus', 'motorbike']:
                category = 'vehicle'
            else:
                category = 'other'
            
            # Denormalize bounding box
            h, w = frame.shape[:2]
            y1, x1, y2, x2 = box
            x1, x2 = int(x1 * w), int(x2 * w)
            y1, y2 = int(y1 * h), int(y2 * h)
            
            detection = {
                'class': class_name,
                'confidence': float(score),
                'priority': priority,
                'box': (x1, y1, x2, y2),
                'center': ((x1 + x2) // 2, (y1 + y2) // 2)
            }
            
            results[category].append(detection)
        
        # Track inference time
        elapsed = time.time() - start_time
        self.inference_times.append(elapsed)
        
        # Log
        total_detections = sum(len(v) for v in results.values())
        if total_detections > 0:
            self.logger.debug(
                f"[INFER] {total_detections} objects detected in {elapsed*1000:.1f}ms"
            )
        
        return results
    
    def get_average_inference_time(self) -> float:
        """Get average inference time (last 10 inferences)."""
        if not self.inference_times:
            return 0.0
        return np.mean(self.inference_times)
    
    def should_alert(self, detections: Dict) -> Tuple[bool, str, str]:
        """
        Determine if alert should be sent based on detections.
        
        Returns:
            (should_alert, alert_type, message)
        """
        # Highest priority first
        if detections['person']:
            person = detections['person'][0]
            confidence = person['confidence']
            return True, 'person', f"Person detected ({confidence*100:.0f}%)"
        
        if detections['vehicle']:
            vehicle = detections['vehicle'][0]
            confidence = vehicle['confidence']
            return True, 'vehicle', f"Vehicle detected ({confidence*100:.0f}%)"
        
        # Low priority - only alert if configured
        if detections['pet']:
            return False, 'pet', f"Pet detected (silent)"
        
        if detections['other']:
            return False, 'other', f"Unknown object detected (silent)"
        
        return False, None, "No significant objects"


class SmartMotionDetector:
    """
    Combines pixel-change detection (fast) with TFLite AI (smart).
    
    Strategy:
    1. Every frame: Compute frame difference (fast, ~5ms)
    2. If motion detected: Capture frame
    3. Every 2-5 seconds: Run TensorFlow inference on captured frame
    4. Decide alert based on AI results
    
    This keeps CPU usage low while getting smart detection.
    """
    
    def __init__(self, model_path: str, 
                 motion_threshold: int = 5000,
                 inference_interval: float = 2.0):
        """
        Args:
            model_path: Path to TFLite model
            motion_threshold: Pixel differences to trigger capture (~5000 for 640x480)
            inference_interval: Run inference every N seconds (2-5 recommended)
        """
        self.logger = logger.bind(name="SmartMotion")
        self.detector = TFLiteDetector(model_path)
        self.motion_threshold = motion_threshold
        self.inference_interval = inference_interval
        
        self.prev_frame = None
        self.last_inference_time = 0
        self.last_detections = None
        
        self.logger.success("[INIT] Smart motion detector ready")
    
    def process_frame(self, frame: np.ndarray) -> Tuple[bool, Optional[Dict], str]:
        """
        Process single frame.
        
        Returns:
            (motion_detected, detections, reason)
        """
        current_time = time.time()
        
        # Step 1: Fast motion detection
        if self.prev_frame is None:
            self.prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return False, None, "Initializing"
        
        # Compute frame difference
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(self.prev_frame, gray)
        motion_pixels = np.sum(diff > 30)  # Pixel threshold
        
        motion_detected = motion_pixels > self.motion_threshold
        self.prev_frame = gray
        
        # Step 2: If motion AND enough time passed → Run AI inference
        if motion_detected and (current_time - self.last_inference_time) > self.inference_interval:
            self.last_detections = self.detector.detect(frame)
            self.last_inference_time = current_time
            
            should_alert, alert_type, message = self.detector.should_alert(self.last_detections)
            
            return should_alert, self.last_detections, message
        
        # Return previously detected objects if fresh
        if self.last_detections:
            should_alert, alert_type, message = self.detector.should_alert(self.last_detections)
            if should_alert:
                return True, self.last_detections, message
        
        return False, None, f"Motion pixels: {motion_pixels}"


class DetectionTracker:
    """
    Track detections across frames to reduce false positives.
    
    Requires 2+ consecutive detections before alerting.
    """
    
    def __init__(self, confidence_for_tracking: float = 0.6):
        self.confidence_for_tracking = confidence_for_tracking
        self.tracked_objects = {}  # {class: count}
        self.logger = logger.bind(name="Tracker")
    
    def update(self, detections: Dict) -> Dict[str, int]:
        """
        Update tracking state.
        
        Returns:
            Count of consecutive detections: {'person': 2, 'vehicle': 1, ...}
        """
        new_tracked = {}
        
        for class_name in ['person', 'pet', 'vehicle', 'other']:
            if detections[class_name]:
                # At least one detection in this class
                high_conf = [d for d in detections[class_name] 
                            if d['confidence'] > self.confidence_for_tracking]
                
                if high_conf:
                    # Increment counter
                    new_tracked[class_name] = self.tracked_objects.get(class_name, 0) + 1
        
        # Remove classes with no detections
        for class_name in ['person', 'pet', 'vehicle', 'other']:
            if class_name not in new_tracked:
                if class_name in self.tracked_objects:
                    del self.tracked_objects[class_name]
        
        self.tracked_objects = new_tracked
        return self.tracked_objects


# ===== Demo/Testing =====

def demo_detection():
    """Demo: Test detector on sample image."""
    if not TFLITE_AVAILABLE:
        print("Install: pip install tflite-runtime")
        return
    
    # Check if model exists
    model_path = "models/coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.tflite"
    
    if not os.path.exists(model_path):
        print(f"Model not found: {model_path}")
        print("Download from: https://storage.googleapis.com/download.tensorflow.org/models/tflite/...")
        return
    
    detector = TFLiteDetector(model_path)
    
    # Create test frame (green background)
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    test_frame[:, :] = [0, 255, 0]  # Green BGR
    
    detections = detector.detect(test_frame)
    print("\nDetections:")
    for class_name, objects in detections.items():
        if objects:
            print(f"  {class_name}: {len(objects)} objects")
            for obj in objects:
                print(f"    - {obj['class']}: {obj['confidence']*100:.1f}%")
    
    print(f"\nAverage inference time: {detector.get_average_inference_time()*1000:.1f}ms")


if __name__ == "__main__":
    print("[!] TensorFlow Lite detector module")
    print("[!] Usage: TFLiteDetector('model.tflite')")
