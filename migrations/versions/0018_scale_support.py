"""P8 scale support: jurisdiction groups (EU), directive WHT exemptions, tiered treaty rates,
per-income-type regulatory consequences

Revision ID: 0018
Revises: 0017
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import DATERANGE, ExcludeConstraint

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def _evidence() -> sa.Column:
    return sa.Column(
        "source_evidence_id",
        sa.Integer,
        sa.ForeignKey("source.source_evidence.id"),
        nullable=False,
    )


def upgrade() -> None:
    op.create_table(
        "jurisdiction_group",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(32), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        schema="core",
    )
    op.create_table(
        "jurisdiction_group_member",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "group_id", sa.Integer, sa.ForeignKey("core.jurisdiction_group.id"), nullable=False
        ),
        sa.Column(
            "jurisdiction_id", sa.Integer, sa.ForeignKey("core.jurisdiction.id"), nullable=False
        ),
        _evidence(),
        sa.Column("valid_period", DATERANGE, nullable=False),
        ExcludeConstraint(
            ("group_id", "="),
            ("jurisdiction_id", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_group_member",
        ),
        schema="core",
    )

    op.create_table(
        "wht_exemption",
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
        sa.Column(
            "recipient_group_id",
            sa.Integer,
            sa.ForeignKey("core.jurisdiction_group.id"),
            nullable=False,
        ),
        sa.Column("min_holding_pct", sa.Numeric(6, 3), nullable=True),
        sa.Column("min_holding_months", sa.Integer, nullable=True),
        sa.Column("legal_ref", sa.String(120), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        _evidence(),
        sa.Column("valid_period", DATERANGE, nullable=False),
        ExcludeConstraint(
            ("jurisdiction_id", "="),
            ("income_category_id", "="),
            ("recipient_group_id", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_wht_exemption",
        ),
        schema="tax",
    )

    # "Lower by 40% or more" (France) is inclusive; "lower than 50%" (LU, CY) is strict.
    op.add_column(
        "cfc_rule",
        sa.Column("threshold_inclusive", sa.Boolean, nullable=False, server_default=sa.false()),
        schema="tax",
    )

    # Tiered treaty rates: one row per (treaty, category, ownership tier).
    op.add_column(
        "treaty_rate", sa.Column("min_holding_days", sa.Integer, nullable=True), schema="treaty"
    )
    op.drop_constraint("no_overlap_treaty_rate", "treaty_rate", schema="treaty")
    op.execute(
        "ALTER TABLE treaty.treaty_rate ADD CONSTRAINT no_overlap_treaty_rate "
        "EXCLUDE USING gist (treaty_id WITH =, income_category_id WITH =, "
        "(coalesce(ownership_threshold, -1)) WITH =, valid_period WITH &&)"
    )

    # Consequences may target one income category (NULL = all).
    op.add_column(
        "regulatory_consequence",
        sa.Column(
            "income_category_id",
            sa.Integer,
            sa.ForeignKey("core.income_category.id"),
            nullable=True,
        ),
        schema="risk",
    )
    op.drop_constraint("no_overlap_consequence", "regulatory_consequence", schema="risk")
    op.execute(
        "ALTER TABLE risk.regulatory_consequence ADD CONSTRAINT no_overlap_consequence "
        "EXCLUDE USING gist (applying_jurisdiction_id WITH =, list_definition_id WITH =, "
        "classification_trigger WITH =, consequence_type WITH =, "
        "(coalesce(income_category_id, 0)) WITH =, valid_period WITH &&)"
    )


def downgrade() -> None:
    op.drop_constraint("no_overlap_consequence", "regulatory_consequence", schema="risk")
    op.drop_column("regulatory_consequence", "income_category_id", schema="risk")
    op.execute(
        "ALTER TABLE risk.regulatory_consequence ADD CONSTRAINT no_overlap_consequence "
        "EXCLUDE USING gist (applying_jurisdiction_id WITH =, list_definition_id WITH =, "
        "classification_trigger WITH =, consequence_type WITH =, valid_period WITH &&)"
    )
    op.drop_constraint("no_overlap_treaty_rate", "treaty_rate", schema="treaty")
    op.drop_column("treaty_rate", "min_holding_days", schema="treaty")
    op.execute(
        "ALTER TABLE treaty.treaty_rate ADD CONSTRAINT no_overlap_treaty_rate "
        "EXCLUDE USING gist (treaty_id WITH =, income_category_id WITH =, valid_period WITH &&)"
    )
    op.drop_column("cfc_rule", "threshold_inclusive", schema="tax")
    op.drop_table("wht_exemption", schema="tax")
    op.drop_table("jurisdiction_group_member", schema="core")
    op.drop_table("jurisdiction_group", schema="core")
