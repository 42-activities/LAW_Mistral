"""tax.cit_refund (shareholder refunds, e.g. Malta); direction-specific treaty rates

Revision ID: 0019
Revises: 0018
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import DATERANGE, ExcludeConstraint

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cit_refund",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "jurisdiction_id", sa.Integer, sa.ForeignKey("core.jurisdiction.id"), nullable=False
        ),
        sa.Column(
            "income_category_id",
            sa.Integer,
            sa.ForeignKey("core.income_category.id"),
            nullable=False,
        ),
        # Share of the corporate tax refunded to the shareholder on distribution, in percent.
        sa.Column("refund_pct", sa.Numeric(7, 4), nullable=False),
        sa.Column("legal_ref", sa.String(120), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column(
            "source_evidence_id",
            sa.Integer,
            sa.ForeignKey("source.source_evidence.id"),
            nullable=False,
        ),
        sa.Column("valid_period", DATERANGE, nullable=False),
        sa.CheckConstraint("refund_pct >= 0 AND refund_pct <= 100", name="refund_pct_range"),
        ExcludeConstraint(
            ("jurisdiction_id", "="),
            ("income_category_id", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_cit_refund",
        ),
        schema="tax",
    )

    # Exemptions may reduce rather than zero the rate (Spain: royalties to EU residents 19%),
    # and one state may grant several for the same income (19% for any EU resident, 0% for an
    # associated EU company).
    op.add_column(
        "wht_exemption", sa.Column("reduced_rate", sa.Numeric(6, 3), nullable=True), schema="tax"
    )
    op.drop_constraint("no_overlap_wht_exemption", "wht_exemption", schema="tax")
    op.execute(
        "ALTER TABLE tax.wht_exemption ADD CONSTRAINT no_overlap_wht_exemption "
        "EXCLUDE USING gist (jurisdiction_id WITH =, income_category_id WITH =, "
        "recipient_group_id WITH =, (coalesce(min_holding_pct, -1)) WITH =, "
        "valid_period WITH &&)"
    )

    # Some treaties cap differently by direction (France–Germany dividends: 0% / 5%).
    op.add_column(
        "treaty_rate",
        sa.Column(
            "source_jurisdiction_id",
            sa.Integer,
            sa.ForeignKey("core.jurisdiction.id"),
            nullable=True,
        ),
        schema="treaty",
    )
    op.drop_constraint("no_overlap_treaty_rate", "treaty_rate", schema="treaty")
    op.execute(
        "ALTER TABLE treaty.treaty_rate ADD CONSTRAINT no_overlap_treaty_rate "
        "EXCLUDE USING gist (treaty_id WITH =, income_category_id WITH =, "
        "(coalesce(ownership_threshold, -1)) WITH =, (coalesce(source_jurisdiction_id, 0)) WITH =, "
        "valid_period WITH &&)"
    )


def downgrade() -> None:
    op.drop_constraint("no_overlap_wht_exemption", "wht_exemption", schema="tax")
    op.drop_column("wht_exemption", "reduced_rate", schema="tax")
    op.execute(
        "ALTER TABLE tax.wht_exemption ADD CONSTRAINT no_overlap_wht_exemption "
        "EXCLUDE USING gist (jurisdiction_id WITH =, income_category_id WITH =, "
        "recipient_group_id WITH =, valid_period WITH &&)"
    )
    op.drop_constraint("no_overlap_treaty_rate", "treaty_rate", schema="treaty")
    op.drop_column("treaty_rate", "source_jurisdiction_id", schema="treaty")
    op.execute(
        "ALTER TABLE treaty.treaty_rate ADD CONSTRAINT no_overlap_treaty_rate "
        "EXCLUDE USING gist (treaty_id WITH =, income_category_id WITH =, "
        "(coalesce(ownership_threshold, -1)) WITH =, valid_period WITH &&)"
    )
    op.drop_table("cit_refund", schema="tax")
