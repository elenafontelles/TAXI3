"""Fernet symmetric encryption for OAuth tokens at rest."""
import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    """Lazy-init Fernet from SECRET_KEY (derive a 32-byte key via SHA-256)."""
    global _fernet
    if _fernet is None:
        from src.config import get_settings
        secret = get_settings().SECRET_KEY.encode()
        # Derive a URL-safe base64-encoded 32-byte key from SECRET_KEY
        key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
        _fernet = Fernet(key)
    return _fernet


def encrypt_token(plaintext: str) -> str:
    """Encrypt a token string. Returns base64-encoded ciphertext."""
    if not plaintext:
        return ""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    """Decrypt a token string. Returns plaintext.

    Returns empty string if decryption fails (e.g. key rotated).
    """
    if not ciphertext:
        return ""
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        logger.warning("Failed to decrypt token — key may have been rotated")
        return ""
