from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, text
from sqlalchemy.dialects.postgresql import DATERANGE, ExcludeConstraint, Range
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ListDefinition(Base):
    __tablename__ = "list_definition"
    __table_args__ = (
        CheckConstraint("family IN ('tax_governance', 'aml_cft')", name="list_family_enum"),
        {"schema": "risk"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(48), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    family: Mapped[str] = mapped_column(String(16))
    publisher: Mapped[str] = mapped_column(String(120))
    update_cadence: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))


class ListMembership(Base):
    __tablename__ = "list_membership"
    __table_args__ = (
        ExcludeConstraint(
            ("list_definition_id", "="),
            ("jurisdiction_id", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_list_membership",
        ),
        {"schema": "risk"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    list_definition_id: Mapped[int] = mapped_column(ForeignKey("risk.list_definition.id"))
    jurisdiction_id: Mapped[int] = mapped_column(ForeignKey("core.jurisdiction.id"))
    classification: Mapped[str] = mapped_column(String(48))
    announcement_date: Mapped[date | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))
    valid_period: Mapped[Range[date]] = mapped_column(DATERANGE)


class RegulatoryConsequence(Base):
    __tablename__ = "regulatory_consequence"
    __table_args__ = (
        ExcludeConstraint(
            ("applying_jurisdiction_id", "="),
            ("list_definition_id", "="),
            ("classification_trigger", "="),
            ("consequence_type", "="),
            (text("coalesce(income_category_id, 0)"), "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_consequence",
        ),
        CheckConstraint(
            "rate IS NULL OR (rate >= 0 AND rate <= 100)", name="consequence_rate_pct_range"
        ),
        {"schema": "risk"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    applying_jurisdiction_id: Mapped[int] = mapped_column(ForeignKey("core.jurisdiction.id"))
    list_definition_id: Mapped[int] = mapped_column(ForeignKey("risk.list_definition.id"))
    # classification_trigger: '' means "any classification on the list" (wildcard); NOT NULL so the
    # exclusion constraint can key on it. See ConsequenceRepository.triggered_by.
    classification_trigger: Mapped[str] = mapped_column(String(48), default="")
    consequence_type: Mapped[str] = mapped_column(String(48))
    # NULL = applies to every income category.
    income_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("core.income_category.id"), nullable=True
    )
    rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    legal_ref: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))
    valid_period: Mapped[Range[date]] = mapped_column(DATERANGE)
