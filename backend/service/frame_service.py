"""
Frame business logic — analysis data, detail view, and label corrections.
"""

from sqlalchemy.orm import Session as DBSession

from core.exceptions import NotFoundError
from core.logger import get_logger
from crud.ai_result_crud import get_ai_results_by_frame, update_ai_result_label
from crud.frame_crud import get_frame_by_id, get_frames_by_session
from utils.label_utils import get_final_label

logger = get_logger(__name__)


def get_analysis_data(db: DBSession, session_id: int) -> list[dict]:
    """Compute per-frame focus/sleeping counts for a session."""
    frames = get_frames_by_session(db, session_id, skip=0, limit=10_000)

    data: list[dict] = []
    for frame in frames:
        results = get_ai_results_by_frame(db, frame.frame_id)

        sleeping = sum(
            1 for r in results if "Sleeping" in (get_final_label(r) or "")
        )
        total = len(results)

        data.append({
            "frame_id": frame.frame_id,
            "image_path": frame.image_path,
            "extracted_at": frame.extracted_at,
            "focus_count": total - sleeping,
            "sleeping_count": sleeping,
            "total_students": total,
        })

    return data


def get_frame_detail(db: DBSession, frame_id: int) -> dict:
    """
    Return detailed info for a single frame including all detections.

    Raises:
        NotFoundError: Frame does not exist.
    """
    frame = get_frame_by_id(db, frame_id)
    if not frame:
        raise NotFoundError(detail="Frame not found")

    rows = get_ai_results_by_frame(db, frame_id)
    total = len(rows)
    sleeping = sum(1 for r in rows if "Sleeping" in (r.ai_label or ""))
    avg_conf = round(sum(r.confidence for r in rows) / total, 2) if total else 0.0

    detections = [
        {
            "result_id": r.result_id,
            "student_id": f"HS{i}",
            "status": get_final_label(r),
            "confidence": r.confidence,
        }
        for i, r in enumerate(rows, start=1)
    ]

    return {
        "frame_id": frame.frame_id,
        "image_path": frame.image_path,
        "total_students": total,
        "sleeping_count": sleeping,
        "focus_count": total - sleeping,
        "avg_confidence": avg_conf,
        "detections": detections,
    }


def update_result_label(db: DBSession, result_id: int, status: str) -> dict:
    """
    Apply a user-corrected label to an AI result.

    Raises:
        NotFoundError: AI result does not exist.
    """
    record = update_ai_result_label(db, result_id, status)
    if not record:
        raise NotFoundError(detail="AI result not found")

    return {
        "result_id": result_id,
        "user_label": record.user_label,
        "ai_label": record.ai_label,
    }
