"""CRUD operations for the User model."""

from typing import Optional

from sqlalchemy.orm import Session as DBSession

from core.security import hash_password
from models.user import User
from schemas.user import UserCreate


def create_user(db: DBSession, user_data: UserCreate) -> User:
    """Create a new user with a hashed password."""
    db_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        password=hash_password(user_data.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: DBSession, email: str) -> Optional[User]:
    """Look up a user by email address."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: DBSession, user_id: int) -> Optional[User]:
    """Look up a user by primary key."""
    return db.query(User).filter(User.user_id == user_id).first()


def update_user_profile(
    db: DBSession,
    user_id: int,
    full_name: str,
    email: str,
) -> Optional[User]:
    """Update a user's display name and email. Returns None if not found."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return None

    user.full_name = full_name
    user.email = email
    db.commit()
    db.refresh(user)
    return user


def update_user_password(
    db: DBSession,
    user_id: int,
    hashed_password: str,
) -> bool:
    """Update a user's password (expects a pre-hashed value)."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return False

    user.password = hashed_password
    db.commit()
    return True