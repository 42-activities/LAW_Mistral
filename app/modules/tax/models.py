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
        CheckConstraint(
            "exempt_share_pct >= 0 AND exempt_share_pct <= 100", name="exempt_share_pct_range"
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
    # Share of qualifying income that is exempt (France: 95, a 5% quote-part stays taxable).
    exempt_share_pct: Mapped[Decimal] = mapped_column(
        Numeric(6, 3), default=Decimal("100"), server_default="100"
    )
    # Minimum CIT rate the payer must be subject to (UAE: 9). NULL = no rate floor recorded.
    min_subject_to_tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))
    valid_period: Mapped[Range[date]] = mapped_column(DATERANGE)


class CfcRule(Base):
    """Controlled-foreign-company rule applied by `jurisdiction` (the parent state)."""

    __tablename__ = "cfc_rule"
    __table_args__ = (
        ExcludeConstraint(
            ("jurisdiction_id", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_cfc_rule",
        ),
        {"schema": "tax"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    jurisdiction_id: Mapped[int] = mapped_column(ForeignKey("core.jurisdiction.id"))
    control_threshold_pct: Mapped[Decimal] = mapped_column(Numeric(6, 3))
    # The foreign entity is low-taxed when its tax < this % of the parent-state tax.
    low_tax_relative_pct: Mapped[Decimal] = mapped_column(Numeric(6, 3))
    # True when a tax exactly at the threshold is already low-taxed ("40% or more lower").
    threshold_inclusive: Mapped[bool] = mapped_column(Boolean, default=False)
    effect: Mapped[str] = mapped_column(String(500))
    legal_ref: Mapped[str] = mapped_column(String(120))
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))
    valid_period: Mapped[Range[date]] = mapped_column(DATERANGE)


class SubstanceRule(Base):
    __tablename__ = "substance_rule"
    __table_args__ = (
        ExcludeConstraint(
            ("jurisdiction_id", "="),
            ("regime", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_substance_rule",
        ),
        CheckConstraint(
            "requirement_band IN ('low', 'medium', 'high')", name="substance_band_enum"
        ),
        {"schema": "tax"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    jurisdiction_id: Mapped[int] = mapped_column(ForeignKey("core.jurisdiction.id"))
    regime: Mapped[str] = mapped_column(String(48))
    requirement_band: Mapped[str] = mapped_column(String(8))
    activity_scope: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))
    valid_period: Mapped[Range[date]] = mapped_column(DATERANGE)


class WhtExemption(Base):
    """Domestic withholding exemption for recipients in a group (e.g. EU directive reliefs)."""

    __tablename__ = "wht_exemption"
    __table_args__ = (
        ExcludeConstraint(
            ("jurisdiction_id", "="),
            ("income_category_id", "="),
            ("recipient_group_id", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_wht_exemption",
        ),
        {"schema": "tax"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    jurisdiction_id: Mapped[int] = mapped_column(ForeignKey("core.jurisdiction.id"))
    income_category_id: Mapped[int] = mapped_column(ForeignKey("core.income_category.id"))
    recipient_group_id: Mapped[int] = mapped_column(ForeignKey("core.jurisdiction_group.id"))
    min_holding_pct: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    min_holding_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    legal_ref: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(500))
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))
    valid_period: Mapped[Range[date]] = mapped_column(DATERANGE)
