from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from models.ai_result import AIResult

router = APIRouter(prefix="/ai-result", tags=["AI Result"])


@router.patch("/{result_id}")
def update_ai_result(
    result_id: int,
    payload: dict,
    db: Session = Depends(get_db)
):
    record = db.query(AIResult).filter(
        AIResult.result_id == result_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="AI result not found")

    # update USER label (không đụng ai_label)
    new_status = payload.get("status")

    if new_status:
        record.user_label = new_status

    db.commit()

    return {
        "result_id": result_id,
        "user_label": record.user_label,
        "ai_label": record.ai_label
    }