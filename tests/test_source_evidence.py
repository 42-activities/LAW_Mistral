from datetime import UTC, datetime

from app.modules.source.models import SourceDocument, SourceEvidence
from app.modules.source.service import EvidenceService


def test_evidence_resolves_to_document(db_session):
    doc = SourceDocument(
        title="UAE Corporate Tax Law",
        url="https://mof.gov.ae/corporate-tax/",
        retrieved_at=datetime.now(UTC),
        content_hash="abc123",
    )
    db_session.add(doc)
    db_session.flush()
    ev = SourceEvidence(
        document_id=doc.id,
        article="Art. 16",
        page=12,
        quoted_text="Withholding tax ... 0%",
        review_status="human_verified",
    )
    db_session.add(ev)
    db_session.flush()

    view = EvidenceService(db_session).get(ev.id)
    assert view is not None
    assert view.document_title == "UAE Corporate Tax Law"
    assert view.article == "Art. 16"
    assert view.review_status == "human_verified"


def test_missing_evidence_returns_none(db_session):
    assert EvidenceService(db_session).get(999999) is None
