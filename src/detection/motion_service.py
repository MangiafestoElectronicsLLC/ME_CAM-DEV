"""
Background motion detection service that doesn't conflict with camera streaming
"""
import time
import threading
from loguru import logger
from .libcamera_motion_detector import LibcameraMotionDetector
from src.core import get_config

class MotionDetectionService:
    """Run motion detection in background without blocking camera"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.detector = None
        
    def start(self):
        """Start the motion detection service"""
        if self.running:
            return
        
        try:
            cfg = get_config()
            if not cfg["storage"].get("motion_only", True):
                logger.info("[MOTION] Motion detection disabled in config")
                return
            
            self.detector = LibcameraMotionDetector(cfg)
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            logger.info("[MOTION] Motion detection service started")
        except Exception as e:
            logger.error(f"[MOTION] Failed to start service: {e}")
    
    def stop(self):
        """Stop the motion detection service"""
        self.running = False
        if self.detector and self.detector.is_recording:
            self.detector.stop_recording()
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("[MOTION] Motion detection service stopped")
    
    def _run(self):
        """Main loop - check for motion periodically"""
        logger.info("[MOTION] Starting motion detection loop...")
        
        while self.running:
            try:
                # Check for motion every 2 seconds (doesn't block streaming)
                self.detector.check_and_record()
                time.sleep(2)
            except Exception as e:
                logger.error(f"[MOTION] Error in detection loop: {e}")
                time.sleep(5)
        
        logger.info("[MOTION] Detection loop ended")

# Global instance
motion_service = MotionDetectionService()
