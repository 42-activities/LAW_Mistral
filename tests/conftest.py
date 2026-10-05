from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

from app.db import engine
from app.main import create_app
from app.modules.seed.france_uae import seed


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture(scope="session")
def _migrated_db():
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    yield


def _session_on(eng: Engine) -> Iterator[Session]:
    """A session whose work, commits included, is rolled back after the test."""
    connection = eng.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def db_session(_migrated_db) -> Iterator[Session]:
    """An empty, migrated database."""
    yield from _session_on(engine)


@pytest.fixture(scope="session")
def _seeded_engine() -> Iterator[Engine]:
    """A second database (`<name>_seeded`), migrated and seeded once per test run.

    Seeding takes seconds, so doing it per test made the suite take minutes. A separate database
    keeps `db_session` empty for the tests that build their own minimal rows.
    """
    url = engine.url
    name = f"{url.database}_seeded"
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{name}"'))
    admin.dispose()

    seeded = create_engine(url.set(database=name))
    with seeded.begin() as conn:
        cfg = Config("alembic.ini")
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")
    with Session(seeded) as session:
        seed(session)
        session.commit()
    yield seeded
    seeded.dispose()


@pytest.fixture
def seeded_session(_seeded_engine) -> Iterator[Session]:
    """The full seed data set; each test's changes are rolled back."""
    yield from _session_on(_seeded_engine)
