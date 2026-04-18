from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./lendlyfin.db"

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Admin credentials (used for first-time seed)
    ADMIN_EMAIL: str = "admin@lendlyfin.com.au"
    ADMIN_PASSWORD: str = "changeme123"
    BROKER_EMAIL: str = "broker@lendlyfin.com.au"
    BROKER_PASSWORD: str = "brokerpass123"

    # Email
    SENDGRID_API_KEY: str = ""
    EMAIL_FROM: str = "hello@lendlyfin.com.au"
    EMAIL_FROM_NAME: str = "Lendlyfin"
    BROKER_NOTIFICATION_EMAIL: str = "broker@lendlyfin.com.au"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    # Google Sheets (for rates)
    GOOGLE_SHEETS_CREDENTIALS_JSON: str = ""  # Path or JSON string
    GOOGLE_SHEETS_RATES_ID: str = ""  # Spreadsheet ID from URL
    GOOGLE_SHEETS_CACHE_TTL: int = 3600  # Cache for 1 hour

    # Google Forms (for leads)
    GOOGLE_FORMS_WEBHOOK_SECRET: str = ""  # Optional webhook validation

    # App
    APP_ENV: str = "development"
    APP_VERSION: str = "2.0.0"

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
