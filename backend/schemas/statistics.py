"""Statistics request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class StatisticResponse(BaseModel):
    """Single statistic record."""

    statistic_id: int
    timestamp: datetime
    total_students: int = Field(..., ge=0)
    sleeping_count: int = Field(..., ge=0)
    focus_rate: float = Field(..., ge=0.0, le=1.0)
    session_id: int

    model_config = {"from_attributes": True}


class DailyStatItem(BaseModel):
    """Aggregated statistics for a single day."""

    date: str
    total: int
    sleeping: int
    focus_rate: float


class WeeklyStatItem(BaseModel):
    """Aggregated statistics for a single week."""

    week: str
    total: int
    focus_rate: float


class DateStatItem(BaseModel):
    """Sleeping count for a specific date."""

    date: str
    value: int


class StatsSummaryResponse(BaseModel):
    """Overall statistics summary for the dashboard."""

    total_records: int
    total_students: int
    avg_focus_rate: float
    sleeping_alerts: int
