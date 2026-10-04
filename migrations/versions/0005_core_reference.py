"""core reference data (currency, tax_type, income_category)

Revision ID: 0005
Revises: 0004
"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "currency",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(3), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.UniqueConstraint("code", name="uq_currency_code"),
        schema="core",
    )
    op.create_table(
        "tax_type",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.UniqueConstraint("code", name="uq_tax_type_code"),
        schema="core",
    )
    op.create_table(
        "income_category",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.UniqueConstraint("code", name="uq_income_category_code"),
        schema="core",
    )


def downgrade() -> None:
    op.drop_table("income_category", schema="core")
    op.drop_table("tax_type", schema="core")
    op.drop_table("currency", schema="core")
