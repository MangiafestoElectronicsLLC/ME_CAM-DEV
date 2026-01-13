from cryptography.fernet import Fernet
import os
from loguru import logger


def _get_key_path():
    # store key in config folder for persistence
    return os.path.join("config", "storage_key.key")


def _ensure_key():
    key_path = _get_key_path()
    os.makedirs("config", exist_ok=True)
    if not os.path.exists(key_path):
        key = Fernet.generate_key()
        with open(key_path, "wb") as f:
            f.write(key)
        logger.info("[ENCRYPT] Generated new encryption key")
    
    with open(key_path, "rb") as f:
        key_data = f.read().strip()
        # Handle both bytes and string key formats
        if isinstance(key_data, str):
            key_data = key_data.encode()
        return key_data


def encrypt_file(in_path: str, out_dir: str) -> str:
    """Encrypt a file to the given output directory using Fernet.

    Returns the path of the encrypted file.
    """
    try:
        key = _ensure_key()
        cipher = Fernet(key)
        os.makedirs(out_dir, exist_ok=True)

        with open(in_path, "rb") as f:
            data = f.read()

        encrypted = cipher.encrypt(data)
        base = os.path.basename(in_path)
        out_path = os.path.join(out_dir, base + ".enc")
        with open(out_path, "wb") as f:
            f.write(encrypted)

        logger.info(f"[ENCRYPT] Encrypted to {out_path}")
        return out_path
    except Exception as e:
        logger.error(f"[ENCRYPT] Failed to encrypt {in_path}: {e}")
        raise
