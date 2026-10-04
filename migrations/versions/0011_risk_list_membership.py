"""risk.list_membership

Revision ID: 0011
Revises: 0010
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import DATERANGE, ExcludeConstraint

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "list_membership",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "list_definition_id",
            sa.Integer,
            sa.ForeignKey("risk.list_definition.id"),
            nullable=False,
        ),
        sa.Column(
            "jurisdiction_id",
            sa.Integer,
            sa.ForeignKey("core.jurisdiction.id"),
            nullable=False,
        ),
        sa.Column("classification", sa.String(48), nullable=False),
        sa.Column("announcement_date", sa.Date, nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column(
            "source_evidence_id",
            sa.Integer,
            sa.ForeignKey("source.source_evidence.id"),
            nullable=False,
        ),
        sa.Column("valid_period", DATERANGE, nullable=False),
        ExcludeConstraint(
            ("list_definition_id", "="),
            ("jurisdiction_id", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_list_membership",
        ),
        schema="risk",
    )


def downgrade() -> None:
    op.drop_table("list_membership", schema="risk")
