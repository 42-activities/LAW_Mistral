from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.modules.source.models import SourceDocument, SourceEvidence


@dataclass(frozen=True)
class EvidenceView:
    id: int
    document_title: str
    document_url: str
    article: str | None
    quoted_text: str
    review_status: str


class EvidenceService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, evidence_id: int) -> EvidenceView | None:
        ev = self.session.get(SourceEvidence, evidence_id)
        if ev is None:
            return None
        doc = self.session.get(SourceDocument, ev.document_id)
        assert doc is not None  # FK guarantees presence
        return EvidenceView(
            id=ev.id,
            document_title=doc.title,
            document_url=doc.url,
            article=ev.article,
            quoted_text=ev.quoted_text,
            review_status=ev.review_status,
        )
