"""Application settings, loaded from environment (12-factor).

Every knob has a safe default so the app boots with zero config for the demo,
but nothing secret is hard-coded for production — set SECRET_KEY via env there.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SecureTask API"
    env: str = "development"  # "production" hardens a few defaults

    # Auth / JWT. In production SECRET_KEY MUST be overridden by env.
    secret_key: str = "dev-only-insecure-secret-change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Database. SQLite by default (zero-config); set DATABASE_URL to Postgres in prod.
    database_url: str = "sqlite:///./securetask.db"

    # Rate limits (slowapi syntax)
    rate_limit_default: str = "120/minute"
    rate_limit_login: str = "5/minute"

    # CORS (comma-separated origins; "*" for demo)
    cors_origins: str = "*"


@lru_cache
def get_settings() -> Settings:
    return Settings()
