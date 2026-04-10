import os
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()

# =========================
# PASSWORD HASHING
# =========================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# =========================
# COOKIE SETTINGS
# =========================
def get_cookie_settings():
    """
    Trả về cài đặt cookie dựa trên environment
    Development: secure=False (để test trên HTTP)
    Production: secure=True (chỉ hoạt động trên HTTPS)
    """
    is_production = os.getenv("ENVIRONMENT", "development") == "production"

    return {
        "httponly": True,
        "secure": is_production,
        "samesite": "lax",
        "max_age": 60 * 60  # 1 hour
    }