"""treaty core tables: treaty, treaty_party, treaty_article, treaty_protocol

Revision ID: 0008
Revises: 0007
"""
import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "treaty",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("signature_date", sa.Date, nullable=False),
        sa.Column("entry_into_force_date", sa.Date, nullable=True),
        sa.Column(
            "source_evidence_id",
            sa.Integer,
            sa.ForeignKey("source.source_evidence.id"),
            nullable=False,
        ),
        schema="treaty",
    )
    op.create_table(
        "treaty_party",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("treaty_id", sa.Integer, sa.ForeignKey("treaty.treaty.id"), nullable=False),
        sa.Column(
            "jurisdiction_id", sa.Integer, sa.ForeignKey("core.jurisdiction.id"), nullable=False
        ),
        schema="treaty",
    )
    op.create_table(
        "treaty_article",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("treaty_id", sa.Integer, sa.ForeignKey("treaty.treaty.id"), nullable=False),
        sa.Column("article_category", sa.String(32), nullable=False),
        sa.Column("article_ref", sa.String(50), nullable=False),
        schema="treaty",
    )
    op.create_table(
        "treaty_protocol",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("treaty_id", sa.Integer, sa.ForeignKey("treaty.treaty.id"), nullable=False),
        sa.Column("signature_date", sa.Date, nullable=False),
        sa.Column("entry_into_force_date", sa.Date, nullable=True),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column(
            "source_evidence_id",
            sa.Integer,
            sa.ForeignKey("source.source_evidence.id"),
            nullable=False,
        ),
        schema="treaty",
    )


def downgrade() -> None:
    op.drop_table("treaty_protocol", schema="treaty")
    op.drop_table("treaty_article", schema="treaty")
    op.drop_table("treaty_party", schema="treaty")
    op.drop_table("treaty", schema="treaty")
