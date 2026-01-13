"""Core functionality - configuration, auth, utilities"""
from .config_manager import get_config, save_config, is_first_run, mark_first_run_complete
from .user_auth import authenticate, create_user, user_exists, get_user
from .battery_monitor import BatteryMonitor
from .thumbnail_gen import extract_thumbnail
from .qr_generator import generate_setup_qr
from .emergency_handler import send_emergency_alert

__all__ = [
    'get_config', 'save_config', 'is_first_run', 'mark_first_run_complete',
    'authenticate', 'create_user', 'user_exists', 'get_user',
    'BatteryMonitor', 'extract_thumbnail', 'generate_setup_qr',
    'send_emergency_alert'
]
