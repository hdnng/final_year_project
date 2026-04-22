"""Camera endpoints — start/stop, list devices, status, video feed."""

import cv2
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from core.exceptions import ValidationError
from core.logger import get_logger
from database.database import get_db
from schemas.camera import (
    CameraInfoResponse,
    CameraListResponse,
    CameraStartResponse,
    CameraStatusResponse,
    CameraStopResponse,
)
from service.camera_service import list_camera_with_name, start_camera, stop_camera
from service.camera_state import CameraState
from service.stream_service import gen_frames

logger = get_logger(__name__)
router = APIRouter(prefix="/camera", tags=["Camera"])


@router.get("/video_feed")
def video_feed():
    """Stream live video in MJPEG format."""
    try:
        return StreamingResponse(
            gen_frames(),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )
    except Exception as exc:
        logger.error(f"Video stream error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start video stream")


@router.post("/start", response_model=CameraStartResponse)
def start(
    camera_index: int = Query(0, ge=0, description="Camera device index"),
    class_id: str = Query(..., min_length=1, max_length=100, description="Class identifier"),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start capturing from a camera and create a new session."""
    if not class_id.strip():
        raise ValidationError(detail="class_id is required")

    try:
        session_id = start_camera(
            user_id=user_id,
            camera_index=camera_index,
            class_id=class_id,
        )
        return {
            "message": f"Camera {camera_index} started",
            "session_id": session_id,
            "status": "running",
            "user_id": user_id,
        }
    except ValidationError:
        raise
    except Exception as exc:
        logger.error(f"Failed to start camera: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start camera: {exc}")


@router.post("/stop", response_model=CameraStopResponse)
def stop(user_id: int = Depends(get_current_user)):
    """Stop the active camera and finalize the session."""
    try:
        stop_camera()
        return {"message": "Camera stopped", "status": "stopped", "user_id": user_id}
    except Exception as exc:
        logger.error(f"Failed to stop camera: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to stop camera: {exc}")


@router.get("/list", response_model=CameraListResponse)
def list_cam():
    """List all available camera devices on the system."""
    try:
        cameras = list_camera_with_name()
        return {"cameras": cameras, "count": len(cameras)}
    except Exception as exc:
        logger.error(f"Failed to list cameras: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list cameras")


@router.get("/info", response_model=CameraInfoResponse)
def camera_info():
    """Get camera resolution and running state."""
    state = CameraState()
    if not state.cap:
        return {"width": 1280, "height": 720, "running": False}

    return {
        "width": int(state.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(state.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "running": state.running,
    }


@router.get("/status", response_model=CameraStatusResponse)
def camera_status():
    """Get current camera status."""
    state = CameraState()
    return {"running": state.running, "session_id": state.current_session_id}
