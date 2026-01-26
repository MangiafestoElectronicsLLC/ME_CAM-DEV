"""
ME Camera Lite Mode - Optimized for Pi Zero 2W (512MB RAM)
===========================================================
This is a stripped-down version that works like your old Streamlit project:
- Minimal memory footprint (~150MB instead of ~400MB)
- Direct camera access (no background threads)
- Essential features only
- HTTPS support maintained
- Domain name support (me_cam.com)
- Auto-boot capability

Perfect for Pi Zero 2W while maintaining compatibility with larger Pi models.
"""

from loguru import logger
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from web.app_lite import create_lite_app
from src.utils.pi_detect import init_pi_detection
from src.core import get_sms_notifier

os.makedirs("logs", exist_ok=True)

if __name__ == "__main__":
    logger.add("logs/mecam_lite.log", rotation="5 MB", retention="7 days", backtrace=True, diagnose=True)
    
    # Detect Pi model
    pi_model, camera_config = init_pi_detection()
    
    logger.info("=== ME_CAM v2.1 LITE MODE ===")
    logger.info(f"[SYSTEM] Running on {pi_model['name']} with {pi_model['ram_mb']}MB RAM")
    logger.info("[SYSTEM] Lightweight mode: Minimal memory footprint for Pi Zero 2W")
    logger.info("[SYSTEM] Features: Camera streaming, battery monitor, storage, HTTPS, Motion detection, SMS alerts")
    logger.info("[SYSTEM] Disabled: Background threads, multi-device polling")
    logger.info("[NETWORK] VPN Support: Enabled - connect from anywhere")
    
    # Initialize SMS notifier
    try:
        sms_notifier = get_sms_notifier()
        if sms_notifier.enabled:
            logger.success("[SMS] Notifier initialized - SMS alerts ENABLED")
        else:
            logger.info("[SMS] Notifier ready - SMS alerts DISABLED")
    except Exception as e:
        logger.error(f"[SMS] Failed to initialize notifier: {e}")
    
    # Create lightweight Flask app
    app = create_lite_app(pi_model, camera_config)
    
    # Run Flask with HTTPS support
    cert_file = os.path.join(os.path.dirname(__file__), 'certs', 'certificate.pem')
    key_file = os.path.join(os.path.dirname(__file__), 'certs', 'private_key.pem')
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        logger.info("[HTTPS] Running with SSL/TLS (https://me_cam.com:8080)")
        logger.info("[HTTPS] Certificate supports: me_cam.com, localhost, 127.0.0.1, and VPN networks")
        # Use ssl_context with proper configuration for VPN support
        app.run(
            host="0.0.0.0", 
            port=8080, 
            debug=False, 
            ssl_context=(cert_file, key_file),
            use_reloader=False  # Disable reloader on Pi Zero (saves memory)
        )
    else:
        logger.warning("[HTTPS] Certificates not found, running without SSL")
        logger.info("[HTTP] Access at: http://[DEVICE-IP]:8080")
        logger.info("[NETWORK] ⚠️ WARNING: HTTPS not available. VPN connections may be insecure!")
        app.run(
            host="0.0.0.0", 
            port=8080, 
            debug=False,
            use_reloader=False
        )
