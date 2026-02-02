# tests/unit/test_auth_service.py
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")

from src.services.auth_service import hash_password, verify_password, create_access_token, decode_access_token


def test_hash_and_verify_password():
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"
    assert verify_password("mypassword", hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_create_and_decode_token():
    token = create_access_token({"sub": "user123", "role": "admin"})
    payload = decode_access_token(token)
    assert payload["sub"] == "user123"
    assert payload["role"] == "admin"


def test_decode_invalid_token():
    result = decode_access_token("invalid.token.here")
    assert result is None
