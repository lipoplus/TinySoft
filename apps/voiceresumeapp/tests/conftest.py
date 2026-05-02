import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = os.getenv(
    "DATABASE_URL",
    "postgresql://voiceresumeai:voiceresumeai@localhost:5432/voiceresumeai_test",
)

from main import app
from platform_db import Base, get_db


@pytest.fixture
def db():
    engine = create_engine(os.environ["DATABASE_URL"])
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    return TestClient(app)
