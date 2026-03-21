from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import schemas.schemas as schemas
import crud.user_crud as user_crud
from database.database import SessionLocal
from core.security import hash_password, verify_password
from core.auth import create_access_token
from core.dependencies import get_current_user
from models.user import User

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

@router.get("/profile")
def get_profile(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    user = user_crud.get_user_by_id(db, user_id)

    return {
        "name": user.name,
        "email": user.email
    }


@router.put("/update")
def update_user(
    data: schemas.UserUpdate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(User.userId == user_id).first()

    user.name = data.name
    user.email = data.email

    db.commit()

    return {"message": "updated"}


@router.put("/change-password")
def change_password(
    data: schemas.ChangePassword,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.userId == user_id).first()

    # kiểm tra mật khẩu cũ
    if not verify_password(data.old_password, user.password):
        raise HTTPException(status_code=400, detail="Sai mật khẩu cũ")

    # cập nhật mật khẩu mới
    user.password = hash_password(data.new_password)
    db.commit()

    return {"message": "Đổi mật khẩu thành công"}