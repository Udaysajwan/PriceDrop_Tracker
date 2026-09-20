from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "Price Drop Tracker & Alert API"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./price_tracker.db"

    # Database Backend: "firestore" or "sqlite"
    DATABASE_BACKEND: str = "firestore"
    FIREBASE_CREDENTIALS_PATH: str = "firebase-credentials.json"
    FIREBASE_PROJECT_ID: str = ""

    # Security & JWT
    SECRET_KEY: str = "supersecret-price-tracker-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Scheduler Settings
    DEFAULT_SCRAPE_INTERVAL_MINUTES: int = 60
    SCHEDULER_ENABLED: bool = True

    # Notification Settings
    SMTP_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    ALERT_FROM_EMAIL: str = "alerts@pricetracker.local"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
