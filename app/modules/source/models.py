from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SourceDocument(Base):
    __tablename__ = "source_document"
    __table_args__ = {"schema": "source"}

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(1000))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    content_hash: Mapped[str] = mapped_column(String(64))


class SourceEvidence(Base):
    __tablename__ = "source_evidence"
    __table_args__ = {"schema": "source"}

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("source.source_document.id"))
    article: Mapped[str | None] = mapped_column(String(100), nullable=True)
    page: Mapped[int | None] = mapped_column(nullable=True)
    quoted_text: Mapped[str] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(
        String(32), default="unreviewed", server_default="unreviewed"
    )
