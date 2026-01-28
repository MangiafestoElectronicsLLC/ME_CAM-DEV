from loguru import logger
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Auto-detect Pi Zero 2W and load LITE version
from src.utils.pi_detect import get_pi_model, get_ram_mb
pi_model = get_pi_model()
ram_mb = get_ram_mb()

if "Zero 2W" in pi_model or ram_mb <= 512:
    logger.info(f"[MAIN] Pi Zero 2W detected ({ram_mb}MB RAM) - Loading LITE v2.1")
    from web.app_lite import app, fast_motion_detector
else:
    logger.info(f"[MAIN] Standard Pi detected ({ram_mb}MB RAM) - Loading full version")
    from web.app import app, fast_motion_detector

from src.detection import motion_service
from src.core import get_sms_notifier

os.makedirs("logs", exist_ok=True)

if __name__ == "__main__":
    logger.add("logs/mecam.log", rotation="10 MB", retention="14 days", backtrace=True, diagnose=True)
    
    logger.info("=== ME_CAM v2.0 - Organized Structure ===")
    
    # Initialize SMS notifier
    try:
        sms_notifier = get_sms_notifier()
        if sms_notifier.enabled:
            logger.success("[SMS] Notifier initialized - SMS alerts ENABLED")
        else:
            logger.info("[SMS] Notifier ready - SMS alerts DISABLED")
    except Exception as e:
        logger.error(f"[SMS] Failed to initialize notifier: {e}")
    
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
