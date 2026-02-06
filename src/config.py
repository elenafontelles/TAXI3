# src/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Auth
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # App
    ENVIRONMENT: str = "development"
    APP_NAME: str = "TAXI API"

    # Email alerts
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    ALERT_EMAIL_TO: str = ""

    # Redis (job queue)
    REDIS_URL: str = "redis://localhost:6379"

    # Platform credentials (Playwright scrapers)
    UBER_EMAIL: str = ""
    UBER_PASSWORD: str = ""
    FREENOW_EMAIL: str = ""
    FREENOW_PASSWORD: str = ""
    PRIMA_EMAIL: str = ""
    PRIMA_PASSWORD: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
