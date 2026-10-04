"""risk.list_definition

Revision ID: 0010
Revises: 0009
"""
import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "list_definition",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(48), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("family", sa.String(16), nullable=False),
        sa.Column("publisher", sa.String(120), nullable=False),
        sa.Column("update_cadence", sa.String(120), nullable=True),
        sa.Column(
            "source_evidence_id",
            sa.Integer,
            sa.ForeignKey("source.source_evidence.id"),
            nullable=False,
        ),
        sa.CheckConstraint("family IN ('tax_governance', 'aml_cft')", name="list_family_enum"),
        schema="risk",
    )


def downgrade() -> None:
    op.drop_table("list_definition", schema="risk")
