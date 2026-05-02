import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base


def get_database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql://voiceresumeai:voiceresumeai@localhost:5432/voiceresumeai",
    )


engine = create_engine(
    get_database_url(),
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
