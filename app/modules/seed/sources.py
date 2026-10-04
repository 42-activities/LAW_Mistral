from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.source.models import SourceDocument, SourceEvidence


def upsert_source(
    session: Session,
    *,
    title: str,
    url: str,
    retrieved_at: datetime,
    content_hash: str,
    article: str | None,
    quoted_text: str,
    review_status: str = "human_verified",
) -> SourceEvidence:
    doc = session.scalar(select(SourceDocument).where(SourceDocument.url == url))
    if doc is None:
        doc = SourceDocument(
            title=title, url=url, retrieved_at=retrieved_at, content_hash=content_hash
        )
        session.add(doc)
        session.flush()
    ev = session.scalar(
        select(SourceEvidence).where(
            SourceEvidence.document_id == doc.id, SourceEvidence.quoted_text == quoted_text
        )
    )
    if ev is None:
        ev = SourceEvidence(
            document_id=doc.id,
            article=article,
            quoted_text=quoted_text,
            review_status=review_status,
        )
        session.add(ev)
        session.flush()
    return ev
