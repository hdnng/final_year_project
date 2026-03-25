from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base

class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(Integer, primary_key=True, index=True)
    class_id = Column(String(100))
    start_time = Column(TIMESTAMP, default=datetime.utcnow)
    end_time = Column(TIMESTAMP, nullable=True)
    camera_url = Column(String)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"))

    # relationship
    user = relationship("User", back_populates="sessions")
    frames = relationship("Frame", back_populates="session", cascade="all, delete")
    statistics = relationship("Statistic", back_populates="session", cascade="all, delete")