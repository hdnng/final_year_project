from models.statistic import Statistic
from datetime import datetime

def create_statistics(db, data, session_id):
    stat = Statistic(
        timestamp=datetime.utcnow(),
        total_students=data["total"],
        sleeping_count=data["sleeping"],
        focus_rate=data["focus_rate"],
        session_id=session_id
    )
    db.add(stat)
    db.flush()  # Để lấy statistic_id trước khi commit
    return stat