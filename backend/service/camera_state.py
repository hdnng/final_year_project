import threading


class CameraState:
    """
    Singleton pattern để quản lý trạng thái camera
    Đảm bảo chỉ có 1 instance duy nhất trong toàn bộ ứng dụng
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.cap = None
        self.running = False
        self.thread = None
        self.current_session_id = None
        self.latest_frame = None
        self.frame_count = 0
        self._initialized = True

    def reset(self):
        """Reset toàn bộ state về ban đầu"""
        self.cap = None
        self.running = False
        self.thread = None
        self.current_session_id = None
        self.latest_frame = None
        self.frame_count = 0

    def is_running(self):
        """Kiểm tra camera có đang chạy không"""
        return self.running

    def __repr__(self):
        return (
            f"CameraState(running={self.running}, "
            f"session_id={self.current_session_id}, "
            f"frame_count={self.frame_count})"
        )