"""holding_regime.payer_group_id: exemption limited to payers in a group (e.g. EU only)

Revision ID: 0020
Revises: 0019
"""
import sqlalchemy as sa
from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "holding_regime",
        sa.Column(
            "payer_group_id",
            sa.Integer,
            sa.ForeignKey("core.jurisdiction_group.id"),
            nullable=True,
        ),
        schema="tax",
    )


def downgrade() -> None:
    op.drop_column("holding_regime", "payer_group_id", schema="tax")
