"""saas org, user, api key

Revision ID: 0004
Revises: 0003
"""
import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organisation_account",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        schema="saas",
    )
    op.create_table(
        "user",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "org_id",
            sa.Integer,
            sa.ForeignKey("saas.organisation_account.id"),
            nullable=False,
        ),
        sa.Column("email", sa.String(320), nullable=False),
        sa.UniqueConstraint("email", name="uq_user_email"),
        schema="saas",
    )
    op.create_table(
        "api_key",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "org_id",
            sa.Integer,
            sa.ForeignKey("saas.organisation_account.id"),
            nullable=False,
        ),
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("key_hash", name="uq_api_key_hash"),
        schema="saas",
    )


def downgrade() -> None:
    op.drop_table("api_key", schema="saas")
    op.drop_table("user", schema="saas")
    op.drop_table("organisation_account", schema="saas")
