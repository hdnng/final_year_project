"""
Camera lifecycle — start, stop, list available devices.
"""

import threading

import cv2
import pythoncom
from pygrabber.dshow_graph import FilterGraph

from crud.session_crud import create_session, end_session
from database.database import SessionLocal
from service.camera_state import CameraState
from service.pipeline_service import capture_loop
from core.logger import get_logger

logger = get_logger(__name__)


def start_camera(
    user_id: int = 1,
    class_id: str = "Unknown",
    camera_index: int = 0,
) -> int:
    """
    Open a camera and begin the background capture loop.

    Returns the session_id (new or existing if already running).
    """
    state = CameraState()

    if state.is_running():
        return state.current_session_id

    db = SessionLocal()
    session = create_session(
        db=db,
        user_id=user_id,
        class_id=class_id,
        camera_url=f"camera_{camera_index}",
    )
    state.current_session_id = session.session_id

    state.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    state.cap.set(cv2.CAP_PROP_FPS, 15)

    if not state.cap.isOpened():
        raise RuntimeError(f"Cannot open camera {camera_index}")

    state.running = True

    state.thread = threading.Thread(target=capture_loop, daemon=True)
    state.thread.start()

    logger.info(f"Camera {camera_index} started — session {session.session_id}")
    return state.current_session_id


def stop_camera() -> None:
    """Stop the running camera and finalize the session."""
    state = CameraState()
    state.running = False

    if state.cap:
        state.cap.release()
        state.cap = None

    if state.current_session_id:
        db = SessionLocal()
        end_session(db, state.current_session_id)

    state.reset()
    logger.info("Camera stopped")


def list_cameras(max_index: int = 5) -> list[int]:
    """Probe for available camera indices by attempting to open each one."""
    available: list[int] = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available.append(i)
        cap.release()
    return available


def list_camera_with_name() -> list[dict]:
    """Return camera devices with their display names (Windows DirectShow)."""
    pythoncom.CoInitialize()
    try:
        devices = FilterGraph().get_input_devices()
        return [{"index": i, "name": name} for i, name in enumerate(devices)]
    finally:
        pythoncom.CoUninitialize()
