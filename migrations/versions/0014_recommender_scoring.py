"""recommender scoring tables, tax.cfc_rule, tax.substance_rule

Revision ID: 0014
Revises: 0013
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import DATERANGE, JSONB, ExcludeConstraint

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def _evidence() -> sa.Column:
    return sa.Column(
        "source_evidence_id",
        sa.Integer,
        sa.ForeignKey("source.source_evidence.id"),
        nullable=False,
    )


def _jurisdiction(name: str) -> sa.Column:
    return sa.Column(name, sa.Integer, sa.ForeignKey("core.jurisdiction.id"), nullable=False)


def upgrade() -> None:
    op.create_table(
        "cfc_rule",
        sa.Column("id", sa.Integer, primary_key=True),
        _jurisdiction("jurisdiction_id"),
        sa.Column("control_threshold_pct", sa.Numeric(6, 3), nullable=False),
        # Foreign entity is low-taxed when its tax < this % of the parent-state tax.
        sa.Column("low_tax_relative_pct", sa.Numeric(6, 3), nullable=False),
        sa.Column("effect", sa.String(500), nullable=False),
        sa.Column("legal_ref", sa.String(120), nullable=False),
        _evidence(),
        sa.Column("valid_period", DATERANGE, nullable=False),
        ExcludeConstraint(
            ("jurisdiction_id", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_cfc_rule",
        ),
        schema="tax",
    )
    op.create_table(
        "substance_rule",
        sa.Column("id", sa.Integer, primary_key=True),
        _jurisdiction("jurisdiction_id"),
        sa.Column("regime", sa.String(48), nullable=False),
        sa.Column("requirement_band", sa.String(8), nullable=False),
        sa.Column("activity_scope", sa.String(200), nullable=True),
        _evidence(),
        sa.Column("valid_period", DATERANGE, nullable=False),
        sa.CheckConstraint(
            "requirement_band IN ('low', 'medium', 'high')", name="substance_band_enum"
        ),
        ExcludeConstraint(
            ("jurisdiction_id", "="),
            ("regime", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_substance_rule",
        ),
        schema="tax",
    )

    op.create_table(
        "weight_set",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("weights", JSONB, nullable=False),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default=sa.false()),
        schema="recommender",
    )
    op.create_index(
        "one_default_weight_set",
        "weight_set",
        ["is_default"],
        unique=True,
        schema="recommender",
        postgresql_where=sa.text("is_default"),
    )
    op.create_table(
        "profile",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "org_id", sa.Integer, sa.ForeignKey("saas.organisation_account.id"), nullable=False
        ),
        sa.Column("answers", JSONB, nullable=False),
        sa.Column("derived", JSONB, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        schema="recommender",
    )
    op.create_table(
        "scoring_run",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "org_id", sa.Integer, sa.ForeignKey("saas.organisation_account.id"), nullable=False
        ),
        sa.Column(
            "profile_id", sa.Integer, sa.ForeignKey("recommender.profile.id"), nullable=True
        ),
        sa.Column("profile_snapshot", JSONB, nullable=False),
        sa.Column(
            "weight_set_id",
            sa.Integer,
            sa.ForeignKey("recommender.weight_set.id"),
            nullable=True,
        ),
        sa.Column("weights", JSONB, nullable=False),
        sa.Column("engine_version", sa.String(16), nullable=False),
        sa.Column("data_asof", sa.Date, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        schema="recommender",
    )
    op.create_table(
        "scorecard",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "scoring_run_id",
            sa.Integer,
            sa.ForeignKey("recommender.scoring_run.id"),
            nullable=False,
        ),
        _jurisdiction("jurisdiction_id"),
        sa.Column("rank", sa.Integer, nullable=False),
        sa.Column("overall_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("complete", sa.Boolean, nullable=False),
        sa.Column("factor_scores", JSONB, nullable=False),
        sa.Column("flow_breakdown", JSONB, nullable=False),
        sa.Column("guardrail_flags", JSONB, nullable=False),
        sa.Column("citations", JSONB, nullable=False),
        sa.UniqueConstraint("scoring_run_id", "jurisdiction_id", name="one_card_per_candidate"),
        schema="recommender",
    )


def downgrade() -> None:
    op.drop_table("scorecard", schema="recommender")
    op.drop_table("scoring_run", schema="recommender")
    op.drop_table("profile", schema="recommender")
    op.drop_index("one_default_weight_set", table_name="weight_set", schema="recommender")
    op.drop_table("weight_set", schema="recommender")
    op.drop_table("substance_rule", schema="tax")
    op.drop_table("cfc_rule", schema="tax")
