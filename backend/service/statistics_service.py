"""
Statistics business logic — daily, weekly, by-date, and summary aggregations.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession

from core.logger import get_logger
from models.statistic import Statistic

logger = get_logger(__name__)


def get_daily_stats(db: DBSession, user_id: int, days: int = 30) -> list[dict]:
    """Aggregate statistics per day for the last *days* days."""
    results = (
        db.query(
            func.date(Statistic.timestamp),
            func.sum(Statistic.total_students),
            func.sum(Statistic.sleeping_count),
        )
        .group_by(func.date(Statistic.timestamp))
        .order_by(func.date(Statistic.timestamp).desc())
        .limit(days)
        .all()
    )

    return [
        {
            "date": str(r[0]),
            "total": int(r[1] or 0),
            "sleeping": int(r[2] or 0),
            "focus_rate": 1 - (r[2] / r[1]) if r[1] else 0.0,
        }
        for r in results
    ]


def get_stats_by_date(db: DBSession, user_id: int, days: int = 30) -> list[dict]:
    """Aggregate sleeping counts per day for the last *days* days."""
    results = (
        db.query(
            func.date(Statistic.timestamp),
            func.sum(Statistic.sleeping_count),
        )
        .group_by(func.date(Statistic.timestamp))
        .order_by(func.date(Statistic.timestamp).desc())
        .limit(days)
        .all()
    )

    return [
        {"date": str(r[0]), "value": int(r[1] or 0)}
        for r in results
    ]


def get_weekly_stats(db: DBSession, user_id: int, weeks: int = 4) -> list[dict]:
    """Aggregate statistics per ISO week for the last *weeks* weeks."""
    week_expr = func.to_char(Statistic.timestamp, 'YYYY-"W"IW')

    results = (
        db.query(
            week_expr.label("week"),
            func.sum(Statistic.total_students),
            func.avg(Statistic.focus_rate),
        )
        .group_by(week_expr)
        .order_by(week_expr.desc())
        .limit(weeks)
        .all()
    )

    return [
        {
            "week": r[0],
            "total": int(r[1] or 0),
            "focus_rate": round(float(r[2]) if r[2] else 0.0, 3),
        }
        for r in results
    ]


def get_stats_summary(db: DBSession, user_id: int) -> dict:
    """Return overall aggregated statistics."""
    result = db.query(
        func.count(Statistic.statistic_id),
        func.sum(Statistic.total_students),
        func.avg(Statistic.focus_rate),
        func.sum(Statistic.sleeping_count),
    ).first()

    return {
        "total_records": int(result[0] or 0),
        "total_students": int(result[1] or 0),
        "avg_focus_rate": round(float(result[2]) if result[2] else 0.0, 3),
        "sleeping_alerts": int(result[3] or 0),
    }
