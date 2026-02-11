"""
ME_CAM v2.2.3 - Simplified for Pi Zero 2W
"""

from loguru import logger
import os
import sys
import uuid

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import only the functions that exist
from src.utils.pi_detect import get_pi_model, get_total_ram, get_camera_config

logger.info("=" * 70)
logger.info("ME_CAM v2.2.3 - Starting")
logger.info("=" * 70)

# Detect Pi model and RAM
pi_model_info = get_pi_model()
ram_mb = pi_model_info.get('ram_mb', get_total_ram())

logger.info("")
logger.info("[HARDWARE]")
logger.info(f"  Pi Model:        {pi_model_info.get('name', 'Unknown')}")
logger.info(f"  RAM:             {ram_mb}MB")

logger.info("")
logger.info("[SYSTEM]")
logger.info(f"  Device ID:       {uuid.getnode()}")

# Use LITE version for Pi Zero 2W
use_lite = "Zero 2W" in pi_model_info.get('name', '') or ram_mb <= 512

if use_lite:
    logger.info("")
    logger.info(f"[APP] Loading LITE version for {pi_model_info.get('name', 'Pi Zero 2W')}")
    
    # Get camera config and boost FPS
    camera_config = get_camera_config(pi_model_info)
    camera_config['fps'] = 40  # Boost from default 15 to 40
    
    # Create LITE Flask app
    from web.app_lite import create_lite_app
    app = create_lite_app(pi_model_info, camera_config)
else:
    logger.info("")
    logger.info("[APP] Loading FULL version")
    from web.app import app

# Run Flask
if __name__ == "__main__":
    logger.info("")
    logger.info("[FLASK] Starting on 0.0.0.0:8080")
    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)
