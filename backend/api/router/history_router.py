from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import List

from database.database import get_db
from core.dependencies import get_current_user
from models.session import Session as SessionModel
from models.frame import Frame
from models.statistic import Statistic
from core.logger import get_logger
from schemas.schemas import SessionResponse, SessionDetailResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/history", tags=["History"])


@router.get("/sessions", response_model=List[dict])
def get_sessions(
    skip: int = Query(0, ge=0, description="Skip số sessions"),
    limit: int = Query(20, ge=1, le=100, description="Giới hạn sessions (max 100)"),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách sessions với pagination

    - **skip**: Số sessions cần bỏ qua (default: 0)
    - **limit**: Số sessions trả về (default: 20, max: 100)

    Optimized: Sử dụng single query thay vì N+1

    Requires: JWT Authentication
    """
    try:
        logger.info(f"📋 Fetching sessions by user {user_id} - skip={skip}, limit={limit}")

        # Single query using outer join + group by
        sessions = db.query(
            SessionModel.session_id,
            SessionModel.class_id,
            SessionModel.start_time,
            func.count(Frame.frame_id).label("frame_count")
        ).outerjoin(
            Frame, Frame.session_id == SessionModel.session_id
        ).filter(
            SessionModel.user_id == user_id
        ).group_by(
            SessionModel.session_id
        ).order_by(
            SessionModel.start_time.desc()
        ).offset(skip).limit(limit).all()

        logger.debug(f"✅ Retrieved {len(sessions)} sessions for user {user_id}")

        return [
            {
                "session_id": s.session_id,
                "class_id": s.class_id,
                "date": s.start_time.strftime("%d/%m/%Y") if s.start_time else "",
                "frame_count": s.frame_count
            }
            for s in sessions
        ]

    except Exception as e:
        logger.error(f"❌ Error fetching sessions by user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch sessions")


@router.get("/summary")
def get_summary(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy tóm tắt thống kê: tổng sessions + sessions tháng này

    Requires: JWT Authentication
    """
    try:
        logger.info(f"📊 Fetching summary statistics by user {user_id}")

        now = datetime.utcnow()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Total sessions for user
        total = db.query(func.count(SessionModel.session_id)).filter(
            SessionModel.user_id == user_id
        ).scalar() or 0

        # Sessions created this month
        month_total = db.query(func.count(SessionModel.session_id)).filter(
            SessionModel.user_id == user_id,
            SessionModel.start_time >= current_month_start
        ).scalar() or 0

        logger.debug(f"✅ Summary retrieved for user {user_id}")

        return {
            "total_sessions": int(total),
            "month_sessions": int(month_total)
        }

    except Exception as e:
        logger.error(f"❌ Error fetching summary by user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch summary")


@router.get("/session/{session_id}", response_model=SessionDetailResponse)
def get_session_detail(
    session_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy chi tiết 1 session bao gồm:
    - Session info
    - Statistics aggregates
    - Frames data
    - Duration

    Optimized: Minimal queries with proper joins

    Requires: JWT Authentication
    """
    try:
        logger.info(f"📋 Fetching session detail by user {user_id} - session_id={session_id}")

        # ===== SESSION =====
        session = db.query(SessionModel).filter(
            SessionModel.session_id == session_id
        ).first()

        if not session:
            logger.warning(f"⚠️ Session not found by user {user_id} - session_id={session_id}")
            raise HTTPException(status_code=404, detail="Session not found")

        # ===== STATS - Tối ưu hóa vào 1 query =====
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

        # ===== FRAMES - Optimized join (not N+1) =====
        frames_data = db.query(
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

        frame_list = [
            {
                "frame_id": f.frame_id,
                "time": f.extracted_at.strftime("%H:%M:%S"),
                "status": "Ngủ gật" if f.sleeping_count > 0 else "Bình thường",
                "students": f.total_students,
                "accuracy": round(f.focus_rate * 100, 1),
                "sleeping": f.sleeping_count
            }
            for f in frames_data
        ]

        logger.debug(f"✅ Session detail retrieved by user {user_id} - frames={len(frame_list)}")

        return {
            "session_id": session_id,
            "class_id": session.class_id,
            "total_students": total_students,
            "sleeping": total_sleeping,
            "focus_rate": round(avg_focus, 3) if avg_focus else 0,
            "alerts": total_sleeping,
            "duration": duration,
            "frames": frame_list
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching session detail by user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch session detail")
