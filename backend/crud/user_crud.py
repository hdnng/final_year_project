from sqlalchemy.orm import Session
import models.user as user
import schemas.schemas as schemas
from core.security import hash_password


def create_user(db: Session, user_data: schemas.UserCreate):

    hashed_password = hash_password(user_data.password)

    db_user = user.User(
        name = user_data.name,
        email = user_data.email,
        password = hashed_password
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def get_user_by_email(db: Session, email: str):

    return db.query(user.User).filter(
        user.User.email == email
    ).first()

def get_user_by_id(db: Session, user_id: int):

    return db.query(user.User).filter(
        user.User.userId == user_id
    ).first()