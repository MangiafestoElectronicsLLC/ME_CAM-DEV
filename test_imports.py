#!/usr/bin/env python3
"""Test if all imports work correctly"""
import sys
import os

print("=" * 60)
print("Testing ME_CAM imports...")
print("=" * 60)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    print("\n[1] Importing loguru...")
    from loguru import logger
    print("    ✅ loguru OK")
except Exception as e:
    print(f"    ❌ loguru FAILED: {e}")
    sys.exit(1)

try:
    print("\n[2] Importing src.core...")
    from src.core import (
        get_config, save_config, is_first_run, mark_first_run_complete,
        authenticate, create_user, user_exists, get_user,
        BatteryMonitor, extract_thumbnail, generate_setup_qr,
        log_motion_event, get_recent_events, get_event_statistics, export_events_csv,
        get_sms_notifier
    )
    print("    ✅ src.core OK")
except Exception as e:
    print(f"    ❌ src.core FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n[3] Importing src.camera...")
    from src.camera import (
        camera_coordinator, LibcameraStreamer, is_libcamera_available,
        FastCameraStreamer, FastMotionDetector, PICAMERA2_AVAILABLE
    )
    print("    ✅ src.camera OK")
except Exception as e:
    print(f"    ❌ src.camera FAILED: {e}")
    import traceback
    traceback.print_exc()
    # This is OK - camera might not be available on Windows
    print("    (This is OK - camera not available on Windows)")

try:
    print("\n[4] Importing src.detection...")
    from src.detection import motion_service, CameraWatchdog
    print("    ✅ src.detection OK")
except Exception as e:
    print(f"    ❌ src.detection FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n[5] Importing src.utils...")
    from src.utils.pi_detect import init_pi_detection, get_pi_info
    print("    ✅ src.utils OK")
except Exception as e:
    print(f"    ❌ src.utils FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n[6] Importing Flask web.app...")
    from web.app import app
    print("    ✅ web.app OK")
except Exception as e:
    print(f"    ❌ web.app FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n[7] Testing main.py imports...")
    from web.app import app, fast_motion_detector
    from src.detection import motion_service
    from src.core import get_sms_notifier
    print("    ✅ main.py imports OK")
except Exception as e:
    print(f"    ❌ main.py imports FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL IMPORTS SUCCESSFUL!")
print("=" * 60)
