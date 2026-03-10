"""
Lightweight Flask App for Pi Zero 2W - COMPLETE VERSION
==========================================================
- Motion detection with video recording
- Emergency alerts
- Configuration page
- Motion event viewer
- Storage cleanup
- Battery monitoring
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response, send_file, after_this_request, abort
from flask_cors import CORS
from loguru import logger
import os
import sys
import subprocess
from datetime import datetime, timedelta
import time
import threading
import json
import shutil
import asyncio
import tempfile
import base64
from functools import wraps
import secrets
import ipaddress
from urllib.parse import urlparse

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from src.core import (
    get_config, save_config, is_first_run, mark_first_run_complete,
    authenticate, BatteryMonitor, log_motion_event, get_recent_events,
    get_event_statistics, ensure_enrollment_key, verify_enrollment_key,
    rotate_enrollment_key
)
from src.utils.pi_detect import detect_camera_rotation
from src.core.secure_encryption import get_encryption
try:
    from src.cloud.encrypted_cloud_storage import get_cloud_storage
    CLOUD_AVAILABLE = True
except Exception as e:
    CLOUD_AVAILABLE = False
    logger.warning(f"[CLOUD] Encrypted cloud storage not available: {e}")

# V3 modules are disabled by default on Pi Zero because some optional native
# dependencies can crash the interpreter during import on constrained devices.
WEBRTC_AVAILABLE = False
AI_DETECTION_AVAILABLE = False
REMOTE_ACCESS_AVAILABLE = False
WebRTCStreamer = None
SmartMotionDetector = None
DetectionTracker = None
TailscaleHelper = None
CloudflareHelper = None

if os.environ.get("MECAM_ENABLE_V3_MODULES", "0") == "1":
    try:
        from src.streaming.webrtc_peer import WebRTCStreamer
        WEBRTC_AVAILABLE = True
        logger.info("[V3] WebRTC module loaded successfully")
    except Exception as e:
        WEBRTC_AVAILABLE = False
        logger.warning(f"[V3] WebRTC not available: {e}")

    try:
        from src.detection.tflite_detector import SmartMotionDetector, DetectionTracker
        AI_DETECTION_AVAILABLE = True
        logger.info("[V3] AI detection module loaded successfully")
    except Exception as e:
        AI_DETECTION_AVAILABLE = False
        logger.warning(f"[V3] AI detection not available: {e}")

    try:
        from src.networking.remote_access import TailscaleHelper, CloudflareHelper
        REMOTE_ACCESS_AVAILABLE = True
        logger.info("[V3] Remote access helpers loaded successfully")
    except Exception as e:
        REMOTE_ACCESS_AVAILABLE = False
        logger.warning(f"[V3] Remote access not available: {e}")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Offline queues (lightweight JSON logs; safe for Pi Zero 2W)
OFFLINE_QUEUE_FILE = os.path.join(BASE_DIR, "logs", "offline_queue.json")
NOTIFY_QUEUE_FILE = os.path.join(BASE_DIR, "logs", "notification_queue.json")
SHARE_LINKS_FILE = os.path.join(BASE_DIR, "logs", "share_links.json")


def _ensure_log_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _load_queue(path: str) -> list:
    _ensure_log_dir(path)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"[QUEUE] Failed to load {path}: {e}")
        return []


def _save_queue(path: str, items: list) -> None:
    _ensure_log_dir(path)
    try:
        with open(path, "w") as f:
            json.dump(items, f, indent=2)
    except Exception as e:
        logger.error(f"[QUEUE] Failed to save {path}: {e}")


def _load_share_links() -> dict:
    _ensure_log_dir(SHARE_LINKS_FILE)
    if not os.path.exists(SHARE_LINKS_FILE):
        return {}
    try:
        with open(SHARE_LINKS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"[SHARE] Failed to load links: {e}")
        return {}


def _save_share_links(links: dict) -> None:
    _ensure_log_dir(SHARE_LINKS_FILE)
    try:
        with open(SHARE_LINKS_FILE, "w") as f:
            json.dump(links, f, indent=2)
    except Exception as e:
        logger.error(f"[SHARE] Failed to save links: {e}")


def _detect_arecord_device() -> str | None:
    preferred = os.environ.get("MECAM_AUDIO_DEVICE", "").strip()
    if preferred:
        return preferred

    if not shutil.which("arecord"):
        return None

    try:
        result = subprocess.run(
            ["arecord", "-l"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        cards = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line.startswith("card "):
                continue
            try:
                left, _ = line.split(":", 1)
                card_part, device_part = left.split(",", 1)
                card_num = card_part.replace("card", "").strip().split()[0]
                device_num = device_part.replace("device", "").strip().split()[0]
                cards.append((card_num, device_num, line.lower()))
            except Exception:
                continue

        for card_num, device_num, description in cards:
            if any(token in description for token in ["usb", "mic", "microphone", "audio"]):
                return f"plughw:{card_num},{device_num}"
        if cards:
            card_num, device_num, _ = cards[0]
            return f"plughw:{card_num},{device_num}"
    except Exception as e:
        logger.warning(f"[AUDIO] Failed to inspect capture devices: {e}")

    return None


def _build_arecord_command(audio_path: str, duration_sec: int) -> list[str]:
    audio_cmd = [
        "arecord",
        "-q",
        "-f", "S16_LE",
        "-r", "16000",
        "-c", "1",
        "-d", str(duration_sec),
        "-t", "wav",
    ]
    device_name = _detect_arecord_device()
    if device_name:
        audio_cmd.extend(["-D", device_name])
    audio_cmd.append(audio_path)
    return audio_cmd


def _get_security_cfg(cfg: dict) -> dict:
    return cfg.get("security", {}) or {}


def _ensure_security_cfg(cfg: dict) -> dict:
    security = cfg.get("security") or {}
    changed = False
    if not security.get("device_token"):
        security["device_token"] = secrets.token_urlsafe(32)
        changed = True
    if not security.get("secret_key"):
        security["secret_key"] = secrets.token_urlsafe(32)
        changed = True
    if "tailscale_only" not in security:
        security["tailscale_only"] = False
        changed = True
    if "share_links_enabled" not in security:
        security["share_links_enabled"] = True
        changed = True
    if "share_link_expiry_hours" not in security:
        security["share_link_expiry_hours"] = 72
        changed = True
    if "session_timeout_minutes" not in security:
        security["session_timeout_minutes"] = 720
        changed = True
    if "allow_localhost" not in security:
        security["allow_localhost"] = True
        changed = True
    if "allow_setup_without_vpn" not in security:
        security["allow_setup_without_vpn"] = True
        changed = True
    if "bootstrap_required" not in security:
        security["bootstrap_required"] = False
        changed = True
    if "bootstrap_admin" not in security:
        security["bootstrap_admin"] = ""
        changed = True
    if not security.get("enrollment_key"):
        security["enrollment_key"] = ensure_enrollment_key(cfg=cfg, force_rotate=False, reason="init")
        changed = True
    cfg["security"] = security
    if changed:
        save_config(cfg)
    return security


def _get_storage_cfg(cfg: dict) -> dict:
    storage = cfg.get("storage", {}) or {}
    return {
        "recordings_dir": storage.get("recordings_dir", "recordings"),
        "encrypted_dir": cfg.get("storage_encrypted_dir", storage.get("encrypted_dir", "recordings_encrypted")),
        "encrypt": True,
        "retention_days": cfg.get("storage_cleanup_days", storage.get("retention_days", 7))
    }


def _get_sms_cfg(cfg: dict) -> dict:
    notifications = cfg.setdefault("notifications", {})
    sms_cfg = dict(notifications.get("sms", {}) or {})
    sms_cfg["enabled"] = bool(cfg.get("sms_enabled", sms_cfg.get("enabled", False)))
    sms_cfg["phone_to"] = cfg.get("sms_phone_to", sms_cfg.get("phone_to", ""))
    sms_cfg["rate_limit_minutes"] = int(cfg.get("sms_rate_limit", sms_cfg.get("rate_limit_minutes", 5)) or 5)
    sms_cfg["motion_threshold"] = 0.0

    provider = sms_cfg.get("provider")
    if cfg.get("sms_api_url"):
        provider = "generic_http"
    sms_cfg["provider"] = provider or "twilio"

    generic_http = dict(sms_cfg.get("generic_http", {}) or {})
    generic_http["url"] = cfg.get("sms_api_url", generic_http.get("url", ""))
    generic_http["auth_token"] = cfg.get("sms_api_key", generic_http.get("auth_token", ""))
    sms_cfg["generic_http"] = generic_http

    notifications["sms"] = sms_cfg
    cfg["notifications"] = notifications
    return sms_cfg


def _motion_profile_map() -> dict:
    return {
        "relaxed": {
            "threshold": 0.03,
            "min_area": 900,
            "ai_sensitivity": 0.55,
            "max_diff": 90,
            "motion_percent": 1.8,
            "edge_motion": 1500,
            "mean_diff": 18,
            "clip_min": 8,
            "clip_mid": 12,
            "clip_max": 14,
        },
        "balanced": {
            "threshold": 0.012,
            "min_area": 220,
            "ai_sensitivity": 0.6,
            "max_diff": 70,
            "motion_percent": 1.0,
            "edge_motion": 900,
            "mean_diff": 12,
            "clip_min": 10,
            "clip_mid": 14,
            "clip_max": 18,
        },
        "high": {
            "threshold": 0.01,
            "min_area": 250,
            "ai_sensitivity": 0.7,
            "max_diff": 40,
            "motion_percent": 0.45,
            "edge_motion": 500,
            "mean_diff": 7,
            "clip_min": 12,
            "clip_mid": 18,
            "clip_max": 24,
        },
    }


def _get_motion_profile_settings(cfg: dict) -> dict:
    sensitivity_mode = cfg.get("motion_sensitivity_mode")
    if sensitivity_mode not in {"relaxed", "balanced", "high"}:
        raw_threshold = float(cfg.get("motion_threshold", 0.02) or 0.02)
        if raw_threshold <= 0.012:
            sensitivity_mode = "high"
        elif raw_threshold <= 0.025:
            sensitivity_mode = "balanced"
        else:
            sensitivity_mode = "relaxed"

    trigger_mode = cfg.get("motion_trigger_mode")
    if trigger_mode not in {"all_motion", "people_vehicles", "people_only"}:
        trigger_mode = "people_only" if cfg.get("detection", {}).get("person_only", False) else "all_motion"

    clip_mode = cfg.get("motion_clip_mode", "auto")
    if clip_mode not in {"auto", "fixed"}:
        clip_mode = "auto"

    settings = dict(_motion_profile_map()[sensitivity_mode])
    settings["sensitivity_mode"] = sensitivity_mode
    settings["trigger_mode"] = trigger_mode
    settings["clip_mode"] = clip_mode
    return settings


def _apply_motion_preferences(cfg: dict, sensitivity_mode: str | None = None, trigger_mode: str | None = None, clip_mode: str | None = None) -> dict:
    if sensitivity_mode:
        cfg["motion_sensitivity_mode"] = sensitivity_mode
    if trigger_mode:
        cfg["motion_trigger_mode"] = trigger_mode
    if clip_mode:
        cfg["motion_clip_mode"] = clip_mode

    settings = _get_motion_profile_settings(cfg)
    cfg["motion_threshold"] = settings["threshold"]
    cfg["motion_record_enabled"] = bool(cfg.get("motion_record_enabled", True))
    cfg.setdefault("detection", {})
    cfg["detection"]["min_motion_area"] = settings["min_area"]
    cfg["detection"]["sensitivity"] = settings["ai_sensitivity"]
    cfg["detection"]["person_only"] = settings["trigger_mode"] == "people_only"
    cfg["motion_light_change_detection"] = settings["trigger_mode"] == "all_motion"
    cfg["storage_encrypt"] = True
    cfg.setdefault("storage", {})
    cfg["storage"]["encrypt"] = True
    cfg["storage"]["encrypted_dir"] = cfg.get("storage_encrypted_dir", "recordings_encrypted")
    return settings


def _auto_motion_clip_duration(cfg: dict, motion_ratio: float = 0.0, contour_count: int = 0, mean_diff: float = 0.0, motion_percent: float = 0.0) -> int:
    settings = _get_motion_profile_settings(cfg)
    if settings["clip_mode"] != "auto":
        return max(5, int(cfg.get("motion_record_duration", settings["clip_mid"]) or settings["clip_mid"]))

    score = max(motion_ratio * 100.0, motion_percent) + (contour_count * 0.35) + min(mean_diff, 40.0) / 4.0
    if score >= 10:
        return settings["clip_max"]
    if score >= 5:
        return settings["clip_mid"]
    return settings["clip_min"]


def _should_extend_motion_capture(previous_gray, current_frame, settings: dict):
    import cv2

    current_gray = cv2.cvtColor(current_frame, cv2.COLOR_RGB2GRAY)
    diff = cv2.absdiff(previous_gray, current_gray)
    blur = cv2.GaussianBlur(diff, (11, 11), 0)
    _, thresh = cv2.threshold(blur, 24, 255, cv2.THRESH_BINARY)
    thresh = cv2.dilate(thresh, None, iterations=1)
    motion_ratio = cv2.countNonZero(thresh) / float(current_gray.shape[0] * current_gray.shape[1])
    mean_diff = float(diff.mean())
    active = motion_ratio > (settings["threshold"] * 0.75) or mean_diff > (settings["mean_diff"] * 0.8)
    return active, current_gray, motion_ratio, mean_diff


def _get_gdrive_cfg(cfg: dict) -> dict:
    gdrive = cfg.get("google_drive", {}) or {}
    return {
        "enabled": cfg.get("gdrive_enabled", gdrive.get("enabled", False)),
        "folder_id": cfg.get("gdrive_folder_id", gdrive.get("folder_id", "")),
        "credentials_file": gdrive.get("credentials_file", "config/gdrive_credentials.json")
    }


def _get_client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or ""


def _is_tailscale_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        if addr.version == 4:
            return addr in ipaddress.ip_network("100.64.0.0/10")
        return addr in ipaddress.ip_network("fd7a:115c:a1e0::/48")
    except Exception:
        return False


def _is_allowed_client(cfg: dict) -> bool:
    security = _get_security_cfg(cfg)
    if not security.get("tailscale_only", False):
        return True

    ip = _get_client_ip()
    if security.get("allow_localhost", True) and ip in ("127.0.0.1", "::1"):
        return True

    if security.get("allow_setup_without_vpn", True) and is_first_run():
        if request.path.startswith("/setup") or request.path.startswith("/login") or request.path.startswith("/register"):
            return True

    return _is_tailscale_ip(ip)


def is_wifi_connected() -> bool:
    """Lightweight WiFi check without depending on specific tools."""
    try:
        import subprocess
        # Check if wlan0 is up using /sys/class/net
        try:
            result = subprocess.run(['cat', '/sys/class/net/wlan0/operstate'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and 'up' in result.stdout.lower():
                return True
        except:
            pass
        
        # Fallback: try iw command
        try:
            result = subprocess.run(['iw', 'dev', 'wlan0', 'link'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and 'Connected to' in result.stdout:
                return True
        except:
            pass
        
        # Last resort: try iwconfig (may not be installed)
        try:
            result = subprocess.run(['iwconfig', 'wlan0'], capture_output=True, text=True, timeout=2)
            return 'ESSID:' in result.stdout and 'ESSID:""' not in result.stdout
        except:
            pass
        
        return False
    except Exception as e:
        logger.debug(f"[NETWORK] WiFi check failed: {e}")
        return False


def queue_offline_clip(video_path: str, meta: dict) -> None:
    """Store video reference to sync when WiFi returns."""
    items = _load_queue(OFFLINE_QUEUE_FILE)
    items.append({
        "video_path": video_path,
        "meta": meta or {},
        "timestamp": datetime.utcnow().isoformat(),
        "synced": False
    })
    _save_queue(OFFLINE_QUEUE_FILE, items)
    logger.info(f"[OFFLINE] Queued clip for later sync: {video_path}")


def queue_notification_retry(phone: str, message: str, reason: str = "unknown") -> None:
    items = _load_queue(NOTIFY_QUEUE_FILE)
    items.append({
        "phone": phone,
        "message": message,
        "attempts": 0,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    })
    _save_queue(NOTIFY_QUEUE_FILE, items)
    logger.info(f"[NOTIFY] Queued notification retry for {phone} (reason: {reason})")


def flush_notification_queue() -> None:
    if not is_wifi_connected():
        return
    items = _load_queue(NOTIFY_QUEUE_FILE)
    if not items:
        return
    cfg = get_config()
    if not cfg.get('sms_enabled'):
        return
    from src.core import get_sms_notifier
    notifier = get_sms_notifier()
    remaining = []
    for item in items:
        phone = item.get("phone")
        message = item.get("message")
        attempts = int(item.get("attempts", 0))
        if not phone or not message:
            continue
        if attempts >= 3:
            logger.warning(f"[NOTIFY] Dropping notification after 3 attempts: {phone}")
            continue
        try:
            notifier.send_sms(phone, message)
            logger.success(f"[NOTIFY] Retry sent to {phone}")
        except Exception as e:
            attempts += 1
            item["attempts"] = attempts
            item["last_error"] = str(e)
            remaining.append(item)
            logger.warning(f"[NOTIFY] Retry failed ({attempts}/3) for {phone}: {e}")
    _save_queue(NOTIFY_QUEUE_FILE, remaining)


def mark_offline_clips_synced() -> None:
    if not is_wifi_connected():
        return
    items = _load_queue(OFFLINE_QUEUE_FILE)
    changed = False
    for item in items:
        if not item.get("synced") and os.path.exists(item.get("video_path", "")):
            item["synced"] = True
            item["synced_at"] = datetime.utcnow().isoformat()
            changed = True
    if changed:
        _save_queue(OFFLINE_QUEUE_FILE, items)


def _resolve_clip_path(filename: str, cfg: dict) -> tuple:
    if not filename or "/" in filename or "\\" in filename or ".." in filename:
        return None, False

    storage = _get_storage_cfg(cfg)
    recordings_path = os.path.join(BASE_DIR, storage["recordings_dir"], filename)
    encrypted_path = os.path.join(BASE_DIR, storage["encrypted_dir"], filename)

    if os.path.exists(recordings_path):
        return recordings_path, False
    if os.path.exists(encrypted_path):
        return encrypted_path, filename.endswith(".enc")

    if not filename.endswith(".enc"):
        alt_enc = os.path.join(BASE_DIR, storage["encrypted_dir"], f"{filename}.enc")
        if os.path.exists(alt_enc):
            return alt_enc, True

    return None, False


def _decrypt_to_temp(enc_path: str) -> str:
    try:
        temp_dir = os.path.join(BASE_DIR, "cache", "temp_decrypt")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"clip_{secrets.token_hex(8)}.mp4")
        enc = get_encryption()
        if enc.decrypt_file(enc_path, temp_path):
            return temp_path
    except Exception as e:
        logger.error(f"[ENCRYPTION] Temp decrypt failed: {e}")
    return None


def _encrypt_clip_if_enabled(file_path: str, cfg: dict) -> tuple:
    storage = _get_storage_cfg(cfg)
    if not storage.get("encrypt"):
        return file_path, False

    try:
        encrypted_dir = os.path.join(BASE_DIR, storage["encrypted_dir"])
        os.makedirs(encrypted_dir, exist_ok=True)
        enc = get_encryption()
        output_path = os.path.join(encrypted_dir, os.path.basename(file_path) + ".enc")
        if enc.encrypt_file(file_path, output_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
            return output_path, True
    except Exception as e:
        logger.error(f"[ENCRYPTION] Clip encryption failed: {e}")
    return file_path, False


def _queue_cloud_upload(file_path: str, meta: dict = None) -> str:
    if not CLOUD_AVAILABLE:
        return None
    cfg = get_config()
    gdrive = _get_gdrive_cfg(cfg)
    if not gdrive.get("enabled"):
        return None
    if not is_wifi_connected():
        return None

    try:
        cloud = get_cloud_storage(base_dir=BASE_DIR, google_credentials=gdrive.get("credentials_file"))
        return cloud.queue_upload(file_path, remote_folder=gdrive.get("folder_id") or None, metadata=meta or {})
    except Exception as e:
        logger.warning(f"[CLOUD] Queue upload failed: {e}")
        return None


def flush_offline_clip_queue() -> None:
    if not is_wifi_connected():
        return

    cfg = get_config()
    gdrive = _get_gdrive_cfg(cfg)
    if not gdrive.get("enabled"):
        return

    items = _load_queue(OFFLINE_QUEUE_FILE)
    if not items:
        return

    remaining = []
    for item in items:
        if item.get("queued") or item.get("synced"):
            remaining.append(item)
            continue

        filename = item.get("video_path")
        path, _ = _resolve_clip_path(filename, cfg)
        if not path or not os.path.exists(path):
            item["error"] = "file_missing"
            remaining.append(item)
            continue

        upload_id = _queue_cloud_upload(path, meta=item.get("meta"))
        if upload_id:
            item["queued"] = True
            item["queued_at"] = datetime.utcnow().isoformat()
            item["upload_id"] = upload_id
        remaining.append(item)

    _save_queue(OFFLINE_QUEUE_FILE, remaining)


# Throttle background flush work to keep Pi Zero responsive
_last_queue_flush = 0

def maybe_flush_queues(throttle_seconds: int = 30) -> None:
    global _last_queue_flush
    now = time.time()
    if now - _last_queue_flush < throttle_seconds:
        return
    _last_queue_flush = now
    flush_notification_queue()
    flush_offline_clip_queue()

def create_lite_app(pi_model, camera_config):
    """Create lightweight Flask app with all features"""
    
    app = Flask(__name__, template_folder='templates', static_folder='static')
    webrtc_streamer = None
    cfg = get_config()
    security = _ensure_security_cfg(cfg)
    app.secret_key = security.get("secret_key")
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=bool(security.get("cookie_secure", False)),
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=int(security.get("session_timeout_minutes", 720)))
    )
    
    # VPN SUPPORT: Add CORS and security headers for VPN connections
    @app.after_request
    def add_vpn_headers(response):
        """Add headers for VPN and remote access support from ANY network"""
        origin = request.headers.get('Origin')
        if origin and origin.startswith(request.host_url.rstrip('/')):
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Vary'] = 'Origin'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Max-Age'] = '3600'
        response.headers['Access-Control-Expose-Headers'] = 'Content-Type'
        
        # Disable buffering for streaming over VPN/remote connections
        response.headers['X-Accel-Buffering'] = 'no'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        # Security headers (but allow VPN/remote access)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Cache control for offline VPN access
        if 'Cache-Control' not in response.headers:
            response.headers['Cache-Control'] = 'public, max-age=3600'
        
        return response
    
    # Handle CORS preflight requests
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = Response()
            origin = request.headers.get('Origin')
            if origin and origin.startswith(request.host_url.rstrip('/')):
                response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response

    @app.before_request
    def enforce_tailscale_only():
        if request.path.startswith("/static"):
            return None

        current_cfg = get_config()
        if _get_security_cfg(current_cfg).get("tailscale_only") and not _is_allowed_client(current_cfg):
            logger.warning(f"[SECURITY] Blocked non-Tailscale access: {request.path} from {_get_client_ip()}")
            if request.path.startswith("/api/"):
                return jsonify({"error": "Tailscale access required"}), 403
            return render_template("access_blocked.html"), 403
    
    app_started_at = time.time()

    # Lightweight battery monitor
    battery = BatteryMonitor(enabled=True)
    low_battery_alert_at = {"ts": 0.0}

    # Background queue flush for offline clips/cloud sync
    def _background_sync():
        while True:
            try:
                maybe_flush_queues(10)
                status = battery.get_status()
                if status.get("is_low"):
                    now = time.time()
                    if now - low_battery_alert_at["ts"] > 1800:
                        cfg = get_config()
                        if cfg.get('sms_enabled') and cfg.get('send_motion_to_emergency'):
                            phone = cfg.get('sms_phone_to') or cfg.get('emergency_phone')
                            if phone:
                                try:
                                    from src.core import get_sms_notifier
                                    notifier = get_sms_notifier()
                                    pct = status.get('percent')
                                    pct_text = f"{pct}%" if isinstance(pct, int) else "unknown"
                                    msg = f"⚠️ {cfg.get('device_name', 'ME Camera')}: Low power detected (battery {pct_text}, undervolt={not status.get('external_power', True)})."
                                    notifier.send_sms(phone, msg)
                                    low_battery_alert_at["ts"] = now
                                    logger.warning(f"[POWER] Low battery alert sent to {phone}")
                                except Exception as e:
                                    logger.warning(f"[POWER] Low battery alert failed: {e}")
            except Exception as e:
                logger.debug(f"[SYNC] Background sync error: {e}")
            time.sleep(5)

    threading.Thread(target=_background_sync, daemon=True).start()
    
    # Motion recording state
    motion_recorder = {
        'recording': False,
        'start_time': None,
        'frames': []
    }

    # Login protection state (in-memory, lightweight)
    login_attempts = {}
    LOGIN_WINDOW_SECONDS = 15 * 60
    LOGIN_MAX_ATTEMPTS = 6
    LOGIN_LOCKOUT_SECONDS = 10 * 60

    def _login_attempt_key(username: str) -> str:
        ip = _get_client_ip() or 'unknown'
        return f"{ip}|{(username or '').strip().lower()}"

    def _is_login_locked(key: str):
        now = time.time()
        entry = login_attempts.get(key)
        if not entry:
            return False, 0
        lock_until = entry.get('lock_until', 0)
        if lock_until > now:
            return True, int(lock_until - now)
        # prune stale history
        failures = [ts for ts in entry.get('failures', []) if (now - ts) <= LOGIN_WINDOW_SECONDS]
        entry['failures'] = failures
        if not failures and lock_until <= now:
            login_attempts.pop(key, None)
        return False, 0

    def _record_login_failure(key: str):
        now = time.time()
        entry = login_attempts.get(key, {'failures': [], 'lock_until': 0})
        failures = [ts for ts in entry.get('failures', []) if (now - ts) <= LOGIN_WINDOW_SECONDS]
        failures.append(now)
        entry['failures'] = failures
        if len(failures) >= LOGIN_MAX_ATTEMPTS:
            entry['lock_until'] = now + LOGIN_LOCKOUT_SECONDS
        login_attempts[key] = entry

    def _clear_login_failures(key: str):
        login_attempts.pop(key, None)

    # Nanny cam mode (when enabled, motion is not logged/recorded)
    nanny_cam_enabled = False
    
    # Initialize camera - try RpicamStreamer first (most compatible)
    camera = None
    camera_available = False
    camera_rotation_mode = detect_camera_rotation() or 'normal'
    
    if camera_config['mode'] in ['lite', 'fast']:
        try:
            stream_cfg = cfg.get('camera', {}) or {}
            try:
                stream_fps = int(stream_cfg.get('stream_fps', 20) or 20)
            except Exception:
                stream_fps = 20
            stream_fps = max(5, min(30, stream_fps))

            raw_quality = stream_cfg.get('stream_quality', 85)
            if isinstance(raw_quality, str):
                quality_map = {
                    'low': 70,
                    'standard': 80,
                    'high': 90,
                    'ultra': 95,
                }
                try:
                    stream_quality = int(raw_quality)
                except Exception:
                    stream_quality = quality_map.get(raw_quality.lower(), 85)
            else:
                stream_quality = int(raw_quality)
            stream_quality = max(50, min(100, stream_quality))

            from src.camera import RpicamStreamer, is_rpicam_available
            rotation_degrees = {
                'rotate_90': 90,
                'rotate_180': 180,
                'rotate_270': 270
            }.get(camera_rotation_mode, 0)
            hflip = camera_rotation_mode == 'flip_horizontal'
            vflip = camera_rotation_mode == 'flip_vertical'
            
            if is_rpicam_available():
                logger.info("[CAMERA] Attempting rpicam-jpeg streaming (OPTIMIZED)...")
                camera = RpicamStreamer(
                    width=640,
                    height=480,
                    fps=stream_fps,
                    quality=stream_quality,
                    rotation=rotation_degrees,
                    hflip=hflip,
                    vflip=vflip,
                )
                if camera.start():
                    camera_available = True
                    logger.success(
                        f"[CAMERA] RPiCam initialized: 640x480 @ {stream_fps} FPS, "
                        f"Quality {stream_quality}, rotation={camera_rotation_mode}"
                    )
            else:
                logger.warning("[CAMERA] rpicam-jpeg not available, falling back to picamera2...")
                from picamera2 import Picamera2
                camera = Picamera2()
                camera.configure(camera.create_preview_configuration(
                    main={"size": (640, 480), "format": "RGB888"}
                ))
                camera.start()
                camera_available = True
                logger.success(f"[CAMERA] Camera initialized (picamera2): 640x480")
        except ImportError as e:
            logger.warning(f"[CAMERA] Required module not available: {e}")
        except Exception as e:
            logger.warning(f"[CAMERA] Camera init failed: {e}")
            camera = None
            camera_available = False
    
    # ============= HELPER FUNCTIONS =============
    
    def get_storage_info():
        """Get storage information"""
        storage_cfg = _get_storage_cfg(get_config())
        recordings_path = os.path.join(BASE_DIR, storage_cfg["recordings_dir"])
        encrypted_path = os.path.join(BASE_DIR, storage_cfg["encrypted_dir"])
        os.makedirs(recordings_path, exist_ok=True)
        os.makedirs(encrypted_path, exist_ok=True)
        
        total, used, free = shutil.disk_usage(recordings_path)
        
        # Count recordings
        recording_count = 0
        total_size_mb = 0
        if os.path.exists(recordings_path):
            for root, dirs, files in os.walk(recordings_path):
                for f in files:
                    if f.endswith(('.mp4', '.h264', '.h265', '.mkv', '.jpg', '.jpeg', '.png')):
                        recording_count += 1
                        try:
                            total_size_mb += os.path.getsize(os.path.join(root, f)) / (1024*1024)
                        except:
                            pass
        if os.path.exists(encrypted_path):
            for root, dirs, files in os.walk(encrypted_path):
                for f in files:
                    if f.endswith('.enc'):
                        recording_count += 1
                        try:
                            total_size_mb += os.path.getsize(os.path.join(root, f)) / (1024*1024)
                        except:
                            pass
        
        return {
            'total_gb': round(total / (1024**3), 2),
            'used_gb': round(used / (1024**3), 2),
            'free_gb': round(free / (1024**3), 2),
            'recording_count': recording_count,
            'recordings_size_mb': round(total_size_mb, 2)
        }

    def list_clips():
        """List recordings and encrypted clips for the library page"""
        cfg = get_config()
        storage_cfg = _get_storage_cfg(cfg)
        recordings_path = os.path.join(BASE_DIR, storage_cfg["recordings_dir"])
        encrypted_path = os.path.join(BASE_DIR, storage_cfg["encrypted_dir"])
        clips = []

        def add_clip(path, name, encrypted=False):
            try:
                stat = os.stat(path)
                clips.append({
                    "name": name,
                    "encrypted": encrypted,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "timestamp": datetime.fromtimestamp(stat.st_mtime),
                    "timestamp_str": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                })
            except Exception:
                pass

        if os.path.isdir(recordings_path):
            for name in os.listdir(recordings_path):
                if name.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
                    add_clip(os.path.join(recordings_path, name), name, encrypted=False)

        if os.path.isdir(encrypted_path):
            for name in os.listdir(encrypted_path):
                if name.lower().endswith(".enc"):
                    add_clip(os.path.join(encrypted_path, name), name, encrypted=True)

        clips.sort(key=lambda c: c["timestamp"], reverse=True)
        return clips
    
    def cleanup_old_recordings(days=7):
        """Delete recordings older than X days"""
        storage_cfg = _get_storage_cfg(get_config())
        recordings_path = os.path.join(BASE_DIR, storage_cfg["recordings_dir"])
        encrypted_path = os.path.join(BASE_DIR, storage_cfg["encrypted_dir"])
        cutoff = datetime.now() - timedelta(days=days)
        
        if not os.path.exists(recordings_path) and not os.path.exists(encrypted_path):
            return {'deleted': 0, 'freed_mb': 0}
        
        deleted_count = 0
        freed_mb = 0
        
        for root, dirs, files in os.walk(recordings_path):
            for f in files:
                if f.endswith(('.mp4', '.h264', '.h265', '.mkv')):
                    fpath = os.path.join(root, f)
                    try:
                        mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                        if mtime < cutoff:
                            size_mb = os.path.getsize(fpath) / (1024*1024)
                            os.remove(fpath)
                            deleted_count += 1
                            freed_mb += size_mb
                            logger.info(f"[STORAGE] Deleted old recording: {f}")
                    except Exception as e:
                        logger.error(f"[STORAGE] Delete failed: {f}: {e}")

        for root, dirs, files in os.walk(encrypted_path):
            for f in files:
                if f.endswith('.enc'):
                    fpath = os.path.join(root, f)
                    try:
                        mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                        if mtime < cutoff:
                            size_mb = os.path.getsize(fpath) / (1024*1024)
                            os.remove(fpath)
                            deleted_count += 1
                            freed_mb += size_mb
                            logger.info(f"[STORAGE] Deleted old encrypted recording: {f}")
                    except Exception as e:
                        logger.error(f"[STORAGE] Encrypted delete failed: {f}: {e}")
        
        return {'deleted': deleted_count, 'freed_mb': round(freed_mb, 2)}
    
    def get_motion_events():
        """Get all motion events"""
        try:
            events_path = os.path.join(BASE_DIR, "logs", "motion_events.json")
            if os.path.exists(events_path):
                with open(events_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"[MOTION] Load events failed: {e}")
        return []

    def save_motion_clip(camera_obj, frame, duration_sec=5):
        """Save a short MP4 clip when motion is detected"""
        try:
            import cv2
            recordings_path = os.path.join(BASE_DIR, "recordings")
            os.makedirs(recordings_path, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"motion_{timestamp}.mp4"
            filepath = os.path.join(recordings_path, filename)

            # Prepare video writer with H.264 codec for browser compatibility
            height, width, _ = frame.shape
            # Use H.264 codec (x264) which all browsers support
            fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 / AVC
            fps = 20.0  # Increased FPS for smoother video
            writer = cv2.VideoWriter(filepath, fourcc, fps, (width, height))

            if not writer.isOpened():
                # Fallback to mp4v if H.264 not available
                logger.warning("[MOTION] H.264 not available, using mp4v")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                writer = cv2.VideoWriter(filepath, fourcc, fps, (width, height))

            # Write initial frame
            writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

            # Capture additional frames for duration_sec seconds
            frame_count = int(duration_sec * fps)
            for i in range(frame_count):
                try:
                    next_frame = camera_obj.capture_array()
                    writer.write(cv2.cvtColor(next_frame, cv2.COLOR_RGB2BGR))
                    time.sleep(1.0 / fps)  # Control frame rate
                except Exception as e:
                    logger.debug(f"[MOTION] Frame {i} capture error: {e}")
                    break

            writer.release()
            logger.info(f"[MOTION] Saved {frame_count} frames to: {filename}")
            return filename
        except Exception as e:
            logger.error(f"[MOTION] Save clip failed: {e}")
            return None
    
    def save_motion_clip_buffered(camera_obj, buffered_frames, duration_sec=5):
        """Save a motion clip using pre-buffered frames + continue recording, with optional audio."""
        try:
            import cv2
            recordings_path = os.path.join(BASE_DIR, "recordings")
            os.makedirs(recordings_path, exist_ok=True)

            cfg = get_config()
            motion_settings = _get_motion_profile_settings(cfg)
            max_duration = motion_settings["clip_max"] if motion_settings["clip_mode"] == "auto" else max(int(duration_sec), motion_settings["clip_min"])
            min_duration = min(max_duration, max(int(duration_sec), motion_settings["clip_min"]))

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"motion_{timestamp}.mp4"
            filepath = os.path.join(recordings_path, filename)

            # Get dimensions from buffered frames
            if not buffered_frames:
                return None
            
            height, width, _ = buffered_frames[0].shape
            fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264
            fps = 20.0  # Increased FPS for smoother motion capture
            writer = cv2.VideoWriter(filepath, fourcc, fps, (width, height))

            if not writer.isOpened():
                logger.warning("[MOTION] H.264 not available, using mp4v")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                writer = cv2.VideoWriter(filepath, fourcc, fps, (width, height))

            audio_proc = None
            audio_path = None
            audio_embedded = False
            audio_sidecar = None

            # Try to capture audio in parallel when enabled and arecord is present.
            if cfg.get('audio_record_on_motion', True) and shutil.which("arecord"):
                try:
                    audio_path = os.path.join(recordings_path, f"motion_{timestamp}.wav")
                    audio_cmd = _build_arecord_command(audio_path, max_duration)
                    audio_proc = subprocess.Popen(audio_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception as e:
                    logger.warning(f"[AUDIO] Failed to start audio capture: {e}")
                    audio_proc = None
                    audio_path = None

            # Write buffered frames first (captures motion that already happened)
            for frame in buffered_frames:
                writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

            previous_gray = cv2.cvtColor(buffered_frames[-1], cv2.COLOR_RGB2GRAY)
            min_total_frames = max(len(buffered_frames), int(min_duration * fps))
            max_total_frames = max(min_total_frames, int(max_duration * fps))
            additional_frames = 0
            last_motion_seen = time.time()

            # Continue capturing and extend recording while motion is still active.
            for i in range(max(0, max_total_frames - len(buffered_frames))):
                try:
                    next_frame = camera_obj.capture_array()
                    writer.write(cv2.cvtColor(next_frame, cv2.COLOR_RGB2BGR))
                    additional_frames += 1
                    active, previous_gray, _, _ = _should_extend_motion_capture(previous_gray, next_frame, motion_settings)
                    if active:
                        last_motion_seen = time.time()

                    total_frames_written = len(buffered_frames) + additional_frames
                    if total_frames_written >= min_total_frames and (time.time() - last_motion_seen) >= 1.5:
                        break
                    time.sleep(1.0 / fps)
                except Exception as e:
                    logger.debug(f"[MOTION] Frame {i} capture error: {e}")
                    break

            writer.release()

            # Wait for audio capture to finish (best-effort)
            if audio_proc:
                try:
                    audio_proc.wait(timeout=max_duration + 2)
                except Exception:
                    audio_proc.kill()
                audio_proc = None

            has_audio_capture = bool(audio_path and os.path.exists(audio_path) and os.path.getsize(audio_path) > 1024)

            # Mux audio if available and ffmpeg present
            if has_audio_capture and shutil.which("ffmpeg"):
                try:
                    muxed_path = filepath.replace(".mp4", "_av.mp4")
                    mux_cmd = [
                        "ffmpeg", "-y",
                        "-loglevel", "error",
                        "-i", filepath,
                        "-i", audio_path,
                        "-c:v", "copy",
                        "-c:a", "aac",
                        "-shortest",
                        "-movflags", "+faststart",
                        muxed_path
                    ]
                    # Pi Zero can take noticeably longer when remuxing AV clips.
                    mux_timeout = max(30, int(max_duration) * 4)
                    subprocess.run(mux_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=mux_timeout)
                    if os.path.exists(muxed_path):
                        os.replace(muxed_path, filepath)
                        audio_embedded = True
                        logger.info(f"[AUDIO] Embedded audio into {filename}")
                    else:
                        logger.warning("[AUDIO] Mux failed; keeping video-only file")
                except Exception as e:
                    logger.warning(f"[AUDIO] Mux error: {e}")
                finally:
                    if audio_embedded:
                        try:
                            if audio_path and os.path.exists(audio_path):
                                os.remove(audio_path)
                        except Exception:
                            pass
            elif has_audio_capture:
                audio_sidecar = os.path.basename(audio_path)
                logger.warning("[AUDIO] ffmpeg unavailable or mux skipped; keeping sidecar WAV file")

            final_path, encrypted = _encrypt_clip_if_enabled(filepath, cfg)
            final_name = os.path.basename(final_path)

            total_frames = len(buffered_frames) + max(0, additional_frames)
            if encrypted:
                logger.info(f"[MOTION] Saved {total_frames} frames to encrypted clip: {final_name}")
            else:
                logger.info(f"[MOTION] Saved {total_frames} frames ({len(buffered_frames)} buffered) to: {filename}")
            return {
                "clip_name": final_name,
                "audio_embedded": audio_embedded,
                "audio_sidecar": audio_sidecar,
                "audio_attempted": bool(cfg.get('audio_record_on_motion', True)),
            }
        except Exception as e:
            logger.error(f"[MOTION] Save buffered clip failed: {e}")
            return None
    
    def save_motion_snapshot(frame):
        """Save a snapshot when motion is detected"""
        try:
            recordings_path = os.path.join(BASE_DIR, "recordings")
            os.makedirs(recordings_path, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"motion_{timestamp}.jpg"
            filepath = os.path.join(recordings_path, filename)
            
            from PIL import Image
            img = Image.fromarray(frame)
            img.save(filepath, quality=95)
            
            logger.info(f"[MOTION] Saved snapshot: {filename}")
            return filename
        except Exception as e:
            logger.error(f"[MOTION] Save snapshot failed: {e}")
            return None
    
    def delete_motion_event(event_id):
        """Delete a specific motion event and its video file"""
        try:
            events_path = os.path.join(BASE_DIR, "logs", "motion_events.json")
            if os.path.exists(events_path):
                with open(events_path, 'r') as f:
                    events = json.load(f)
                
                # Find event and delete its video file
                event_to_delete = next((e for e in events if e.get('id') == event_id), None)
                if event_to_delete:
                    video_path = event_to_delete.get('details', {}).get('video_path')
                    if video_path:
                        cfg = get_config()
                        full_path, _ = _resolve_clip_path(video_path, cfg)
                        if full_path and os.path.exists(full_path):
                            os.remove(full_path)
                            logger.info(f"[MOTION] Deleted video file: {full_path}")
                        else:
                            logger.warning(f"[MOTION] Video file not found: {full_path}")
                
                # Remove from events list
                events = [e for e in events if e.get('id') != event_id]
                
                with open(events_path, 'w') as f:
                    json.dump(events, f, indent=2)
                
                return True
        except Exception as e:
            logger.error(f"[MOTION] Delete event failed: {e}")
        return False
    
    # ============= ROUTES =============
    
    @app.route("/")
    def index():
        """Main dashboard"""
        if is_first_run():
            return redirect(url_for('setup'))
        
        if 'user' not in session:
            return redirect(url_for('login'))

        cfg = get_config()
        security_cfg = _ensure_security_cfg(cfg)
        if security_cfg.get('bootstrap_required') and session.get('user') == security_cfg.get('bootstrap_admin'):
            return redirect(url_for('customer_setup'))

        storage = get_storage_info()
        try:
            total_gb = storage.get('total_gb', 0) or 0
            used_gb = storage.get('used_gb', 0) or 0
            storage_percent = int((used_gb / total_gb) * 100) if total_gb > 0 else 0
        except Exception:
            storage_percent = 0
        battery_status = battery.get_status()
        motion_events = get_motion_events()
        
        return render_template('dashboard_lite.html',
            device_name=cfg.get('device_name', 'ME Camera'),
            device_id=cfg.get('device_id', 'camera-001'),
            pi_model=pi_model['name'],
            ram_mb=pi_model['ram_mb'],
            camera_available=bool(camera is not None and camera_available),
            battery_pct=battery_status.get('percent', 0),
            storage=storage,
            storage_percent=storage_percent,
            motion_count=len(motion_events),
            tts_available=bool(shutil.which('espeak') or shutil.which('espeak-ng') or shutil.which('spd-say')),
            audio_playback_available=bool(shutil.which('aplay') or shutil.which('paplay') or shutil.which('ffplay')),
            version='2.2.3-LITE'
        )
    
    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Login page"""
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            attempt_key = _login_attempt_key(username)

            locked, seconds_left = _is_login_locked(attempt_key)
            if locked:
                minutes_left = max(1, int(seconds_left / 60))
                logger.warning(f"[AUTH] Login temporarily locked for key={attempt_key}")
                return render_template('login.html', error=f"Too many failed attempts. Try again in {minutes_left} minute(s).")

            cfg = get_config()
            security_cfg = _ensure_security_cfg(cfg)
            bootstrap_required = security_cfg.get('bootstrap_required')
            bootstrap_admin = security_cfg.get('bootstrap_admin') or 'admin'
            
            if authenticate(username, password):
                _clear_login_failures(attempt_key)
                if bootstrap_required and username != bootstrap_admin:
                    return render_template('login.html', error="Initial setup requires the admin account. Please sign in as admin to create the customer account.")
                session.permanent = True
                session['user'] = username
                session['login_at'] = datetime.utcnow().isoformat()
                session['device_token'] = _get_security_cfg(get_config()).get('device_token')
                if bootstrap_required and username == bootstrap_admin:
                    return redirect(url_for('customer_setup'))
                return redirect(url_for('index'))
            else:
                _record_login_failure(attempt_key)
                return render_template('login.html', error="Invalid credentials")
        
        return render_template('login.html')

    @app.route("/customer-setup", methods=["GET", "POST"])
    def customer_setup():
        """Create customer account and remove bootstrap admin"""
        if 'user' not in session:
            return redirect(url_for('login'))

        cfg = get_config()
        security_cfg = _ensure_security_cfg(cfg)
        if not security_cfg.get('bootstrap_required'):
            return redirect(url_for('index'))

        bootstrap_admin = security_cfg.get('bootstrap_admin') or 'admin'
        if session.get('user') != bootstrap_admin:
            return redirect(url_for('login'))

        if request.method == "POST":
            customer_username = request.form.get("customer_username", "").strip()
            customer_password = request.form.get("customer_password", "")
            customer_password_confirm = request.form.get("customer_password_confirm", "")
            security_key = request.form.get("security_key", "").strip()

            if not customer_username or len(customer_username) < 3:
                return render_template('customer_setup.html', error="Username must be at least 3 characters")
            if customer_username == bootstrap_admin:
                return render_template('customer_setup.html', error="Customer username must be different from admin")
            if not customer_password or len(customer_password) < 8:
                return render_template('customer_setup.html', error="Password must be at least 8 characters")
            if customer_password != customer_password_confirm:
                return render_template('customer_setup.html', error="Passwords do not match")
            if not verify_enrollment_key(security_key):
                return render_template('customer_setup.html', error="Invalid customer security key")

            from src.core import create_user, delete_user, user_exists
            if user_exists(customer_username):
                return render_template('customer_setup.html', error="Username already exists")
            if not create_user(customer_username, customer_password):
                return render_template('customer_setup.html', error="Failed to create customer account")

            if not delete_user(bootstrap_admin):
                return render_template('customer_setup.html', error="Customer created, but failed to remove admin. Please retry.")

            security_cfg['bootstrap_required'] = False
            security_cfg['bootstrap_admin'] = ""
            cfg['security'] = security_cfg
            save_config(cfg)

            session['user'] = customer_username
            session['login_at'] = datetime.utcnow().isoformat()
            return redirect(url_for('index'))

        return render_template('customer_setup.html')
    
    @app.route("/register", methods=["GET", "POST"])
    def register():
        """User registration"""
        cfg = get_config()
        security_cfg = _ensure_security_cfg(cfg)
        if security_cfg.get('bootstrap_required'):
            return render_template("register.html", error="Registration is disabled until the customer account is created by admin.")
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            password_confirm = request.form.get("password_confirm", "")
            security_key = request.form.get("security_key", "").strip()
            
            # Validation
            if not username or len(username) < 3:
                return render_template("register.html", error="Username must be at least 3 characters")
            
            if not password or len(password) < 6:
                return render_template("register.html", error="Password must be at least 6 characters")
            
            if password != password_confirm:
                return render_template("register.html", error="Passwords don't match")

            if not verify_enrollment_key(security_key):
                return render_template("register.html", error="Invalid customer security key")
            
            from src.core import user_exists, create_user
            if user_exists(username):
                return render_template("register.html", error="Username already exists")
            
            # Create user
            if create_user(username, password):
                logger.info(f"[AUTH] New user registered: {username}")
                return render_template("register.html", success="Account created! Please login.")
            else:
                return render_template("register.html", error="Error creating account")
        
        return render_template("register.html")
    
    @app.route("/logout")
    def logout():
        """Logout"""
        session.pop('user', None)
        return redirect(url_for('login'))
    
    @app.route("/setup", methods=["GET", "POST"])
    def setup():
        """First-run setup"""
        if not is_first_run():
            return redirect(url_for('index'))
        
        if request.method == "POST":
            cfg = get_config()
            security_cfg = _ensure_security_cfg(cfg)
            cfg['device_name'] = request.form.get('device_name', 'ME Camera')
            cfg['device_id'] = request.form.get('device_id', 'camera-001')
            cfg['device_location'] = request.form.get('device_location', '')
            cfg['pin_enabled'] = request.form.get('pin_enabled', False) == 'on'
            cfg['pin_code'] = request.form.get('pin_code', '')
            cfg['storage_cleanup_days'] = int(request.form.get('retention_days', 7))
            cfg['motion_record_enabled'] = request.form.get('motion_only', True) == 'on'
            cfg['storage_encrypt'] = request.form.get('encrypt', False) == 'on'
            cfg['detection_person_only'] = request.form.get('person_only', False) == 'on'
            cfg['detection_sensitivity'] = float(request.form.get('sensitivity', 0.5))
            cfg['emergency_phone'] = request.form.get('emergency_phone', '')
            cfg['send_motion_to_emergency'] = request.form.get('send_motion_to_emergency', False) == 'on'
            cfg['email_enabled'] = request.form.get('email_enabled', False) == 'on'
            cfg['email_address'] = request.form.get('email_address', '')
            cfg['gdrive_enabled'] = request.form.get('gdrive_enabled', False) == 'on'
            cfg['gdrive_folder_id'] = request.form.get('gdrive_folder_id', '')
            cfg['wifi_enabled'] = request.form.get('wifi_enabled', True) == 'on'
            cfg['bluetooth_enabled'] = request.form.get('bluetooth_enabled', False) == 'on'
            security_cfg['tailscale_only'] = request.form.get('tailscale_only', True) == 'on'
            security_cfg['share_links_enabled'] = request.form.get('share_links_enabled', True) == 'on'
            cfg['security'] = security_cfg
            cfg.setdefault('storage', {})
            cfg['storage']['retention_days'] = int(request.form.get('retention_days', 7))
            cfg['storage']['encrypt'] = cfg.get('storage_encrypt', False)
            cfg['storage']['encrypted_dir'] = cfg.get('storage_encrypted_dir', 'recordings_encrypted')
            cfg.setdefault('google_drive', {})
            cfg['google_drive']['enabled'] = cfg.get('gdrive_enabled', False)
            cfg['google_drive']['folder_id'] = cfg.get('gdrive_folder_id', '')
            save_config(cfg)

            admin_username = request.form.get('admin_username', '').strip()
            admin_password = request.form.get('admin_password', '')
            admin_password_confirm = request.form.get('admin_password_confirm', '')

            if not admin_username or len(admin_username) < 3:
                return render_template('first_run.html', pi_model=pi_model, config=get_config(), error="Admin username must be at least 3 characters")
            if not admin_password or len(admin_password) < 8:
                return render_template('first_run.html', pi_model=pi_model, config=get_config(), error="Admin password must be at least 8 characters")
            if admin_password != admin_password_confirm:
                return render_template('first_run.html', pi_model=pi_model, config=get_config(), error="Admin passwords do not match")

            from src.core import create_user
            if not create_user(admin_username, admin_password):
                return render_template('first_run.html', pi_model=pi_model, config=get_config(), error="Failed to create admin user")

            security_cfg['bootstrap_required'] = True
            security_cfg['bootstrap_admin'] = admin_username
            cfg['security'] = security_cfg
            save_config(cfg)

            mark_first_run_complete()
            return redirect(url_for('login'))
        
        # Get current config for display
        cfg = get_config()
        security_cfg = _ensure_security_cfg(cfg)
        config_display = {
            'device_name': cfg.get('device_name', 'ME Camera'),
            'device_id': cfg.get('device_id', 'camera-001'),
            'device_location': cfg.get('device_location', ''),
            'pin_enabled': cfg.get('pin_enabled', False),
            'pin_code': cfg.get('pin_code', ''),
            'storage': {
                'retention_days': cfg.get('storage_cleanup_days', 7),
                'motion_only': cfg.get('motion_record_enabled', True),
                'encrypt': cfg.get('storage_encrypt', False),
                'encrypted_dir': cfg.get('storage_encrypted_dir', '/mnt/encrypted')
            },
            'detection': {
                'person_only': cfg.get('detection_person_only', False),
                'sensitivity': cfg.get('detection_sensitivity', 0.5)
            },
            'emergency_phone': cfg.get('emergency_phone', ''),
            'send_motion_to_emergency': cfg.get('send_motion_to_emergency', False),
            'email': {
                'enabled': cfg.get('email_enabled', False)
            },
            'email_address': cfg.get('email_address', ''),
            'google_drive': {
                'enabled': cfg.get('gdrive_enabled', False),
                'folder_id': cfg.get('gdrive_folder_id', '')
            },
            'wifi_enabled': cfg.get('wifi_enabled', True),
            'bluetooth_enabled': cfg.get('bluetooth_enabled', False),
            'motion_threshold': cfg.get('motion_threshold', 0.02),
            'motion_record_enabled': cfg.get('motion_record_enabled', True),
            'motion_record_duration': cfg.get('motion_record_duration', 10),
            'sms_enabled': cfg.get('sms_enabled', False),
            'sms_phone_to': cfg.get('sms_phone_to', ''),
            'security': {
                'tailscale_only': security_cfg.get('tailscale_only', True),
                'share_links_enabled': security_cfg.get('share_links_enabled', True)
            }
        }
        
        return render_template('first_run.html', pi_model=pi_model, config=config_display)
    
    @app.route("/config", methods=["GET", "POST"])
    def config_page():
        """Configuration page"""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        cfg = get_config()
        storage = get_storage_info()
        motion_settings = _get_motion_profile_settings(cfg)
        sms_cfg = _get_sms_cfg(cfg)
        
        return render_template('config.html',
            device_name=cfg.get('device_name', 'ME Camera'),
            device_id=cfg.get('device_id', 'camera-001'),
            device_location=cfg.get('device_location', 'Unknown'),
            emergency_phone=cfg.get('emergency_phone', ''),
            send_motion_to_emergency=cfg.get('send_motion_to_emergency', False),
            motion_threshold=cfg.get('motion_threshold', 0.02),
            motion_record_enabled=cfg.get('motion_record_enabled', True),
            audio_record_on_motion=cfg.get('audio_record_on_motion', True),
            motion_record_duration=cfg.get('motion_record_duration', 10),
            motion_sensitivity_mode=motion_settings['sensitivity_mode'],
            motion_trigger_mode=motion_settings['trigger_mode'],
            motion_clip_mode=motion_settings['clip_mode'],
            camera_stream_fps=int((cfg.get('camera', {}) or {}).get('stream_fps', 20) or 20),
            camera_stream_quality=(cfg.get('camera', {}) or {}).get('stream_quality', 85),
            storage_cleanup_days=cfg.get('storage_cleanup_days', 7),
            sms_enabled=sms_cfg.get('enabled', False),
            sms_phone_to=sms_cfg.get('phone_to', ''),
            sms_api_url=sms_cfg.get('generic_http', {}).get('url', cfg.get('sms_api_url', '')),
            sms_api_key=sms_cfg.get('generic_http', {}).get('auth_token', cfg.get('sms_api_key', '')),
            sms_rate_limit=sms_cfg.get('rate_limit_minutes', 5),
            sms_provider=sms_cfg.get('provider', 'twilio'),
            storage=storage,
            current_user=session.get('user', ''),
            config=cfg
        )
    
    @app.route("/recordings/<path:filename>")
    def serve_recording(filename):
        """Serve recorded video/image files"""
        if 'user' not in session:
            return redirect(url_for('login'))

        cfg = get_config()
        file_path, encrypted = _resolve_clip_path(filename, cfg)
        if not file_path or not os.path.exists(file_path):
            abort(404)

        if encrypted:
            temp_path = _decrypt_to_temp(file_path)
            if not temp_path:
                abort(500)

            @after_this_request
            def cleanup(response):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
                return response

            return send_file(temp_path, mimetype='video/mp4', as_attachment=False)

        return send_file(file_path, mimetype='video/mp4', as_attachment=False)
    
    @app.route("/motion-events", methods=["GET"])
    def motion_events_page():
        """View motion events"""
        if 'user' not in session:
            return redirect(url_for('login'))
        events = get_motion_events()
        return render_template('motion_events.html', events=events)

    @app.route("/clips", methods=["GET"])
    def clips_page():
        """Clips library (view/share/download)"""
        if 'user' not in session:
            return redirect(url_for('login'))

        cfg = get_config()
        security_cfg = _get_security_cfg(cfg)
        clips = list_clips()
        return render_template(
            'clips.html',
            clips=clips,
            share_enabled=security_cfg.get('share_links_enabled', True)
        )
    
    @app.route("/video_feed")
    def video_feed():
        """Live video stream - accessible from authenticated dashboard"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        # Stream available if first-run complete (setup done) but allow if logged in too
        # This is an MJPEG stream meant to be embedded in authenticated page
        try:
            if camera is None or not camera_available:
                return Response(generate_test_pattern(), mimetype='multipart/x-mixed-replace; boundary=frame')
            
            # BUG FIX #4: Add keep-alive timeout to prevent orphan connections
            response = Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
            response.headers['Connection'] = 'keep-alive'
            response.headers['Keep-Alive'] = 'timeout=300'  # 5 min timeout to force browser reconnect
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        except Exception as e:
            logger.error(f"[CAMERA] Stream error: {e}")
            return Response(generate_test_pattern(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
    # ============= API ROUTES =============
    
    @app.route("/api/battery", methods=["GET"])
    def api_battery():
        """Battery status"""
        status = battery.get_status()
        return jsonify({
            'percentage': status.get('percent', 0),
            'percent': status.get('percent', 0),
            'runtime_hours': status.get('runtime_hours', 0),
            'runtime_minutes': status.get('runtime_minutes', 0),
            'external_power': status.get('external_power', False),
            'is_low': status.get('is_low', False),
            'note': status.get('note', ''),
            'percent_source': status.get('percent_source', 'unknown'),
            'timestamp': datetime.utcnow().isoformat()
        })

    @app.route("/api/status", methods=["GET"])
    def api_status():
        """Unified runtime status endpoint for health checks and fleet monitoring."""
        try:
            battery_status = battery.get_status()
            storage = get_storage_info()
            cfg = get_config()

            # System uptime from kernel when available
            system_uptime_seconds = None
            try:
                with open('/proc/uptime', 'r') as f:
                    system_uptime_seconds = int(float(f.read().split()[0]))
            except Exception:
                pass

            app_uptime_seconds = int(max(0, time.time() - app_started_at))

            return jsonify({
                'active': True,
                'timestamp': time.time(),
                'device_name': cfg.get('device_name', 'ME_CAM'),
                'mode': camera_config.get('mode', 'lite'),
                'camera_available': bool(camera is not None and camera_available),
                'camera_rotation': camera_rotation_mode,
                'wifi_connected': is_wifi_connected(),
                'battery': {
                    'percent': battery_status.get('percent', 0),
                    'is_low': battery_status.get('is_low', False),
                    'external_power': battery_status.get('external_power', False),
                    'source': battery_status.get('percent_source', 'unknown')
                },
                'storage': {
                    'free_gb': storage.get('free_gb', 0),
                    'used_gb': storage.get('used_gb', 0),
                    'recording_count': storage.get('recording_count', 0)
                },
                'queues': {
                    'offline_clips': len(_load_queue(OFFLINE_QUEUE_FILE)),
                    'notifications': len(_load_queue(NOTIFY_QUEUE_FILE))
                },
                'uptime': {
                    'app_seconds': app_uptime_seconds,
                    'system_seconds': system_uptime_seconds
                }
            })
        except Exception as e:
            logger.error(f"[STATUS] Failed to build status payload: {e}")
            return jsonify({
                'active': False,
                'error': str(e),
                'timestamp': time.time()
            }), 500

    @app.route("/api/health", methods=["GET"])
    def api_health():
        """Lightweight health probe endpoint for load balancers and watchdogs."""
        try:
            return jsonify({
                'ok': True,
                'service': 'mecamera',
                'camera_available': bool(camera is not None and camera_available),
                'wifi_connected': is_wifi_connected(),
                'timestamp': time.time()
            })
        except Exception as e:
            return jsonify({'ok': False, 'error': str(e), 'timestamp': time.time()}), 500

    @app.route("/api/security/enrollment-key/view", methods=["POST"])
    def api_view_enrollment_key():
        """Reveal enrollment key only after confirming current account credentials."""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        try:
            data = request.get_json() or {}
            username = (session.get('user') or data.get('username') or '').strip()
            password = data.get('password') or ''

            if not password:
                return jsonify({'error': 'Password is required'}), 400

            if not authenticate(username, password):
                return jsonify({'error': 'Invalid credentials'}), 403

            cfg = get_config()
            key = ensure_enrollment_key(cfg=cfg, force_rotate=False, reason='view')
            security_cfg = _ensure_security_cfg(cfg)
            return jsonify({
                'ok': True,
                'enrollment_key': key,
                'updated_at': security_cfg.get('enrollment_key_updated_at')
            })
        except Exception as e:
            logger.error(f"[SECURITY] Enrollment key view failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    # NEW: WiFi status API endpoints
    @app.route("/api/network/wifi", methods=["GET"])
    def api_wifi_status():
        """Get WiFi connection status - works with wpa_cli"""
        # Note: This endpoint doesn't require auth so dashboard can always fetch WiFi status
        try:
            import subprocess
            is_connected = False
            ssid = "Unknown"
            signal = "N/A"
            
            # Method 1: Check if interface is up
            try:
                with open('/sys/class/net/wlan0/operstate', 'r') as f:
                    state = f.read().strip()
                    if state == 'up':
                        is_connected = True
            except:
                pass
            
            # Method 2: Try to get SSID from wpa_cli
            if is_connected:
                try:
                    result = subprocess.run(['/usr/sbin/wpa_cli', '-i', 'wlan0', 'status'], 
                                          capture_output=True, text=True, timeout=2)
                    if result.returncode == 0 and result.stdout:
                        for line in result.stdout.split('\n'):
                            if line.startswith('ssid='):
                                ssid = line.split('=', 1)[1].strip()
                                break
                except Exception as e:
                    logger.debug(f"[NETWORK] wpa_cli error: {e}")
            
            # Method 3: Fallback to config if still Unknown
            if ssid == "Unknown":
                try:
                    from src.core import get_config
                    cfg = get_config()
                    if cfg.get('wifi_ssid'):
                        ssid = cfg.get('wifi_ssid')
                        logger.info(f"[NETWORK] Using SSID from config: {ssid}")
                except Exception as e:
                    logger.error(f"[NETWORK] Config fallback failed: {e}")
            
            # Method 4: Get signal strength from /proc/net/wireless
            if is_connected:
                try:
                    with open('/proc/net/wireless', 'r') as f:
                        lines = f.readlines()
                        for line in lines:
                            if 'wlan0' in line:
                                parts = line.split()
                                if len(parts) >= 4:
                                    signal_value = parts[3].rstrip('.')
                                    signal = f"{signal_value} dBm"
                                    break
                except:
                    pass
            
            logger.info(f"[NETWORK] WiFi: connected={is_connected}, ssid={ssid}, signal={signal}")
            
            return jsonify({
                'connected': is_connected,
                'ssid': ssid,
                'signal': signal,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.warning(f"[NETWORK] WiFi status error: {e}")
            return jsonify({'connected': False, 'error': str(e), 'ssid': 'Unknown', 'signal': 'N/A'}), 200

    @app.route("/api/audio/speak", methods=["POST"])
    def api_audio_speak():
        """Speak dashboard text through the device speaker (USB/HDMI/audio jack)."""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        try:
            data = request.get_json() or {}
            text = (data.get('text') or '').strip()
            if not text:
                return jsonify({'ok': False, 'error': 'Message text is required'}), 400
            if len(text) > 160:
                text = text[:160]

            if shutil.which('espeak'):
                subprocess.run(['espeak', '-s', '155', '-a', '120', text], timeout=12, check=False)
                return jsonify({'ok': True, 'message': 'Played on device speaker'})

            if shutil.which('espeak-ng'):
                subprocess.run(['espeak-ng', '-s', '155', '-a', '120', text], timeout=12, check=False)
                return jsonify({'ok': True, 'message': 'Played on device speaker'})

            if shutil.which('spd-say'):
                subprocess.run(['spd-say', text], timeout=12, check=False)
                return jsonify({'ok': True, 'message': 'Played on device speaker'})

            return jsonify({'ok': False, 'error': 'No text-to-speech engine found (install espeak)'}), 503
        except Exception as e:
            logger.error(f"[AUDIO] Speak failed: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500

    def _play_audio_file(path: str) -> str:
        """Play an uploaded WAV/PCM file on the device using available tools."""
        players = [
            ['aplay', '-q', path],
            ['paplay', path],
            ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', path],
        ]
        for cmd in players:
            if not shutil.which(cmd[0]):
                continue
            try:
                result = subprocess.run(cmd, timeout=18, capture_output=True, check=False)
                if result.returncode == 0:
                    return cmd[0]
                logger.warning(f"[AUDIO] {cmd[0]} returned {result.returncode}: {(result.stderr or b'')[:120]}")
            except Exception as e:
                logger.warning(f"[AUDIO] {cmd[0]} playback failed: {e}")
        return ''

    @app.route("/api/audio/play-upload", methods=["POST"])
    def api_audio_play_upload():
        """Play uploaded browser microphone audio on the device speaker."""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        tmp_path = None
        try:
            data = request.get_json() or {}
            audio_b64 = (data.get('audio_wav_base64') or '').strip()
            if not audio_b64:
                return jsonify({'ok': False, 'error': 'Audio payload is required'}), 400

            if ',' in audio_b64:
                audio_b64 = audio_b64.split(',', 1)[1]

            # Keep payload bounded for Pi Zero memory safety (~4MB raw base64).
            if len(audio_b64) > 4_200_000:
                return jsonify({'ok': False, 'error': 'Audio message is too large. Keep it under ~20 seconds.'}), 413

            audio_bytes = base64.b64decode(audio_b64, validate=True)
            if len(audio_bytes) < 128:
                return jsonify({'ok': False, 'error': 'Invalid audio payload'}), 400

            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                tmp.write(audio_bytes)
                tmp.flush()
                tmp_path = tmp.name

            player = _play_audio_file(tmp_path)
            if not player:
                return jsonify({'ok': False, 'error': 'No audio playback tool found (install alsa-utils)'}), 503

            return jsonify({'ok': True, 'message': f'Voice message played on device ({player})'})
        except Exception as e:
            logger.error(f"[AUDIO] Upload playback failed: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
    
    @app.route("/api/network/wifi/update", methods=["POST"])
    def api_wifi_update():
        """Update WiFi settings"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            data = request.get_json()
            ssid = data.get('ssid', '').strip()
            password = data.get('password', '').strip()
            
            if not ssid:
                return jsonify({'error': 'SSID required'}), 400
            
            # Save to config
            cfg = get_config()
            previous_ssid = cfg.get('wifi_ssid', '')
            previous_password = cfg.get('wifi_password', '')
            cfg['wifi_ssid'] = ssid
            cfg['wifi_password'] = password
            cfg['wifi_enabled'] = True
            save_config(cfg)

            if ssid != previous_ssid or password != previous_password:
                rotate_enrollment_key(reason='wifi_change')
                logger.warning("[SECURITY] Enrollment key rotated due to WiFi credential change")
            
            # Try to apply WiFi config at system level
            try:
                import subprocess

                temp_network = '/tmp/mecam_network.conf'
                result = subprocess.run(
                    ['wpa_passphrase', ssid, password],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False
                )
                if result.returncode != 0:
                    raise RuntimeError(result.stderr.strip() or 'wpa_passphrase failed')

                with open(temp_network, 'w') as f:
                    f.write("ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n")
                    f.write("update_config=1\n")
                    f.write(f"country={cfg.get('wifi_country', 'US')}\n\n")
                    f.write(result.stdout)

                subprocess.run(
                    ['sudo', 'install', '-m', '600', temp_network, '/etc/wpa_supplicant/wpa_supplicant.conf'],
                    timeout=8,
                    capture_output=True,
                    check=False
                )
                subprocess.run(['sudo', 'systemctl', 'restart', 'dhcpcd'], timeout=8, capture_output=True, check=False)
                subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'reconfigure'], timeout=8, capture_output=True, check=False)
                
                logger.success(f"[NETWORK] WiFi applied: {ssid}")
            except Exception as e:
                logger.warning(f"[NETWORK] System config pending: {e}")
            
            logger.info(f"[NETWORK] WiFi settings updated to: {ssid}")
            return jsonify({'ok': True, 'message': f'WiFi configured for {ssid}. Device connecting...'})
        except Exception as e:
            logger.error(f"[NETWORK] WiFi update error: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500
    
    @app.route("/api/storage", methods=["GET"])
    def api_storage():
        """Storage info"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        storage = get_storage_info()
        return jsonify(storage)
    
    @app.route("/api/motion/events", methods=["GET"])
    def api_motion_events():
        """Get motion events with optional time filtering"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated', 'events': [], 'count': 0}), 401
        try:
            all_events = get_motion_events()
            
            # Get query parameters
            hours = request.args.get('hours', type=int, default=None)
            limit = request.args.get('limit', type=int, default=None)
            
            # Filter by time if hours parameter provided
            from datetime import datetime, timedelta, timezone
            now = datetime.now(timezone.utc)
            
            filtered_events = []
            if hours:
                cutoff_time = now - timedelta(hours=hours)
                for event in all_events:
                    try:
                        # Parse timestamp (handles timezone offsets)
                        event_dt = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                        if event_dt >= cutoff_time:
                            filtered_events.append(event)
                    except:
                        # If parsing fails, include the event
                        filtered_events.append(event)
            else:
                filtered_events = all_events
            
            # Apply limit if specified
            if limit and len(filtered_events) > limit:
                filtered_events = filtered_events[-limit:]  # Get most recent
            
            # Calculate statistics
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            total = len(filtered_events)
            today_count = 0
            latest_time = None
            by_type = {}
            
            for event in filtered_events:
                # Count by type
                event_type = event.get('type', 'unknown')
                by_type[event_type] = by_type.get(event_type, 0) + 1
                
                # Count today
                try:
                    event_dt = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                    if event_dt >= today_start:
                        today_count += 1
                    
                    # Track latest time
                    if latest_time is None or event_dt > latest_time:
                        latest_time = event_dt
                except:
                    pass
            
            # Latest timestamp (raw string so frontend can render in local timezone)
            latest_raw = None
            if filtered_events:
                # events are chronological; take last item
                latest_raw = filtered_events[-1].get('timestamp')

            statistics = {
                'total': total,
                'today': today_count,
                'by_type': by_type,
                'latest': latest_raw
            }
            
            return jsonify({
                'events': filtered_events,
                'count': total,
                'statistics': statistics
            })
        except Exception as e:
            logger.error(f"[API] Motion events error: {e}")
            return jsonify({'error': str(e), 'events': [], 'count': 0}), 500
    
    @app.route("/api/motion/delete/<event_id>", methods=["POST"])
    def api_delete_motion(event_id):
        """Delete motion event"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        if delete_motion_event(event_id):
            return jsonify({'ok': True})
        return jsonify({'ok': False}), 500
    
    @app.route("/api/motion/clear", methods=["POST"])
    def api_clear_motion():
        """Clear all motion events and delete video files"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            events_path = os.path.join(BASE_DIR, "logs", "motion_events.json")
            deleted_count = 0
            freed_mb = 0
            
            # Delete all video files first
            if os.path.exists(events_path):
                with open(events_path, 'r') as f:
                    events = json.load(f)
                
                for event in events:
                    # Check both old and new video_path locations
                    video_filename = event.get('video_path') or event.get('details', {}).get('video_path')
                    if video_filename:
                        # video_path is just filename, need to add recordings folder
                        full_path = os.path.join(BASE_DIR, "recordings", video_filename)
                        if os.path.exists(full_path):
                            try:
                                file_size = os.path.getsize(full_path) / (1024 * 1024)  # MB
                                os.remove(full_path)
                                deleted_count += 1
                                freed_mb += file_size
                                logger.debug(f"[MOTION] Deleted: {full_path}")
                            except Exception as e:
                                logger.error(f"[MOTION] Failed to delete {full_path}: {e}")
            
            # Clear events list
            with open(events_path, 'w') as f:
                json.dump([], f)
            
            logger.info(f"[MOTION] Cleared {deleted_count} events, freed {freed_mb:.2f}MB")
            return jsonify({'ok': True, 'deleted': deleted_count, 'freed_mb': round(freed_mb, 2)})
        except Exception as e:
            logger.error(f"[MOTION] Clear failed: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500
    
    @app.route("/api/motion/video/<video_filename>", methods=["GET"])
    def api_get_video(video_filename):
        """Stream or download motion event video"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            # Prevent directory traversal
            if '/' in video_filename or '\\' in video_filename or '..' in video_filename:
                return jsonify({'error': 'Invalid filename'}), 400
            
            cfg = get_config()
            video_path, encrypted = _resolve_clip_path(video_filename, cfg)
            if not video_path or not os.path.exists(video_path):
                return jsonify({'error': 'Video not found'}), 404
            
            if encrypted:
                temp_path = _decrypt_to_temp(video_path)
                if not temp_path:
                    return jsonify({'error': 'Decryption failed'}), 500

                @after_this_request
                def cleanup(response):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                    return response

                return send_file(temp_path, mimetype='video/mp4', as_attachment=False)

            return send_file(video_path, mimetype='video/mp4', as_attachment=False)
        except Exception as e:
            logger.error(f"[VIDEO] Stream error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route("/api/motion/video/<video_filename>/download", methods=["GET"])
    def api_download_video(video_filename):
        """Download motion event video"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            # Prevent directory traversal
            if '/' in video_filename or '\\' in video_filename or '..' in video_filename:
                return jsonify({'error': 'Invalid filename'}), 400
            
            cfg = get_config()
            video_path, encrypted = _resolve_clip_path(video_filename, cfg)
            if not video_path or not os.path.exists(video_path):
                return jsonify({'error': 'Video not found'}), 404
            
            if encrypted:
                temp_path = _decrypt_to_temp(video_path)
                if not temp_path:
                    return jsonify({'error': 'Decryption failed'}), 500

                @after_this_request
                def cleanup(response):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                    return response

                return send_file(temp_path, mimetype='video/mp4', as_attachment=True, download_name=video_filename.replace('.enc', ''))

            return send_file(video_path, mimetype='video/mp4', as_attachment=True, download_name=video_filename)
        except Exception as e:
            logger.error(f"[VIDEO] Download error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route("/api/motion/video/<video_filename>", methods=["DELETE"])
    def api_delete_video(video_filename):
        """Delete motion event video"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            # Prevent directory traversal
            if '/' in video_filename or '\\' in video_filename or '..' in video_filename:
                return jsonify({'error': 'Invalid filename'}), 400
            
            cfg = get_config()
            video_path, _ = _resolve_clip_path(video_filename, cfg)
            if not video_path or not os.path.exists(video_path):
                return jsonify({'error': 'Video not found'}), 404
            
            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            os.remove(video_path)
            
            # Update motion events to mark video as deleted
            events_path = os.path.join(BASE_DIR, "logs", "motion_events.json")
            if os.path.exists(events_path):
                with open(events_path, 'r') as f:
                    events = json.load(f)
                
                for event in events:
                    if event.get('video_path') == video_filename:
                        event['has_video'] = False
                        event['video_path'] = None
                
                with open(events_path, 'w') as f:
                    json.dump(events, f, indent=2)
            
            logger.info(f"[VIDEO] Deleted: {video_filename} ({file_size_mb:.1f}MB)")
            return jsonify({'ok': True, 'freed_mb': round(file_size_mb, 2)})
        except Exception as e:
            logger.error(f"[VIDEO] Delete error: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500

    def _get_share_record(token: str) -> dict:
        links = _load_share_links()
        record = links.get(token)
        if not record:
            return None
        try:
            expires_at = record.get("expires_at")
            if expires_at:
                expiry = datetime.fromisoformat(expires_at)
                if datetime.utcnow() > expiry:
                    links.pop(token, None)
                    _save_share_links(links)
                    return None
        except Exception:
            pass
        return record

    @app.route("/api/clips/share", methods=["POST"])
    def api_create_share_link():
        """Create a shareable link for a clip"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        cfg = get_config()
        security_cfg = _get_security_cfg(cfg)
        if not security_cfg.get('share_links_enabled', True):
            return jsonify({'error': 'Share links disabled'}), 403

        data = request.get_json() or {}
        filename = (data.get('filename') or '').strip()
        if not filename:
            return jsonify({'error': 'Filename required'}), 400

        clip_path, _ = _resolve_clip_path(filename, cfg)
        if not clip_path or not os.path.exists(clip_path):
            return jsonify({'error': 'Clip not found'}), 404

        token = secrets.token_urlsafe(32)
        expiry_hours = int(security_cfg.get('share_link_expiry_hours', 72))
        expires_at = (datetime.utcnow() + timedelta(hours=expiry_hours)).isoformat()

        links = _load_share_links()
        links[token] = {
            "filename": filename,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at
        }
        _save_share_links(links)

        share_url = f"{request.host_url.rstrip('/')}/share/{token}"
        return jsonify({"ok": True, "share_url": share_url, "expires_at": expires_at})

    @app.route("/api/clips/share/<token>", methods=["DELETE"])
    def api_revoke_share_link(token):
        """Revoke a share link"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        links = _load_share_links()
        if token in links:
            links.pop(token, None)
            _save_share_links(links)
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Not found"}), 404

    @app.route("/share/<token>", methods=["GET"])
    def share_view(token):
        record = _get_share_record(token)
        if not record:
            return render_template('access_blocked.html'), 404

        cfg = get_config()
        clip_path, encrypted = _resolve_clip_path(record.get("filename"), cfg)
        if not clip_path or not os.path.exists(clip_path):
            return render_template('access_blocked.html'), 404

        return render_template('share_view.html', token=token, filename=record.get("filename"), encrypted=encrypted)

    @app.route("/share/<token>/stream", methods=["GET"])
    def share_stream(token):
        record = _get_share_record(token)
        if not record:
            return jsonify({'error': 'Invalid share link'}), 404

        cfg = get_config()
        clip_path, encrypted = _resolve_clip_path(record.get("filename"), cfg)
        if not clip_path or not os.path.exists(clip_path):
            return jsonify({'error': 'Clip not found'}), 404

        if encrypted:
            temp_path = _decrypt_to_temp(clip_path)
            if not temp_path:
                return jsonify({'error': 'Decryption failed'}), 500

            @after_this_request
            def cleanup(response):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
                return response

            return send_file(temp_path, mimetype='video/mp4', as_attachment=False)

        return send_file(clip_path, mimetype='video/mp4', as_attachment=False)

    @app.route("/share/<token>/download", methods=["GET"])
    def share_download(token):
        record = _get_share_record(token)
        if not record:
            return jsonify({'error': 'Invalid share link'}), 404

        cfg = get_config()
        clip_path, encrypted = _resolve_clip_path(record.get("filename"), cfg)
        if not clip_path or not os.path.exists(clip_path):
            return jsonify({'error': 'Clip not found'}), 404

        if encrypted:
            temp_path = _decrypt_to_temp(clip_path)
            if not temp_path:
                return jsonify({'error': 'Decryption failed'}), 500

            @after_this_request
            def cleanup(response):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
                return response

            return send_file(temp_path, mimetype='video/mp4', as_attachment=True, download_name=record.get("filename", "clip.mp4").replace('.enc', ''))

        return send_file(clip_path, mimetype='video/mp4', as_attachment=True, download_name=record.get("filename", "clip.mp4"))
    
    @app.route("/api/config/update", methods=["POST"])
    def api_config_update():
        """Update configuration"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            data = request.get_json()
            cfg = get_config()
            previous_ssid = cfg.get('wifi_ssid', '')
            previous_password = cfg.get('wifi_password', '')
            
            # Update settings
            cfg['device_name'] = data.get('device_name', cfg.get('device_name'))
            cfg['device_location'] = data.get('device_location', cfg.get('device_location'))
            cfg['emergency_phone'] = data.get('emergency_phone', cfg.get('emergency_phone'))
            cfg['send_motion_to_emergency'] = data.get('send_motion_to_emergency', False)
            cfg['motion_record_enabled'] = data.get('motion_record_enabled', True)
            cfg['audio_record_on_motion'] = data.get('audio_record_on_motion', cfg.get('audio_record_on_motion', True))
            cfg['motion_record_duration'] = int(data.get('motion_record_duration', cfg.get('motion_record_duration', 10) or 10))
            cfg.setdefault('camera', {})
            cfg['camera']['stream_fps'] = max(5, min(30, int(data.get('camera_stream_fps', cfg.get('camera', {}).get('stream_fps', 20)) or 20)))

            incoming_quality = data.get('camera_stream_quality', cfg.get('camera', {}).get('stream_quality', 85))
            if isinstance(incoming_quality, str):
                try:
                    incoming_quality = int(incoming_quality)
                except Exception:
                    incoming_quality = 85
            cfg['camera']['stream_quality'] = max(50, min(100, int(incoming_quality)))

            cfg['storage_cleanup_days'] = int(data.get('storage_cleanup_days', 7))
            cfg['nanny_cam_enabled'] = data.get('nanny_cam_enabled', False)
            cfg['storage_encrypt'] = True
            cfg['storage_encrypted_dir'] = data.get('storage_encrypted_dir', cfg.get('storage_encrypted_dir', 'recordings_encrypted')) or 'recordings_encrypted'
            _apply_motion_preferences(
                cfg,
                sensitivity_mode=data.get('motion_sensitivity_mode', cfg.get('motion_sensitivity_mode', 'balanced')),
                trigger_mode=data.get('motion_trigger_mode', cfg.get('motion_trigger_mode', 'all_motion')),
                clip_mode=data.get('motion_clip_mode', cfg.get('motion_clip_mode', 'auto')),
            )

            # WiFi settings
            cfg['wifi_enabled'] = data.get('wifi_enabled', cfg.get('wifi_enabled', True))
            cfg['wifi_ssid'] = data.get('wifi_ssid', cfg.get('wifi_ssid', ''))
            cfg['wifi_password'] = data.get('wifi_password', cfg.get('wifi_password', ''))
            cfg['wifi_country'] = data.get('wifi_country', cfg.get('wifi_country', 'US'))
            
            # SMS configuration
            cfg['sms_enabled'] = data.get('sms_enabled', False)
            cfg['sms_phone_to'] = data.get('sms_phone_to', '')
            cfg['sms_api_url'] = data.get('sms_api_url', '')
            cfg['sms_api_key'] = data.get('sms_api_key', '')
            cfg['sms_rate_limit'] = int(data.get('sms_rate_limit', 5))

            # Keep existing provider credentials if user only updates number/rate.
            if not cfg['sms_api_url']:
                cfg['sms_api_url'] = cfg.get('notifications', {}).get('sms', {}).get('generic_http', {}).get('url', '')
            if not cfg['sms_api_key']:
                cfg['sms_api_key'] = cfg.get('notifications', {}).get('sms', {}).get('generic_http', {}).get('auth_token', '')

            sms_cfg = _get_sms_cfg(cfg)
            requested_provider = data.get('sms_provider')
            if requested_provider:
                sms_cfg['provider'] = requested_provider

            if sms_cfg.get('enabled') and sms_cfg.get('provider') == 'generic_http':
                parsed = urlparse((cfg.get('sms_api_url') or '').strip())
                host = (parsed.hostname or '').strip().lower()
                local_hosts = {'localhost', '127.0.0.1', '0.0.0.0'}
                device_ip = (request.host or '').split(':')[0].strip().lower()
                if not parsed.scheme or not host or host in local_hosts or (device_ip and host == device_ip):
                    return jsonify({
                        'ok': False,
                        'error': 'Text Delivery URL must be an external SMS gateway, not this camera URL.'
                    }), 400

            sms_destination = (cfg['sms_phone_to'] or (cfg.get('emergency_phone', '') if cfg.get('send_motion_to_emergency') else '')).strip()
            sms_cfg['enabled'] = bool(cfg['sms_enabled'] and sms_destination)
            sms_cfg['phone_to'] = sms_destination
            sms_cfg['rate_limit_minutes'] = cfg['sms_rate_limit']
            sms_cfg['motion_threshold'] = 0.0
            sms_cfg.setdefault('generic_http', {})
            sms_cfg['generic_http']['url'] = cfg['sms_api_url']
            sms_cfg['generic_http']['auth_token'] = cfg['sms_api_key']
            cfg['notifications']['sms'] = sms_cfg

            # Cloud sync configuration
            cfg['gdrive_enabled'] = data.get('gdrive_enabled', cfg.get('gdrive_enabled', False))
            cfg['gdrive_folder_id'] = data.get('gdrive_folder_id', cfg.get('gdrive_folder_id', ''))

            # Security settings
            security_cfg = _ensure_security_cfg(cfg)
            security_cfg['tailscale_only'] = data.get('tailscale_only', security_cfg.get('tailscale_only', True))
            security_cfg['share_links_enabled'] = data.get('share_links_enabled', security_cfg.get('share_links_enabled', True))
            security_cfg['share_link_expiry_hours'] = int(data.get('share_link_expiry_hours', security_cfg.get('share_link_expiry_hours', 72)))
            cfg['security'] = security_cfg

            # Keep nested storage settings in sync for other modules
            cfg.setdefault('storage', {})
            cfg['storage']['retention_days'] = int(data.get('storage_cleanup_days', 7))
            cfg['storage']['encrypt'] = True
            cfg['storage']['encrypted_dir'] = cfg.get('storage_encrypted_dir', 'recordings_encrypted')
            
            save_config(cfg)
            from src.core import reset_sms_notifier
            reset_sms_notifier()
            if cfg.get('wifi_ssid', '') != previous_ssid or cfg.get('wifi_password', '') != previous_password:
                rotate_enrollment_key(reason='wifi_change')
                logger.warning("[SECURITY] Enrollment key rotated due to WiFi/config change")
            logger.info("[CONFIG] Settings updated")
            return jsonify({'ok': True, 'message': 'Configuration saved'})
        except Exception as e:
            logger.error(f"[CONFIG] Update failed: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500

    @app.route("/api/nanny-cam/status", methods=["GET"])
    def api_nanny_status():
        """Get nanny cam enabled status - no auth required"""
        cfg = get_config()
        enabled = cfg.get('nanny_cam_enabled', False)
        return jsonify({'enabled': enabled})

    @app.route("/api/nanny-cam/toggle", methods=["POST"])
    def api_nanny_toggle():
        """Toggle nanny cam mode (disables motion logging/recording when on) - no auth required"""
        try:
            data = request.get_json()
            enabled = bool(data.get('enabled', False))
            cfg = get_config()
            cfg['nanny_cam_enabled'] = enabled
            save_config(cfg)
            return jsonify({'ok': True, 'enabled': enabled})
        except Exception as e:
            logger.error(f"[NANNY] Toggle failed: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500
    
    @app.route("/api/emergency/alert", methods=["POST"])
    def api_emergency_alert():
        """Send emergency alert"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            data = request.get_json()
            message = data.get('message', 'Emergency alert')
            event_type = data.get('type', 'security_alert')
            
            cfg = get_config()
            emergency_phone = cfg.get('emergency_phone')
            device_name = cfg.get('device_name', 'ME_CAM')
            
            if not emergency_phone:
                return jsonify({'ok': False, 'error': 'No emergency number configured'}), 400
            
            # Log as motion event
            log_motion_event(event_type=event_type, confidence=1.0, 
                           details={'emergency': True, 'message': message})
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            alert_msg = f"🚨 ALERT: {message}\nDevice: {device_name}\nTime: {timestamp}"
            
            logger.warning(f"[EMERGENCY] {alert_msg}")
            
            return jsonify({
                'ok': True,
                'message': 'Emergency alert triggered',
                'phone': emergency_phone
            })
        except Exception as e:
            logger.error(f"[EMERGENCY] Alert failed: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500
    
    @app.route("/api/motion/send", methods=["POST"])
    def api_motion_send():
        """Send motion event via SMS or notification"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            data = request.get_json()
            event_id = data.get('event_id')
            phone = data.get('phone', '')
            media_type = data.get('media_type', 'image')
            
            cfg = get_config()
            
            # Get event details
            events_path = os.path.join(BASE_DIR, "logs", "motion_events.json")
            events = []
            if os.path.exists(events_path):
                with open(events_path, 'r') as f:
                    events = json.load(f)
            
            event = next((e for e in events if e.get('id') == event_id), None)
            if not event:
                return jsonify({'ok': False, 'error': 'Event not found'}), 404
            
            # Format timestamp for EST (Brockport, NY)
            from datetime import datetime
            event_time = event.get('timestamp', 'Unknown time')
            device_name = cfg.get('device_name', 'ME_CAM')
            
            message = f"🎥 Motion Alert from {device_name}\n"
            message += f"Time: {event_time}\n"
            message += f"Type: {event.get('type', 'motion').upper()}\n"
            message += f"Confidence: {int(event.get('confidence', 0) * 100)}%"
            
            sms_cfg = _get_sms_cfg(cfg)
            recipient = (
                phone
                or sms_cfg.get('phone_to')
                or cfg.get('sms_phone_to', '')
                or (cfg.get('emergency_phone', '') if cfg.get('send_motion_to_emergency') else '')
            ).strip()

            if not sms_cfg.get('enabled'):
                logger.info("[SMS] SMS notifications are disabled")
                return jsonify({'ok': False, 'error': 'SMS notifications are disabled'}), 400

            if not recipient:
                return jsonify({'ok': False, 'error': 'No destination phone configured'}), 400

            from src.core import get_sms_notifier
            notifier = get_sms_notifier()
            accepted = notifier.send_sms(recipient, message)

            if not accepted:
                return jsonify({'ok': False, 'error': 'SMS send rejected (disabled or rate-limited)'}), 429

            logger.info(f"[SMS] Message accepted for delivery to {recipient}")
            return jsonify({
                'ok': True,
                'message': 'SMS accepted for delivery',
                'phone': recipient
            })
        except Exception as e:
            logger.error(f"[MOTION] Send failed: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500
    
    @app.route("/api/storage/cleanup", methods=["POST"])
    def api_storage_cleanup():
        """Clean up old recordings"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            data = request.get_json()
            days = int(data.get('days', 7))
            
            result = cleanup_old_recordings(days)
            logger.info(f"[STORAGE] Cleanup: {result['deleted']} files, {result['freed_mb']}MB freed")
            
            return jsonify({
                'ok': True,
                'deleted': result['deleted'],
                'freed_mb': result['freed_mb']
            })
        except Exception as e:
            logger.error(f"[STORAGE] Cleanup failed: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500
    
    # ============= FRAME GENERATORS =============
    
    def generate_frames():
        """Generate camera frames with motion detection and video recording"""
        import cv2
        import numpy as np
        from PIL import Image
        import io
        from collections import deque
        from threading import Thread
        
        last_frame = None
        motion_cooldown_until = 0.0
        # Circular buffer for pre-motion frames (2-3 seconds at 20 FPS = 40-60 frames)
        frame_buffer = deque(maxlen=60)
        buffer_size = 60 if pi_model.get('ram_mb', 1024) <= 512 else 120
        frame_buffer = deque(maxlen=buffer_size)
        
        recording = False
        frame_count = 0
        recording_frames = []
        recording_start = None
        no_frame_count = 0
        motion_streak = 0
        stream_error_count = 0
        
        def save_video_async(frames_list, event_id, duration_sec=5):
            """Save video in background thread to avoid blocking stream"""
            try:
                if not frames_list:
                    logger.warning("[MOTION] No frames available for video")
                    return
                
                recordings_path = os.path.join(BASE_DIR, "recordings")
                os.makedirs(recordings_path, exist_ok=True)
                
                # Get first frame dimensions
                h, w = frames_list[0].shape[:2]
                
                # Create video file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                video_filename = f"motion_{timestamp}.mp4"
                video_path = os.path.join(recordings_path, video_filename)
                
                # Use H.264 codec for browser compatibility
                fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 codec
                fps = 20.0
                out = cv2.VideoWriter(video_path, fourcc, fps, (w, h))
                
                if not out.isOpened():
                    logger.warning("[MOTION] H.264 not available, using mp4v")
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    out = cv2.VideoWriter(video_path, fourcc, fps, (w, h))
                
                if not out.isOpened():
                    logger.error("[MOTION] Could not open video writer")
                    return
                
                # Write pre-motion frames first
                for frame in frames_list:
                    out.write(frame)

                # Continue appending live frames without buffering entire clip in RAM
                target_frames = max(len(frames_list), int(max(3, duration_sec) * fps))
                appended_frames = len(frames_list)
                append_deadline = time.time() + max(3, duration_sec) + 1

                while appended_frames < target_frames and time.time() < append_deadline:
                    next_frame = None
                    if hasattr(camera, 'get_jpeg_frame'):
                        live_jpeg = camera.get_jpeg_frame()
                        if live_jpeg:
                            live_np = np.frombuffer(live_jpeg, np.uint8)
                            next_frame = cv2.imdecode(live_np, cv2.IMREAD_COLOR)
                    elif hasattr(camera, 'capture_array'):
                        live_arr = camera.capture_array()
                        if live_arr is not None:
                            next_frame = cv2.cvtColor(live_arr, cv2.COLOR_RGB2BGR)

                    if next_frame is not None:
                        out.write(next_frame)
                        appended_frames += 1

                    time.sleep(1.0 / fps)
                
                out.release()
                
                cfg = get_config()
                final_path, encrypted = _encrypt_clip_if_enabled(video_path, cfg)
                final_name = os.path.basename(final_path)
                file_size = os.path.getsize(final_path) / (1024 * 1024)
                logger.success(f"[MOTION] Video saved: {final_name} ({file_size:.1f}MB, {appended_frames} frames)")
                
                # Update motion event with video path
                try:
                    events_path = os.path.join(BASE_DIR, "logs", "motion_events.json")
                    if os.path.exists(events_path):
                        with open(events_path, 'r') as f:
                            events = json.load(f)
                        
                        # Find the event by ID and update it
                        updated = False
                        for event in events:
                            if event.get('id') == event_id:
                                event['has_video'] = True
                                event['video_path'] = final_name
                                if 'details' not in event:
                                    event['details'] = {}
                                event['details']['video_path'] = final_name
                                event['details']['mode'] = 'lite'
                                event['details']['encrypted'] = encrypted
                                upload_id = _queue_cloud_upload(final_path, meta={
                                    "event_id": event_id,
                                    "type": event.get("type"),
                                    "timestamp": event.get("timestamp")
                                })
                                if upload_id:
                                    event['details']['cloud_upload_id'] = upload_id
                                elif not is_wifi_connected():
                                    # Preserve detections while offline and sync/upload later.
                                    queue_offline_clip(final_name, {
                                        "event_id": event_id,
                                        "type": event.get("type"),
                                        "timestamp": event.get("timestamp")
                                    })
                                updated = True
                                logger.info(f"[MOTION] Updated event {event_id} with video: {final_name}")
                                break
                        
                        if updated:
                            with open(events_path, 'w') as f:
                                json.dump(events, f, indent=2)
                        else:
                            logger.warning(f"[MOTION] Could not find event {event_id} to update")
                except Exception as e:
                    logger.error(f"[MOTION] Could not update event metadata: {e}")
            
            except Exception as e:
                logger.error(f"[MOTION] Video save error: {e}")
        
        while True:
            try:
                maybe_flush_queues()

                if camera is None:
                    break
                
                # Check if using RpicamStreamer or picamera2
                if hasattr(camera, 'get_jpeg_frame'):
                    # RpicamStreamer - get JPEG directly
                    jpeg_bytes = camera.get_jpeg_frame()
                    if not jpeg_bytes:
                        no_frame_count += 1
                        if no_frame_count > 50 and hasattr(camera, 'restart'):
                            logger.warning("[CAMERA] Stream stalled, restarting rpicam streamer...")
                            try:
                                if camera.restart():
                                    no_frame_count = 0
                                    logger.success("[CAMERA] rpicam streamer restarted")
                            except Exception as restart_error:
                                logger.error(f"[CAMERA] Restart failed: {restart_error}")
                        time.sleep(0.05)
                        continue

                    no_frame_count = 0
                    stream_error_count = 0
                    
                    frame_count += 1
                    
                    # Decode JPEG for motion detection and buffering
                    try:
                        nparr = np.frombuffer(jpeg_bytes, np.uint8)
                        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        
                        if frame is not None:
                            # Add to frame buffer for pre-motion recording
                            frame_buffer.append(frame.copy())
                            
                            # Motion detection (every frame for fast response)
                            if True:
                                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                                
                                if last_frame is not None:
                                    diff = cv2.absdiff(last_frame, gray)
                                    blur = cv2.GaussianBlur(diff, (11, 11), 0)
                                    _, thresh = cv2.threshold(blur, 28, 255, cv2.THRESH_BINARY)
                                    thresh = cv2.dilate(thresh, None, iterations=2)
                                    thresh = cv2.erode(thresh, None, iterations=1)

                                    motion_pixels = cv2.countNonZero(thresh)
                                    total_pixels = gray.shape[0] * gray.shape[1]
                                    motion_ratio = motion_pixels / total_pixels
                                    
                                    cfg = get_config()
                                    motion_settings = _get_motion_profile_settings(cfg)
                                    motion_threshold = motion_settings['threshold']
                                    min_area = motion_settings['min_area']
                                    trigger_mode = motion_settings['trigger_mode']
                                    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                                    significant_contours = sum(1 for c in contours if cv2.contourArea(c) >= min_area)
                                    trigger_now = motion_ratio > motion_threshold and significant_contours > 0
                                    motion_streak = (motion_streak + 1) if trigger_now else max(0, motion_streak - 1)
                                    
                                    cfg = get_config()
                                    nanny_cam = cfg.get('nanny_cam_enabled', False)
                                    motion_enabled = cfg.get('motion_record_enabled', True)

                                    # Motion detected and not in cooldown
                                    cooldown_active = time.time() < motion_cooldown_until
                                    if motion_streak >= 1 and not cooldown_active and not recording:
                                        if nanny_cam or not motion_enabled:
                                            motion_streak = 0
                                        else:
                                            logger.info(f"[MOTION] Motion detected: {motion_ratio*100:.1f}% pixels")

                                            # Log motion event and get event_id
                                            event_data = log_motion_event('motion', motion_ratio, {
                                                'threshold': motion_threshold,
                                                'contours': significant_contours,
                                                'motion_pixels': motion_pixels,
                                                'trigger_mode': trigger_mode,
                                                'sensitivity_mode': motion_settings['sensitivity_mode']
                                            })
                                            event_id = event_data.get('id') if event_data else f"evt_{int(time.time()*1000)}"

                                            # Keep a small pre-motion buffer on Pi Zero to reduce memory pressure
                                            pre_frames = list(frame_buffer)[-24:] if pi_model.get('ram_mb', 1024) <= 512 else list(frame_buffer)
                                            duration_sec = _auto_motion_clip_duration(cfg, motion_ratio=motion_ratio, contour_count=significant_contours)
                                            video_thread = Thread(
                                                target=save_video_async,
                                                args=(pre_frames, event_id, duration_sec),
                                                daemon=True
                                            )
                                            video_thread.start()

                                            recording = True
                                            recording_start = time.time()
                                            cooldown_seconds = float(cfg.get('motion_cooldown_seconds', 1.0) or 1.0)
                                            cooldown_seconds = min(10.0, max(0.2, cooldown_seconds))
                                            motion_cooldown_until = time.time() + cooldown_seconds
                                            motion_streak = 0

                                            logger.info(f"[MOTION] Recording started with {len(pre_frames)} pre-motion frames")

                                            # Keep SMS behavior consistent with picamera motion path.
                                            if cfg.get('sms_enabled') and cfg.get('send_motion_to_emergency'):
                                                phone = cfg.get('sms_phone_to') or cfg.get('emergency_phone')
                                                if phone:
                                                    try:
                                                        from src.core import get_sms_notifier
                                                        sms_notifier = get_sms_notifier()
                                                        device_name = cfg.get('device_name', 'ME Camera')
                                                        location = cfg.get('device_location', 'Unknown')
                                                        timestamp_txt = datetime.now().strftime("%I:%M:%S %p")
                                                        msg = f"🚨 {device_name}: Motion detected at {location} - {timestamp_txt}"
                                                        sms_notifier.send_sms(phone, msg)
                                                        logger.success(f"[SMS] Motion alert sent to {phone}")
                                                    except Exception as sms_error:
                                                        logger.error(f"[SMS] Notification failed: {sms_error}")
                                                        queue_notification_retry(phone, msg, reason="send_failed")
                                
                                last_frame = gray
                    except Exception as e:
                        logger.debug(f"[MOTION] Frame processing error: {e}")
                    
                    # Clear recording flag after duration; saving happens in background thread
                    if recording:
                        if time.time() - recording_start > 5:
                            recording = False
                            logger.info("[MOTION] Recording window complete")
                    
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
                    time.sleep(0.03)  # ~33 FPS to reduce CPU and memory pressure on Pi Zero
                    continue
                
                # picamera2 - get array and convert
                frame = camera.capture_array()
                if camera_rotation_mode == 'rotate_180':
                    frame = cv2.rotate(frame, cv2.ROTATE_180)
                elif camera_rotation_mode == 'rotate_90':
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                elif camera_rotation_mode == 'rotate_270':
                    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                elif camera_rotation_mode == 'flip_horizontal':
                    frame = cv2.flip(frame, 1)
                elif camera_rotation_mode == 'flip_vertical':
                    frame = cv2.flip(frame, 0)
                frame_count += 1  # BUG FIX #3: Increment frame counter
                
                # Motion detection - check every 2nd frame for performance
                # BUG FIX: Changed logic - now processes motion detection on EVERY frame for responsiveness
                if frame_count % 2 == 0:  # Skip buffering on even frames
                    # Process frame for motion detection (every 2nd frame)
                    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                else:
                    # Just buffer the frame and stream it
                    frame_buffer.append(frame.copy())
                    if len(frame_buffer) > buffer_size:
                        frame_buffer.pop(0)
                    
                    img = Image.fromarray(frame)
                    buf = io.BytesIO()
                    img.save(buf, format='JPEG', quality=85)
                    jpeg_bytes = buf.getvalue()
                    
                    # BUG FIX #5: Explicit cleanup for PIL objects
                    del img
                    buf.close()
                    del buf
                    
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
                    time.sleep(0.033)
                    continue
                
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                
                # Always add current frame to buffer
                frame_buffer.append(frame.copy())
                if len(frame_buffer) > buffer_size:
                    frame_buffer.pop(0)  # Remove oldest
                
                # Motion detection - check every frame for responsiveness
                if time.time() >= motion_cooldown_until:
                    if last_frame is not None and not recording:
                        # Advanced motion detection - filter out shadows and lighting
                        diff = cv2.absdiff(last_frame, gray)
                        
                        # Apply Gaussian blur to reduce noise and small changes
                        blurred_diff = cv2.GaussianBlur(diff, (21, 21), 0)
                        
                        # Threshold to get significant changes only
                        _, thresh = cv2.threshold(blurred_diff, 25, 255, cv2.THRESH_BINARY)
                        
                        # Calculate metrics
                        mean_diff = np.mean(diff)
                        max_diff = np.max(diff)
                        motion_pixels = np.sum(thresh > 0)  # Count pixels with significant change
                        total_pixels = thresh.shape[0] * thresh.shape[1]
                        motion_percent = (motion_pixels / total_pixels) * 100
                        
                        # Detect edges to distinguish objects from shadows
                        edges = cv2.Canny(gray, 50, 150)
                        edge_motion = np.sum(edges > 0)
                        
                        # Contour-based filtering to ignore tiny movements (leaves, shadows)
                        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        cfg = get_config()
                        motion_settings = _get_motion_profile_settings(cfg)
                        trigger_mode = motion_settings['trigger_mode']
                        min_area = motion_settings['min_area']
                        allowed_labels = []
                        for c in contours:
                            area = cv2.contourArea(c)
                            if area < min_area:
                                continue
                            x, y, w, h = cv2.boundingRect(c)
                            aspect = w / float(h)
                            if 0.3 <= aspect <= 0.8:
                                allowed_labels.append("person")
                            elif 0.8 < aspect <= 3.5:
                                allowed_labels.append("vehicle")

                        if trigger_mode == 'people_only':
                            label_match = 'person' in allowed_labels
                        elif trigger_mode == 'people_vehicles':
                            label_match = len(allowed_labels) > 0
                        else:
                            label_match = len(contours) > 0

                        motion = (
                            max_diff > motion_settings['max_diff'] and
                            motion_percent > motion_settings['motion_percent'] and
                            edge_motion > motion_settings['edge_motion'] and
                            mean_diff > motion_settings['mean_diff'] and
                            label_match
                        )
                        
                        if motion:
                            nanny_cam = cfg.get('nanny_cam_enabled', False)

                            if not nanny_cam and cfg.get('motion_record_enabled', True):
                                logger.info(f"[MOTION] Motion detected (mean:{mean_diff:.1f}, max:{max_diff:.1f})")
                                recording = True
                                try:
                                    # Save clip using buffered frames + continue recording
                                    clip_duration = _auto_motion_clip_duration(
                                        cfg,
                                        contour_count=len(contours),
                                        mean_diff=mean_diff,
                                        motion_percent=motion_percent,
                                    )
                                    clip_result = save_motion_clip_buffered(camera, frame_buffer.copy(), duration_sec=clip_duration)
                                    video_path = clip_result.get("clip_name") if isinstance(clip_result, dict) else clip_result
                                    if not video_path:
                                        # Fallback to snapshot if clip fails
                                        video_path = save_motion_snapshot(frame)

                                    detected_label = allowed_labels[0] if allowed_labels else "motion"
                                    event = log_motion_event(
                                        event_type=detected_label,
                                        confidence=1.0,
                                        details={
                                            "mode": "lite",
                                            "video_path": video_path,
                                            "encrypted": bool(video_path and str(video_path).endswith('.enc')),
                                            "audio_embedded": bool(isinstance(clip_result, dict) and clip_result.get("audio_embedded")),
                                            "audio_sidecar": (clip_result.get("audio_sidecar") if isinstance(clip_result, dict) else None),
                                            "mean_diff": float(mean_diff),
                                            "max_diff": float(max_diff),
                                            "label": detected_label,
                                            "contours": len(allowed_labels)
                                        }
                                    )
                                    try:
                                        clip_path, _ = _resolve_clip_path(video_path, cfg)
                                        upload_id = _queue_cloud_upload(clip_path, meta={
                                            "event_id": event.get("id"),
                                            "type": event.get("type"),
                                            "timestamp": event.get("timestamp")
                                        }) if clip_path else None
                                        if upload_id:
                                            events_path = os.path.join(BASE_DIR, "logs", "motion_events.json")
                                            if os.path.exists(events_path):
                                                with open(events_path, 'r') as f:
                                                    events = json.load(f)
                                                for evt in events:
                                                    if evt.get('id') == event.get('id'):
                                                        evt.setdefault('details', {})['cloud_upload_id'] = upload_id
                                                        break
                                                with open(events_path, 'w') as f:
                                                    json.dump(events, f, indent=2)
                                    except Exception as e:
                                        logger.warning(f"[CLOUD] Auto upload queue failed: {e}")
                                    # If WiFi is down, remember this clip to sync/notify later
                                    if not is_wifi_connected():
                                        queue_offline_clip(video_path, {
                                            "event_id": event.get("id"),
                                            "type": event.get("type"),
                                            "timestamp": event.get("timestamp")
                                        })
                                    
                                    # Send SMS notification if enabled
                                    if cfg.get('sms_enabled') and cfg.get('send_motion_to_emergency'):
                                        try:
                                            from src.core import get_sms_notifier
                                            sms_notifier = get_sms_notifier()
                                            phone = cfg.get('sms_phone_to') or cfg.get('emergency_phone')
                                            if phone:
                                                device_name = cfg.get('device_name', 'ME Camera')
                                                location = cfg.get('device_location', 'Unknown')
                                                timestamp = datetime.now().strftime("%I:%M:%S %p")
                                                msg = f"🚨 {device_name}: Motion detected at {location} - {timestamp}"
                                                sms_notifier.send_sms(phone, msg)
                                                logger.success(f"[SMS] Motion alert sent to {phone}")
                                        except Exception as sms_error:
                                            logger.error(f"[SMS] Notification failed: {sms_error}")
                                            if phone:
                                                queue_notification_retry(phone, msg, reason="send_failed")
                                except Exception as e:
                                    logger.error(f"[MOTION] Recording error: {e}")
                                finally:
                                    recording = False

                            # Cooldown: 20 frames (~1 sec) to avoid duplicate triggers
                            cooldown_seconds = float(cfg.get('motion_cooldown_seconds', 1.0) or 1.0)
                            cooldown_seconds = min(10.0, max(0.2, cooldown_seconds))
                            motion_cooldown_until = time.time() + cooldown_seconds
                
                last_frame = gray
                
                # Convert to JPEG
                img = Image.fromarray(frame)
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=85)
                jpeg_bytes = buf.getvalue()
                
                # BUG FIX #5: Explicit cleanup for PIL objects
                del img
                buf.close()
                del buf
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
                
                time.sleep(0.033)  # ~30 FPS for better responsiveness
            except Exception as e:
                stream_error_count += 1
                logger.warning(f"[CAMERA] Frame error ({stream_error_count}): {e}")
                if stream_error_count >= 20 and hasattr(camera, 'restart'):
                    try:
                        logger.warning("[CAMERA] Repeated frame errors, restarting camera backend...")
                        if camera.restart():
                            stream_error_count = 0
                            no_frame_count = 0
                            logger.success("[CAMERA] Camera backend restarted")
                    except Exception as restart_error:
                        logger.error(f"[CAMERA] Backend restart failed: {restart_error}")
                time.sleep(0.1)
                continue
    
    def generate_test_pattern():
        """Generate test pattern"""
        from PIL import Image, ImageDraw
        import io
        
        while True:
            img = Image.new('RGB', (640, 480), color=(40, 40, 40))
            draw = ImageDraw.Draw(img)
            draw.text((120, 200), "TEST MODE\nPi Zero 2W\n512MB RAM", fill=(255, 255, 255))
            
            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            jpeg_bytes = buf.getvalue()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
            
            time.sleep(0.1)
    
    # ============= V3.0 WEBRTC ROUTES =============
    
    @app.route("/api/webrtc/offer", methods=["POST"])
    def api_webrtc_offer():
        """Handle WebRTC offer from client"""
        if not WEBRTC_AVAILABLE:
            return jsonify({'error': 'WebRTC not available'}), 503
        
        if 'user' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        try:
            data = request.get_json()
            if not data or 'sdp' not in data or 'type' not in data:
                return jsonify({'error': 'Invalid SDP offer'}), 400
            
            logger.info("[WebRTC] Received SDP offer from client")
            
            # Create answer (async operation)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            answer = loop.run_until_complete(webrtc_streamer.handle_offer(data))
            loop.close()
            
            logger.success("[WebRTC] SDP answer created")
            return jsonify(answer)
            
        except Exception as e:
            logger.error(f"[WebRTC] Offer handling failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route("/api/webrtc/ice", methods=["POST"])
    def api_webrtc_ice():
        """Handle ICE candidate from client"""
        if not WEBRTC_AVAILABLE:
            return jsonify({'error': 'WebRTC not available'}), 503
        
        if 'user' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        try:
            data = request.get_json()
            if not data or 'candidate' not in data:
                return jsonify({'error': 'Invalid ICE candidate'}), 400
            
            logger.debug("[WebRTC] Received ICE candidate from client")
            # Add ICE candidate (implementation depends on WebRTC peer)
            return jsonify({'ok': True})
            
        except Exception as e:
            logger.error(f"[WebRTC] ICE handling failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route("/api/webrtc/status", methods=["GET"])
    def api_webrtc_status():
        """Get WebRTC connection status"""
        return jsonify({
            'available': WEBRTC_AVAILABLE,
            'connected': webrtc_streamer.pc.connectionState == 'connected' if webrtc_streamer else False,
            'ice_state': webrtc_streamer.pc.iceConnectionState if webrtc_streamer else 'new'
        })
    
    # ============= V3.0 REMOTE ACCESS ROUTES =============
    
    @app.route("/api/remote/tailscale/status", methods=["GET"])
    def api_tailscale_status():
        """Get Tailscale VPN status"""
        if not REMOTE_ACCESS_AVAILABLE:
            return jsonify({'error': 'Remote access not available'}), 503
        
        try:
            helper = TailscaleHelper()
            return jsonify({
                'installed': helper.is_installed(),
                'enabled': helper.is_enabled() if helper.is_installed() else False,
                'ip': helper.get_tailscale_ip() if helper.is_installed() else None,
                'status': helper.get_status() if helper.is_installed() else None
            })
        except Exception as e:
            logger.error(f"[Tailscale] Status check failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route("/api/remote/cloudflare/status", methods=["GET"])
    def api_cloudflare_status():
        """Get Cloudflare tunnel status"""
        if not REMOTE_ACCESS_AVAILABLE:
            return jsonify({'error': 'Remote access not available'}), 503
        
        try:
            helper = CloudflareHelper()
            return jsonify({
                'installed': helper.is_installed()
            })
        except Exception as e:
            logger.error(f"[Cloudflare] Status check failed: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route("/api/remote/info", methods=["GET"])
    def api_remote_info():
        """Get remote access information"""
        import socket
        
        info = {
            'local_ip': None,
            'tailscale_ip': None,
            'webrtc_available': WEBRTC_AVAILABLE,
            'vpn_compatible': True
        }
        
        # Get local IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info['local_ip'] = s.getsockname()[0]
            s.close()
        except:
            pass
        
        # Get Tailscale IP if available
        if REMOTE_ACCESS_AVAILABLE:
            try:
                helper = TailscaleHelper()
                if helper.is_installed():
                    info['tailscale_ip'] = helper.get_tailscale_ip()
            except:
                pass
        
        return jsonify(info)
    
    # ============= SYSTEM ROUTES =============
    
    @app.route("/api/system/reboot", methods=["POST"])
    def api_system_reboot():
        """Reboot the device"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            import subprocess
            logger.warning("[SYSTEM] Reboot requested by user")
            # Schedule reboot in 5 seconds to allow response to be sent
            subprocess.Popen(['sudo', 'shutdown', '-r', '+1'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return jsonify({'ok': True, 'message': 'Device rebooting in 1 minute...'})
        except Exception as e:
            logger.error(f"[SYSTEM] Reboot failed: {e}")
            return jsonify({'ok': False, 'error': str(e)}), 500
    
    # ============= V3.0 REMOTE ACCESS & WEBRTC =============
    
    @app.route("/api/v3/status", methods=["GET"])
    def api_v3_status():
        """Check v3.0 feature availability"""
        status = {
            "version": "3.0",
            "webrtc": False,
            "ai_detection": False,
            "remote_access": False
        }
        
        # Check WebRTC
        try:
            from src.streaming.webrtc_peer import WebRTCStreamer
            status["webrtc"] = True
        except:
            pass
        
        # Check AI detection
        try:
            from src.detection.tflite_detector import SmartMotionDetector
            status["ai_detection"] = True
        except:
            pass
        
        # Check remote access
        try:
            from src.networking.remote_access import TailscaleHelper
            status["remote_access"] = True
        except:
            pass
        
        return jsonify(status)
    
    @app.route("/api/remote/access-info", methods=["GET"])
    def api_remote_access_info():
        """Get information for remote access from different networks"""
        import socket
        
        info = {
            "local_ip": None,
            "tailscale_ip": None,
            "hostname": socket.gethostname(),
            "vpn_ready": True,
            "different_network_ready": True,
            "ports": {
                "http": 8080,
                "https": 8443
            },
            "access_methods": [
                "local_network",
                "tailscale_vpn",
                "port_forwarding",
                "cloudflare_tunnel"
            ]
        }
        
        # Get local IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info["local_ip"] = s.getsockname()[0]
            s.close()
        except:
            pass
        
        # Try to get Tailscale IP
        try:
            from src.networking.remote_access import TailscaleHelper
            helper = TailscaleHelper()
            if helper.is_installed():
                ts_ip = helper.get_tailscale_ip()
                if ts_ip:
                    info["tailscale_ip"] = ts_ip
                    info["tailscale_enabled"] = True
        except:
            info["tailscale_enabled"] = False
        
        return jsonify(info)
    
    @app.route("/api/test/remote", methods=["GET"])
    def api_test_remote():
        """Test endpoint to verify remote access from different networks/VPNs"""
        import socket
        
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        return jsonify({
            "success": True,
            "message": "Remote access working! You can connect from any network.",
            "client_ip": client_ip,
            "user_agent": user_agent,
            "server_time": datetime.now().isoformat(),
            "server_hostname": socket.gethostname(),
            "authenticated": 'user' in session,
            "connection_type": "vpn" if "100." in client_ip else "direct",
            "tips": {
                "local": f"http://{info.get('local_ip', 'LOCAL_IP')}:8080",
                "tailscale": "Install Tailscale for secure VPN access",
                "port_forward": "Configure port forwarding on your router"
            }
        })
    
    @app.route("/api/tailscale/install", methods=["POST"])
    def api_tailscale_install():
        """Guide for installing Tailscale VPN"""
        if 'user' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        return jsonify({
            "instructions": [
                "SSH into your device",
                "Run: curl -fsSL https://tailscale.com/install.sh | sh",
                "Run: sudo tailscale up",
                "Follow the authentication link",
                "Access camera from anywhere using Tailscale IP"
            ],
            "status_endpoint": "/api/remote/access-info",
            "documentation": "https://tailscale.com/kb/1017/install/"
        })
    
    return app
