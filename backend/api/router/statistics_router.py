"""Statistics endpoints — daily, weekly, by-date, and summary."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from core.logger import get_logger
from database.database import get_db
from models.user import User
from schemas.statistics import DailyStatItem, DateStatItem, StatsSummaryResponse, WeeklyStatItem
from service.statistics_service import (
    get_daily_stats,
    get_stats_by_date,
    get_stats_summary,
    get_weekly_stats,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/stats", tags=["Statistics"])


@router.get("/daily", response_model=list[DailyStatItem])
def stats_daily(
    days: int = Query(30, ge=1, le=365, description="Number of past days"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get daily aggregated statistics for the last N days."""
    try:
        user_id_filter = None if user.role == "admin" else user.user_id
        return get_daily_stats(db, user_id_filter, days)
    except Exception as exc:
        logger.error(f"Error fetching daily stats: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch daily statistics")


@router.get("/by-date", response_model=list[DateStatItem])
def stats_by_date(
    days: int = Query(30, ge=1, le=365, description="Number of past days"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get sleeping counts by date for the last N days."""
    try:
        user_id_filter = None if user.role == "admin" else user.user_id
        return get_stats_by_date(db, user_id_filter, days)
    except Exception as exc:
        logger.error(f"Error fetching by-date stats: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch date statistics")


@router.get("/weekly", response_model=list[WeeklyStatItem])
def stats_weekly(
    weeks: int = Query(4, ge=1, le=52, description="Number of past weeks"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get weekly aggregated statistics for the last N weeks."""
    try:
        user_id_filter = None if user.role == "admin" else user.user_id
        return get_weekly_stats(db, user_id_filter, weeks)
    except Exception as exc:
        logger.error(f"Error fetching weekly stats: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch weekly statistics")


@router.get("/summary", response_model=StatsSummaryResponse)
def stats_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get overall statistics summary."""
    try:
        user_id_filter = None if user.role == "admin" else user.user_id
        return get_stats_summary(db, user_id_filter)
    except Exception as exc:
        logger.error(f"Error fetching summary: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch summary")
