from service.camera_state import CameraState
import os
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
    try:
        session = db.query(SessionModel).filter(
            SessionModel.session_id == session_id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # ===== lấy frames =====
        frames = db.query(Frame).filter(
            Frame.session_id == session_id
        ).order_by(Frame.extracted_at.desc()).all()

        # ===== lấy statistics =====
        stats = db.query(Statistic).filter(
            Statistic.session_id == session_id
        ).order_by(Statistic.timestamp.desc()).all()

        # ===== ghép frame với statistic theo index =====
        frame_list = []

        total_students = 0
        total_sleeping = 0
        total_focus = 0

        for i, frame in enumerate(frames):

            stat = stats[i] if i < len(stats) else None

            students = stat.total_students if stat else 0
            sleeping = stat.sleeping_count if stat else 0
            focus = stat.focus_rate if stat else 0

            total_students += students
            total_sleeping += sleeping
            total_focus += focus

            frame_list.append({
                "frame_id": frame.frame_id,
                "time": frame.extracted_at.strftime("%H:%M:%S"),
                "status": "Ngủ gật" if sleeping > 0 else "Bình thường",
                "students": students,
                "accuracy": round(focus * 100, 1),
                "sleeping": sleeping
            })

        # ===== averages =====
        count = len(frame_list)

        avg_students = round(total_students / count) if count else 0
        avg_focus = round(total_focus / count, 3) if count else 0

        # ===== duration =====
        duration = 0
        if session.start_time and session.end_time:
            duration = int(
                (session.end_time - session.start_time).total_seconds() / 60
            )

        return {
            "session_id": session_id,
            "class_id": session.class_id,
            "total_students": avg_students,
            "sleeping": total_sleeping,
            "focus_rate": avg_focus,
            "alerts": total_sleeping,
            "duration": duration,
            "frames": frame_list
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@router.delete("/session/{session_id}")
@router.delete("/session/{session_id}")
def delete_session(
    session_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # =========================
        # 1. GET SESSION + CHECK USER
        # =========================
        session = db.query(SessionModel).filter(
            SessionModel.session_id == session_id,
            SessionModel.user_id == user_id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # =========================
        # 2. BLOCK IF RUNNING
        # =========================
        state = CameraState()

        if state.running and state.current_session_id == session_id:
            raise HTTPException(
                status_code=400,
                detail="Không thể xóa phiên đang chạy"
            )

        # =========================
        # 3. DELETE FILES (SAFE PATH)
        # =========================
        BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        frames = db.query(Frame).filter(Frame.session_id == session_id).all()

        for frame in frames:
            if frame.image_path:
                full_path = os.path.join(BASE_DIR, frame.image_path)

                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                    except Exception as e:
                        logger.warning(f"❌ Cannot delete file {full_path}: {e}")

        # =========================
        # 4. MANUAL DELETE DB (SAFE - NO DEPENDENCY ON CASCADE)
        # =========================

        # AI results
        from models.ai_result import AIResult

        db.query(AIResult).filter(
            AIResult.frame_id.in_(
                db.query(Frame.frame_id).filter(Frame.session_id == session_id)
            )
        ).delete(synchronize_session=False)

        # statistics
        db.query(Statistic).filter(
            Statistic.session_id == session_id
        ).delete(synchronize_session=False)

        # frames
        db.query(Frame).filter(
            Frame.session_id == session_id
        ).delete(synchronize_session=False)

        # session
        db.delete(session)

        db.commit()

        return {
            "message": "Xóa session thành công",
            "session_id": session_id
        }

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Delete session failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))