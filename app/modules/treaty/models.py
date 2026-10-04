from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import DATERANGE, ExcludeConstraint, Range
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


class TreatyRate(Base):
    __tablename__ = "treaty_rate"
    __table_args__ = (
        ExcludeConstraint(
            ("treaty_id", "="),
            ("income_category_id", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_treaty_rate",
        ),
        CheckConstraint(
            "relief_mechanism IS NULL OR relief_mechanism IN ('at_source','refund','credit')",
            name="relief_mechanism_enum",
        ),
        CheckConstraint(
            "max_rate IS NULL OR (max_rate >= 0 AND max_rate <= 100)",
            name="treaty_rate_pct_range",
        ),
        {"schema": "treaty"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    treaty_id: Mapped[int] = mapped_column(ForeignKey("treaty.treaty.id"))
    treaty_article_id: Mapped[int] = mapped_column(ForeignKey("treaty.treaty_article.id"))
    income_category_id: Mapped[int] = mapped_column(ForeignKey("core.income_category.id"))
    max_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    exclusive_residence_taxation: Mapped[bool] = mapped_column(Boolean, default=False)
    relief_mechanism: Mapped[str | None] = mapped_column(String(16), nullable=True)
    beneficial_owner_required: Mapped[bool] = mapped_column(Boolean, default=False)
    ownership_threshold: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))
    valid_period: Mapped[Range[date]] = mapped_column(DATERANGE)
