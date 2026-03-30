from sqlalchemy import Column, Integer, Float, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base

class Statistic(Base):
    __tablename__ = "statistics"

    statistic_id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    total_students = Column(Integer)
    sleeping_count = Column(Integer)
    focus_rate = Column(Float)
    session_id = Column(Integer, ForeignKey("sessions.session_id", ondelete="CASCADE"))

    # relationship
    session = relationship("Session", back_populates="statistics")