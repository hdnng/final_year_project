from sqlalchemy.orm import Session
from models.session import Session as SessionModel
from datetime import datetime

def create_session(db: Session, user_id: int, class_id: str, camera_url: str):
    new_session = SessionModel(
        class_id=class_id,
        start_time=datetime.now(),
        camera_url=camera_url,
        user_id=user_id
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


def end_session(db, session_id):
    session = db.query(SessionModel).filter(
        SessionModel.session_id == session_id
    ).first()

    if session:
        session.end_time = datetime.now()
        db.commit()