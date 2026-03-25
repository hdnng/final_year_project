from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

from database.database import get_db
from service.camera_service import (
    gen_frames,
    list_camera_with_name,
    start_camera,
    stop_camera,
    list_cameras
)

router = APIRouter(prefix="/camera", tags=["camera"])


# =========================
# STREAM VIDEO
# =========================
@router.get("/video_feed")
def video_feed():
    return StreamingResponse(
        gen_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


# =========================
# START CAMERA (TẠO SESSION)
# =========================
@router.post("/start")
def start(
    camera_index: int = 0,
    class_id: str = ""
):
    if not class_id.strip():
        raise HTTPException(status_code=400, detail="class_id is required")

    try:
        session_id = start_camera(
            camera_index=camera_index,
            class_id=class_id
        )

        return {
            "message": f"camera {camera_index} started",
            "session_id": session_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
def stop():
    try:
        stop_camera()
        return {"message": "camera stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================
# LIST CAMERA
# =========================
@router.get("/list")
def list_cam():
    return {"cameras": list_camera_with_name()}


# =========================
# GET FRAMES BY SESSION
# =========================
@router.get("/frames/{session_id}")
def get_frames(session_id: int, db: Session = Depends(get_db)):
    from models.frame import Frame

    frames = db.query(Frame).filter(
        Frame.session_id == session_id
    ).order_by(Frame.extracted_at.desc()).all()

    return frames


# =========================
# GET ALL SESSIONS (HISTORY)
# =========================
@router.get("/sessions")
def get_sessions(db: Session = Depends(get_db)):
    from models import session as SessionModel

    sessions = db.query(SessionModel).order_by(
        SessionModel.start_time.desc()
    ).all()

    return sessions