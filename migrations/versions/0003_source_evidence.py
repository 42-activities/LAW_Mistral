"""source document and evidence

Revision ID: 0003
Revises: 0002
"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "source_document",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        schema="source",
    )
    op.create_table(
        "source_evidence",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "document_id",
            sa.Integer,
            sa.ForeignKey("source.source_document.id"),
            nullable=False,
        ),
        sa.Column("article", sa.String(100), nullable=True),
        sa.Column("page", sa.Integer, nullable=True),
        sa.Column("quoted_text", sa.Text, nullable=False),
        sa.Column("review_status", sa.String(32), nullable=False, server_default="unreviewed"),
        schema="source",
    )


def downgrade() -> None:
    op.drop_table("source_evidence", schema="source")
    op.drop_table("source_document", schema="source")
