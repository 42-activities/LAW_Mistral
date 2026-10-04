from datetime import UTC, date, datetime

from app.modules.core.models import Jurisdiction
from app.modules.source.models import SourceDocument, SourceEvidence
from app.modules.treaty.models import Treaty, TreatyArticle, TreatyParty, TreatyProtocol


def _ev(db_session):
    doc = SourceDocument(
        title="FR-UAE treaty",
        url="https://impots",
        retrieved_at=datetime.now(UTC),
        content_hash="h",
    )
    db_session.add(doc)
    db_session.flush()
    ev = SourceEvidence(document_id=doc.id, quoted_text="t", review_status="human_verified")
    db_session.add(ev)
    db_session.flush()
    return ev


def test_treaty_with_two_parties_and_article(db_session):
    ev = _ev(db_session)
    fr = Jurisdiction(code="FR", name="France")
    ae = Jurisdiction(code="AE", name="UAE")
    db_session.add_all([fr, ae])
    db_session.flush()
    t = Treaty(
        name="France-UAE",
        signature_date=date(1989, 7, 19),
        entry_into_force_date=date(1990, 7, 1),
        source_evidence_id=ev.id,
    )
    db_session.add(t)
    db_session.flush()
    db_session.add_all(
        [
            TreatyParty(treaty_id=t.id, jurisdiction_id=fr.id),
            TreatyParty(treaty_id=t.id, jurisdiction_id=ae.id),
            TreatyArticle(treaty_id=t.id, article_category="DIVIDENDS", article_ref="Article 8"),
            TreatyProtocol(
                treaty_id=t.id,
                signature_date=date(1993, 12, 6),
                entry_into_force_date=None,
                description="1993 amendment",
                source_evidence_id=ev.id,
            ),
        ]
    )
    db_session.flush()
    assert len(t.parties) == 2
    assert t.articles[0].article_category == "DIVIDENDS"
