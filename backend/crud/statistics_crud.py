"""CRUD operations for the Statistic model."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session as DBSession

from models.ai_result import AIResult
from models.statistic import Statistic
from utils.label_utils import get_final_label


def create_statistics(db: DBSession, data: dict, session_id: int) -> Statistic:
    """Create a new statistic snapshot. Uses ``flush()`` so the ID is available before commit."""
    stat = Statistic(
        timestamp=datetime.now(timezone.utc),
        total_students=data["total"],
        sleeping_count=data["sleeping"],
        focus_rate=data["focus_rate"],
        session_id=session_id,
    )
    db.add(stat)
    db.flush()
    return stat


def get_stats_by_session(db: DBSession, session_id: int) -> list[Statistic]:
    """Retrieve all statistics for a session, newest first."""
    return (
        db.query(Statistic)
        .filter(Statistic.session_id == session_id)
        .order_by(Statistic.timestamp.desc())
        .all()
    )


def recalculate_statistics_for_frame(
    db: DBSession,
    session_id: int,
    frame_id: int,
) -> Optional[Statistic]:
    """
    Recalculate the statistics row that corresponds to a specific frame's
    AI results. This is called after a user corrects a label so that
    session-level aggregates stay in sync.

    The function finds the statistic record closest to the frame's capture
    time and updates its counts based on the current effective labels
    (respecting ``user_label`` overrides via ``get_final_label``).
    """
    from models.frame import Frame

    # Get all results for this specific frame
    results = db.query(AIResult).filter(AIResult.frame_id == frame_id).all()
    if not results:
        return None

    total = len(results)
    sleeping = sum(
        1 for r in results if "Sleeping" in (get_final_label(r) or "")
    )
    focus_rate = 1 - (sleeping / total) if total else 0.0

    # Find the frame to get its timestamp
    frame = db.query(Frame).filter(Frame.frame_id == frame_id).first()
    if not frame:
        return None

    # Find the statistic record closest to this frame's extraction time.
    # Statistics are created at the same moment as frames in _save_snapshot,
    # so we find the one with the closest timestamp.
    stats = (
        db.query(Statistic)
        .filter(Statistic.session_id == session_id)
        .order_by(Statistic.timestamp.desc())
        .all()
    )

    if not stats:
        return None

    # Match by position: frames and stats are created in pairs.
    # Get all frames for this session ordered the same way as stats.
    frames = (
        db.query(Frame)
        .filter(Frame.session_id == session_id)
        .order_by(Frame.extracted_at.desc())
        .all()
    )

    # Find the index of our frame in the list
    target_idx = None
    for idx, f in enumerate(frames):
        if f.frame_id == frame_id:
            target_idx = idx
            break

    if target_idx is not None and target_idx < len(stats):
        stat = stats[target_idx]
        stat.total_students = total
        stat.sleeping_count = sleeping
        stat.focus_rate = focus_rate
        db.commit()
        db.refresh(stat)
        return stat

    return None