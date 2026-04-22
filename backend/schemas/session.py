"""Session request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SessionResponse(BaseModel):
    """Full session record."""

    session_id: int
    class_id: str = Field(..., min_length=1, max_length=100)
    start_time: datetime
    end_time: Optional[datetime] = None
    camera_url: str
    user_id: Optional[int] = None

    model_config = {"from_attributes": True}


class SessionListItem(BaseModel):
    """Lightweight session entry for history lists."""

    session_id: int
    class_id: str
    date: str
    frame_count: int


class SessionFrameItem(BaseModel):
    """Frame summary within a session detail view."""

    frame_id: int
    time: str
    status: str
    students: int
    accuracy: float
    sleeping: int


class SessionDetailResponse(BaseModel):
    """Session detail with aggregated stats and frame list."""

    session_id: int
    class_id: str
    total_students: int
    sleeping: int
    focus_rate: float
    alerts: int
    duration: int  # minutes
    frames: list[SessionFrameItem]

    model_config = {"from_attributes": True}


class SessionSummaryResponse(BaseModel):
    """High-level session counts for the dashboard."""

    total_sessions: int
    month_sessions: int
