from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base

class AIResult(Base):
    __tablename__ = "ai_results"

    result_id = Column(Integer, primary_key=True, index=True)
    temporary_student_id = Column(String(100))
    face_bbox = Column(String)
    ai_label = Column(String(100))
    user_label = Column(String(100))
    confidence = Column(Float)
    frame_id = Column(Integer, ForeignKey("frames.frame_id", ondelete="CASCADE"))

    # relationship
    frame = relationship("Frame", back_populates="ai_results")