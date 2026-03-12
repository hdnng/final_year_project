import cv2
import os
import time
import threading
from datetime import datetime

cap = None
running = False


def start_camera():

    global cap, running

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

    while running:

        ret, frame = cap.read()

        if ret:

            filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"

            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

            image_path = os.path.join(base_dir, "images", filename)

            cv2.imwrite(image_path, frame)

            print("Saved:", image_path)

        time.sleep(30)


def stop_camera():

    global running, cap

    running = False

    if cap:
        cap.release()

    print("Camera stopped")