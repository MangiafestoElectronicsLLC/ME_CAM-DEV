"""Motion detection and AI modules"""
from .motion_service import motion_service
from .watchdog import CameraWatchdog

__all__ = ['motion_service', 'CameraWatchdog']
