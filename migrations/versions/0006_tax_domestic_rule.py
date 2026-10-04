"""tax.domestic_tax_rule + tax_bracket with no-overlap exclusion constraint

Revision ID: 0006
Revises: 0005
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.create_table(
        "domestic_tax_rule",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "jurisdiction_id",
            sa.Integer,
            sa.ForeignKey("core.jurisdiction.id"),
            nullable=False,
        ),
        sa.Column("tax_type_id", sa.Integer, sa.ForeignKey("core.tax_type.id"), nullable=False),
        sa.Column(
            "income_category_id",
            sa.Integer,
            sa.ForeignKey("core.income_category.id"),
            nullable=False,
        ),
        sa.Column("taxpayer_type", sa.String(16), nullable=False, server_default="any"),
        sa.Column("rate", sa.Numeric(6, 3), nullable=True),
        sa.Column("is_bracketed", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "source_evidence_id",
            sa.Integer,
            sa.ForeignKey("source.source_evidence.id"),
            nullable=False,
        ),
        sa.Column("valid_period", postgresql.DATERANGE, nullable=False),
        sa.CheckConstraint("rate IS NULL OR (rate >= 0 AND rate <= 100)", name="rate_pct_range"),
        postgresql.ExcludeConstraint(
            ("jurisdiction_id", "="),
            ("tax_type_id", "="),
            ("income_category_id", "="),
            ("taxpayer_type", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_domestic_rule",
        ),
        schema="tax",
    )
    op.create_table(
        "tax_bracket",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "domestic_tax_rule_id",
            sa.Integer,
            sa.ForeignKey("tax.domestic_tax_rule.id"),
            nullable=False,
        ),
        sa.Column("lower_bound", sa.Numeric(18, 2), nullable=False),
        sa.Column("upper_bound", sa.Numeric(18, 2), nullable=True),
        sa.Column("rate", sa.Numeric(6, 3), nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        schema="tax",
    )


def downgrade() -> None:
    op.drop_table("tax_bracket", schema="tax")
    op.drop_table("domestic_tax_rule", schema="tax")
