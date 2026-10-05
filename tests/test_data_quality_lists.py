from datetime import UTC, date, datetime

from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.risk.models import ListDefinition, RegulatoryConsequence
from app.modules.seed.quality import run_checks
from app.modules.source.models import SourceDocument, SourceEvidence


def test_seeded_fixture_passes_quality_checks(seeded_session: Session) -> None:
    assert run_checks(seeded_session) == [], run_checks(seeded_session)


def test_wht_consequence_without_rate_is_flagged(db_session: Session) -> None:
    doc = SourceDocument(
        title="x", url="https://x", retrieved_at=datetime.now(UTC), content_hash="h"
    )
    xx = Jurisdiction(code="XX", name="Test")
    db_session.add_all([doc, xx])
    db_session.flush()
    ev = SourceEvidence(document_id=doc.id, quoted_text="q", review_status="human_verified")
    db_session.add(ev)
    db_session.flush()
    ld = ListDefinition(
        code="XX_TEST",
        name="TEST",
        family="tax_governance",
        publisher="Test",
        update_cadence=None,
        source_evidence_id=ev.id,
    )
    db_session.add(ld)
    db_session.flush()
    db_session.add(
        RegulatoryConsequence(
            applying_jurisdiction_id=xx.id,
            list_definition_id=ld.id,
            classification_trigger="full_measures",
            consequence_type="withholding_tax",
            rate=None,
            legal_ref="CGI 238-0 A",
            description=None,
            source_evidence_id=ev.id,
            valid_period=Range(date(2010, 2, 12), None, bounds="[)"),
        )
    )
    db_session.flush()
    assert any("rate" in v.lower() for v in run_checks(db_session))
