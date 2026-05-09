"""
config.py — Application settings loaded from environment variables.
Set these in a .env file or Docker environment.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── App ─────────────────────────────────────────────────────
    APP_NAME: str = "WeeklyReminder"
    APP_ENV: str = "development"          # development | production
    SECRET_KEY: str = "change-me-in-production"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost:80"

    # ── Database ─────────────────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "reminders"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ── Email (SMTP) ──────────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    EMAIL_FROM: str = ""
    EMAIL_TO: str = ""

    # ── Twilio (SMS + WhatsApp) ───────────────────────────────────
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""          # E.164: +12015550123
    NOTIFICATION_PHONE: str = ""          # Your phone E.164

    # ── Scheduler ────────────────────────────────────────────────
    SCHEDULER_TIMEZONE: str = "Asia/Kolkata"
    WEEKLY_SEND_DAY: str = "monday"       # monday … sunday
    WEEKLY_SEND_TIME: str = "08:00"       # HH:MM (24-hour)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
