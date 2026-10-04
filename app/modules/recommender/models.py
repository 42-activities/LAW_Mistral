from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class WeightSet(Base):
    __tablename__ = "weight_set"
    __table_args__ = {"schema": "recommender"}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    weights: Mapped[dict[str, Any]] = mapped_column(JSONB)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)


class Profile(Base):
    __tablename__ = "profile"
    __table_args__ = {"schema": "recommender"}

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("saas.organisation_account.id"))
    answers: Mapped[dict[str, Any]] = mapped_column(JSONB)
    derived: Mapped[dict[str, Any]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScoringRun(Base):
    __tablename__ = "scoring_run"
    __table_args__ = {"schema": "recommender"}

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("saas.organisation_account.id"))
    profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("recommender.profile.id"), nullable=True
    )
    profile_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)
    weight_set_id: Mapped[int | None] = mapped_column(
        ForeignKey("recommender.weight_set.id"), nullable=True
    )
    weights: Mapped[dict[str, Any]] = mapped_column(JSONB)
    engine_version: Mapped[str] = mapped_column(String(16))
    data_asof: Mapped[date] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Scorecard(Base):
    __tablename__ = "scorecard"
    __table_args__ = {"schema": "recommender"}

    id: Mapped[int] = mapped_column(primary_key=True)
    scoring_run_id: Mapped[int] = mapped_column(ForeignKey("recommender.scoring_run.id"))
    jurisdiction_id: Mapped[int] = mapped_column(ForeignKey("core.jurisdiction.id"))
    rank: Mapped[int] = mapped_column(Integer)
    overall_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    complete: Mapped[bool] = mapped_column(Boolean)
    factor_scores: Mapped[dict[str, Any]] = mapped_column(JSONB)
    flow_breakdown: Mapped[list[Any]] = mapped_column(JSONB)
    guardrail_flags: Mapped[list[Any]] = mapped_column(JSONB)
    citations: Mapped[list[Any]] = mapped_column(JSONB)
