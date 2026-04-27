"""Frame & session API calls — frames list, frame detail, session detail, analysis."""

import logging

import requests

from config import API_BASE_URL
from utils.http import get_auth_headers

logger = logging.getLogger(__name__)


def get_frames_by_session(session: requests.Session, session_id: int) -> list:
    """Fetch all frames extracted for a given session. Returns [] on failure."""
    try:
        res = session.get(
            f"{API_BASE_URL}/frames/{session_id}",
            headers=get_auth_headers(),
        )
        if res.status_code == 200:
            return res.json()
        logger.warning(f"get_frames_by_session failed: {res.status_code}")
        return []
    except requests.RequestException as exc:
        logger.warning(f"get_frames_by_session error: {exc}")
        return []


def get_frame_detail(session: requests.Session, frame_id: int) -> dict | None:
    """Fetch detailed detection data for a single frame. Returns None on failure."""
    try:
        res = session.get(
            f"{API_BASE_URL}/frames/detail/{frame_id}",
            headers=get_auth_headers(),
        )
        if res.status_code == 200:
            return res.json()
        logger.warning(f"get_frame_detail failed: {res.status_code}")
        return None
    except requests.RequestException as exc:
        logger.warning(f"get_frame_detail error: {exc}")
        return None


def get_frame_analysis(session: requests.Session, session_id: int) -> list:
    """Fetch analysis results (focus/sleeping counts) for all frames in a session."""
    try:
        res = session.get(
            f"{API_BASE_URL}/frames/analysis/{session_id}",
            headers=get_auth_headers(),
        )
        if res.status_code == 200:
            return res.json()
        logger.warning(f"get_frame_analysis failed: {res.status_code}")
        return []
    except requests.RequestException as exc:
        logger.warning(f"get_frame_analysis error: {exc}")
        return []
