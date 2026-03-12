from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import schemas.schemas as schemas
import crud.user_crud as user_crud
from database.database import SessionLocal
from core.security import verify_password
from core.auth import create_access_token

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return user_crud.create_user(db, user)


@router.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):

    db_user = user_crud.get_user_by_email(db, user.email)

    if not db_user:
        return {"error": "User not found"}

    if not verify_password(user.password, db_user.password):
        return {"error": "Wrong password"}
    
    token = create_access_token(
        data={"user_Id": db_user.userId}
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }