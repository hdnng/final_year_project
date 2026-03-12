from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from database.database import Base

class User(Base):
    __tablename__ = "users"

    userId = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    name = Column(String)
    password = Column(String)
    role = Column(String, default="student")