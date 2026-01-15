from loguru import logger
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from web.app import app, fast_motion_detector
from src.detection import motion_service

os.makedirs("logs", exist_ok=True)

if __name__ == "__main__":
    logger.add("logs/mecam.log", rotation="10 MB", retention="14 days", backtrace=True, diagnose=True)
    
    logger.info("=== ME_CAM v2.0 - Organized Structure ===")
    
    # Only start libcamera-still motion service if fast motion detector is NOT available
    # DISABLED: libcamera-still hangs on Pi Zero 2W - use TEST MODE instead
    # if not fast_motion_detector and motion_service:
    #     try:
    #         motion_service.start()
    #         logger.info("[MAIN] Motion detection service initialized (libcamera-still mode)")
    #     except Exception as e:
    #         logger.error(f"[MAIN] Could not start motion service: {e}")
    if fast_motion_detector:
        logger.info("[MAIN] Using fast motion detector (integrated with camera streamer)")
    else:
        logger.info("[MAIN] Motion detection disabled (libcamera-still hangs on Pi Zero 2W)")
    
    app.run(host="0.0.0.0", port=8080, debug=False)
