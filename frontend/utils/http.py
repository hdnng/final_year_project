"""
Shared HTTP helpers for API calls.

Provides centralized auth headers, safe GET/POST wrappers, and
session state initialization.
"""

import requests
import streamlit as st

from config import API_BASE_URL


# ── Session State Defaults ──────────────────────────────────

_DEFAULTS = {
    "is_login": False,
    "access_token_value": None,
    "refresh_token_value": None,
    "running": False,
    "session_id": None,
    "frame_id": None,
    "capture_start_time": None,
    "refresh_key": 0,
    "page_loaded": "",
    "user_role": "teacher",
}


def init_session_state() -> None:
    """Ensure all required session state keys exist with defaults."""
    for key, value in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "client" not in st.session_state:
        st.session_state.client = requests.Session()


# ── Auth Headers ────────────────────────────────────────────


def get_auth_headers() -> dict:
    """Build Authorization header from stored token."""
    token = (
        st.session_state.get("access_token_value")
        or st.session_state.get("token")
    )
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# ── Safe HTTP Wrappers ──────────────────────────────────────


def safe_get(url: str, timeout: int = 5):
    """GET with auth headers. Returns None on connection error."""
    try:
        return st.session_state.client.get(
            url, headers=get_auth_headers(), timeout=timeout
        )
    except requests.RequestException:
        return None


def safe_post(url: str, params: dict = None, json: dict = None, timeout: int = 10):
    """POST with auth headers. Returns None on connection error."""
    try:
        return st.session_state.client.post(
            url, params=params, json=json,
            headers=get_auth_headers(), timeout=timeout,
        )
    except requests.RequestException:
        return None
