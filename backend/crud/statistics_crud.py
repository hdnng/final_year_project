from models.statistic import Statistic
from datetime import datetime

def create_statistics(db, data, session_id):
    stat = Statistic(
        timestamp=datetime.now(),
        total_students=data["total"],
        sleeping_count=data["sleeping"],
        focus_rate=data["focus_rate"],
        session_id=session_id
    )
    db.add(stat)
    return stat