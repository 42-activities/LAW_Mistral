"""VAT / GST / general sales tax per jurisdiction

Revision ID: 0021
Revises: 0020
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import DATERANGE, JSONB, ExcludeConstraint

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vat_rule",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "jurisdiction_id", sa.Integer, sa.ForeignKey("core.jurisdiction.id"), nullable=False
        ),
        sa.Column("has_vat", sa.Boolean, nullable=False),
        sa.Column("tax_name", sa.String(200), nullable=False),
        sa.Column("standard_rate", sa.Numeric(6, 3), nullable=True),
        sa.Column("reduced_rates", JSONB, nullable=False, server_default="[]"),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column(
            "source_evidence_id",
            sa.Integer,
            sa.ForeignKey("source.source_evidence.id"),
            nullable=False,
        ),
        sa.Column("valid_period", DATERANGE, nullable=False),
        ExcludeConstraint(
            ("jurisdiction_id", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_vat_rule",
        ),
        schema="tax",
    )


def downgrade() -> None:
    op.drop_table("vat_rule", schema="tax")
