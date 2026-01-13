"""
High-performance camera streamer using picamera2
MUCH FASTER than libcamera-still subprocess approach
Continuous stream like Tkinter GUI - 15-30 FPS possible
"""
import io
import time
from threading import Thread, Lock, Event
from queue import Queue
from loguru import logger
import numpy as np

try:
    from picamera2 import Picamera2
    from picamera2.encoders import JpegEncoder, H264Encoder
    from picamera2.outputs import FileOutput
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    logger.warning("[CAMERA] picamera2 not available, falling back to libcamera-still")


class FastCameraStreamer:
    """
    High-performance camera streamer using continuous capture
    
    Performance comparison:
    - libcamera-still: 500-1000ms per frame (subprocess overhead)
    - picamera2: 30-60ms per frame (continuous stream)
    
    This is why your Tkinter GUI is faster!
    """
    
    def __init__(self, width=640, height=480, fps=15):
        self.width = width
        self.height = height
        self.fps = fps
        self.camera = None
        self.running = False
        self.frame_queue = Queue(maxsize=2)  # Small queue for latest frames
        self.current_jpeg = None
        self.lock = Lock()
        self.capture_thread = None
        self.frame_count = 0
        self.start_time = time.time()
        
    def start(self):
        """Start continuous camera capture in background thread"""
        if not PICAMERA2_AVAILABLE:
            logger.error("[CAMERA] picamera2 not installed - install with: sudo apt install -y python3-picamera2")
            return False
            
        try:
            self.camera = Picamera2()
            
            # Configure for fast JPEG streaming
            config = self.camera.create_still_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"},
                buffer_count=2  # Double buffering for speed
            )
            self.camera.configure(config)
            self.camera.start()
            
            # Wait for camera to warm up
            time.sleep(0.5)
            
            self.running = True
            self.capture_thread = Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            logger.success(f"[CAMERA] Fast streamer started: {self.width}x{self.height} @ {self.fps} FPS")
            return True
            
        except Exception as e:
            logger.error(f"[CAMERA] Failed to start fast streamer: {e}")
            return False
    
    def _capture_loop(self):
        """Continuous capture loop - runs in background thread"""
        import cv2
        
        frame_delay = 1.0 / self.fps
        
        while self.running:
            try:
                # Capture frame from camera (FAST - already streaming!)
                array = self.camera.capture_array()
                
                # Convert to JPEG (fast in-memory operation)
                _, jpeg = cv2.imencode('.jpg', array, [cv2.IMWRITE_JPEG_QUALITY, 85])
                jpeg_bytes = jpeg.tobytes()
                
                # Update current frame
                with self.lock:
                    self.current_jpeg = jpeg_bytes
                    self.frame_count += 1
                
                # Also put in queue for motion detection
                if not self.frame_queue.full():
                    self.frame_queue.put(array)
                
                time.sleep(frame_delay)
                
            except Exception as e:
                logger.error(f"[CAMERA] Capture error: {e}")
                time.sleep(0.1)
        
        # Calculate actual FPS achieved
        elapsed = time.time() - self.start_time
        actual_fps = self.frame_count / elapsed if elapsed > 0 else 0
        logger.info(f"[CAMERA] Stream stopped. Achieved {actual_fps:.1f} FPS avg")
    
    def get_jpeg_frame(self):
        """
        Get latest JPEG frame - INSTANT (already captured in background)
        
        This is why it's fast compared to libcamera-still subprocess!
        """
        with self.lock:
            return self.current_jpeg
    
    def get_frame_for_motion(self):
        """Get latest frame for motion detection (numpy array)"""
        try:
            if not self.frame_queue.empty():
                return self.frame_queue.get_nowait()
        except:
            pass
        return None
    
    def stop(self):
        """Stop camera stream"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        if self.camera:
            self.camera.stop()
            self.camera.close()
        logger.info("[CAMERA] Fast streamer stopped")
    
    def get_stats(self):
        """Get performance statistics"""
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        return {
            "frames_captured": self.frame_count,
            "elapsed_seconds": elapsed,
            "fps": fps,
            "resolution": f"{self.width}x{self.height}"
        }


class FastMotionDetector:
    """
    High-performance motion detector using continuous camera stream
    MUCH faster than spawning libcamera-still subprocess every 2 seconds
    """
    
    def __init__(self, streamer, config):
        self.streamer = streamer
        self.config = config
        self.last_frame = None
        self.motion_threshold = config["detection"].get("sensitivity", 0.6)
        self.min_area = config["detection"].get("min_motion_area", 500)
        self.detection_thread = None
        self.running = False
        self.motion_callback = None
        
    def start(self, motion_callback=None):
        """Start motion detection in background thread"""
        self.motion_callback = motion_callback
        self.running = True
        self.detection_thread = Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()
        logger.success("[MOTION] Fast motion detector started")
    
    def _detection_loop(self):
        """Continuous motion detection loop"""
        import cv2
        
        while self.running:
            try:
                # Get frame from camera streamer (fast - already captured!)
                frame = self.streamer.get_frame_for_motion()
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                # Convert to grayscale for motion detection
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                
                # First frame - just store it
                if self.last_frame is None:
                    self.last_frame = gray
                    continue
                
                # Calculate frame difference
                frame_diff = cv2.absdiff(self.last_frame, gray)
                _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
                
                # Dilate to fill gaps
                kernel = np.ones((5, 5), np.uint8)
                thresh = cv2.dilate(thresh, kernel, iterations=2)
                
                # Find contours
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Check for motion
                motion_detected = False
                for contour in contours:
                    if cv2.contourArea(contour) > self.min_area:
                        motion_detected = True
                        break
                
                if motion_detected and self.motion_callback:
                    self.motion_callback(frame)
                
                self.last_frame = gray
                time.sleep(0.2)  # Check every 200ms (5 times per second!)
                
            except Exception as e:
                logger.error(f"[MOTION] Detection error: {e}")
                time.sleep(0.5)
    
    def stop(self):
        """Stop motion detection"""
        self.running = False
        if self.detection_thread:
            self.detection_thread.join(timeout=2)
        logger.info("[MOTION] Fast motion detector stopped")
