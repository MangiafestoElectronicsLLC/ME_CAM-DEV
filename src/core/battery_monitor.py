import subprocess
import os
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

    def _read_capacity_percent(self):
        """Read battery percentage from common Linux power_supply paths."""
        candidates = [
            "/sys/class/power_supply/BAT0/capacity",
            "/sys/class/power_supply/BAT1/capacity",
            "/sys/class/power_supply/ups/capacity",
        ]
        for path in candidates:
            try:
                if os.path.exists(path):
                    with open(path, "r") as f:
                        value = int(float(f.read().strip()))
                    return max(0, min(100, value)), path
            except Exception:
                continue
        return None, None

    def get_status(self):
        if not self.enabled:
            return {"enabled": False, "percent": None, "is_low": False, "external_power": None}

        cfg = get_config()
        percent_override = cfg.get("battery_percent_override")

        throttled = self._vcgencmd_throttled()
        undervolt_now = bool(throttled & 0x1)
        undervolt_ever = bool(throttled & 0x10000)

        percent = None
        percent_source = "unknown"
        try:
            if isinstance(percent_override, (int, float)):
                percent = int(percent_override)
                percent_source = "override"
            else:
                sensed, source_path = self._read_capacity_percent()
                if sensed is not None:
                    percent = sensed
                    percent_source = f"sensor:{source_path}"
                else:
                    percent = 100 if not undervolt_now else 15
                    percent_source = "power_state_fallback"
        except Exception as e:
            logger.debug(f"Battery estimation error: {e}")
            percent = 100 if not undervolt_now else 15
            percent_source = "error_fallback"

        is_low = undervolt_now or (percent is not None and percent <= self.low_threshold_percent)
        external_power = not undervolt_now
        
        # Runtime estimate (only meaningful when capacity percentage is known).
        # Defaults reflect common USB power-bank conversion losses.
        try:
            powerbank_mah = float(cfg.get("powerbank_capacity_mah", 10000) or 10000)
        except Exception:
            powerbank_mah = 10000.0

        try:
            powerbank_cell_voltage = float(cfg.get("powerbank_cell_voltage", 3.7) or 3.7)
        except Exception:
            powerbank_cell_voltage = 3.7

        try:
            device_voltage = float(cfg.get("device_voltage", 5.0) or 5.0)
        except Exception:
            device_voltage = 5.0

        try:
            conversion_efficiency = float(cfg.get("power_conversion_efficiency", 0.85) or 0.85)
        except Exception:
            conversion_efficiency = 0.85
        conversion_efficiency = max(0.5, min(1.0, conversion_efficiency))

        try:
            avg_current_draw_ma = float(cfg.get("avg_current_draw_ma", 300) or 300)
        except Exception:
            avg_current_draw_ma = 300.0
        avg_current_draw_ma = max(50.0, avg_current_draw_ma)

        usable_mah_at_device_voltage = powerbank_mah * (powerbank_cell_voltage / device_voltage) * conversion_efficiency

        if percent is not None and percent > 0:
            remaining_mah = (percent / 100.0) * usable_mah_at_device_voltage
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
            "percent_source": percent_source,
            "note": "Battery level uses sensor/override when available; runtime is an estimate based on configured power-bank/current settings"
        }
