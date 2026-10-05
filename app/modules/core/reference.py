from datetime import date

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import DATERANGE, ExcludeConstraint, Range
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Currency(Base):
    __tablename__ = "currency"
    __table_args__ = {"schema": "core"}

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(3), unique=True)
    name: Mapped[str] = mapped_column(String(100))


class TaxType(Base):
    __tablename__ = "tax_type"
    __table_args__ = {"schema": "core"}

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(100))


class IncomeCategory(Base):
    __tablename__ = "income_category"
    __table_args__ = {"schema": "core"}

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(100))


class JurisdictionGroup(Base):
    """A named set of jurisdictions with dated membership, e.g. the EU for directive reliefs."""

    __tablename__ = "jurisdiction_group"
    __table_args__ = {"schema": "core"}

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(200))


class JurisdictionGroupMember(Base):
    __tablename__ = "jurisdiction_group_member"
    __table_args__ = (
        ExcludeConstraint(
            ("group_id", "="),
            ("jurisdiction_id", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_group_member",
        ),
        {"schema": "core"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("core.jurisdiction_group.id"))
    jurisdiction_id: Mapped[int] = mapped_column(ForeignKey("core.jurisdiction.id"))
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))
    valid_period: Mapped[Range[date]] = mapped_column(DATERANGE)
