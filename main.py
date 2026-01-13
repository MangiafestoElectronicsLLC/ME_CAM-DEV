from loguru import logger
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from web.app import app
from src.detection import motion_service

os.makedirs("logs", exist_ok=True)

if __name__ == "__main__":
    logger.add("logs/mecam.log", rotation="10 MB", retention="14 days", backtrace=True, diagnose=True)
    
    logger.info("=== ME_CAM v2.0 - Organized Structure ===")
    
    # Start motion detection service (with camera coordinator)
    if motion_service:
        try:
            motion_service.start()
            logger.info("[MAIN] Motion detection service initialized")
        except Exception as e:
            logger.error(f"[MAIN] Could not start motion service: {e}")
    
    app.run(host="0.0.0.0", port=8080, debug=False)
