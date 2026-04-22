"""CRUD operations for the AIResult model."""

from typing import Optional

from sqlalchemy.orm import Session as DBSession

from models.ai_result import AIResult


def create_ai_result(db: DBSession, data: dict, frame_id: int) -> AIResult:
    """Create a new AI detection result. Uses ``flush()`` so the ID is available before commit."""
    ai = AIResult(
        temporary_student_id="unknown",
        face_bbox=str(data["bbox"]),
        ai_label=data["label"],
        confidence=data["confidence"],
        frame_id=frame_id,
    )
    db.add(ai)
    db.flush()
    return ai


def get_ai_results_by_frame(db: DBSession, frame_id: int) -> list[AIResult]:
    """Retrieve all AI results associated with a frame."""
    return db.query(AIResult).filter(AIResult.frame_id == frame_id).all()


def update_ai_result_label(
    db: DBSession,
    result_id: int,
    user_label: str,
) -> Optional[AIResult]:
    """Apply a user correction to an AI result. Returns None if not found."""
    record = db.query(AIResult).filter(AIResult.result_id == result_id).first()
    if not record:
        return None

    record.user_label = user_label
    db.commit()
    db.refresh(record)
    return record