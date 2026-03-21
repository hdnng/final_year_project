import cv2
import os
import time
import threading
from datetime import datetime
from pathlib import Path

cap = None
running = False
thread = None


def start_camera():
    global cap, running, thread

    if running:
        print("Camera already running")
        return

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Cannot open camera")
        return

    running = True

    thread = threading.Thread(target=capture_loop)
    thread.daemon = True
    thread.start()

    print("Camera started")


def capture_loop():
    global running, cap

    BASE_DIR = Path(__file__).resolve().parents[2]  # về project_root
    IMAGE_DIR = BASE_DIR / "images"

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)

    while running:
        ret, frame = cap.read()

        if ret:
            filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
            image_path = IMAGE_DIR / filename

            cv2.imwrite(str(image_path), frame)

            print("Saved to:", image_path)

        time.sleep(30)





def stop_camera():
    global running, cap

    running = False

    if cap:
        cap.release()
        cap = None

    print("Camera stopped")

def gen_frames():
    global cap

    if cap is None:
        cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')