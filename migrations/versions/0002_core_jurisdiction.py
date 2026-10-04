"""core.jurisdiction and alias

Revision ID: 0002
Revises: 0001
"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jurisdiction",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(8), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.UniqueConstraint("code", name="uq_jurisdiction_code"),
        schema="core",
    )
    op.create_table(
        "jurisdiction_alias",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "jurisdiction_id",
            sa.Integer,
            sa.ForeignKey("core.jurisdiction.id"),
            nullable=False,
        ),
        sa.Column("alias", sa.String(200), nullable=False),
        schema="core",
    )


def downgrade() -> None:
    op.drop_table("jurisdiction_alias", schema="core")
    op.drop_table("jurisdiction", schema="core")
