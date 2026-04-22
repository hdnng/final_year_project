"""
Password hashing and cookie utilities.
"""

from passlib.context import CryptContext

from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_cookie_settings() -> dict:
    """
    Return cookie configuration based on the current environment.

    - Development: secure=False (allows HTTP).
    - Production:  secure=True  (requires HTTPS).
    """
    return {
        "httponly": True,
        "secure": settings.is_production,
        "samesite": "lax",
        "max_age": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }