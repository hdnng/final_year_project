from sqlalchemy.orm import Session
from models.ai_result import AIResult

def create_ai_result(db: Session, data: dict, frame_id: int):
    ai = AIResult(
        temporary_student_id="unknown",
        face_bbox=str(data["bbox"]),
        ai_label=data["label"],
        confidence=data["confidence"],
        frame_id=frame_id
    )
    db.add(ai)
    db.flush()  # Để lấy ai_result_id trước khi commit
    return ai