# src/services/credential_service.py
"""Encrypt/decrypt platform credentials and provide unified access."""
import base64
import hashlib
import json
import logging

from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from src.models.platform_credential import PlatformCredential

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    """Derive a Fernet key from SECRET_KEY."""
    from src.config import get_settings
    secret = get_settings().SECRET_KEY.encode()
    key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return Fernet(key)


def encrypt_password(password: str) -> str:
    return _get_fernet().encrypt(password.encode()).decode()


def decrypt_password(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()


def get_credential(session: Session, platform: str, account_label: str = "") -> dict | None:
    """Get credentials for a platform. DB first, then .env fallback.

    Returns dict with 'email', 'password', and optionally 'extra_config',
    or None if not configured.
    """
    cred = (
        session.query(PlatformCredential)
        .filter_by(platform=platform, account_label=account_label)
        .first()
    )

    if cred and cred.email and cred.encrypted_password:
        try:
            result = {
                "email": cred.email,
                "password": decrypt_password(cred.encrypted_password),
            }
            if cred.extra_config:
                result["extra_config"] = json.loads(cred.extra_config)
            return result
        except Exception:
            logger.warning(f"Failed to decrypt {platform}/{account_label}, trying .env")

    # Fallback to .env
    return _env_fallback(platform, account_label)


def _env_fallback(platform: str, account_label: str) -> dict | None:
    """Read credentials from .env via Settings."""
    from src.config import get_settings
    settings = get_settings()

    if platform == "freenow":
        accounts = settings.get_freenow_accounts()
        if account_label:
            acc = next((a for a in accounts if a["label"] == account_label), None)
            if acc:
                return {"email": acc["email"], "password": acc["password"]}
        elif accounts:
            return {"email": accounts[0]["email"], "password": accounts[0]["password"]}

    elif platform == "prima":
        if settings.PRIMA_EMAIL and settings.PRIMA_PASSWORD:
            return {"email": settings.PRIMA_EMAIL, "password": settings.PRIMA_PASSWORD}

    return None


def save_credential(
    session: Session,
    platform: str,
    account_label: str,
    email: str,
    password: str,
    extra_config: dict | None = None,
    updated_by: str = "admin",
) -> PlatformCredential:
    """Save or update credentials for a platform."""
    cred = (
        session.query(PlatformCredential)
        .filter_by(platform=platform, account_label=account_label)
        .first()
    )

    if not cred:
        cred = PlatformCredential(
            platform=platform,
            account_label=account_label,
        )
        session.add(cred)

    cred.email = email
    cred.encrypted_password = encrypt_password(password)
    cred.extra_config = json.dumps(extra_config) if extra_config else None
    cred.updated_by = updated_by
    session.commit()
    return cred


def list_credentials(session: Session) -> list[dict]:
    """List all saved credentials (passwords masked)."""
    creds = session.query(PlatformCredential).order_by(
        PlatformCredential.platform, PlatformCredential.account_label
    ).all()

    return [
        {
            "id": c.id,
            "platform": c.platform,
            "account_label": c.account_label,
            "email": c.email,
            "has_password": bool(c.encrypted_password),
            "extra_config": json.loads(c.extra_config) if c.extra_config else None,
            "updated_at": c.updated_at,
            "updated_by": c.updated_by,
        }
        for c in creds
    ]
