"""Configuration management using pydantic-settings."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "LED Product Development AI Copilot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # API Keys
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./led_copilot.db"

    # ChromaDB
    CHROMA_PATH: str = "./chroma_data"

    # LCSC
    LCSC_API_URL: str = "https://wmsc.lcsc.com/ftps/wm"

    # File upload
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIR: str = "./uploads"

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
