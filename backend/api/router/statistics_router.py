from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import List

from database.database import get_db
from core.dependencies import get_current_user
from models.statistic import Statistic
from core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/stats", tags=["Statistics"])


@router.get("/daily", response_model=List[dict])
def stats_daily(
    days: int = Query(30, ge=1, le=365, description="Số ngày quá khứ (max: 365)"),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy thống kê hàng ngày trong N ngày quá khứ

    - **days**: Số ngày cần lấy dữ liệu (default: 30, max: 365)

    Returns:
    - date: Ngày (YYYY-MM-DD)
    - total: Tổng số sinh viên
    - sleeping: Số sinh viên ngủ gật
    - focus_rate: Tỷ lệ tập trung

    Requires: JWT Authentication
    """
    try:
        logger.info(f"📊 Fetching daily stats by user {user_id} for {days} days")

        results = db.query(
            func.date(Statistic.timestamp),
            func.sum(Statistic.total_students),
            func.sum(Statistic.sleeping_count)
        ).group_by(
            func.date(Statistic.timestamp)
        ).order_by(
            func.date(Statistic.timestamp).desc()
        ).limit(days).all()

        logger.debug(f"✅ Retrieved {len(results)} days of statistics for user {user_id}")

        return [
            {
                "date": str(r[0]),
                "total": int(r[1] or 0),
                "sleeping": int(r[2] or 0),
                "focus_rate": 1 - (r[2] / r[1]) if r[1] else 0
            }
            for r in results
        ]

    except Exception as e:
        logger.error(f"❌ Error fetching daily stats by user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch daily statistics")


@router.get("/by-date", response_model=List[dict])
def stats_by_date(
    days: int = Query(30, ge=1, le=365, description="Số ngày quá khứ"),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy tổng số sinh viên ngủ gật theo ngày

    - **days**: Số ngày cần lấy dữ liệu

    Returns:
    - date: Ngày (YYYY-MM-DD)
    - value: Số sinh viên ngủ gật

    Requires: JWT Authentication
    """
    try:
        logger.info(f"📊 Fetching sleeping stats by user {user_id} for {days} days")

        results = db.query(
            func.date(Statistic.timestamp),
            func.sum(Statistic.sleeping_count)
        ).group_by(
            func.date(Statistic.timestamp)
        ).order_by(
            func.date(Statistic.timestamp).desc()
        ).limit(days).all()

        logger.debug(f"✅ Retrieved {len(results)} dates for user {user_id}")

        return [
            {"date": str(r[0]), "value": int(r[1] or 0)}
            for r in results
        ]

    except Exception as e:
        logger.error(f"❌ Error fetching by-date stats by user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch date statistics")


@router.get("/weekly", response_model=List[dict])
def stats_weekly(
    weeks: int = Query(4, ge=1, le=52, description="Số tuần quá khứ"),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy thống kê hàng tuần

    - **weeks**: Số tuần cần lấy dữ liệu (default: 4)

    Returns:
    - week: Tuần (YYYY-W##)
    - total: Tổng sinh viên
    - focus_rate: Tỷ lệ tập trung trung bình

    Requires: JWT Authentication
    """
    try:
        logger.info(f"📊 Fetching weekly stats by user {user_id} for {weeks} weeks")

        results = db.query(
            func.to_char(
                Statistic.timestamp, 'YYYY-"W"IW'
            ).label("week"),
            func.sum(Statistic.total_students),
            func.avg(Statistic.focus_rate)
        ).group_by(
            func.to_char(Statistic.timestamp, 'YYYY-"W"IW')
        ).order_by(
            func.to_char(Statistic.timestamp, 'YYYY-"W"IW').desc()
        ).limit(weeks).all()

        logger.debug(f"✅ Retrieved {len(results)} weeks for user {user_id}")

        return [
            {
                "week": r[0],
                "total": int(r[1] or 0),
                "focus_rate": round(float(r[2]) if r[2] else 0, 3)
            }
            for r in results
        ]

    except Exception as e:
        logger.error(f"❌ Error fetching weekly stats by user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch weekly statistics")


@router.get("/summary", response_model=dict)
def stats_summary(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy tóm tắt thống kê tổng hợp

    Returns:
    - total_records: Tổng số records
    - total_students: Tổng sinh viên được phát hiện
    - avg_focus_rate: Tỷ lệ tập trung trung bình
    - sleeping_alerts: Tổng cảnh báo ngủ gật

    Requires: JWT Authentication
    """
    try:
        logger.info(f"📊 Fetching statistics summary by user {user_id}")

        result = db.query(
            func.count(Statistic.statistic_id),
            func.sum(Statistic.total_students),
            func.avg(Statistic.focus_rate),
            func.sum(Statistic.sleeping_count)
        ).first()

        summary = {
            "total_records": int(result[0] or 0),
            "total_students": int(result[1] or 0),
            "avg_focus_rate": round(float(result[2]) if result[2] else 0, 3),
            "sleeping_alerts": int(result[3] or 0)
        }

        logger.debug(f"✅ Summary retrieved for user {user_id}")
        return summary

    except Exception as e:
        logger.error(f"❌ Error fetching summary by user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch summary")
