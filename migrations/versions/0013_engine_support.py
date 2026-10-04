"""engine support: holding_regime exemption share + STT minimum, treaty MLI and MFN

Revision ID: 0013
Revises: 0012
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import DATERANGE, ExcludeConstraint

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "holding_regime",
        sa.Column("exempt_share_pct", sa.Numeric(6, 3), nullable=False, server_default="100"),
        schema="tax",
    )
    op.add_column(
        "holding_regime",
        sa.Column("min_subject_to_tax_rate", sa.Numeric(6, 3), nullable=True),
        schema="tax",
    )
    op.create_check_constraint(
        "exempt_share_pct_range",
        "holding_regime",
        "exempt_share_pct >= 0 AND exempt_share_pct <= 100",
        schema="tax",
    )

    op.create_table(
        "mli_application",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("treaty_id", sa.Integer, sa.ForeignKey("treaty.treaty.id"), nullable=False),
        sa.Column("ppt_applies", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("dividend_min_holding_days", sa.Integer, nullable=True),
        sa.Column(
            "source_evidence_id",
            sa.Integer,
            sa.ForeignKey("source.source_evidence.id"),
            nullable=False,
        ),
        sa.Column("valid_period", DATERANGE, nullable=False),
        ExcludeConstraint(
            ("treaty_id", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_mli_application",
        ),
        schema="treaty",
    )

    op.create_table(
        "mfn_clause",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("treaty_id", sa.Integer, sa.ForeignKey("treaty.treaty.id"), nullable=False),
        sa.Column(
            "income_category_id",
            sa.Integer,
            sa.ForeignKey("core.income_category.id"),
            nullable=False,
        ),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column(
            "source_evidence_id",
            sa.Integer,
            sa.ForeignKey("source.source_evidence.id"),
            nullable=False,
        ),
        sa.Column("valid_period", DATERANGE, nullable=False),
        ExcludeConstraint(
            ("treaty_id", "="),
            ("income_category_id", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_mfn_clause",
        ),
        schema="treaty",
    )


def downgrade() -> None:
    op.drop_table("mfn_clause", schema="treaty")
    op.drop_table("mli_application", schema="treaty")
    op.drop_constraint("exempt_share_pct_range", "holding_regime", schema="tax")
    op.drop_column("holding_regime", "min_subject_to_tax_rate", schema="tax")
    op.drop_column("holding_regime", "exempt_share_pct", schema="tax")
