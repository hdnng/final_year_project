from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from typing import List

from models.frame import Frame
from models.session import Session as SessionModel
from database.database import get_db
from core.dependencies import get_current_user
from service.camera_service import (
    list_camera_with_name,
    start_camera,
    stop_camera,
    list_cameras
)
from service.stream_service import gen_frames
from schemas.schemas import FrameResponse, SessionResponse
from core.logger import get_logger
from core.exceptions import ValidationError, NotFoundError, AuthenticationError

logger = get_logger(__name__)
router = APIRouter(prefix="/camera", tags=["Camera"])


# =========================
# STREAM VIDEO
# =========================
@router.get("/video_feed")
def video_feed():
    """
    Stream video frames trong MJPEG format

    Public endpoint - được control bởi /start và /stop (đã protected)

    Trả về: Stream video từ camera đang chạy
    Content-Type: multipart/x-mixed-replace
    """
    try:
        logger.debug(f"📹 Video feed requested")
        return StreamingResponse(
            gen_frames(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
    except Exception as e:
        logger.error(f"❌ Video stream error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start video stream")


# =========================
# START CAMERA (TẠO SESSION)
# =========================
@router.post("/start", response_model=dict)
def start(
    camera_index: int = Query(0, ge=0, description="Camera index"),
    class_id: str = Query(..., min_length=1, max_length=100, description="Class ID"),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bắt đầu capture video từ camera

    - **camera_index**: Index của camera (default: 0)
    - **class_id**: ID lớp học (bắt buộc)

    Returns:
    - session_id: ID của session vừa tạo
    - message: Trạng thái

    Requires: JWT Authentication
    """
    try:
        if not class_id.strip():
            logger.warning(f"❌ Start camera - empty class_id by user: {user_id}")
            raise ValidationError(detail="class_id is required")

        logger.info(f"🎬 Starting camera by user {user_id} - index={camera_index}, class_id={class_id}")

        session_id = start_camera(
            user_id=user_id,
            camera_index=camera_index,
            class_id=class_id
        )

        logger.info(f"✅ Camera started by user {user_id} - session_id={session_id}")

        return {
            "message": f"Camera {camera_index} started",
            "session_id": session_id,
            "status": "running",
            "user_id": user_id
        }

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to start camera by user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start camera: {str(e)}")


# =========================
# STOP CAMERA
# =========================
@router.post("/stop", response_model=dict)
def stop(user_id: int = Depends(get_current_user)):
    """
    Dừng camera capture và kết thúc session

    Requires: JWT Authentication
    """
    try:
        logger.info(f"🛑 Stopping camera by user: {user_id}")
        stop_camera()
        logger.info(f"✅ Camera stopped by user: {user_id}")
        return {
            "message": "Camera stopped",
            "status": "stopped",
            "user_id": user_id
        }
    except Exception as e:
        logger.error(f"❌ Failed to stop camera by user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to stop camera: {str(e)}")


# =========================
# LIST CAMERA
# =========================
@router.get("/list", response_model=dict)
def list_cam():
    """
    Liệt kê tất cả camera sẵn có trên hệ thống

    Returns:
    - cameras: List camera với index và name
    """
    try:
        logger.debug("📋 Listing available cameras")
        cameras = list_camera_with_name()
        logger.debug(f"✅ Found {len(cameras)} cameras")

        return {
            "cameras": cameras,
            "count": len(cameras)
        }
    except Exception as e:
        logger.error(f"❌ Failed to list cameras: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list cameras")


# =========================
# GET FRAMES BY SESSION
# =========================
@router.get("/frames/{session_id}", response_model=List[FrameResponse])
def get_frames(
    session_id: int,
    skip: int = Query(0, ge=0, description="Skip frames"),
    limit: int = Query(50, ge=1, le=500, description="Limit frames"),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách frames của 1 session

    - **session_id**: ID của session
    - **skip**: Số frames bỏ qua (pagination)
    - **limit**: Số frames trả về (max: 500)

    Returns: List[FrameResponse]

    Requires: JWT Authentication
    """
    try:
        logger.debug(f"📷 Fetching frames by user {user_id} - session_id={session_id}, skip={skip}, limit={limit}")

        frames = db.query(Frame).filter(
            Frame.session_id == session_id
        ).order_by(Frame.extracted_at.desc()).offset(skip).limit(limit).all()

        if not frames:
            logger.warning(f"⚠️ No frames found by user {user_id} - session_id={session_id}")

        logger.debug(f"✅ Retrieved {len(frames)} frames for user {user_id}")
        return frames

    except Exception as e:
        logger.error(f"❌ Failed to fetch frames by user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch frames")


# =========================
# GET ALL SESSIONS (HISTORY)
# =========================
@router.get("/sessions", response_model=List[SessionResponse])
def get_sessions(
    skip: int = Query(0, ge=0, description="Skip sessions"),
    limit: int = Query(20, ge=1, le=100, description="Limit sessions"),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách tất cả sessions

    - **skip**: Số sessions bỏ qua
    - **limit**: Số sessions trả về (max: 100)

    Returns: List[SessionResponse]

    Requires: JWT Authentication
    """
    try:
        logger.debug(f"📋 Fetching sessions by user {user_id} - skip={skip}, limit={limit}")

        sessions = db.query(SessionModel).order_by(
            SessionModel.start_time.desc()
        ).offset(skip).limit(limit).all()

        logger.debug(f"✅ Retrieved {len(sessions)} sessions for user {user_id}")
        return sessions

    except Exception as e:
        logger.error(f"❌ Failed to fetch sessions by user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch sessions")
