"""risk.regulatory_consequence

Revision ID: 0012
Revises: 0011
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import DATERANGE, ExcludeConstraint

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "regulatory_consequence",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "applying_jurisdiction_id",
            sa.Integer,
            sa.ForeignKey("core.jurisdiction.id"),
            nullable=False,
        ),
        sa.Column(
            "list_definition_id",
            sa.Integer,
            sa.ForeignKey("risk.list_definition.id"),
            nullable=False,
        ),
        # '' = wildcard (any classification); NOT NULL so the exclusion key catches duplicates.
        sa.Column("classification_trigger", sa.String(48), nullable=False, server_default=""),
        sa.Column("consequence_type", sa.String(48), nullable=False),
        sa.Column("rate", sa.Numeric(6, 3), nullable=True),
        sa.Column("legal_ref", sa.String(120), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column(
            "source_evidence_id",
            sa.Integer,
            sa.ForeignKey("source.source_evidence.id"),
            nullable=False,
        ),
        sa.Column("valid_period", DATERANGE, nullable=False),
        sa.CheckConstraint(
            "rate IS NULL OR (rate >= 0 AND rate <= 100)", name="consequence_rate_pct_range"
        ),
        ExcludeConstraint(
            ("applying_jurisdiction_id", "="),
            ("list_definition_id", "="),
            ("classification_trigger", "="),
            ("consequence_type", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_consequence",
        ),
        schema="risk",
    )


def downgrade() -> None:
    op.drop_table("regulatory_consequence", schema="risk")
