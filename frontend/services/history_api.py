"""History API calls — session deletion."""

import requests

from config import API_BASE_URL
from utils.http import get_auth_headers


def delete_session(session_id: int):
    """Delete a session by ID. Returns None on connection error."""
    try:
        return requests.delete(
            f"{API_BASE_URL}/history/session/{session_id}",
            headers=get_auth_headers(),
        )
    except requests.RequestException:
        return None