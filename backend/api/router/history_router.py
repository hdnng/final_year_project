"""History endpoints — session list, detail, summary, and deletion."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from core.logger import get_logger
from database.database import get_db
from schemas.common import MessageResponse
from schemas.session import SessionDetailResponse, SessionListItem, SessionSummaryResponse
from service.session_service import (
    delete_session,
    get_session_detail,
    get_session_list,
    get_session_summary,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/history", tags=["History"])


@router.get("/sessions", response_model=list[SessionListItem])
def get_sessions(
    skip: int = Query(0, ge=0, description="Number of sessions to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max sessions to return"),
    search: str = Query("", description="Search by class name"),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List sessions with pagination and optional class search."""
    try:
        return get_session_list(db, user_id, skip, limit, search or None)
    except Exception as exc:
        logger.error(f"Error fetching sessions: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch sessions")


@router.get("/summary", response_model=SessionSummaryResponse)
def get_summary(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get dashboard summary: total sessions + sessions this month."""
    try:
        return get_session_summary(db, user_id)
    except Exception as exc:
        logger.error(f"Error fetching summary: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch summary")


@router.get("/session/{session_id}", response_model=SessionDetailResponse)
def get_session_detail_endpoint(
    session_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full session detail with frames and statistics."""
    try:
        return get_session_detail(db, session_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error fetching session detail: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/session/{session_id}")
def delete_session_endpoint(
    session_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a session and all related data (blocked if currently running)."""
    try:
        return delete_session(db, session_id, user_id)
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        logger.error(f"Delete session failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))