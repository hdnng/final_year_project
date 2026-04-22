"""Camera request/response schemas."""

from typing import Optional

from pydantic import BaseModel


class CameraDevice(BaseModel):
    """A single camera device entry."""

    index: int
    name: str


class CameraListResponse(BaseModel):
    """List of available camera devices."""

    cameras: list[CameraDevice]
    count: int


class CameraStartResponse(BaseModel):
    """Response when a camera session starts."""

    message: str
    session_id: int
    status: str
    user_id: int


class CameraStopResponse(BaseModel):
    """Response when a camera session stops."""

    message: str
    status: str
    user_id: int


class CameraInfoResponse(BaseModel):
    """Camera resolution and running state."""

    width: int
    height: int
    running: bool


class CameraStatusResponse(BaseModel):
    """Current camera status."""

    running: bool
    session_id: Optional[int] = None
