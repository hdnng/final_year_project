"""CRUD operations for the Frame model."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session as DBSession

from models.frame import Frame


def create_frame(db: DBSession, image_path: str, session_id: int) -> Frame:
    """Create a new frame record. Uses ``flush()`` so the ID is available before commit."""
    frame = Frame(
        image_path=image_path,
        extracted_at=datetime.now(timezone.utc),
        session_id=session_id,
    )
    db.add(frame)
    db.flush()
    return frame


def get_frame_by_id(db: DBSession, frame_id: int) -> Optional[Frame]:
    """Retrieve a single frame by its primary key."""
    return db.query(Frame).filter(Frame.frame_id == frame_id).first()


def get_frames_by_session(
    db: DBSession,
    session_id: int,
    skip: int = 0,
    limit: int = 50,
) -> list[Frame]:
    """Retrieve frames for a session, newest first, with pagination."""
    return (
        db.query(Frame)
        .filter(Frame.session_id == session_id)
        .order_by(Frame.extracted_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )