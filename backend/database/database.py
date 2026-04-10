import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# =========================
# LOAD ENV VARIABLES
# =========================
load_dotenv()

# =========================
# DATABASE CONFIG
# =========================
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file")

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