from app.modules.seed.france_uae import seed
from app.modules.seed.quality import run_checks


def test_seeded_fixture_passes_quality_checks(db_session):
    seed(db_session)
    db_session.flush()
    violations = run_checks(db_session)
    assert violations == [], violations


def test_treaty_without_two_parties_is_flagged(db_session):
    from datetime import date

    from app.modules.core.models import Jurisdiction
    from app.modules.source.models import SourceDocument, SourceEvidence
    from app.modules.treaty.models import Treaty, TreatyParty

    doc = SourceDocument(
        title="t",
        url="https://x",
        retrieved_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
        content_hash="h",
    )
    gb = Jurisdiction(code="GB", name="United Kingdom")
    db_session.add_all([doc, gb])
    db_session.flush()
    ev = SourceEvidence(
        document_id=doc.id, quoted_text="q", review_status="human_verified"
    )
    db_session.add(ev)
    db_session.flush()
    t = Treaty(name="lonely", signature_date=date(2000, 1, 1), source_evidence_id=ev.id)
    db_session.add(t)
    db_session.flush()
    db_session.add(TreatyParty(treaty_id=t.id, jurisdiction_id=gb.id))  # only one party
    db_session.flush()
    violations = run_checks(db_session)
    assert any("party" in v.lower() for v in violations)
