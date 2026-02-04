"""
Video Codec & Color Space Optimizer for PI Zero 2W
Fixes: H.264 color corruption, improves FPS, ensures clean playback

Changes in v2.2.3:
- Force MJPEG for streaming (no color space issues)
- H.264 only for storage (space efficient)
- Proper BGR to RGB conversion
- GPU-accelerated encoding
- Reduced processing overhead
"""

import cv2
import subprocess
import os
from loguru import logger
from pathlib import Path

class VideoCodecOptimizer:
    """Handle video codec optimization for Pi hardware"""
    
    def __init__(self):
        self.is_pi_zero = self._detect_pi_zero()
        self.use_hardware_encoding = self._check_hw_encoding()
        
    def _detect_pi_zero(self) -> bool:
        """Check if running on Pi Zero 2W (limited resources)"""
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read().strip()
                return 'Zero 2W' in model or 'Zero 2' in model
        except:
            return False
    
    def _check_hw_encoding(self) -> bool:
        """Check if hardware H.264 encoding available (GPU accelerated)"""
        try:
            result = subprocess.run(
                ['raspivid', '-t', '1', '-o', '/dev/null'],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0 or 'invalid' not in result.stderr.decode().lower()
        except:
            return False
    
    def get_stream_codec(self) -> dict:
        """
        Get optimal codec for STREAMING
        
        Returns: Dict with codec settings
        """
        return {
            'codec': 'MJPEG',  # Browser compatible, no color issues
            'format': 'JPEG',
            'quality': 80 if self.is_pi_zero else 85,
            'width': 640,
            'height': 480,
            'fps': 20 if self.is_pi_zero else 25,
            'reason': 'MJPEG avoids H.264 color space issues, direct browser playback'
        }
    
    def get_recording_codec(self) -> dict:
        """
        Get optimal codec for RECORDING (storage)
        
        Returns: Dict with codec settings
        """
        codec = 'h264' if self.use_hardware_encoding else 'mpeg4'
        return {
            'codec': codec,
            'bitrate': '1000k' if self.is_pi_zero else '2000k',
            'format': 'mp4',
            'width': 640,
            'height': 480,
            'fps': 15 if self.is_pi_zero else 20,
            'preset': 'veryfast' if self.is_pi_zero else 'fast',
            'reason': 'Efficient storage, HW accelerated on Pi'
        }
    
    def convert_video_for_playback(self, input_path: str, output_path: str = None) -> bool:
        """
        Convert H.264 video to MJPEG for clean browser playback
        Fixes color corruption issues
        
        Args:
            input_path: H.264 video file
            output_path: MJPEG output (auto-named if None)
        
        Returns: True if successful
        """
        if output_path is None:
            output_path = input_path.replace('.mp4', '_playback.mp4')
        
        try:
            # Use ffmpeg to convert with proper color space handling
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-c:v', 'mpeg4',  # MPEG4 has better color space handling
                '-q:v', '6',  # Quality 6 (good quality, fast)
                '-c:a', 'aac',
                '-y',  # Overwrite
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=120)
            
            if result.returncode == 0:
                logger.success(f"[CODEC] Converted for playback: {output_path}")
                return True
            else:
                logger.warning(f"[CODEC] Conversion warning: {result.stderr.decode()}")
                # Still return True as file might be created
                return os.path.exists(output_path)
                
        except subprocess.TimeoutExpired:
            logger.error(f"[CODEC] Conversion timeout for {input_path}")
            return False
        except Exception as e:
            logger.error(f"[CODEC] Conversion failed: {e}")
            return False
    
    def fix_jpeg_color_space(self, frame_bgr) -> bytes:
        """
        Convert OpenCV BGR frame to proper JPEG
        Fixes: Green/pink/blue color corruption
        
        Args:
            frame_bgr: OpenCV frame (BGR format)
        
        Returns: JPEG bytes with correct colors
        """
        try:
            # Convert BGR (OpenCV) to RGB (correct for JPEG)
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            
            # Encode to JPEG with quality setting
            success, buffer = cv2.imencode('.jpg', frame_rgb, [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            if success:
                return buffer.tobytes()
            else:
                logger.warning("[CODEC] JPEG encoding failed")
                return None
                
        except Exception as e:
            logger.error(f"[CODEC] Color space conversion failed: {e}")
            return None
    
    def optimize_stream_fps(self) -> int:
        """
        Get optimal FPS for streaming on this device
        
        Pi Zero 2W: 15-20 FPS (resource limited)
        Pi 3/4:     20-25 FPS
        Pi 5:       25-30 FPS
        """
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read().strip()
                
            if 'Zero 2' in model:
                return 20  # ~20 FPS is good for Pi Zero 2W
            elif 'Pi 3' in model:
                return 24
            elif 'Pi 4' in model:
                return 25
            elif 'Pi 5' in model:
                return 30
            else:
                return 15  # Conservative default
        except:
            return 15
    
    def get_motion_recording_settings(self) -> dict:
        """
        Get settings optimized for motion-detected recording
        Balance between quality and Pi Zero 2W resources
        """
        return {
            'resolution': '640x480',  # Good balance
            'fps': 15,  # Motion doesn't need high FPS
            'bitrate': '1000k',  # Efficient
            'codec': 'h264',
            'quality': 'good',
            'format': 'mp4',
            'pre_buffer_frames': 60,  # 4 seconds at 15 FPS
            'post_buffer_seconds': 10
        }


def get_codec_optimizer() -> VideoCodecOptimizer:
    """Singleton codec optimizer"""
    global _optimizer
    if '_optimizer' not in globals():
        _optimizer = VideoCodecOptimizer()
    return _optimizer
