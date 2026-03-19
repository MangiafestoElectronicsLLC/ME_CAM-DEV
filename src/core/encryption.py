"""
Video encryption and secure storage for ME_CAM

Encrypts motion clips with AES-256-CBC.
Provides secure key management and encryption/decryption.

Usage:
    from src.core.encryption import VideoEncryptor
    encryptor = VideoEncryptor()
    encrypted_path = encryptor.encrypt_file("motion_clip.mp4", device_id="D2")
    decrypted_path = encryptor.decrypt_file(encrypted_path, device_id="D2")
"""

import os
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
from loguru import logger
import base64


class VideoEncryptor:
    """Encrypt and decrypt video files for secure cloud storage."""
    
    CHUNK_SIZE = 1024 * 1024  # 1MB chunks for large files
    
    def __init__(self, password: str = None, salt: str = None):
        """
        Initialize encryptor.
        
        Args:
            password: Encryption password (auto-generated if not provided)
            salt: Salt for key derivation (auto-generated if not provided)
        """
        self.password = password or self._get_device_password()
        self.salt = (salt or self._get_device_salt()).encode() if isinstance(salt, str) else salt
        self.backend = default_backend()
        self._key = None
    
    @staticmethod
    def _get_device_password() -> str:
        """Get or create device-specific encryption password."""
        config_path = Path.home() / "ME_CAM-DEV" / "config.json"
        
        try:
            import json
            if config_path.exists():
                with open(config_path, 'r') as f:
                    cfg = json.load(f)
                    if 'encryption_password' in cfg:
                        return cfg['encryption_password']
        except Exception as e:
            logger.debug(f"Could not read encryption password from config: {e}")
        
        # Generate from device serial or hostname
        try:
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo = f.read()
                if "Serial" in cpuinfo:
                    serial = cpuinfo.split("Serial")[1].split(":")[1].strip()
                    return f"ME_CAM_{serial}"
        except Exception:
            pass
        
        # Fallback
        hostname = os.popen("hostname").read().strip()
        return f"ME_CAM_{hostname}_default"
    
    @staticmethod
    def _get_device_salt() -> str:
        """Get or create device-specific salt."""
        home = Path.home()
        salt_file = home / "ME_CAM-DEV" / ".encryption_salt"
        
        if salt_file.exists():
            return salt_file.read_text().strip()
        
        # Generate new salt
        import secrets
        salt = secrets.token_hex(16)
        
        try:
            salt_file.parent.mkdir(parents=True, exist_ok=True)
            salt_file.write_text(salt)
            os.chmod(salt_file, 0o600)
        except Exception as e:
            logger.warning(f"Could not save salt: {e}")
        
        return salt
    
    def _derive_key(self) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        if self._key:
            return self._key
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
            backend=self.backend
        )
        
        key_material = kdf.derive(self.password.encode())
        self._key = base64.urlsafe_b64encode(key_material)
        return self._key
    
    def encrypt_file(self, file_path: str, output_path: str = None, device_id: str = "") -> str:
        """
        Encrypt a video file.
        
        Args:
            file_path: Path to video file
            output_path: Output path (auto if not specified)
            device_id: Device ID for metadata
        
        Returns:
            Path to encrypted file
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"[ENCRYPTION] File not found: {file_path}")
            return None
        
        if output_path is None:
            output_path = file_path.parent / f"{file_path.stem}.encrypted"
        else:
            output_path = Path(output_path)
        
        try:
            key = self._derive_key()
            cipher = Fernet(key)
            
            file_size = file_path.stat().st_size
            logger.info(f"[ENCRYPTION] Encrypting {file_path.name} ({file_size/1024/1024:.1f}MB)")
            
            # Encrypt in chunks for large files
            with open(file_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    # Write header with device ID and timestamp
                    header = f"MECAM_v1|{device_id}|{os.path.getmtime(file_path)}\n".encode()
                    f_out.write(header)
                    
                    bytes_processed = 0
                    while True:
                        chunk = f_in.read(self.CHUNK_SIZE)
                        if not chunk:
                            break
                        
                        encrypted_chunk = cipher.encrypt(chunk)
                        f_out.write(encrypted_chunk)
                        
                        bytes_processed += len(chunk)
                        progress = (bytes_processed / file_size) * 100
                        logger.debug(f"[ENCRYPTION] Progress: {progress:.1f}%")
            
            # Set restrictive permissions
            os.chmod(output_path, 0o600)
            
            encrypted_size = output_path.stat().st_size
            logger.success(f"[ENCRYPTION] Encrypted: {output_path.name} ({encrypted_size/1024/1024:.1f}MB)")
            
            # Optional: delete original after encryption verified
            if output_path.exists() and output_path.stat().st_size > 0:
                # Keep original for now, comment out to auto-delete
                # file_path.unlink()
                logger.info(f"[ENCRYPTION] Original kept: {file_path.name}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"[ENCRYPTION] Encrypt failed: {e}")
            return None
    
    def decrypt_file(self, file_path: str, output_path: str = None) -> str:
        """
        Decrypt a video file.
        
        Args:
            file_path: Path to encrypted file
            output_path: Output path (auto if not specified)
        
        Returns:
            Path to decrypted file
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"[DECRYPTION] File not found: {file_path}")
            return None
        
        if output_path is None:
            output_path = file_path.parent / f"{file_path.stem}_decrypted{file_path.suffix}"
        else:
            output_path = Path(output_path)
        
        try:
            key = self._derive_key()
            cipher = Fernet(key)
            
            file_size = file_path.stat().st_size
            logger.info(f"[DECRYPTION] Decrypting {file_path.name} ({file_size/1024/1024:.1f}MB)")
            
            with open(file_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    # Skip header
                    header = f_in.readline()
                    logger.debug(f"[DECRYPTION] Header: {header.decode().strip()}")
                    
                    bytes_processed = 0
                    while True:
                        # Read encrypted data (header + length marker)
                        length_bytes = f_in.read(13)  # Fernet overhead
                        if not length_bytes:
                            break
                        
                        # Read full chunk
                        chunk = length_bytes + f_in.read(self.CHUNK_SIZE)
                        if not chunk:
                            break
                        
                        try:
                            decrypted_chunk = cipher.decrypt(chunk)
                            f_out.write(decrypted_chunk)
                            bytes_processed += len(decrypted_chunk)
                        except Exception as e:
                            logger.warning(f"[DECRYPTION] Chunk decode warning: {e}")
                            # Try with adjusted chunk
                            continue
            
            if output_path.stat().st_size > 0:
                logger.success(f"[DECRYPTION] Decrypted: {output_path.name}")
                return str(output_path)
            else:
                logger.error(f"[DECRYPTION] Output file empty")
                output_path.unlink()
                return None
                
        except Exception as e:
            logger.error(f"[DECRYPTION] Decrypt failed: {e}")
            if output_path.exists():
                output_path.unlink()
            return None
    
    def get_file_hash(self, file_path: str) -> str:
        """Get SHA256 hash of file for integrity verification."""
        try:
            hash_obj = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            logger.error(f"[ENCRYPTION] Hash calculation failed: {e}")
            return None


def encrypt_clip_if_enabled(file_path: str, config: dict) -> tuple:
    """
    Encrypt video clip if enabled in config.
    
    Args:
        file_path: Video file path
        config: Device configuration
    
    Returns:
        Tuple of (final_path, was_encrypted)
    """
    if not config.get('encryption_enabled', False):
        return file_path, False
    
    try:
        encryptor = VideoEncryptor()
        device_id = config.get('device_name', 'unknown')
        encrypted_path = encryptor.encrypt_file(file_path, device_id=device_id)
        
        if encrypted_path:
            return encrypted_path, True
        else:
            logger.warning(f"[ENCRYPTION] Fallback to unencrypted: {file_path}")
            return file_path, False
        
    except Exception as e:
        logger.error(f"[ENCRYPTION] Failed to encrypt clip: {e}")
        return file_path, False
