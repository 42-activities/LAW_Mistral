"""recommender.question_definition

Revision ID: 0015
Revises: 0014
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "question_definition",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(48), nullable=False, unique=True),
        sa.Column("text", sa.String(300), nullable=False),
        sa.Column("help", sa.String(500), nullable=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("options", JSONB, nullable=False),
        sa.Column("maps_to", sa.String(64), nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.CheckConstraint("kind IN ('single', 'flows')", name="question_kind_enum"),
        schema="recommender",
    )


def downgrade() -> None:
    op.drop_table("question_definition", schema="recommender")
