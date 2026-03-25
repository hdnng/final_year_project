import cv2
import time
import threading
import pythoncom
from datetime import datetime
from pathlib import Path

from database.database import SessionLocal
from crud.session_crud import create_session, end_session
from crud.frame_crud import create_frame
from pygrabber.dshow_graph import FilterGraph
from ai_model.ai_pipeline import process_frame

# ===== GLOBAL STATE =====
cap = None
running = False
thread = None
current_session_id = None
latest_frame = None   # 🔥 dùng cho stream


# =========================
# START CAMERA
# =========================
def start_camera(user_id=1, class_id="Unknown", camera_index=0):
    global cap, running, thread, current_session_id

    if running:
        return current_session_id

    db = SessionLocal()

    # ===== TẠO SESSION =====
    session = create_session(
        db=db,
        user_id=user_id,
        class_id=class_id,
        camera_url=f"camera_{camera_index}"
    )

    current_session_id = session.session_id

    # ===== OPEN CAMERA (FIX BACKEND) =====
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

    if not cap.isOpened():
        raise Exception(f"Cannot open camera {camera_index}")

    running = True

    # ===== START THREAD =====
    thread = threading.Thread(target=capture_loop)
    thread.daemon = True
    thread.start()

    print(f"Camera {camera_index} started with session {current_session_id}")

    return current_session_id


# =========================
# CAPTURE LOOP
# =========================
def capture_loop():
    global running, cap, current_session_id, latest_frame

    db = SessionLocal()

    BASE_DIR = Path(__file__).resolve().parents[2]
    IMAGE_DIR = BASE_DIR / "images"
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    last_save_time = 0

    while running:
        if cap is None:
            time.sleep(0.1)
            continue

        ret, frame = cap.read()

        if not ret:
            continue

        # 🔥 dùng cho stream
        #latest_frame = frame.copy()

        processed_frame = process_frame(frame)
        latest_frame = processed_frame.copy()

        # ===== SAVE mỗi 30s =====
        if time.time() - last_save_time > 30:
            filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
            image_path = IMAGE_DIR / filename

            cv2.imwrite(str(image_path), frame)

            if current_session_id:
                create_frame(db, str(image_path), current_session_id)

            print(f"Saved: {image_path}")

            last_save_time = time.time()

        time.sleep(0.03)  # ~30 FPS


# =========================
# STOP CAMERA
# =========================
def stop_camera():
    global running, cap, current_session_id

    if not running:
        return

    running = False

    if cap:
        cap.release()
        cap = None

    db = SessionLocal()

    if current_session_id:
        end_session(db, current_session_id)
        print(f"Session {current_session_id} ended")

    current_session_id = None

    print("Camera stopped")


# =========================
# STREAM VIDEO
# =========================
def gen_frames():
    global latest_frame

    while True:
        if latest_frame is None:
            time.sleep(0.1)
            continue

        ret, buffer = cv2.imencode('.jpg', latest_frame)
        frame_bytes = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
        )


# =========================
# LIST CAMERA
# =========================
def list_cameras(max_index=5):
    available = []

    for i in range(max_index):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)

        if cap is None or not cap.isOpened():
            continue

        # 🔥 test đọc frame (quan trọng)
        ret, _ = cap.read()

        if ret:
            available.append(i)

        cap.release()

    return available


def list_camera_with_name():
    pythoncom.CoInitialize()  # 🔥 bắt buộc

    try:
        devices = FilterGraph().get_input_devices()

        return [
            {"index": i, "name": name}
            for i, name in enumerate(devices)
        ]

    finally:
        pythoncom.CoUninitialize()  # 🔥 cleanup