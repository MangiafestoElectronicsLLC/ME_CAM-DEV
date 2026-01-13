from loguru import logger
from web.app import app, motion_service
import os

os.makedirs("logs", exist_ok=True)

if __name__ == "__main__":
    logger.add("logs/mecam.log", rotation="10 MB", retention="14 days", backtrace=True, diagnose=True)
    
    # Start motion detection service
    if motion_service and not motion_service.running:
        logger.info("[MOTION] Starting motion detection service on app startup")
        motion_service.start()
    
    app.run(host="0.0.0.0", port=8080, debug=False)
