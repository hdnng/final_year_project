from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: str
    password: str


class User(BaseModel):
    user_id: int
    email: str
    full_name: str

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: str
    email: str

class ChangePassword(BaseModel):
    old_password: str
    new_password: str