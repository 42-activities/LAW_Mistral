from sqlalchemy import Boolean, ForeignKey, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class OrganisationAccount(Base):
    __tablename__ = "organisation_account"
    __table_args__ = {"schema": "saas"}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))


class User(Base):
    __tablename__ = "user"
    __table_args__ = {"schema": "saas"}

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("saas.organisation_account.id"))
    email: Mapped[str] = mapped_column(String(320), unique=True)


class ApiKey(Base):
    __tablename__ = "api_key"
    __table_args__ = {"schema": "saas"}

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("saas.organisation_account.id"))
    key_hash: Mapped[str] = mapped_column(String(64), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
