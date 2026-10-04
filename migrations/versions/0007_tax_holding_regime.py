"""tax.holding_regime with no-overlap exclusion constraint

Revision ID: 0007
Revises: 0006
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "holding_regime",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "jurisdiction_id",
            sa.Integer,
            sa.ForeignKey("core.jurisdiction.id"),
            nullable=False,
        ),
        sa.Column(
            "participation_exemption_dividends",
            sa.Boolean,
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "participation_exemption_capgains",
            sa.Boolean,
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("min_holding_pct", sa.Numeric(6, 3), nullable=True),
        sa.Column("min_holding_period_months", sa.Integer, nullable=True),
        sa.Column(
            "subject_to_tax_condition", sa.Boolean, nullable=False, server_default=sa.false()
        ),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column(
            "source_evidence_id",
            sa.Integer,
            sa.ForeignKey("source.source_evidence.id"),
            nullable=False,
        ),
        sa.Column("valid_period", postgresql.DATERANGE, nullable=False),
        postgresql.ExcludeConstraint(
            ("jurisdiction_id", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_holding_regime",
        ),
        schema="tax",
    )


def downgrade() -> None:
    op.drop_table("holding_regime", schema="tax")
