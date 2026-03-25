from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database.database import Base

class Frame(Base):
    __tablename__ = "frames"

    frame_id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String)
    extracted_at = Column(TIMESTAMP, default=datetime.utcnow)
    session_id = Column(Integer, ForeignKey("sessions.session_id", ondelete="CASCADE"))

    # relationship
    session = relationship("Session", back_populates="frames")
    ai_results = relationship("AIResult", back_populates="frame", cascade="all, delete")