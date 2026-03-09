from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

DEFAULT_DB_FILE = Path(__file__).resolve().parents[1] / "hoferland.db"
if settings.database_url:
    SQLALCHEMY_DATABASE_URL = settings.database_url
else:
    db_path = Path(settings.sqlite_db_path) if settings.sqlite_db_path else DEFAULT_DB_FILE
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
