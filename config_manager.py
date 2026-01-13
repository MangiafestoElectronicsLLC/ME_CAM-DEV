import json
import os
from threading import RLock

CONFIG_PATH = "config/config.json"
DEFAULT_CONFIG_PATH = "config/config_default.json"

_lock = RLock()
_config_cache = None


def _load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _merge_configs(user_config, default_config):
    """Merge user config with defaults, preserving user values but adding missing keys"""
    result = default_config.copy()
    for key, value in user_config.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = _merge_configs(value, result[key])
        else:
            result[key] = value
    return result


def get_config():
    global _config_cache
    with _lock:
        if _config_cache is None:
            os.makedirs("config", exist_ok=True)
            default = _load_json(DEFAULT_CONFIG_PATH)
            
            if not os.path.exists(CONFIG_PATH):
                _config_cache = default
                with open(CONFIG_PATH, "w") as f:
                    json.dump(default, f, indent=2)
            else:
                user_config = _load_json(CONFIG_PATH)
                # Merge user config with defaults (adds missing keys from defaults)
                _config_cache = _merge_configs(user_config, default)
                
        return _config_cache


def save_config(new_config: dict):
    global _config_cache
    with _lock:
        os.makedirs("config", exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(new_config, f, indent=2)
        _config_cache = new_config


def update_config(updates: dict):
    cfg = get_config()
    cfg.update(updates)
    save_config(cfg)


def is_first_run():
    cfg = get_config()
    return not cfg.get("first_run_completed", False)


def mark_first_run_complete():
    cfg = get_config()
    cfg["first_run_completed"] = True
    save_config(cfg)
