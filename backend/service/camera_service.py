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
from crud.statistics_crud import create_statistics
from crud.ai_result_crud import create_ai_result

# ===== GLOBAL =====
cap = None
running = False
thread = None
current_session_id = None
latest_frame = None

frame_count = 0


# =========================
# START CAMERA
# =========================
def start_camera(user_id=1, class_id="Unknown", camera_index=0):
    global cap, running, thread, current_session_id

    if running:
        return current_session_id

    db = SessionLocal()

    session = create_session(
        db=db,
        user_id=user_id,
        class_id=class_id,
        camera_url=f"camera_{camera_index}"
    )

    current_session_id = session.session_id

    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

    # 🔥 giảm FPS
    cap.set(cv2.CAP_PROP_FPS, 15)

    if not cap.isOpened():
        raise Exception(f"Cannot open camera {camera_index}")

    running = True

    thread = threading.Thread(target=capture_loop)
    thread.daemon = True
    thread.start()

    print(f"Camera {camera_index} started")

    return current_session_id


# =========================
# CAPTURE LOOP
# =========================
def capture_loop():
    global running, cap, current_session_id, latest_frame, frame_count

    db = SessionLocal()

    BASE_DIR = Path(__file__).resolve().parents[2]
    IMAGE_DIR = BASE_DIR / "images"
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    last_save_time = 0

    while running:
        ret, frame = cap.read()
        if not ret:
            continue

        frame_count += 1

        # ===== SKIP FRAME (chỉ xử lý mỗi 3 frame) =====
        processed_frame, results = process_frame(frame, frame_count)
        latest_frame = processed_frame

        # ===== SAVE mỗi 30s =====
        if time.time() - last_save_time > 30:
            filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
            image_path = IMAGE_DIR / filename

            cv2.imwrite(str(image_path), frame)

            if current_session_id:
                frame_obj = create_frame(db, str(image_path), current_session_id)

                # 🔥 LƯU AI RESULTS
                

                # lưu ai_results
                for r in results:
                    create_ai_result(db, r, frame_obj.frame_id)

                # 🔥 TÍNH & LƯU STATISTICS
                stats_data = calculate_stats(results)

                create_statistics(db, stats_data, current_session_id)

                db.commit()
            print(f"Saved: {image_path}")
            last_save_time = time.time()

        time.sleep(0.03)  # ~30 FPS


# =========================
# STOP CAMERA
# =========================
def stop_camera():
    global running, cap, current_session_id

    running = False

    if cap:
        cap.release()
        cap = None

    db = SessionLocal()

    if current_session_id:
        end_session(db, current_session_id)

    current_session_id = None
    print("Camera stopped")


# =========================
# STREAM
# =========================
def gen_frames():
    global latest_frame

    while True:
        if latest_frame is None:
            time.sleep(0.05)
            continue

        # 🔥 giảm chất lượng JPEG
        ret, buffer = cv2.imencode(
            '.jpg',
            latest_frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), 70]
        )

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            buffer.tobytes() +
            b'\r\n'
        )


# =========================
# LIST CAMERA
# =========================
def list_cameras(max_index=5):
    available = []

    for i in range(max_index):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available.append(i)
        cap.release()

    return available


def list_camera_with_name():
    pythoncom.CoInitialize()

    try:
        devices = FilterGraph().get_input_devices()
        return [{"index": i, "name": name} for i, name in enumerate(devices)]
    finally:
        pythoncom.CoUninitialize()


def calculate_stats(results):
    total = len(results)
    sleeping = sum(1 for r in results if "Sleeping" in r["label"])

    focus_rate = 1 - (sleeping / total) if total else 0

    return {
        "total": total,
        "sleeping": sleeping,
        "focus_rate": focus_rate
    }