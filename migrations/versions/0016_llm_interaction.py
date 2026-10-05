"""workflow.llm_interaction audit

Revision ID: 0016
Revises: 0015
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llm_interaction",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "org_id", sa.Integer, sa.ForeignKey("saas.organisation_account.id"), nullable=True
        ),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("input_ref", sa.String(64), nullable=True),
        sa.Column("model", sa.String(64), nullable=False),
        sa.Column("prompt_version", sa.String(16), nullable=False),
        sa.Column("attempt", sa.Integer, nullable=False, server_default="1"),
        sa.Column("output", sa.Text, nullable=True),
        sa.Column("grounding_status", sa.String(16), nullable=False),
        sa.Column("grounding_errors", JSONB, nullable=False, server_default="[]"),
        sa.Column("citations", JSONB, nullable=False, server_default="[]"),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("prompt_tokens", sa.Integer, nullable=True),
        sa.Column("completion_tokens", sa.Integer, nullable=True),
        # Left NULL until a verified price list is configured; never estimated.
        sa.Column("cost", sa.Numeric(12, 6), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("kind IN ('nl_parse', 'summary')", name="llm_kind_enum"),
        sa.CheckConstraint(
            "grounding_status IN ('pass', 'repaired', 'rejected', 'error')",
            name="llm_grounding_status_enum",
        ),
        schema="workflow",
    )


def downgrade() -> None:
    op.drop_table("llm_interaction", schema="workflow")
