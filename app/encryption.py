"""
Encryption utilities for sensitive data like API keys and passwords.
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pathlib import Path
from loguru import logger

# Path to the secret key file
SECRET_KEY_FILE = Path("secret_key.key")

def generate_secret_key():
    """Generate a new secret key and save it to a file"""
    key = Fernet.generate_key()
    with open(SECRET_KEY_FILE, "wb") as key_file:
        key_file.write(key)
    logger.info(f"Generated new secret key and saved to {SECRET_KEY_FILE}")
    return key

def load_secret_key():
    """Load the secret key from file or generate a new one if it doesn't exist"""
    if not SECRET_KEY_FILE.exists():
        logger.warning(f"Secret key file not found at {SECRET_KEY_FILE}, generating new key")
        return generate_secret_key()
    
    with open(SECRET_KEY_FILE, "rb") as key_file:
        key = key_file.read()
    logger.info(f"Loaded secret key from {SECRET_KEY_FILE}")
    return key

def derive_key_from_password(password, salt=None):
    """Derive a key from a password using PBKDF2"""
    if salt is None:
        # Use the secret key as salt if no salt is provided
        salt = load_secret_key()[:16]  # Use first 16 bytes as salt
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def encrypt_text(text, key=None):
    """Encrypt text using Fernet symmetric encryption"""
    if text is None:
        return None
    
    if key is None:
        key = load_secret_key()
    
    f = Fernet(key)
    encrypted_text = f.encrypt(text.encode())
    return base64.urlsafe_b64encode(encrypted_text).decode()

def decrypt_text(encrypted_text, key=None):
    """Decrypt text that was encrypted with Fernet"""
    if encrypted_text is None:
        return None
    
    if key is None:
        key = load_secret_key()
    
    f = Fernet(key)
    try:
        decrypted_text = f.decrypt(base64.urlsafe_b64decode(encrypted_text.encode()))
        return decrypted_text.decode()
    except Exception as e:
        logger.error(f"Error decrypting text: {str(e)}")
        return None

# Initialize the secret key when the module is imported
SECRET_KEY = load_secret_key()
