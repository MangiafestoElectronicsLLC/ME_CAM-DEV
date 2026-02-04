"""
ME_CAM v2.2.3 - Main Application with Auto-Detection & Updates

ENHANCEMENTS (Feb 2, 2026):
✓ Hardware auto-detection (Pi model, camera type, RAM)
✓ Auto-rotation detection for cameras
✓ Enhanced motion event logging (immediate, debounced)
✓ Notification queue system with retries
✓ GitHub auto-update checker
✓ Per-hardware optimization (Pi Zero 2W vs Pi 5)
✓ Improved error handling and recovery
"""

from loguru import logger
import os
import sys
import threading
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# ============================================================================
# PHASE 1: Hardware Detection & Initialization
# ============================================================================

from src.utils.pi_detect import (
    get_pi_model, get_total_ram, get_camera_config,
    detect_camera_type, detect_camera_rotation, get_device_uuid,
    init_pi_detection
)

logger.info("=" * 70)
logger.info("ME_CAM v2.2.3 - Starting with Enhanced Auto-Detection")
logger.info("=" * 70)

# Detect hardware on startup
pi_model_info = get_pi_model()
camera_info = detect_camera_type()
camera_rotation = detect_camera_rotation()
device_uuid = get_device_uuid()

logger.info(f"\n[HARDWARE]")
logger.info(f"  Pi Model:        {pi_model_info['name']}")
logger.info(f"  RAM:             {pi_model_info['ram_mb']}MB")
logger.info(f"  Max Cameras:     {pi_model_info['max_cameras']}")
logger.info(f"  Recommended:     {pi_model_info['recommended_mode'].upper()}")

if camera_info:
    logger.success(f"\n[CAMERA]")
    logger.success(f"  Type:            {camera_info.get('type', 'Unknown')}")
    logger.success(f"  Name:            {camera_info.get('name', 'Unknown')}")
    logger.success(f"  Megapixels:      {camera_info.get('megapixels', 0)}")
    logger.success(f"  Max FPS:         {camera_info.get('max_fps', 0)}")
else:
    logger.warning(f"\n[CAMERA]")
    logger.warning(f"  NO CAMERA DETECTED - Using test mode")

if camera_rotation:
    logger.info(f"  Rotation:        {camera_rotation}")

logger.info(f"\n[SYSTEM]")
logger.info(f"  Device ID:       {device_uuid}")

# ============================================================================
# PHASE 2: Auto-Select App Version Based on Hardware
# ============================================================================

ram_mb = pi_model_info['ram_mb']
use_lite = "Zero 2W" in pi_model_info['name'] or ram_mb <= 512

if use_lite:
    logger.info(f"\n[APP] Loading LITE version for {pi_model_info['name']}")
    logger.info(f"[APP] Memory constraints: {ram_mb}MB < 1024MB threshold")
    
    from web.app_lite import create_lite_app
    from src.utils.pi_detect import get_camera_config
    
    camera_config = get_camera_config(pi_model_info)
    app = create_lite_app(pi_model_info, camera_config)
    fast_motion_detector = False
    app_version = "LITE"
else:
    logger.info(f"\n[APP] Loading FULL version for {pi_model_info['name']}")
    logger.info(f"[APP] Performance mode: {pi_model_info['recommended_mode']}")
    
    from web.app import app, fast_motion_detector
    app_version = "FULL"

# ============================================================================
# PHASE 3: Enhanced Motion & Notification Systems
# ============================================================================

from src.core.motion_logger import get_motion_logger, cleanup_on_startup
from src.core.notification_queue import get_notification_queue
from src.detection import motion_service
from src.core import get_sms_notifier

logger.info(f"\n[MOTION] Initializing motion detection system...")
motion_logger = get_motion_logger()
notification_queue = get_notification_queue()

logger.success(f"[MOTION] ✓ Motion logger initialized (debouncing enabled)")
logger.success(f"[MOTION] ✓ Notification queue ready")

# ============================================================================
# PHASE 4: GitHub Auto-Update Checker
# ============================================================================

from src.utils.github_updater import get_updater

updater = get_updater()
current_version = updater.get_current_version()
logger.info(f"[UPDATE] Current version: {current_version}")

# ============================================================================
# PHASE 5: SMS & Notifications Setup
# ============================================================================

os.makedirs("logs", exist_ok=True)

if __name__ == "__main__":
    logger.add("logs/mecam.log", rotation="10 MB", retention="14 days", 
               backtrace=True, diagnose=True)
    
    logger.info("=" * 70)
    logger.info(f"ME_CAM {app_version} v{current_version} - Main Application")
    logger.info("=" * 70)
    
    # Initialize SMS notifier
    try:
        sms_notifier = get_sms_notifier()
        if sms_notifier.enabled:
            logger.success("[SMS] Notifier initialized - SMS alerts ENABLED")
        else:
            logger.info("[SMS] Notifier ready - SMS alerts DISABLED")
    except Exception as e:
        logger.error(f"[SMS] Failed to initialize notifier: {e}")
    
    # Start background update checker (async, non-blocking)
    def check_updates_async():
        """Check for updates without blocking startup"""
        try:
            time.sleep(5)  # Wait for app to start
            has_update, version, url = updater.check_for_updates()
            if has_update:
                logger.warning(f"[UPDATE] ⚠ New version {version} available")
                logger.warning(f"[UPDATE] Run: git pull origin main")
        except Exception as e:
            logger.debug(f"[UPDATE] Background check skipped: {e}")
    
    update_thread = threading.Thread(target=check_updates_async, daemon=True)
    update_thread.start()
    
    # Log motion statistics
    motion_stats = motion_logger.get_statistics()
    logger.info(f"\n[MOTION] Statistics:")
    logger.info(f"  Total events: {motion_stats['total']}")
    logger.info(f"  Today: {motion_stats['today']}")
    logger.info(f"  With video: {motion_stats['with_video']}")
    
    # Display camera configuration
    if use_lite:
        camera_config = get_camera_config(pi_model_info)
        logger.info(f"\n[CONFIG] Recommended settings for {pi_model_info['name']}:")
        logger.info(f"  Mode: {camera_config['mode']}")
        logger.info(f"  Resolution: {camera_config['resolution']}")
        logger.info(f"  FPS: {camera_config['fps']}")
        logger.info(f"  Reason: {camera_config['reason']}")
    
    # Motion detection status
    if fast_motion_detector:
        logger.success("[MOTION] ✓ Using fast motion detector (integrated with camera)")
    else:
        logger.info("[MOTION] Motion detection mode: adaptive (based on camera availability)")
    
    logger.info(f"\n[SERVER] Starting Flask app on http://0.0.0.0:8080")
    logger.info(f"[SERVER] App version: {app_version}")
    logger.info(f"[SERVER] Device: {device_uuid}")
    logger.info(f"[SERVER] Camera rotation: {camera_rotation or 'none'}")
    logger.info("=" * 70)
    
    # Run Flask app
    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

