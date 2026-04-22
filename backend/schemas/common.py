"""Common response schemas shared across multiple endpoints."""

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Standard single-message response."""

    message: str


class TokenResponse(BaseModel):
    """Token payload returned by login/refresh endpoints."""

    message: str
    user_id: int
    access_token: str
    refresh_token: str | None = None
