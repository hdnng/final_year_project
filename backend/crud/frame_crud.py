from models.frame import Frame
from datetime import datetime

def create_frame(db, image_path, session_id):
    frame = Frame(
        image_path=image_path,
        extracted_at=datetime.now(),
        session_id=session_id
    )
    db.add(frame)
    db.commit()