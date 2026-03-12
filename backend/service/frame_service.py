import cv2
import time

def capture_frame(cap):

    ret, frame = cap.read()

    if not ret:
        return None

    return frame


def save_frame(frame):

    filename = f"images/frame_{int(time.time())}.jpg"

    cv2.imwrite(filename, frame)

    return filename