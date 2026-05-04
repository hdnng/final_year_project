"""Frame request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FrameResponse(BaseModel):
    """Basic frame record."""

    frame_id: int
    image_path: str
    extracted_at: datetime
    session_id: int

    model_config = {"from_attributes": True}


class FrameAnalysisItem(BaseModel):
    """Frame with computed focus/sleeping counts."""

    frame_id: int
    image_path: str
    extracted_at: datetime
    focus_count: int
    sleeping_count: int
    total_students: int


class DetectionItem(BaseModel):
    """Single AI detection within a frame."""

    result_id: int
    student_id: str
    status: str
    confidence: float
    user_label: Optional[str] = None
    face_bbox: Optional[list[int]] = None


class FrameDetailResponse(BaseModel):
    """Full frame detail with all detections."""

    frame_id: int
    session_id: int
    image_path: str
    total_students: int
    sleeping_count: int
    focus_count: int
    avg_confidence: float
    detections: list[DetectionItem]
