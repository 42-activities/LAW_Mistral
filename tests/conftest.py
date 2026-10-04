import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import engine
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture(scope="session")
def _migrated_db():
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    yield


@pytest.fixture
def db_session(_migrated_db) -> Session:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
