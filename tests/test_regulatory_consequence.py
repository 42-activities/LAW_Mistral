from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.dialects.postgresql import Range

from app.modules.core.models import Jurisdiction
from app.modules.risk.models import ListDefinition, RegulatoryConsequence
from app.modules.risk.repository import ConsequenceRepository
from app.modules.source.models import SourceDocument, SourceEvidence


def _seed(db_session):
    doc = SourceDocument(
        title="CGI", url="https://legifrance", retrieved_at=datetime.now(UTC), content_hash="h"
    )
    fr = Jurisdiction(code="FR", name="France")
    db_session.add_all([doc, fr])
    db_session.flush()
    ev = SourceEvidence(
        document_id=doc.id, article="CGI 238-0 A", quoted_text="75%",
        review_status="human_verified",
    )
    db_session.add(ev)
    db_session.flush()
    etnc = ListDefinition(
        code="FR_ETNC", name="ETNC", family="tax_governance", publisher="France",
        update_cadence="per national law", source_evidence_id=ev.id,
    )
    db_session.add(etnc)
    db_session.flush()
    db_session.add(RegulatoryConsequence(
        applying_jurisdiction_id=fr.id, list_definition_id=etnc.id, classification_trigger="full_measures",
        consequence_type="withholding_tax", rate=Decimal("75"), legal_ref="CGI art. 238-0 A",
        description="75% WHT on certain payments to ETNC (full measures)",
        source_evidence_id=ev.id,
        valid_period=Range(date(2010, 2, 12), None, bounds="[)"),
    ))
    db_session.flush()
    return fr, etnc


def test_for_applying_jurisdiction(db_session):
    _seed(db_session)
    repo = ConsequenceRepository(db_session)
    rows = repo.for_applying_jurisdiction("FR", date(2024, 1, 1))
    assert len(rows) == 1 and rows[0].rate == Decimal("75")


def test_triggered_by_classification(db_session):
    _seed(db_session)
    repo = ConsequenceRepository(db_session)
    assert len(repo.triggered_by("FR_ETNC", "full_measures", date(2024, 1, 1))) == 1
    assert len(repo.triggered_by("FR_ETNC", "certain_measures", date(2024, 1, 1))) == 0
