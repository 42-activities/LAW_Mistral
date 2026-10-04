from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Jurisdiction(Base):
    __tablename__ = "jurisdiction"
    __table_args__ = {"schema": "core"}

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(8), unique=True)
    name: Mapped[str] = mapped_column(String(200))

    aliases: Mapped[list["JurisdictionAlias"]] = relationship(back_populates="jurisdiction")


class JurisdictionAlias(Base):
    __tablename__ = "jurisdiction_alias"
    __table_args__ = {"schema": "core"}

    id: Mapped[int] = mapped_column(primary_key=True)
    jurisdiction_id: Mapped[int] = mapped_column(ForeignKey("core.jurisdiction.id"))
    alias: Mapped[str] = mapped_column(String(200))

    jurisdiction: Mapped[Jurisdiction] = relationship(back_populates="aliases")
