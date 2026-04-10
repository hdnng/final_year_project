import cv2
import time

from service.camera_state import CameraState


def gen_frames():
    """
    Generator để stream video frames trong MJPEG format
    Sử dụng latest_frame từ camera state
    """
    state = CameraState()

    while True:
        if state.latest_frame is None:
            time.sleep(0.05)
            continue

        # Compress JPEG với quality 70%
        ret, buffer = cv2.imencode(
            '.jpg',
            state.latest_frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), 70]
        )

        if not ret:
            continue

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            buffer.tobytes() +
            b'\r\n'
        )
