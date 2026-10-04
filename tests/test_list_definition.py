from datetime import UTC, datetime

from app.modules.risk.repository import ListDefinitionRepository
from app.modules.source.models import SourceDocument, SourceEvidence


def _evidence(db_session):
    doc = SourceDocument(
        title="FATF",
        url="https://fatf-gafi.org",
        retrieved_at=datetime.now(UTC),
        content_hash="h",
    )
    db_session.add(doc)
    db_session.flush()
    ev = SourceEvidence(
        document_id=doc.id,
        quoted_text="increased monitoring",
        review_status="human_verified",
    )
    db_session.add(ev)
    db_session.flush()
    return ev


def test_create_and_lookup(db_session):
    ev = _evidence(db_session)
    repo = ListDefinitionRepository(db_session)
    created = repo.get_or_create(
        "FATF_GREY",
        name="FATF jurisdictions under increased monitoring",
        family="aml_cft",
        publisher="FATF",
        update_cadence="after each plenary",
        source_evidence_id=ev.id,
    )
    db_session.flush()
    assert created.id is not None
    assert repo.get("FATF_GREY").family == "aml_cft"
    assert repo.get("NOPE") is None


def test_get_or_create_idempotent(db_session):
    ev = _evidence(db_session)
    repo = ListDefinitionRepository(db_session)
    a = repo.get_or_create(
        "EU_TAX_ANNEX_I",
        name="EU Annex I",
        family="tax_governance",
        publisher="Council of the EU",
        update_cadence="twice a year",
        source_evidence_id=ev.id,
    )
    db_session.flush()
    b = repo.get_or_create(
        "EU_TAX_ANNEX_I",
        name="EU Annex I",
        family="tax_governance",
        publisher="Council of the EU",
        update_cadence="twice a year",
        source_evidence_id=ev.id,
    )
    db_session.flush()
    assert a.id == b.id
