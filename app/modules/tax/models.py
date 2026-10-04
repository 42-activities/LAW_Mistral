from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import DATERANGE, ExcludeConstraint, Range
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class DomesticTaxRule(Base):
    __tablename__ = "domestic_tax_rule"
    __table_args__ = (
        ExcludeConstraint(
            ("jurisdiction_id", "="),
            ("tax_type_id", "="),
            ("income_category_id", "="),
            ("taxpayer_type", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_domestic_rule",
        ),
        CheckConstraint("rate IS NULL OR (rate >= 0 AND rate <= 100)", name="rate_pct_range"),
        {"schema": "tax"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    jurisdiction_id: Mapped[int] = mapped_column(ForeignKey("core.jurisdiction.id"))
    tax_type_id: Mapped[int] = mapped_column(ForeignKey("core.tax_type.id"))
    income_category_id: Mapped[int] = mapped_column(ForeignKey("core.income_category.id"))
    taxpayer_type: Mapped[str] = mapped_column(String(16), default="any")
    rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    is_bracketed: Mapped[bool] = mapped_column(Boolean, default=False)
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))
    valid_period: Mapped[Range[date]] = mapped_column(DATERANGE)

    brackets: Mapped[list["TaxBracket"]] = relationship(
        back_populates="rule", order_by="TaxBracket.position"
    )


class TaxBracket(Base):
    __tablename__ = "tax_bracket"
    __table_args__ = {"schema": "tax"}

    id: Mapped[int] = mapped_column(primary_key=True)
    domestic_tax_rule_id: Mapped[int] = mapped_column(ForeignKey("tax.domestic_tax_rule.id"))
    lower_bound: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    upper_bound: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(6, 3))
    position: Mapped[int] = mapped_column(Integer)

    rule: Mapped[DomesticTaxRule] = relationship(back_populates="brackets")


class HoldingRegime(Base):
    __tablename__ = "holding_regime"
    __table_args__ = (
        ExcludeConstraint(
            ("jurisdiction_id", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_holding_regime",
        ),
        {"schema": "tax"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    jurisdiction_id: Mapped[int] = mapped_column(ForeignKey("core.jurisdiction.id"))
    participation_exemption_dividends: Mapped[bool] = mapped_column(Boolean, default=False)
    participation_exemption_capgains: Mapped[bool] = mapped_column(Boolean, default=False)
    min_holding_pct: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    min_holding_period_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subject_to_tax_condition: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))
    valid_period: Mapped[Range[date]] = mapped_column(DATERANGE)
