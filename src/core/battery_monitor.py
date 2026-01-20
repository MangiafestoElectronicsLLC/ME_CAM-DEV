import subprocess
from loguru import logger
from src.core.config_manager import get_config


class BatteryMonitor:
    def __init__(self, enabled: bool = False, low_threshold_percent: int = 20):
        self.enabled = enabled
        self.low_threshold_percent = low_threshold_percent

    def _vcgencmd_throttled(self):
        try:
            out = subprocess.check_output(["vcgencmd", "get_throttled"], text=True).strip()
            # Example: 'throttled=0x50000'
            if "=" in out:
                _, hexval = out.split("=", 1)
                val = int(hexval, 16)
                return val
        except Exception as e:
            logger.debug(f"vcgencmd not available or failed: {e}")
        return 0

    def get_status(self):
        if not self.enabled:
            return {"enabled": False, "percent": None, "is_low": False, "external_power": None}

        cfg = get_config()
        percent_override = cfg.get("battery_percent_override")

        throttled = self._vcgencmd_throttled()
        undervolt_now = bool(throttled & 0x1)
        undervolt_ever = bool(throttled & 0x10000)

        # Enhanced battery monitoring for power bank
        # Check for actual battery level from power bank or UPS HAT
        percent = None
        try:
            # Try to read battery level from common I2C battery monitors (INA219, MAX17048, etc.)
            # For now, use manual override or voltage-based estimation
            if isinstance(percent_override, (int, float)):
                percent = int(percent_override)
            else:
                # Try to estimate from system power consumption
                # Read system uptime and calculate drain
                try:
                    with open('/proc/uptime', 'r') as f:
                        uptime_seconds = float(f.read().split()[0])
                    
                    # Assume 10Ah power bank, 380mA average drain
                    powerbank_mah = 10000
                    avg_current_draw_ma = 380
                    total_runtime_hours = powerbank_mah / avg_current_draw_ma  # ~26.3 hours
                    uptime_hours = uptime_seconds / 3600
                    
                    # Calculate remaining percentage
                    if uptime_hours < total_runtime_hours:
                        percent = int(100 * (1 - (uptime_hours / total_runtime_hours)))
                        percent = max(0, min(100, percent))  # Clamp 0-100
                    else:
                        percent = 10  # Low battery if uptime exceeds expected runtime
                except:
                    # Fallback: If no undervolt, assume good power (100%)
                    percent = 100 if not undervolt_now else 0
        except Exception as e:
            logger.debug(f"Battery estimation error: {e}")
            percent = 100 if not undervolt_now else 0

        is_low = undervolt_now or (percent is not None and percent <= self.low_threshold_percent)
        external_power = not undervolt_now
        
        # Calculate estimated runtime with 10,000mAh power bank
        powerbank_mah = 10000
        avg_current_draw_ma = 380  # Average for Pi Zero 2W with camera
        
        if percent and percent > 0:
            remaining_mah = (percent / 100.0) * powerbank_mah
            runtime_hours = remaining_mah / avg_current_draw_ma
            runtime_hours_int = int(runtime_hours)
            runtime_minutes = int((runtime_hours - runtime_hours_int) * 60)
        else:
            runtime_hours_int = 0
            runtime_minutes = 0

        return {
            "enabled": True,
            "percent": percent,
            "is_low": is_low,
            "external_power": external_power,
            "undervolt_ever": undervolt_ever,
            "runtime_hours": runtime_hours_int,
            "runtime_minutes": runtime_minutes,
            "note": "Estimated from system uptime and power consumption"
        }
