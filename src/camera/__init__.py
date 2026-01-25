"""Camera streaming and coordination"""
from .camera_coordinator import camera_coordinator
from .libcamera_streamer import LibcameraStreamer, is_libcamera_available
from .rpicam_streamer import RpicamStreamer, is_rpicam_available

try:
    from .fast_camera_streamer import FastCameraStreamer, FastMotionDetector, PICAMERA2_AVAILABLE
except ImportError:
    FastCameraStreamer = None
    FastMotionDetector = None
    PICAMERA2_AVAILABLE = False

__all__ = [
    'camera_coordinator',
    'LibcameraStreamer', 'is_libcamera_available',
    'RpicamStreamer', 'is_rpicam_available',
    'FastCameraStreamer', 'FastMotionDetector', 'PICAMERA2_AVAILABLE'
]
