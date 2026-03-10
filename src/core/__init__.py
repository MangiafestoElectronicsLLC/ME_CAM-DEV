"""Core functionality - configuration, auth, utilities"""
from .config_manager import get_config, save_config, is_first_run, mark_first_run_complete
from .user_auth import (
    authenticate, create_user, user_exists, get_user, delete_user,
    get_enrollment_key, verify_enrollment_key, rotate_enrollment_key, ensure_enrollment_key
)
from .battery_monitor import BatteryMonitor
from .thumbnail_gen import extract_thumbnail
from .qr_generator import generate_setup_qr
from .emergency_handler import EmergencyHandler
from .motion_logger import log_motion_event, get_recent_events, get_event_statistics, clear_old_events, export_events_csv
from .sms_notifier import SMSNotifier, get_sms_notifier, reset_sms_notifier, resolve_sms_config

__all__ = [
    'get_config', 'save_config', 'is_first_run', 'mark_first_run_complete',
    'authenticate', 'create_user', 'user_exists', 'get_user', 'delete_user',
    'get_enrollment_key', 'verify_enrollment_key', 'rotate_enrollment_key', 'ensure_enrollment_key',
    'BatteryMonitor', 'extract_thumbnail', 'generate_setup_qr',
    'EmergencyHandler', 'log_motion_event', 'get_recent_events', 
    'get_event_statistics', 'clear_old_events', 'export_events_csv',
    'SMSNotifier', 'get_sms_notifier', 'reset_sms_notifier', 'resolve_sms_config'
]
