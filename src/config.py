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
    FREENOW_EMAIL_2: str = ""
    FREENOW_PASSWORD_2: str = ""
    PRIMA_EMAIL: str = ""
    PRIMA_PASSWORD: str = ""

    def get_freenow_accounts(self) -> list[dict]:
        """Return list of configured FreeNow accounts with label/email/password."""
        accounts = []
        if self.FREENOW_EMAIL and self.FREENOW_PASSWORD:
            accounts.append({
                "label": "account1",
                "email": self.FREENOW_EMAIL,
                "password": self.FREENOW_PASSWORD,
            })
        if self.FREENOW_EMAIL_2 and self.FREENOW_PASSWORD_2:
            accounts.append({
                "label": "account2",
                "email": self.FREENOW_EMAIL_2,
                "password": self.FREENOW_PASSWORD_2,
            })
        return accounts

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
