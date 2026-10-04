"""treaty.treaty_rate

Revision ID: 0009
Revises: 0008
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "treaty_rate",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("treaty_id", sa.Integer, sa.ForeignKey("treaty.treaty.id"), nullable=False),
        sa.Column(
            "treaty_article_id",
            sa.Integer,
            sa.ForeignKey("treaty.treaty_article.id"),
            nullable=False,
        ),
        sa.Column(
            "income_category_id",
            sa.Integer,
            sa.ForeignKey("core.income_category.id"),
            nullable=False,
        ),
        sa.Column("max_rate", sa.Numeric(6, 3), nullable=True),
        sa.Column("exclusive_residence_taxation", sa.Boolean, nullable=False),
        sa.Column("relief_mechanism", sa.String(16), nullable=True),
        sa.Column("beneficial_owner_required", sa.Boolean, nullable=False),
        sa.Column("ownership_threshold", sa.Numeric(6, 3), nullable=True),
        sa.Column(
            "source_evidence_id",
            sa.Integer,
            sa.ForeignKey("source.source_evidence.id"),
            nullable=False,
        ),
        sa.Column("valid_period", postgresql.DATERANGE, nullable=False),
        postgresql.ExcludeConstraint(
            ("treaty_id", "="),
            ("income_category_id", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_treaty_rate",
        ),
        sa.CheckConstraint(
            "relief_mechanism IS NULL OR relief_mechanism IN ('at_source','refund','credit')",
            name="relief_mechanism_enum",
        ),
        sa.CheckConstraint(
            "max_rate IS NULL OR (max_rate >= 0 AND max_rate <= 100)",
            name="treaty_rate_pct_range",
        ),
        schema="treaty",
    )


def downgrade() -> None:
    op.drop_table("treaty_rate", schema="treaty")
