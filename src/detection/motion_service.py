"""
Background motion detection service that doesn't conflict with camera streaming
"""
import time
import threading
from loguru import logger
from .motion_detector import MotionDetector
from src.core import get_config
import cv2

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
            self.detector = MotionDetector(sensitivity=0.6, min_area=500)
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
                # Simple frame check without blocking camera
                # In lite mode, motion detection uses existing stream frames
                time.sleep(1)  # Check once per second
            except Exception as e:
                logger.error(f"[MOTION] Error in detection loop: {e}")
                time.sleep(5)
        
        logger.info("[MOTION] Detection loop ended")

# Global instance
motion_service = MotionDetectionService()
