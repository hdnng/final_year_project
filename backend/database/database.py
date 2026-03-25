from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# =========================
# DATABASE CONFIG
# =========================
DATABASE_URL = "postgresql+psycopg2://postgres:410183Hd%40@127.0.0.1:5432/student_behavior_ai"

# =========================
# ENGINE
# =========================
engine = create_engine(
    DATABASE_URL,
    echo=False  # bật True nếu muốn debug SQL
)

# =========================
# SESSION LOCAL
# =========================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# =========================
# BASE
# =========================
Base = declarative_base()


# =========================
# DEPENDENCY (QUAN TRỌNG)
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()