"""
Pi Model Detection and Camera Adaptation
Detects Raspberry Pi model and adapts camera initialization accordingly
"""
import subprocess
import os
import re
from loguru import logger

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
