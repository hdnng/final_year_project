"""
User business logic — registration, login, profile, and token management.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DBSession

from core.auth import create_access_token, create_refresh_token, verify_token
from core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from core.logger import get_logger
from core.rate_limiter import RateLimiter
from core.security import get_cookie_settings, hash_password, verify_password
from core.token_blacklist import TokenBlacklist
from crud.user_crud import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user_password,
    update_user_profile,
)
from models.user import User
from schemas.user import UserCreate, UserUpdate

logger = get_logger(__name__)


# ── Registration ────────────────────────────────────────────


def register_user(db: DBSession, user_data: UserCreate, client_ip: str) -> User:
    """
    Register a new user with rate-limit protection.

    Raises:
        RateLimitError: Too many registration attempts from this IP.
        ConflictError:  Email is already registered.
    """
    rate_limiter = RateLimiter()
    reg_key = f"reg:{client_ip}"

    if rate_limiter.is_rate_limited(reg_key):
        minutes = _minutes_until_reset(rate_limiter, reg_key)
        logger.warning(f"Registration rate-limited for IP: {client_ip}")
        raise RateLimitError(
            detail=f"Too many registration attempts. Try again in {minutes} minutes."
        )

    if get_user_by_email(db, user_data.email):
        rate_limiter.record_attempt(reg_key)
        logger.warning(f"Registration with existing email: {user_data.email}")
        raise ConflictError(detail="Email already exists")

    logger.info(f"Registering user: {user_data.email} from {client_ip}")

    try:
        created_user = create_user(db, user_data)
    except IntegrityError:
        db.rollback()
        logger.error("Database integrity error during registration", exc_info=True)
        raise ConflictError(detail="Failed to create user — duplicate email")

    rate_limiter.reset_for_ip(reg_key)
    logger.info(f"User registered: {user_data.email}")
    return created_user


# ── Authentication ──────────────────────────────────────────


def login_user(
    db: DBSession,
    email: str,
    password: str,
    client_ip: str,
) -> dict:
    """
    Authenticate a user and generate JWT tokens.

    Returns:
        Dict with ``user_id``, ``access_token``, ``refresh_token``.

    Raises:
        RateLimitError:      Too many login attempts from this IP.
        AuthenticationError: Invalid email or password.
    """
    rate_limiter = RateLimiter()

    if rate_limiter.is_rate_limited(client_ip):
        minutes = _minutes_until_reset(rate_limiter, client_ip)
        logger.warning(f"Login rate-limited for IP: {client_ip}")
        raise RateLimitError(
            detail=f"Too many login attempts. Try again in {minutes} minutes."
        )

    logger.info(f"Login attempt: {email} from {client_ip}")

    db_user = get_user_by_email(db, email)
    if not db_user or not verify_password(password, db_user.password):
        rate_limiter.record_attempt(client_ip)
        logger.warning(f"Login failed for: {email} from {client_ip}")
        raise AuthenticationError(detail="Invalid email or password")

    # Success — reset rate limit
    rate_limiter.reset_for_ip(client_ip)

    access_token, _ = create_access_token(data={"user_id": db_user.user_id})
    refresh_token, _ = create_refresh_token(data={"user_id": db_user.user_id})

    logger.info(f"Login successful: {email}")

    return {
        "user_id": db_user.user_id,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


# ── Profile ─────────────────────────────────────────────────


def get_profile(db: DBSession, user_id: int) -> User:
    """
    Retrieve a user's profile.

    Raises:
        NotFoundError: User does not exist.
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise NotFoundError(detail="User not found")
    return user


def update_profile(db: DBSession, user_id: int, data: UserUpdate) -> User:
    """
    Update a user's display name and email.

    Raises:
        NotFoundError: User does not exist.
        ConflictError: Email is already in use by another user.
    """
    try:
        user = update_user_profile(db, user_id, data.full_name, data.email)
        if not user:
            raise NotFoundError(detail="User not found")
        logger.info(f"Profile updated for user: {user_id}")
        return user
    except IntegrityError:
        db.rollback()
        raise ConflictError(detail="Email already in use")


def change_user_password(
    db: DBSession,
    user_id: int,
    old_password: str,
    new_password: str,
) -> None:
    """
    Change a user's password after verifying the old one.

    Raises:
        NotFoundError:  User does not exist.
        ValidationError: Old password is incorrect.
    """
    user = get_user_by_id(db, user_id)
    if not user:
        raise NotFoundError(detail="User not found")

    if not verify_password(old_password, user.password):
        raise ValidationError(detail="Old password is incorrect")

    update_user_password(db, user_id, hash_password(new_password))
    logger.info(f"Password changed for user: {user_id}")


# ── Token Management ────────────────────────────────────────


def logout_user(
    user_id: int,
    access_token: Optional[str],
    refresh_token: Optional[str],
) -> None:
    """Revoke the user's tokens by adding them to the blacklist."""
    logger.info(f"Logout for user: {user_id}")

    if access_token:
        _blacklist_token(access_token, "access", user_id)
    if refresh_token:
        _blacklist_token(refresh_token, "refresh", user_id)


def refresh_access_token(refresh_token: Optional[str]) -> dict:
    """
    Issue a new access token using a valid refresh token.

    Returns:
        Dict with ``access_token`` and ``user_id``.

    Raises:
        AuthenticationError: Refresh token is missing, revoked, or invalid.
    """
    if not refresh_token:
        raise AuthenticationError(detail="Refresh token not provided")

    if TokenBlacklist.is_blacklisted(refresh_token):
        raise AuthenticationError(detail="Refresh token has been revoked")

    payload = verify_token(refresh_token, token_type="refresh")
    if not payload:
        raise AuthenticationError(detail="Invalid refresh token")

    user_id = payload.get("user_id")
    if not user_id:
        raise AuthenticationError(detail="Invalid refresh token")

    access_token, _ = create_access_token(data={"user_id": user_id})
    logger.info(f"Access token refreshed for user: {user_id}")

    return {"access_token": access_token, "user_id": user_id}


# ── Helpers (private) ───────────────────────────────────────


def _blacklist_token(token: str, token_type: str, user_id: int) -> None:
    """Add a token to the blacklist if it can be decoded."""
    try:
        payload = verify_token(token, token_type=token_type)
        if payload and (exp := payload.get("exp")):
            TokenBlacklist.add(token, datetime.fromtimestamp(exp, tz=timezone.utc))
            logger.debug(f"{token_type.title()} token blacklisted for user: {user_id}")
    except Exception as exc:
        logger.debug(f"Could not blacklist {token_type} token: {exc}")


def _minutes_until_reset(rate_limiter: RateLimiter, key: str) -> int:
    """Calculate minutes remaining until the rate-limit window resets."""
    reset_time = rate_limiter.get_reset_time(key)
    delta = (reset_time - datetime.now(timezone.utc)).total_seconds()
    return max(1, int(delta / 60))
