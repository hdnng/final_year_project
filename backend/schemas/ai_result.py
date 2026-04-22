"""AI result request/response schemas."""

from typing import Optional

from pydantic import BaseModel, Field


class AIResultResponse(BaseModel):
    """Full AI result record."""

    result_id: int
    temporary_student_id: str
    ai_label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    face_bbox: str
    frame_id: int

    model_config = {"from_attributes": True}


class AIResultUpdate(BaseModel):
    """Payload for user label correction."""

    status: str = Field(..., min_length=1, max_length=100)


class AIResultUpdateResponse(BaseModel):
    """Response after updating an AI result label."""

    result_id: int
    user_label: Optional[str] = None
    ai_label: Optional[str] = None
