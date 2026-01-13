import subprocess
import time
from loguru import logger
import os
from camera_coordinator import camera_coordinator

class LibcameraStreamer:
    """Stream video using libcamera (native Raspberry Pi camera support)."""
    
    def __init__(self):
        self.jpeg_dir = "/tmp/libcamera_frames"
        os.makedirs(self.jpeg_dir, exist_ok=True)
    
    def get_single_frame_jpeg(self, width=640, height=480):
        """Capture single JPEG frame - more reliable than video streaming."""
        # Use camera coordinator to prevent conflicts with motion detection
        with camera_coordinator.access(user="streaming", priority="high") as granted:
            if not granted:
                logger.warning("[CAMERA] Could not acquire camera for streaming (busy)")
                return None
            
            try:
                output_path = f"{self.jpeg_dir}/frame.jpg"
                cmd = [
                    "libcamera-still",
                    "--width", str(width),
                    "--height", str(height),
                    "-o", output_path,
                    "--nopreview",
                    "--immediate",  # Capture immediately without preview
                    "-t", "100"  # 100ms timeout for capture
                ]
                
                result = subprocess.run(cmd, timeout=5, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if result.returncode == 0 and os.path.exists(output_path):
                    with open(output_path, 'rb') as f:
                        jpeg_data = f.read()
                    return jpeg_data
                else:
                    return None
            except subprocess.TimeoutExpired:
                logger.warning("[CAMERA] libcamera-still timeout (increase timeout or check camera)")
                return None
            except Exception as e:
                logger.warning(f"[CAMERA] Frame capture error: {e}")
                return None

def is_libcamera_available():
    """Check if libcamera is available."""
    try:
        result = subprocess.run(["which", "libcamera-still"], capture_output=True)
        return result.returncode == 0
    except:
        return False

