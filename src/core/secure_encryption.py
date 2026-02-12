"""Enhanced encryption for secure video storage and data protection"""
import os
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
from loguru import logger

class SecureEncryption:
    """End-to-end encryption system for ME Camera"""
    
    def __init__(self, password: str = None, key_file: str = "config/.encryption_key"):
        self.key_file = key_file
        self.cipher = None
        
        if password:
            self.cipher = self._derive_cipher_from_password(password)
        else:
            self.cipher = self._load_or_create_key()
    
    def _derive_cipher_from_password(self, password: str) -> Fernet:
        """Derive encryption key from password using PBKDF2"""
        try:
            salt = b"ME_CAM_SECURITY"  # Fixed salt for consistency
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            return Fernet(key)
        except Exception as e:
            logger.error(f"[ENCRYPTION] Failed to derive cipher from password: {e}")
            return None
    
    def _load_or_create_key(self) -> Fernet:
        """Load encryption key from file or create new one"""
        try:
            os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
            
            if os.path.exists(self.key_file):
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                logger.info("[ENCRYPTION] Loaded existing encryption key")
            else:
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                # Restrict file permissions to owner only
                os.chmod(self.key_file, 0o600)
                logger.info("[ENCRYPTION] Created new encryption key")
            
            return Fernet(key)
        except Exception as e:
            logger.error(f"[ENCRYPTION] Error managing encryption key: {e}")
            return None
    
    def encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data"""
        if not self.cipher:
            logger.warning("[ENCRYPTION] No cipher available, returning unencrypted")
            return data
        
        try:
            return self.cipher.encrypt(data)
        except Exception as e:
            logger.error(f"[ENCRYPTION] Encryption error: {e}")
            return data
    
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt data"""
        if not self.cipher:
            logger.warning("[ENCRYPTION] No cipher available, returning unchanged")
            return encrypted_data
        
        try:
            return self.cipher.decrypt(encrypted_data)
        except Exception as e:
            logger.error(f"[ENCRYPTION] Decryption error: {e}")
            return None
    
    def encrypt_file(self, input_path: str, output_path: str = None) -> bool:
        """Encrypt a file"""
        if not output_path:
            output_path = input_path + ".enc"
        
        try:
            with open(input_path, 'rb') as f:
                data = f.read()
            
            encrypted = self.encrypt_data(data)
            
            with open(output_path, 'wb') as f:
                f.write(encrypted)
            
            logger.info(f"[ENCRYPTION] Encrypted {input_path} -> {output_path}")
            return True
        except Exception as e:
            logger.error(f"[ENCRYPTION] File encryption error: {e}")
            return False
    
    def decrypt_file(self, input_path: str, output_path: str = None) -> bool:
        """Decrypt a file"""
        if not output_path:
            output_path = input_path.replace('.enc', '')
        
        try:
            with open(input_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted = self.decrypt_data(encrypted_data)
            if not decrypted:
                return False
            
            with open(output_path, 'wb') as f:
                f.write(decrypted)
            
            logger.info(f"[ENCRYPTION] Decrypted {input_path} -> {output_path}")
            return True
        except Exception as e:
            logger.error(f"[ENCRYPTION] File decryption error: {e}")
            return False
    
    def encrypt_json(self, data: dict) -> str:
        """Encrypt JSON data and return base64 string"""
        try:
            json_str = json.dumps(data)
            encrypted = self.encrypt_data(json_str.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"[ENCRYPTION] JSON encryption error: {e}")
            return None
    
    def decrypt_json(self, encrypted_str: str) -> dict:
        """Decrypt base64 JSON data"""
        try:
            encrypted = base64.b64decode(encrypted_str)
            decrypted = self.decrypt_data(encrypted)
            if not decrypted:
                return None
            return json.loads(decrypted.decode())
        except Exception as e:
            logger.error(f"[ENCRYPTION] JSON decryption error: {e}")
            return None
    
    def hash_password(self, password: str) -> str:
        """Hash password using Fernet (one-way)"""
        try:
            # Use a temporary cipher to hash
            cipher = self._derive_cipher_from_password(password)
            if cipher:
                # Hash by encrypting a constant
                return cipher.encrypt(b"hashed").decode()
            return None
        except Exception as e:
            logger.error(f"[ENCRYPTION] Password hashing error: {e}")
            return None


# Initialize global encryption object
def init_encryption(password: str = None) -> SecureEncryption:
    """Initialize the encryption system"""
    enc = SecureEncryption(password=password)
    logger.info("[ENCRYPTION] System initialized")
    return enc

# Create default instance
_encryption = None

def get_encryption(password: str = None) -> SecureEncryption:
    """Get or create encryption instance"""
    global _encryption
    if _encryption is None:
        _encryption = init_encryption(password=password)
    return _encryption
