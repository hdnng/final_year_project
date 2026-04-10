import os
from dotenv import load_dotenv
from jose import JWTError, jwt
from datetime import datetime, timedelta

# =========================
# LOAD ENV VARIABLES
# =========================
load_dotenv()

# =========================
# SECURITY CONFIG
# =========================
SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

if os.getenv("ENVIRONMENT") == "production" and SECRET_KEY == "default-secret-key-change-this":
    raise ValueError("SECRET_KEY must be set in .env for production")


def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Create JWT access token

    Args:
        data: Payload (e.g., {"user_id": 1})
        expires_delta: Custom expiration time (default: 60 minutes)
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expire


def create_refresh_token(data: dict, expires_delta: timedelta = None):
    """
    Create JWT refresh token (longer expiration)

    Args:
        data: Payload (e.g., {"user_id": 1})
        expires_delta: Custom expiration time (default: 7 days)
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expire


def verify_token(token: str, token_type: str = "access"):
    """
    Verify JWT token type and extract payload
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Verify token type
        if payload.get("type") != token_type:
            raise ValueError(f"Invalid token type. Expected {token_type}")

        return payload
    except JWTError:
        return None
