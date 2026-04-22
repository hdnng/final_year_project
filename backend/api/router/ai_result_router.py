"""AI result endpoints — label correction."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from database.database import get_db
from schemas.ai_result import AIResultUpdate, AIResultUpdateResponse
from service.frame_service import update_result_label

router = APIRouter(prefix="/ai-result", tags=["AI Result"])


@router.patch("/{result_id}", response_model=AIResultUpdateResponse)
def update_ai_result(
    result_id: int,
    payload: AIResultUpdate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Apply a user-corrected label to an AI detection result."""
    return update_result_label(db, result_id, payload.status)