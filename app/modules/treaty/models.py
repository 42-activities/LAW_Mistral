from datetime import date

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Treaty(Base):
    __tablename__ = "treaty"
    __table_args__ = {"schema": "treaty"}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    signature_date: Mapped[date] = mapped_column()
    entry_into_force_date: Mapped[date | None] = mapped_column(nullable=True)
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))

    parties: Mapped[list["TreatyParty"]] = relationship(back_populates="treaty")
    articles: Mapped[list["TreatyArticle"]] = relationship(back_populates="treaty")
    protocols: Mapped[list["TreatyProtocol"]] = relationship(back_populates="treaty")


class TreatyParty(Base):
    __tablename__ = "treaty_party"
    __table_args__ = {"schema": "treaty"}

    id: Mapped[int] = mapped_column(primary_key=True)
    treaty_id: Mapped[int] = mapped_column(ForeignKey("treaty.treaty.id"))
    jurisdiction_id: Mapped[int] = mapped_column(ForeignKey("core.jurisdiction.id"))

    treaty: Mapped[Treaty] = relationship(back_populates="parties")


class TreatyArticle(Base):
    __tablename__ = "treaty_article"
    __table_args__ = {"schema": "treaty"}

    id: Mapped[int] = mapped_column(primary_key=True)
    treaty_id: Mapped[int] = mapped_column(ForeignKey("treaty.treaty.id"))
    article_category: Mapped[str] = mapped_column(String(32))
    article_ref: Mapped[str] = mapped_column(String(50))

    treaty: Mapped[Treaty] = relationship(back_populates="articles")


class TreatyProtocol(Base):
    __tablename__ = "treaty_protocol"
    __table_args__ = {"schema": "treaty"}

    id: Mapped[int] = mapped_column(primary_key=True)
    treaty_id: Mapped[int] = mapped_column(ForeignKey("treaty.treaty.id"))
    signature_date: Mapped[date] = mapped_column()
    entry_into_force_date: Mapped[date | None] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(String(500))
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))

    treaty: Mapped[Treaty] = relationship(back_populates="protocols")
