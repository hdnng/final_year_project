"""CRUD operations for the Session model."""

import os
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession

from core.logger import get_logger
from models.ai_result import AIResult
from models.frame import Frame
from models.session import Session as SessionModel
from models.statistic import Statistic

logger = get_logger(__name__)


def create_session(
    db: DBSession,
    user_id: int,
    class_id: str,
    camera_url: str,
) -> SessionModel:
    """Create a new camera session."""
    session = SessionModel(
        class_id=class_id,
        start_time=datetime.now(timezone.utc),
        camera_url=camera_url,
        user_id=user_id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def end_session(db: DBSession, session_id: int) -> None:
    """Mark a session as ended by setting its end_time."""
    session = (
        db.query(SessionModel)
        .filter(SessionModel.session_id == session_id)
        .first()
    )
    if session:
        session.end_time = datetime.now(timezone.utc)
        db.commit()


def get_session_by_id(
    db: DBSession,
    session_id: int,
) -> Optional[SessionModel]:
    """Retrieve a single session by its primary key."""
    return (
        db.query(SessionModel)
        .filter(SessionModel.session_id == session_id)
        .first()
    )


def get_sessions_by_user(
    db: DBSession,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
) -> list[SessionModel]:
    """Retrieve sessions for a user, newest first, with pagination."""
    return (
        db.query(SessionModel)
        .filter(SessionModel.user_id == user_id)
        .order_by(SessionModel.start_time.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_sessions_with_frame_count(
    db: DBSession,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
) -> list[Any]:
    """Retrieve sessions with an aggregated frame count (single query)."""
    query = (
        db.query(
            SessionModel.session_id,
            SessionModel.class_id,
            SessionModel.start_time,
            func.count(Frame.frame_id).label("frame_count"),
        )
        .outerjoin(Frame, Frame.session_id == SessionModel.session_id)
        .filter(SessionModel.user_id == user_id)
    )

    if search:
        query = query.filter(SessionModel.class_id.ilike(f"%{search}%"))

    return (
        query
        .group_by(SessionModel.session_id)
        .order_by(SessionModel.start_time.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_session_count_by_user(db: DBSession, user_id: int) -> int:
    """Count total sessions for a user."""
    return (
        db.query(func.count(SessionModel.session_id))
        .filter(SessionModel.user_id == user_id)
        .scalar()
        or 0
    )


def get_monthly_session_count_by_user(db: DBSession, user_id: int) -> int:
    """Count sessions created during the current month."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    return (
        db.query(func.count(SessionModel.session_id))
        .filter(
            SessionModel.user_id == user_id,
            SessionModel.start_time >= month_start,
        )
        .scalar()
        or 0
    )


def delete_session_cascade(
    db: DBSession,
    session_id: int,
    user_id: int,
    base_dir: str,
) -> bool:
    """
    Delete a session and all related data.

    Cascade order: image files → AI results → statistics → frames → session.
    Returns True if the session was found and deleted.
    """
    session = (
        db.query(SessionModel)
        .filter(
            SessionModel.session_id == session_id,
            SessionModel.user_id == user_id,
        )
        .first()
    )
    if not session:
        return False

    # Remove image files from disk
    frames = db.query(Frame).filter(Frame.session_id == session_id).all()
    for frame in frames:
        if frame.image_path:
            full_path = os.path.join(base_dir, frame.image_path)
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                except OSError as exc:
                    logger.warning(f"Failed to delete file {full_path}: {exc}")

    # Delete related records
    frame_ids = db.query(Frame.frame_id).filter(Frame.session_id == session_id)

    db.query(AIResult).filter(
        AIResult.frame_id.in_(frame_ids)
    ).delete(synchronize_session=False)

    db.query(Statistic).filter(
        Statistic.session_id == session_id
    ).delete(synchronize_session=False)

    db.query(Frame).filter(
        Frame.session_id == session_id
    ).delete(synchronize_session=False)

    db.delete(session)
    db.commit()
    return True