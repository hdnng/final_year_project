"""
MJPEG streaming generator for live video feed.
"""

import time

import cv2

from service.camera_state import CameraState

JPEG_QUALITY = 65
TARGET_FPS = 15
_FRAME_INTERVAL = 1.0 / TARGET_FPS


def gen_frames():
    """
    Yield MJPEG frames from the latest camera state.

    Used by the ``/camera/video_feed`` endpoint as a streaming response.
    Throttled to TARGET_FPS to avoid flooding the browser and wasting CPU.
    """
    state = CameraState()
    last_send_time = 0.0
    prev_frame_id = None  # Track frame identity to skip duplicates

    while state.running:
        if state.latest_frame is None:
            time.sleep(0.05)
            continue

        # Throttle to target FPS
        now = time.time()
        elapsed = now - last_send_time
        if elapsed < _FRAME_INTERVAL:
            time.sleep(_FRAME_INTERVAL - elapsed)

        # Skip encoding if the frame hasn't changed
        current_id = id(state.latest_frame)
        if current_id == prev_frame_id:
            time.sleep(0.01)
            continue
        prev_frame_id = current_id

        # Resize for streaming (cap width at 720px for performance)
        frame = state.latest_frame
        h, w = frame.shape[:2]
        if w > 720:
            scale = 720 / w
            frame = cv2.resize(frame, (720, int(h * scale)))

        ret, buffer = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY],
        )
        if not ret:
            continue

        last_send_time = time.time()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )
