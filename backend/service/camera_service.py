import cv2
import threading
import pythoncom

from database.database import SessionLocal
from crud.session_crud import create_session, end_session
from pygrabber.dshow_graph import FilterGraph
from service.pipeline_service import capture_loop
from service.camera_state import CameraState


# =========================
# START CAMERA
# =========================
def start_camera(user_id=1, class_id="Unknown", camera_index=0):

    state = CameraState()

    if state.is_running():
        return state.current_session_id

    db = SessionLocal()

    session = create_session(
        db=db,
        user_id=user_id,
        class_id=class_id,
        camera_url=f"camera_{camera_index}"
    )

    state.current_session_id = session.session_id

    state.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

    # Reduce FPS to 15
    state.cap.set(cv2.CAP_PROP_FPS, 15)

    if not state.cap.isOpened():
        raise Exception(f"Cannot open camera {camera_index}")

    state.running = True

    state.thread = threading.Thread(target=capture_loop)
    state.thread.daemon = True
    state.thread.start()

    print(f"Camera {camera_index} started")

    return state.current_session_id

# =========================
# STOP CAMERA
# =========================
def stop_camera():

    state = CameraState()
    state.running = False

    if state.cap:
        state.cap.release()
        state.cap = None

    db = SessionLocal()

    if state.current_session_id:
        end_session(db, state.current_session_id)

    state.reset()
    print("Camera stopped")

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
