from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional, List


# =========================
# USER SCHEMAS
# =========================
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    full_name: str = Field(..., min_length=3, max_length=100)

    @field_validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(BaseModel):
    user_id: int
    email: str
    full_name: str

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr


class ChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=100)


# =========================
# FRAME SCHEMAS
# =========================
class FrameResponse(BaseModel):
    frame_id: int
    image_path: str
    extracted_at: datetime
    session_id: int

    class Config:
        from_attributes = True


# =========================
# AI RESULT SCHEMAS
# =========================
class AIResultResponse(BaseModel):
    result_id: int
    temporary_student_id: str
    ai_label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    face_bbox: str
    frame_id: int

    class Config:
        from_attributes = True


# =========================
# STATISTICS SCHEMAS
# =========================
class StatisticResponse(BaseModel):
    statistic_id: int
    timestamp: datetime
    total_students: int = Field(..., ge=0)
    sleeping_count: int = Field(..., ge=0)
    focus_rate: float = Field(..., ge=0.0, le=1.0)
    session_id: int

    class Config:
        from_attributes = True


# =========================
# SESSION SCHEMAS
# =========================
class SessionResponse(BaseModel):
    session_id: int
    class_id: str = Field(..., min_length=1, max_length=100)
    start_time: datetime
    end_time: Optional[datetime] = None
    camera_url: str
    user_id: Optional[int] = None

    class Config:
        from_attributes = True


class SessionDetailResponse(BaseModel):
    session_id: int
    class_id: str
    total_students: int
    sleeping: int
    focus_rate: float
    alerts: int
    duration: int  # minutes
    frames: List[dict]

    class Config:
        from_attributes = True