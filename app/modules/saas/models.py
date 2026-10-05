from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, func, true
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

ROLES = ("viewer", "analyst", "admin")


class Plan(Base):
    __tablename__ = "plan"
    __table_args__ = {"schema": "saas"}

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    analyses_per_day: Mapped[int] = mapped_column(Integer)
    analyses_per_minute: Mapped[int] = mapped_column(Integer)
    llm_calls_per_day: Mapped[int] = mapped_column(Integer)


class OrganisationAccount(Base):
    __tablename__ = "organisation_account"
    __table_args__ = {"schema": "saas"}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("saas.plan.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "user"
    __table_args__ = {"schema": "saas"}

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("saas.organisation_account.id"))
    email: Mapped[str] = mapped_column(String(320), unique=True)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(200), nullable=True)
    role: Mapped[str] = mapped_column(String(16), default="analyst", server_default="analyst")
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ApiKey(Base):
    __tablename__ = "api_key"
    __table_args__ = {"schema": "saas"}

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("saas.organisation_account.id"))
    key_hash: Mapped[str] = mapped_column(String(64), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    name: Mapped[str] = mapped_column(String(100), default="unnamed", server_default="unnamed")
    role: Mapped[str] = mapped_column(String(16), default="analyst", server_default="analyst")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("saas.user.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UserSession(Base):
    __tablename__ = "session"
    __table_args__ = {"schema": "saas"}

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("saas.user.id"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UsageEvent(Base):
    __tablename__ = "usage_event"
    __table_args__ = {"schema": "saas"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("saas.organisation_account.id"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("saas.user.id"), nullable=True)
    api_key_id: Mapped[int | None] = mapped_column(ForeignKey("saas.api_key.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(16))
    units: Mapped[int] = mapped_column(Integer, default=1)
    ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditEvent(Base):
    __tablename__ = "audit_event"
    __table_args__ = {"schema": "workflow"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    org_id: Mapped[int | None] = mapped_column(
        ForeignKey("saas.organisation_account.id"), nullable=True
    )
    user_id: Mapped[int | None] = mapped_column(ForeignKey("saas.user.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(32))
    target: Mapped[str | None] = mapped_column(String(200), nullable=True)
    detail: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
