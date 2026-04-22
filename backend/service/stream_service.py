"""
MJPEG streaming generator for live video feed.
"""

import time

import cv2

from service.camera_state import CameraState

JPEG_QUALITY = 70


def gen_frames():
    """
    Yield MJPEG frames from the latest camera state.

    Used by the ``/camera/video_feed`` endpoint as a streaming response.
    """
    state = CameraState()

    while True:
        if state.latest_frame is None:
            time.sleep(0.05)
            continue

        ret, buffer = cv2.imencode(
            ".jpg",
            state.latest_frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY],
        )
        if not ret:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )
