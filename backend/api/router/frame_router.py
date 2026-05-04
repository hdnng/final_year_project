"""Frame endpoints — frame list, analysis data, and frame detail."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from core.logger import get_logger
from database.database import get_db
from schemas.frame import FrameAnalysisItem, FrameDetailResponse, FrameResponse
from crud.frame_crud import get_frames_by_session
from service.frame_service import get_analysis_data, get_frame_detail
from models.user import User

logger = get_logger(__name__)
router = APIRouter(prefix="/frames", tags=["Frame"])


@router.get("/{session_id}", response_model=list[FrameAnalysisItem])
def get_frames(
    session_id: int,
    skip: int = Query(0, ge=0, description="Number of frames to skip"),
    limit: int = Query(50, ge=1, le=500, description="Max frames to return"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List frames for a session with pagination and analysis data."""
    try:
        return get_analysis_data(db, session_id, skip, limit)
    except Exception as exc:
        logger.error(f"Error fetching frames: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch frames")


@router.get("/analysis/{session_id}", response_model=list[FrameAnalysisItem])
def get_analysis(
    session_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10000, ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get per-frame analysis data (focus/sleeping counts) for a session."""
    return get_analysis_data(db, session_id, skip, limit)


@router.get("/detail/{frame_id}", response_model=FrameDetailResponse)
def frame_detail(
    frame_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed info for a single frame including all detections."""
    return get_frame_detail(db, frame_id)
