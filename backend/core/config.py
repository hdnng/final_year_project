"""
Centralized application configuration.

All settings are loaded from environment variables with sensible defaults.
Uses Pydantic BaseSettings for validation and type coercion.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # --- Paths ---
    BASE_DIR: Path = Path(__file__).resolve().parents[1]
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
    IMAGE_DIR: Path = PROJECT_ROOT / "images"

    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # --- Security ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default-secret-key-change-this")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Environment ---
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1")

    # --- API ---
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # --- CORS ---
    ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]

    # --- Rate Limiting ---
    RATE_LIMIT_MAX_ATTEMPTS: int = 5
    RATE_LIMIT_WINDOW_MINUTES: int = 15

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    def validate(self) -> None:
        """Validate critical settings on startup."""
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL must be set in .env file")

        if self.is_production and self.SECRET_KEY == "default-secret-key-change-this":
            raise ValueError("SECRET_KEY must be changed for production")


settings = Settings()
