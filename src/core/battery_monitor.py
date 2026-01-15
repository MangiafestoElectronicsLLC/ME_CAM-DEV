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

        # Pi Zero 2W with USB power: no battery HAT available
        # Show 100% if external power is good, 0% if undervolt detected
        percent = None
        if isinstance(percent_override, (int, float)):
            percent = int(percent_override)
        else:
            # Heuristic: If no undervolt, assume good USB power (100%)
            # If undervolt, warn user (0%)
            if undervolt_now:
                percent = 0  # Undervolt = insufficient power
            else:
                percent = 100  # Good external power

        is_low = undervolt_now or (percent is not None and percent <= self.low_threshold_percent)
        external_power = not undervolt_now  # heuristic: if no undervolt, likely adequate external power

        return {
            "enabled": True,
            "percent": percent,
            "is_low": is_low,
            "external_power": external_power,
            "undervolt_ever": undervolt_ever,
            "note": "USB power detection - 100% if healthy, 0% if undervolt"
        }
