"""
Singleton camera state — shared across the capture loop and API endpoints.
"""

import threading
from typing import Optional

import numpy as np


class CameraState:
    """Thread-safe singleton holding the live camera state."""

    _instance: Optional["CameraState"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "CameraState":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self.cap = None
        self.running: bool = False
        self.thread: Optional[threading.Thread] = None
        self.current_session_id: Optional[int] = None
        self.latest_frame: Optional[np.ndarray] = None
        self.frame_count: int = 0
        self._initialized = True

    def reset(self) -> None:
        """Restore all fields to initial state."""
        self.cap = None
        self.running = False
        self.thread = None
        self.current_session_id = None
        self.latest_frame = None
        self.frame_count = 0

    def is_running(self) -> bool:
        """Return True if the camera is active."""
        return self.running

    def __repr__(self) -> str:
        return (
            f"CameraState(running={self.running}, "
            f"session_id={self.current_session_id}, "
            f"frame_count={self.frame_count})"
        )