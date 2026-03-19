import subprocess
import os
from loguru import logger
from src.core.config_manager import get_config


class BatteryMonitor:
    def __init__(self, enabled: bool = False, low_threshold_percent: int = 20):
        self.enabled = enabled
        self.low_threshold_percent = low_threshold_percent
        self.power_source_cache = {"source": "unknown", "time": 0}

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

    def _detect_power_source(self):
        """
        Detect if device is powered by wall charger, USB adapter, powerbank, or pure battery.
        Returns: "wall_adapter", "usb_adapter", "powerbank", "battery", or "unknown"
        """
        try:
            # Check for AC adapter or USB power supplies
            power_supply_path = "/sys/class/power_supply"
            if not os.path.exists(power_supply_path):
                return "unknown"
            
            # Look for AC or USB supplies with online=1
            for supply_name in os.listdir(power_supply_path):
                supply_path = os.path.join(power_supply_path, supply_name)
                try:
                    # Check if this is an AC adapter (wall power)
                    if "ac" in supply_name.lower():
                        online_path = os.path.join(supply_path, "online")
                        if os.path.exists(online_path):
                            with open(online_path, "r") as f:
                                if f.read().strip() == "1":
                                    return "wall_adapter"
                    
                    # Check if this is a USB supply
                    if "usb" in supply_name.lower():
                        online_path = os.path.join(supply_path, "online")
                        if os.path.exists(online_path):
                            with open(online_path, "r") as f:
                                if f.read().strip() == "1":
                                    # Check current to differentiate wall adapter vs powerbank
                                    current_path = os.path.join(supply_path, "current_max")
                                    if os.path.exists(current_path):
                                        try:
                                            with open(current_path, "r") as f:
                                                current_ma = int(f.read().strip())
                                                # Wall adapters typically provide >1A (1000mA)
                                                if current_ma > 1000000:  # in microamps
                                                    return "wall_adapter"
                                        except Exception:
                                            pass
                                    # Less certain, likely powerbank
                                    return "usb_adapter"
                except Exception:
                    continue
            
            return "battery"
        except Exception as e:
            logger.debug(f"Power source detection error: {e}")
            return "unknown"

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
                percent = max(0, min(100, int(percent_override)))
                percent_source = "override"
            else:
                sensed, source_path = self._read_capacity_percent()
                if sensed is not None:
                    percent = sensed
                    percent_source = f"sensor:{source_path}"
                else:
                    # No battery telemetry device found; keep percent unknown
                    # instead of reporting synthetic values.
                    percent = None
                    percent_source = "unavailable"
        except Exception as e:
            logger.debug(f"Battery estimation error: {e}")
            percent = None
            percent_source = "error"

        is_low = undervolt_now or (percent is not None and percent <= self.low_threshold_percent)
        
        # Detect actual power source instead of relying on undervolt detection
        power_source = self._detect_power_source()
        external_power = power_source in ["wall_adapter", "usb_adapter"]
        
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

        # IMPORTANT: avg_current_draw_ma should reflect ACTIVE usage (camera + WiFi)
        # 300 mA is unrealistically low for streaming devices. Use 600 mA as realisticdefault.
        # Users should adjust based on their usage patterns.
        try:
            avg_current_draw_ma = float(cfg.get("avg_current_draw_ma", 600) or 600)
        except Exception:
            avg_current_draw_ma = 600.0
        avg_current_draw_ma = max(50.0, avg_current_draw_ma)

        usable_mah_at_device_voltage = powerbank_mah * (powerbank_cell_voltage / device_voltage) * conversion_efficiency

        if percent is not None and percent > 0:
            remaining_mah = (percent / 100.0) * usable_mah_at_device_voltage
            runtime_hours = remaining_mah / avg_current_draw_ma
            runtime_hours_int = int(runtime_hours)
            runtime_minutes = int((runtime_hours - runtime_hours_int) * 60)
        else:
            runtime_hours_int = None
            runtime_minutes = None

        return {
            "enabled": True,
            "percent": percent,
            "is_low": is_low,
            "external_power": external_power,
            "power_source": power_source,
            "undervolt_ever": undervolt_ever,
            "runtime_hours": runtime_hours_int,
            "runtime_minutes": runtime_minutes,
            "percent_source": percent_source,
            "battery_present": percent is not None,
            "note": "Battery level uses sensor/override when available; runtime is estimate based on configured power-bank/current settings. Active camera/WiFi draw typically 600-900 mA."
        }
