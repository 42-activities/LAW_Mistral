"""saas hardening: plans, user auth fields, key roles, sessions, usage, audit

Revision ID: 0017
Revises: 0016
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None

ROLE_CHECK = "role IN ('viewer', 'analyst', 'admin')"


def _now() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )


def upgrade() -> None:
    op.create_table(
        "plan",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(32), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("analyses_per_day", sa.Integer, nullable=False),
        sa.Column("analyses_per_minute", sa.Integer, nullable=False),
        sa.Column("llm_calls_per_day", sa.Integer, nullable=False),
        schema="saas",
    )
    op.execute(
        "INSERT INTO saas.plan (code, name, analyses_per_day, analyses_per_minute, "
        "llm_calls_per_day) VALUES ('standard', 'Standard', 300, 20, 300)"
    )
    op.add_column(
        "organisation_account",
        sa.Column("plan_id", sa.Integer, sa.ForeignKey("saas.plan.id"), nullable=True),
        schema="saas",
    )
    op.add_column(
        "organisation_account",
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        schema="saas",
    )

    for col in [
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("password_hash", sa.String(200), nullable=True),
        sa.Column("role", sa.String(16), nullable=False, server_default="analyst"),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        _now(),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    ]:
        op.add_column("user", col, schema="saas")
    op.create_check_constraint("user_role_enum", "user", ROLE_CHECK, schema="saas")

    for col in [
        sa.Column("name", sa.String(100), nullable=False, server_default="unnamed"),
        sa.Column("role", sa.String(16), nullable=False, server_default="analyst"),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("saas.user.id"), nullable=True),
        _now(),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    ]:
        op.add_column("api_key", col, schema="saas")
    op.create_check_constraint("api_key_role_enum", "api_key", ROLE_CHECK, schema="saas")

    op.create_table(
        "session",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("saas.user.id"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        _now(),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        schema="saas",
    )
    op.create_table(
        "usage_event",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column(
            "org_id", sa.Integer, sa.ForeignKey("saas.organisation_account.id"), nullable=False
        ),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("saas.user.id"), nullable=True),
        sa.Column("api_key_id", sa.Integer, sa.ForeignKey("saas.api_key.id"), nullable=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("units", sa.Integer, nullable=False, server_default="1"),
        sa.Column("ref", sa.String(64), nullable=True),
        _now(),
        sa.CheckConstraint("kind IN ('analysis', 'ask', 'llm_call')", name="usage_kind_enum"),
        schema="saas",
    )
    op.create_index(
        "ix_usage_org_kind_time", "usage_event", ["org_id", "kind", "created_at"], schema="saas"
    )
    op.create_table(
        "audit_event",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column(
            "org_id", sa.Integer, sa.ForeignKey("saas.organisation_account.id"), nullable=True
        ),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("saas.user.id"), nullable=True),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("target", sa.String(200), nullable=True),
        sa.Column("detail", JSONB, nullable=False, server_default="{}"),
        _now(),
        schema="workflow",
    )
    op.create_index(
        "ix_audit_action_target_time",
        "audit_event",
        ["action", "target", "created_at"],
        schema="workflow",
    )


def downgrade() -> None:
    op.drop_table("audit_event", schema="workflow")
    op.drop_table("usage_event", schema="saas")
    op.drop_table("session", schema="saas")
    op.drop_constraint("api_key_role_enum", "api_key", schema="saas")
    for c in ("last_used_at", "created_at", "created_by", "role", "name"):
        op.drop_column("api_key", c, schema="saas")
    op.drop_constraint("user_role_enum", "user", schema="saas")
    for c in ("last_login_at", "created_at", "active", "role", "password_hash", "name"):
        op.drop_column("user", c, schema="saas")
    op.drop_column("organisation_account", "created_at", schema="saas")
    op.drop_column("organisation_account", "plan_id", schema="saas")
    op.drop_table("plan", schema="saas")
