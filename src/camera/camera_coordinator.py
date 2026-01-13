"""
Camera Access Coordinator - Manages shared access to libcamera
Prevents conflicts between streaming and motion detection
"""
import threading
import time
from loguru import logger
from contextlib import contextmanager

class CameraCoordinator:
    """Coordinate camera access between streaming and motion detection"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._last_user = None
        self._last_access_time = 0
        self._min_delay = 0.5  # 500ms minimum between camera operations
    
    @contextmanager
    def access(self, user="unknown", priority="normal"):
        """
        Context manager for camera access
        
        Args:
            user: Name of the user (e.g., "streaming", "motion_detection")
            priority: "high" or "normal" - high priority can skip delay
        """
        acquired = False
        try:
            # High priority can acquire immediately
            if priority == "high":
                acquired = self._lock.acquire(timeout=10)
            else:
                # Normal priority respects minimum delay
                while True:
                    acquired = self._lock.acquire(timeout=1)
                    if acquired:
                        # Check if enough time has passed since last access
                        elapsed = time.time() - self._last_access_time
                        if elapsed >= self._min_delay:
                            break
                        else:
                            # Release and wait
                            self._lock.release()
                            acquired = False
                            time.sleep(self._min_delay - elapsed)
            
            if acquired:
                self._last_user = user
                self._last_access_time = time.time()
                logger.debug(f"[CAMERA] Access granted to {user}")
                yield True
            else:
                logger.warning(f"[CAMERA] Access timeout for {user}")
                yield False
                
        finally:
            if acquired:
                self._lock.release()
                logger.debug(f"[CAMERA] Access released by {user}")

    def is_busy(self):
        """Check if camera is currently in use"""
        return self._lock.locked()
    
    def get_last_user(self):
        """Get the last user who accessed the camera"""
        return self._last_user

# Global singleton instance
camera_coordinator = CameraCoordinator()
