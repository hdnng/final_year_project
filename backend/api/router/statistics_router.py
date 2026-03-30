from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.database import get_db
from models.ai_result import AIResult
from models.frame import Frame
from models.statistic import Statistic
router = APIRouter(prefix="/stats", tags=["Statistics"])

@router.get("/daily")
def stats_daily(db: Session = Depends(get_db)):

    results = db.query(
        func.date(Statistic.timestamp),
        func.sum(Statistic.total_students),
        func.sum(Statistic.sleeping_count)
    ).group_by(
        func.date(Statistic.timestamp)
    ).all()

    return [
        {
            "date": str(r[0]),
            "total": int(r[1] or 0),
            "sleeping": int(r[2] or 0),
            "focus_rate": 1 - (r[2] / r[1]) if r[1] else 0
        }
        for r in results
    ]


@router.get("/by-date")
def stats_by_date(db: Session = Depends(get_db)):

    results = db.query(
        func.date(Statistic.timestamp),
        func.sum(Statistic.sleeping_count)
    ).group_by(
        func.date(Statistic.timestamp)
    ).all()

    return [
        {"date": str(r[0]), "value": int(r[1] or 0)}
        for r in results
    ]