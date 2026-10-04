from datetime import date

from sqlalchemy import CheckConstraint, ForeignKey, String
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
