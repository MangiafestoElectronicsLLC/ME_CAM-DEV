from loguru import logger
from web.app import app, motion_service
import os

os.makedirs("logs", exist_ok=True)

if __name__ == "__main__":
    logger.add("logs/mecam.log", rotation="10 MB", retention="14 days", backtrace=True, diagnose=True)
    
    logger.info("=== ME_CAM Starting with Camera Coordination ===")
    
    # Start motion detection service (with camera coordinator)
    if motion_service:
        try:
            motion_service.start()
            logger.info("[MAIN] Motion detection service initialized")
        except Exception as e:
            logger.error(f"[MAIN] Could not start motion service: {e}")
    
    app.run(host="0.0.0.0", port=8080, debug=False)
