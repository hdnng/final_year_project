from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from database.database import get_db
from models.session import Session as SessionModel
from models.frame import Frame

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/sessions")
def get_sessions(db: Session = Depends(get_db)):
    sessions = db.query(
        SessionModel.session_id,
        SessionModel.class_id,
        SessionModel.start_time,
        func.count(Frame.frame_id).label("frame_count")
    ).outerjoin(
        Frame, Frame.session_id == SessionModel.session_id
    ).group_by(
        SessionModel.session_id
    ).order_by(
        SessionModel.start_time.desc()
    ).all()

    return [
        {
            "session_id": s.session_id,
            "class_id": s.class_id,
            "date": s.start_time.strftime("%d/%m/%Y") if s.start_time else "",
            "frame_count": s.frame_count
        }
        for s in sessions
    ]


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    now = datetime.now()

    total = db.query(func.count(SessionModel.session_id)).scalar()

    month = db.query(func.count(SessionModel.session_id)).filter(
        func.extract("month", SessionModel.start_time) == now.month,
        func.extract("year", SessionModel.start_time) == now.year
    ).scalar()

    return {
        "total_sessions": total,
        "month_sessions": month
    }



@router.get("/session/{session_id}")
def get_session_detail(session_id: int, db: Session = Depends(get_db)):
    from models.session import Session as SessionModel
    from models.frame import Frame
    from models.statistic import Statistic
    from sqlalchemy import func

    # ===== SESSION =====
    session = db.query(SessionModel).filter(
        SessionModel.session_id == session_id
    ).first()

    if not session:
        return {"error": "Session not found"}

    # ===== STATS =====
    stats = db.query(
        func.sum(Statistic.total_students),
        func.sum(Statistic.sleeping_count),
        func.avg(Statistic.focus_rate),
        func.count(Statistic.statistic_id)
    ).filter(
        Statistic.session_id == session_id
    ).first()

    total_students = int(stats[0] or 0)
    total_sleeping = int(stats[1] or 0)
    avg_focus = float(stats[2] or 0)
    total_records = int(stats[3] or 0)

    # ===== THỜI GIAN =====
    duration = 0
    if session.start_time and session.end_time:
        duration = int((session.end_time - session.start_time).total_seconds() / 60)

    # ===== FRAME TABLE =====
    frames = db.query(
        Frame.frame_id,
        Frame.extracted_at,
        Statistic.total_students,
        Statistic.sleeping_count,
        Statistic.focus_rate
    ).join(
        Statistic, Statistic.session_id == Frame.session_id
    ).filter(
        Frame.session_id == session_id
    ).order_by(Frame.extracted_at.desc()).all()

    frame_list = []
    for f in frames:
        frame_list.append({
            "time": f.extracted_at.strftime("%H:%M:%S"),
            "status": "Ngủ gật" if f.sleeping_count > 0 else "Bình thường",
            "students": f.total_students,
            "accuracy": round(f.focus_rate * 100, 1),
            "sleeping": f.sleeping_count
        })

    return {
        "session_id": session_id,
        "class_id": session.class_id,
        "total_students": total_students,
        "sleeping": total_sleeping,
        "focus_rate": avg_focus,
        "alerts": total_sleeping,
        "duration": duration,
        "frames": frame_list
    }