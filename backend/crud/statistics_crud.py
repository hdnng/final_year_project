"""CRUD operations for the Statistic model."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session as DBSession

from models.statistic import Statistic


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