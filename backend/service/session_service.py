"""
Session business logic — listing, detail, summary, and deletion.
"""

from sqlalchemy.orm import Session as DBSession

from core.config import settings
from core.exceptions import NotFoundError, ValidationError
from core.logger import get_logger
from crud.ai_result_crud import get_ai_results_by_frames
from crud.frame_crud import get_frames_by_session
from crud.session_crud import (
    delete_session_cascade,
    get_monthly_session_count_by_user,
    get_session_by_id,
    get_session_count_by_user,
    get_sessions_with_frame_count,
)
from service.camera_state import CameraState
from utils.label_utils import get_final_label

logger = get_logger(__name__)


def get_session_list(
    db: DBSession,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
) -> list[dict]:
    """Return a lightweight list of sessions with frame counts."""
    sessions = get_sessions_with_frame_count(db, user_id, skip, limit, search)

    return [
        {
            "session_id": s.session_id,
            "class_id": s.class_id,
            "date": s.start_time.strftime("%d/%m/%Y") if s.start_time else "",
            "frame_count": s.frame_count,
        }
        for s in sessions
    ]


def get_session_summary(db: DBSession, user_id: int) -> dict:
    """Return dashboard summary: total sessions + sessions this month."""
    return {
        "total_sessions": get_session_count_by_user(db, user_id),
        "month_sessions": get_monthly_session_count_by_user(db, user_id),
    }


def get_session_detail(db: DBSession, session_id: int) -> dict:
    """
    Return full session detail with per-frame statistics.

    Computes sleeping/focus counts directly from ai_results (respecting
    user label corrections) so that changes propagate in real time.

    Raises:
        NotFoundError: Session does not exist.
    """
    session = get_session_by_id(db, session_id)
    if not session:
        raise NotFoundError(detail="Session not found")

    frames = get_frames_by_session(db, session_id, skip=0, limit=10_000)

    # Batch fetch all AI results for these frames to prevent N+1 query problem
    frame_ids = [frame.frame_id for frame in frames]
    all_ai_results = get_ai_results_by_frames(db, frame_ids)

    # Group results by frame_id for O(1) lookup
    results_by_frame = {frame_id: [] for frame_id in frame_ids}
    for r in all_ai_results:
        results_by_frame[r.frame_id].append(r)

    # Build frame list — compute stats from ai_results directly
    frame_list: list[dict] = []
    total_students = 0
    total_sleeping = 0
    total_focus = 0.0

    for frame in frames:
        results = results_by_frame.get(frame.frame_id, [])

        students = len(results)
        sleeping = sum(
            1 for r in results if "Sleeping" in (get_final_label(r) or "")
        )
        focus = 1 - (sleeping / students) if students else 0.0

        total_students += students
        total_sleeping += sleeping
        total_focus += focus

        frame_list.append({
            "frame_id": frame.frame_id,
            "time": frame.extracted_at.strftime("%H:%M:%S"),
            "status": "Sleeping detected" if sleeping > 0 else "Normal",
            "students": students,
            "accuracy": round(focus * 100, 1),
            "sleeping": sleeping,
        })

    # Averages
    count = len(frame_list)
    avg_students = round(total_students / count) if count else 0
    avg_focus = round(total_focus / count, 3) if count else 0.0

    # Duration in minutes
    duration = 0
    if session.start_time and session.end_time:
        duration = int((session.end_time - session.start_time).total_seconds() / 60)

    return {
        "session_id": session_id,
        "class_id": session.class_id,
        "total_students": avg_students,
        "sleeping": total_sleeping,
        "focus_rate": avg_focus,
        "alerts": total_sleeping,
        "duration": duration,
        "frames": frame_list,
    }


def delete_session(
    db: DBSession,
    session_id: int,
    user_id: int,
) -> dict:
    """
    Delete a session and all related data.

    Raises:
        ValidationError: Session is currently running.
        NotFoundError:   Session does not exist.
    """
    state = CameraState()
    if state.running and state.current_session_id == session_id:
        raise ValidationError(detail="Cannot delete a running session")

    success = delete_session_cascade(
        db, session_id, user_id, str(settings.BASE_DIR)
    )

    if not success:
        raise NotFoundError(detail="Session not found")

    return {"message": "Session deleted successfully", "session_id": session_id}

