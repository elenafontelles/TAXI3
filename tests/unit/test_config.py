# tests/unit/test_config.py
import os
import pytest


def test_config_loads_from_env(monkeypatch):
    """Config should load all required settings from environment variables."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/taxi_api")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")
    monkeypatch.setenv("ENVIRONMENT", "testing")

    from src.config import Settings
    settings = Settings()

    assert settings.DATABASE_URL == "postgresql://user:pass@localhost:5432/taxi_api"
    assert settings.SECRET_KEY == "test-secret-key-at-least-32-chars-long!!"
    assert settings.ENVIRONMENT == "testing"


def test_config_has_defaults(monkeypatch):
    """Config should have sensible defaults for optional fields."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/taxi_api")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")

    from src.config import Settings
    settings = Settings()

    assert settings.ENVIRONMENT == "development"
    assert settings.APP_NAME == "TAXI API"
