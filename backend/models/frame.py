"""Frame (captured image) model."""

from datetime import datetime, timezone

from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP
from sqlalchemy.orm import relationship

from database.database import Base


class Frame(Base):
    __tablename__ = "frames"

    frame_id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String, nullable=False)
    extracted_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))
    session_id = Column(Integer, ForeignKey("sessions.session_id", ondelete="CASCADE"))

    # Relationships
    session = relationship("Session", back_populates="frames")
    ai_results = relationship("AIResult", back_populates="frame", cascade="all, delete")

    def __repr__(self) -> str:
        return f"<Frame(id={self.frame_id}, session={self.session_id})>"