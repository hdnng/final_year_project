"""Authentication API calls — login, register, logout, refresh."""

import logging

import requests

from config import API_BASE_URL
from utils.http import get_auth_headers

logger = logging.getLogger(__name__)


def login(session: requests.Session, email: str, password: str):
    """Authenticate and return the response (token in JSON body)."""
    return session.post(
        f"{API_BASE_URL}/users/login",
        json={"email": email, "password": password},
    )


def register(session: requests.Session, full_name: str, email: str, password: str):
    """Register a new user account."""
    return session.post(
        f"{API_BASE_URL}/users/register",
        json={"email": email, "password": password, "full_name": full_name},
    )


def logout(session: requests.Session):
    """Logout — blacklist the active token."""
    try:
        return session.post(
            f"{API_BASE_URL}/users/logout",
            headers=get_auth_headers(),
        )
    except requests.RequestException as exc:
        logger.warning(f"Logout API error: {exc}")
        return None


def refresh_token(session: requests.Session):
    """Refresh the access token using the refresh token cookie."""
    try:
        return session.post(
            f"{API_BASE_URL}/users/refresh",
            headers=get_auth_headers(),
        )
    except requests.RequestException as exc:
        logger.warning(f"Refresh token error: {exc}")
        return None
