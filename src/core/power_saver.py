"""
Power-saving system for battery-powered cameras.

Provides dynamic power management based on battery level and power source.
Adapts camera settings, recording frequency, and feature availability.
"""

import time
from loguru import logger
from src.core.config_manager import get_config, save_config


class PowerSaver:
    """Dynamic power management system for battery devices."""
    
    # Battery thresholds for power modes
    BATTERY_CRITICAL = 10  # Below 10%: critical mode
    BATTERY_LOW = 25       # Below 25%: low mode
    BATTERY_MEDIUM = 50    # Below 50%: medium mode
    BATTERY_NORMAL = 100   # 50%+: normal mode
    
    # Power mode settings
    POWER_MODES = {
        'critical': {
            'stream_quality': 40,      # Lowest quality to save CPU
            'stream_fps': 15,          # Lowest FPS
            'motion_detect': False,    # Disable motion detection
            'motion_record': False,    # Don't record motion clips
            'audio_record': False,     # Disable audio recording
            'cloud_sync': False,       # Disable cloud uploads
            'wifi_transmit_power': 'low',  # Reduce WiFi power
            'description': 'Emergency mode - minimal streaming only'
        },
        'low': {
            'stream_quality': 50,      # Lower quality
            'stream_fps': 20,          # Lower FPS
            'motion_detect': True,     # Keep motion detection
            'motion_record': False,    # Minimal recording (motion preserver only)
            'audio_record': False,     # Disable audio
            'cloud_sync': False,       # Disable cloud sync
            'wifi_transmit_power': 'low',
            'description': 'Battery saver mode'
        },
        'medium': {
            'stream_quality': 70,      # Medium quality
            'stream_fps': 30,          # Medium FPS
            'motion_detect': True,
            'motion_record': True,     # Record motion clips
            'audio_record': False,     # Audio optional
            'cloud_sync': False,       # No realtime cloud sync
            'wifi_transmit_power': 'medium',
            'description': 'Balanced mode'
        },
        'normal': {
            'stream_quality': 85,      # Full quality
            'stream_fps': 40,          # Full FPS
            'motion_detect': True,
            'motion_record': True,     # Full motion recording
            'audio_record': True,      # Enable audio
            'cloud_sync': True,        # Cloud sync enabled
            'wifi_transmit_power': 'high',
            'description': 'Normal operation (plugged in or good battery)'
        }
    }
    
    def __init__(self):
        self.last_mode_check = 0
        self.mode_check_interval = 30  # Check every 30 seconds
        self.current_mode = 'normal'
        self.applied_settings = {}
    
    def get_power_mode_for_battery(self, battery_percent: float, external_power: bool) -> str:
        """
        Determine power mode based on battery percentage.
        
        Args:
            battery_percent: Battery charge level (0-100)
            external_power: Whether device is on external power
        
        Returns:
            Power mode name: 'critical', 'low', 'medium', or 'normal'
        """
        if external_power:
            return 'normal'
        
        if battery_percent < self.BATTERY_CRITICAL:
            return 'critical'
        elif battery_percent < self.BATTERY_LOW:
            return 'low'
        elif battery_percent < self.BATTERY_MEDIUM:
            return 'medium'
        else:
            return 'normal'
    
    def should_check_power_mode(self) -> bool:
        """Check if enough time has passed to re-check power mode."""
        now = time.time()
        if now - self.last_mode_check >= self.mode_check_interval:
            self.last_mode_check = now
            return True
        return False
    
    def apply_power_mode(self, mode: str, cfg: dict) -> dict:
        """
        Apply power mode settings to configuration.
        
        Args:
            mode: Power mode name
            cfg: Current device configuration
        
        Returns:
            Modified configuration with power-saving settings applied
        """
        if mode not in self.POWER_MODES:
            logger.warning(f"[POWER] Unknown power mode: {mode}")
            return cfg
        
        if mode == self.current_mode:
            # No change needed
            return cfg
        
        mode_settings = self.POWER_MODES[mode]
        self.current_mode = mode
        
        logger.info(f"[POWER] Applying power mode: {mode} - {mode_settings['description']}")
        
        # Apply camera settings
        if 'camera' in cfg:
            cfg['camera']['stream_quality'] = mode_settings['stream_quality']
            cfg['camera']['stream_fps'] = mode_settings['stream_fps']
        
        # Apply motion settings
        cfg['motion_detection'] = mode_settings['motion_detect']
        cfg['motion_record_enabled'] = mode_settings['motion_record']
        
        # Apply audio settings
        cfg['audio_record_on_motion'] = mode_settings['audio_record']
        
        # Apply cloud settings
        cfg['cloud_push_enabled'] = mode_settings['cloud_sync']
        cfg['enable_realtime_cloud_push'] = mode_settings['cloud_sync']
        
        self.applied_settings = {
            'mode': mode,
            'quality': mode_settings['stream_quality'],
            'fps': mode_settings['stream_fps'],
            'timestamp': time.time()
        }
        
        return cfg
    
    def get_power_status(self) -> dict:
        """Get current power mode and settings."""
        return {
            'current_mode': self.current_mode,
            'mode_description': self.POWER_MODES[self.current_mode]['description'],
            'applied_settings': self.applied_settings,
            'available_modes': list(self.POWER_MODES.keys())
        }
    
    @staticmethod
    def estimate_runtime_on_mode(battery_percent: float, mode: str) -> tuple:
        """
        Estimate runtime remaining in specific power mode.
        
        Estimates power consumption for each mode:
        - critical: ~200 mA (minimal CPU, WiFi minimal)
        - low: ~350 mA (low CPU, low WiFi)
        - medium: ~500 mA (moderate CPU, normal WiFi)
        - normal: ~700 mA (full CPU, full WiFi)
        
        Args:
            battery_percent: Current battery percentage
            mode: Power mode name
        
        Returns:
            Tuple of (hours, minutes) estimated runtime
        """
        mode_current_ma = {
            'critical': 200,
            'low': 350,
            'medium': 500,
            'normal': 700
        }
        
        if mode not in mode_current_ma:
            mode = 'normal'
        
        # Assume 10,000 mAh powerbank with standard conversion
        powerbank_mah = 10000
        conversion_efficiency = 0.85
        usable_mah = powerbank_mah * (3.7 / 5.0) * conversion_efficiency  # ~6,290 mAh
        
        remaining_mah = (battery_percent / 100.0) * usable_mah
        current_ma = mode_current_ma[mode]
        
        runtime_hours = remaining_mah / current_ma
        hours = int(runtime_hours)
        minutes = int((runtime_hours - hours) * 60)
        
        return hours, minutes


def should_enable_power_saving(cfg: dict, battery_percent: float, external_power: bool) -> bool:
    """
    Check if power saving should be enabled based on config and battery status.
    
    Returns: True if power saving should be applied
    """
    if external_power:
        return False  # Always full power when plugged in
    
    power_saving_enabled = cfg.get('power_saving_enabled', True)
    return power_saving_enabled and battery_percent < 100
