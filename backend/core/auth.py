"""
JWT token creation and verification.
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from core.config import settings


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> tuple[str, datetime]:
    """
    Create a JWT access token.

    Args:
        data: Payload data (e.g. {"user_id": 1}).
        expires_delta: Custom TTL. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Tuple of (encoded_token, expiry_datetime).
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, expire


def create_refresh_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> tuple[str, datetime]:
    """
    Create a JWT refresh token with a longer expiration.

    Args:
        data: Payload data (e.g. {"user_id": 1}).
        expires_delta: Custom TTL. Defaults to REFRESH_TOKEN_EXPIRE_DAYS.

    Returns:
        Tuple of (encoded_token, expiry_datetime).
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, expire


def verify_token(token: str, token_type: str = "access") -> dict | None:
    """
    Decode and verify a JWT token.

    Returns the payload dict if valid, or None if verification fails.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None
