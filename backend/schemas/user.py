"""User request/response schemas."""

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Requests ────────────────────────────────────────────────


class UserCreate(BaseModel):
    """Registration payload."""

    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    full_name: str = Field(..., min_length=3, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """Login payload."""

    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Profile update payload."""

    full_name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr


class ChangePassword(BaseModel):
    """Password change payload."""

    old_password: str
    new_password: str = Field(..., min_length=6, max_length=100)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# ── Responses ───────────────────────────────────────────────


class UserResponse(BaseModel):
    """Public user profile (no sensitive fields)."""

    user_id: int
    email: str
    full_name: str

    model_config = {"from_attributes": True}
