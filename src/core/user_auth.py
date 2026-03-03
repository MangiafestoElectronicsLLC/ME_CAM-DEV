import json
import os
import secrets
import hmac
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from loguru import logger
from .config_manager import get_config, save_config

USERS_FILE = "config/users.json"

def _ensure_users_file():
    """Create users file if it doesn't exist."""
    if not os.path.exists(USERS_FILE):
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f, indent=2)
        logger.info("[AUTH] Created empty users file (admin will be set in first-run setup)")

def get_users():
    """Load all users from file."""
    _ensure_users_file()
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[AUTH] Error loading users: {e}")
        return {}

def save_users(users):
    """Save users to file."""
    try:
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        logger.info("[AUTH] Users saved")
        return True
    except Exception as e:
        logger.error(f"[AUTH] Error saving users: {e}")
        return False

def user_exists(username):
    """Check if username exists."""
    users = get_users()
    return username in users

def authenticate(username, password):
    """Authenticate user with username and password."""
    users = get_users()
    if username not in users:
        return False
    
    user = users[username]
    return check_password_hash(user.get("password_hash", ""), password)

def create_user(username, password, pin="1234"):
    """Create new user."""
    if user_exists(username):
        logger.warning(f"[AUTH] User {username} already exists")
        return False
    
    users = get_users()
    users[username] = {
        "password_hash": generate_password_hash(password),
        "pin": pin,
        "role": "user"
    }
    return save_users(users)

def delete_user(username):
    """Delete user account."""
    users = get_users()
    if username not in users:
        logger.warning(f"[AUTH] User {username} not found for delete")
        return False
    users.pop(username, None)
    return save_users(users)

def change_password(username, old_password, new_password):
    """Change user password."""
    if not authenticate(username, old_password):
        logger.warning(f"[AUTH] Wrong password for user {username}")
        return False
    
    users = get_users()
    users[username]["password_hash"] = generate_password_hash(new_password)
    return save_users(users)

def get_user(username):
    """Get user details."""
    users = get_users()
    return users.get(username)


def _format_security_key(raw: str) -> str:
    raw = (raw or "").upper().replace("-", "")
    if not raw:
        return ""
    groups = [raw[i:i+4] for i in range(0, min(len(raw), 20), 4)]
    return "-".join(groups)


def _new_security_key() -> str:
    return _format_security_key(secrets.token_hex(10))


def ensure_enrollment_key(cfg: dict = None, force_rotate: bool = False, reason: str = "manual") -> str:
    """Ensure an enrollment key exists in config.security, optionally rotate it."""
    if cfg is None:
        cfg = get_config()

    security = cfg.get("security") or {}
    current_key = security.get("enrollment_key", "")

    if force_rotate or not current_key:
        current_key = _new_security_key()
        security["enrollment_key"] = current_key
        security["enrollment_key_updated_at"] = datetime.utcnow().isoformat()
        security["enrollment_key_reason"] = reason
        cfg["security"] = security
        save_config(cfg)
        logger.info(f"[SECURITY] Enrollment key rotated ({reason})")

    return current_key


def rotate_enrollment_key(reason: str = "manual") -> str:
    """Rotate and return the new enrollment key."""
    cfg = get_config()
    return ensure_enrollment_key(cfg=cfg, force_rotate=True, reason=reason)


def get_enrollment_key() -> str:
    """Return current enrollment key, creating one if missing."""
    cfg = get_config()
    return ensure_enrollment_key(cfg=cfg, force_rotate=False, reason="init")


def verify_enrollment_key(candidate_key: str) -> bool:
    """Constant-time comparison for enrollment key verification."""
    expected = get_enrollment_key().strip()
    provided = (candidate_key or "").strip().upper()
    return bool(expected) and hmac.compare_digest(expected.upper(), provided)
