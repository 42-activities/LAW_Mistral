from sqlalchemy import text

from app.db import engine


def test_expected_schemas_exist(_migrated_db):
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT schema_name FROM information_schema.schemata")
        ).scalars().all()
    for schema in ["core", "source", "saas", "tax", "treaty", "risk", "recommender", "workflow"]:
        assert schema in rows


def test_migrations_are_idempotent(_migrated_db):
    # Running upgrade head twice must not raise.
    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
