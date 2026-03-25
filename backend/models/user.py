from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database.database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    full_name = Column(String)
    password = Column(String)
    role = Column(String, default="teacher")

    # relationship
    sessions = relationship("Session", back_populates="user")