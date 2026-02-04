"""
Pi Model Detection and Camera Adaptation - ENHANCED Feb 2026
Detects Raspberry Pi model, camera type, and auto-configures optimal settings

Improvements:
- Pi 5 detection and optimization
- Camera type detection (IMX519, OV5647, etc.)
- Rotation/flip auto-detection
- Hardware capability mapping
"""
import subprocess
import os
import re
from loguru import logger
from typing import Dict, Optional

def get_pi_model():
    """
    Detect Raspberry Pi model from /proc/cpuinfo
    Returns: dict with model info
    """
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        
        # Extract model from cpuinfo
        model_match = re.search(r'Model\s+:\s+(.+)', cpuinfo)
        if model_match:
            model_str = model_match.group(1)
            
            # Detect specific models
            if 'Pi Zero 2' in model_str:
                return {
                    'name': 'Raspberry Pi Zero 2W',
                    'ram_mb': 512,
                    'can_stream': True,  # LITE MODE supports camera streaming
                    'max_cameras': 1,
                    'recommended_mode': 'lite'  # Use LITE mode for Pi Zero 2W
                }
            elif 'Pi 3 Model B Plus' in model_str or 'Pi 3B+' in model_str:
                return {
                    'name': 'Raspberry Pi 3B+',
                    'ram_mb': 1024,
                    'can_stream': True,
                    'max_cameras': 2,
                    'recommended_mode': 'fast'
                }
            elif 'Pi 3' in model_str:
                return {
                    'name': 'Raspberry Pi 3B',
                    'ram_mb': 1024,
                    'can_stream': True,
                    'max_cameras': 2,
                    'recommended_mode': 'fast'
                }
            elif 'Pi 4' in model_str:
                # Check RAM from /proc/meminfo
                ram_mb = get_total_ram()
                return {
                    'name': f'Raspberry Pi 4B ({ram_mb}MB)',
                    'ram_mb': ram_mb,
                    'can_stream': True,
                    'max_cameras': 4 if ram_mb >= 4096 else 2,
                    'recommended_mode': 'fast'
                }
            elif 'Pi 5' in model_str:
                ram_mb = get_total_ram()
                return {
                    'name': f'Raspberry Pi 5 ({ram_mb}MB)',
                    'ram_mb': ram_mb,
                    'can_stream': True,
                    'max_cameras': 8 if ram_mb >= 8192 else 4,
                    'recommended_mode': 'fast'
                }
        
        # Fallback - check RAM and guess
        ram_mb = get_total_ram()
        if ram_mb < 1024:
            return {
                'name': 'Unknown Pi (Low RAM)',
                'ram_mb': ram_mb,
                'can_stream': False,
                'max_cameras': 1,
                'recommended_mode': 'test'
            }
        else:
            return {
                'name': 'Unknown Pi',
                'ram_mb': ram_mb,
                'can_stream': True,
                'max_cameras': 2,
                'recommended_mode': 'fast'
            }
    
    except Exception as e:
        logger.error(f"[PI_DETECT] Error detecting Pi model: {e}")
        return {
            'name': 'Unknown',
            'ram_mb': 1024,
            'can_stream': True,
            'max_cameras': 1,
            'recommended_mode': 'test'
        }

def get_total_ram():
    """Get total system RAM in MB"""
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    # Extract number and convert to MB
                    kb = int(line.split()[1])
                    return kb // 1024
        return 1024  # Default fallback
    except:
        return 1024

def get_camera_config(pi_model):
    """
    Get recommended camera configuration based on Pi model
    """
    if not pi_model['can_stream']:
        return {
            'mode': 'test',
            'use_fast_streamer': False,
            'resolution': '640x480',
            'fps': 1,
            'enable_motion': False,
            'reason': 'Insufficient RAM for camera streaming'
        }
    # Pi Zero 2W and other 512MB devices → LITE mode
    elif pi_model['ram_mb'] < 1024:
        return {
            'mode': 'lite',
            'use_fast_streamer': False,
            'resolution': '640x480',
            'fps': 20,
            'enable_motion': False,
            'reason': 'LITE MODE for 512MB RAM'
        }
    elif pi_model['ram_mb'] >= 4096:
        # Pi 4/5 with 4GB+ RAM
        return {
            'mode': 'fast',
            'use_fast_streamer': True,
            'resolution': '1280x720',
            'fps': 30,
            'enable_motion': True,
            'reason': 'High-performance configuration'
        }
    elif pi_model['ram_mb'] >= 2048:
        # Pi 4 with 2GB RAM
        return {
            'mode': 'fast',
            'use_fast_streamer': True,
            'resolution': '1280x720',
            'fps': 20,
            'enable_motion': True,
            'reason': 'Balanced configuration'
        }
    else:
        # Pi 3B/3B+ with 1GB RAM
        return {
            'mode': 'fast',
            'use_fast_streamer': True,
            'resolution': '640x480',
            'fps': 15,
            'enable_motion': True,
            'reason': 'Optimized for 1GB RAM'
        }

# Export singleton instance
_pi_model = None
_camera_config = None

def init_pi_detection():
    """Initialize Pi detection (call once on startup)"""
    global _pi_model, _camera_config
    _pi_model = get_pi_model()
    _camera_config = get_camera_config(_pi_model)
    
    logger.info(f"[PI_DETECT] Detected: {_pi_model['name']}")
    logger.info(f"[PI_DETECT] RAM: {_pi_model['ram_mb']}MB")
    logger.info(f"[PI_DETECT] Camera mode: {_camera_config['mode']} ({_camera_config['reason']})")
    logger.info(f"[PI_DETECT] Max cameras: {_pi_model['max_cameras']}")
    
    return _pi_model, _camera_config

def get_pi_info():
    """Get current Pi model info"""
    global _pi_model, _camera_config
    if _pi_model is None:
        init_pi_detection()
    return _pi_model, _camera_config

def detect_camera_type() -> Optional[Dict]:
    """
    Detect connected camera module and its type
    
    Returns:
        Dict with camera info or None if no camera detected
    
    Detects:
    - IMX519 (Arducam 16MP)
    - OV5647 (Pi Camera v1)
    - IMX219 (Pi Camera v2)
    - IMX477 (Pi Camera v2 HQ)
    - And others via libcamera
    """
    try:
        import subprocess
        
        # Try libcamera-hello to detect camera
        result = subprocess.run(
            ['libcamera-hello', '--list-cameras'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        output = result.stdout + result.stderr
        
        if 'imx519' in output.lower():
            logger.success("[CAMERA_DETECT] ✓ Found IMX519 (Arducam 16MP)")
            return {
                'type': 'IMX519',
                'name': 'Arducam IMX519',
                'megapixels': 16,
                'max_fps': 20,
                'modes': ['photo', 'video'],
                'needs_overlay': 'imx519'
            }
        elif 'ov5647' in output.lower():
            logger.success("[CAMERA_DETECT] ✓ Found OV5647 (Pi Camera v1)")
            return {
                'type': 'OV5647',
                'name': 'Raspberry Pi Camera v1',
                'megapixels': 5,
                'max_fps': 90,
                'modes': ['photo', 'video'],
                'legacy': True
            }
        elif 'imx219' in output.lower():
            logger.success("[CAMERA_DETECT] ✓ Found IMX219 (Pi Camera v2)")
            return {
                'type': 'IMX219',
                'name': 'Raspberry Pi Camera v2',
                'megapixels': 8,
                'max_fps': 60,
                'modes': ['photo', 'video']
            }
        elif 'imx477' in output.lower():
            logger.success("[CAMERA_DETECT] ✓ Found IMX477 (Pi Camera v2 HQ)")
            return {
                'type': 'IMX477',
                'name': 'Raspberry Pi Camera v2 HQ',
                'megapixels': 12.3,
                'max_fps': 50,
                'modes': ['photo', 'video']
            }
        elif 'imx708' in output.lower():
            logger.success("[CAMERA_DETECT] ✓ Found IMX708 (Pi Camera 3)")
            return {
                'type': 'IMX708',
                'name': 'Raspberry Pi Camera 3',
                'megapixels': 12.3,
                'max_fps': 120,
                'modes': ['photo', 'video', 'ir']
            }
        elif len(output) > 0 and 'Camera' in output:
            logger.info(f"[CAMERA_DETECT] Found camera: {output[:100]}")
            return {
                'type': 'Unknown',
                'name': 'Unknown camera',
                'megapixels': 0,
                'max_fps': 15,
                'modes': ['video']
            }
        else:
            logger.warning("[CAMERA_DETECT] No camera detected via libcamera")
            return None
            
    except subprocess.TimeoutExpired:
        logger.warning("[CAMERA_DETECT] libcamera-hello timeout")
        return None
    except FileNotFoundError:
        logger.warning("[CAMERA_DETECT] libcamera not installed")
        return None
    except Exception as e:
        logger.warning(f"[CAMERA_DETECT] Camera detection failed: {e}")
        return None


def detect_camera_rotation() -> Optional[str]:
    """
    Auto-detect if camera needs rotation/flip
    
    Checks:
    1. IMX519 on Pi Zero 2W (usually upside down)
    2. Check device orientation from /boot/config.txt
    
    Returns:
        'normal', 'rotate_90', 'rotate_180', 'rotate_270', or None
    """
    try:
        camera_info = detect_camera_type()
        if not camera_info:
            return None
        
        camera_type = camera_info.get('type', '')
        
        # IMX519 on Pi Zero 2W is typically upside down (180 rotation)
        if camera_type == 'IMX519':
            pi_model_info = get_pi_model()
            if 'Zero' in pi_model_info.get('name', ''):
                logger.info("[CAMERA_DETECT] IMX519 on Pi Zero detected - applying 180° rotation")
                return 'rotate_180'
        
        # Check /boot/firmware/config.txt for overlay rotation
        config_paths = [
            '/boot/firmware/config.txt',
            '/boot/config.txt'
        ]
        
        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        content = f.read()
                        
                    if 'dtparam=rotate=1' in content:
                        return 'rotate_90'
                    elif 'dtparam=rotate=2' in content:
                        return 'rotate_180'
                    elif 'dtparam=rotate=3' in content:
                        return 'rotate_270'
                    elif 'dtparam=flip_horizontal=1' in content:
                        return 'flip_horizontal'
                    elif 'dtparam=flip_vertical=1' in content:
                        return 'flip_vertical'
                except:
                    pass
        
        return None
        
    except Exception as e:
        logger.warning(f"[CAMERA_DETECT] Rotation detection failed: {e}")
        return None


def get_device_uuid() -> str:
    """
    Get unique device UUID based on CPU serial
    Used for cloud device identification
    """
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        
        # Extract serial
        serial_match = re.search(r'Serial\s+:\s+([0-9a-f]+)', cpuinfo)
        if serial_match:
            serial = serial_match.group(1)
            # Create UUID-like identifier
            return f"mecam-{serial[-8:]}"
        
        # Fallback to hostname
        import socket
        hostname = socket.gethostname()
        return f"mecam-{hostname}"
        
    except Exception as e:
        logger.warning(f"[DEVICE_UUID] Failed to get UUID: {e}")
        return "mecam-unknown"


def get_full_system_info() -> Dict:
    """Get comprehensive system information for setup"""
    try:
        pi_model = get_pi_model()
        camera_type = detect_camera_type()
        camera_rotation = detect_camera_rotation()
        device_uuid = get_device_uuid()
        
        return {
            'pi_model': pi_model,
            'camera_type': camera_type,
            'camera_rotation': camera_rotation,
            'device_uuid': device_uuid,
            'detected_at': datetime.now().isoformat() if 'datetime' in dir() else None
        }
    except Exception as e:
        logger.error(f"[SYSTEM_INFO] Failed to get system info: {e}")
        return {}