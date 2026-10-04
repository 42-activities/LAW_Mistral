"""create schemas

Revision ID: 0001
Revises:
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SCHEMAS = ["core", "source", "saas", "tax", "treaty", "risk", "recommender", "workflow"]


def upgrade() -> None:
    for schema in SCHEMAS:
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")


def downgrade() -> None:
    for schema in SCHEMAS:
        op.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
