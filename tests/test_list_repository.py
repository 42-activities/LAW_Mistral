from datetime import UTC, date, datetime

from sqlalchemy.dialects.postgresql import Range

from app.modules.core.models import Jurisdiction
from app.modules.risk.models import ListDefinition, ListMembership
from app.modules.risk.repository import ListRepository
from app.modules.source.models import SourceDocument, SourceEvidence


def _seed(db_session):
    doc = SourceDocument(
        title="s", url="https://s", retrieved_at=datetime.now(UTC), content_hash="h"
    )
    ae = Jurisdiction(code="AE", name="UAE")
    db_session.add_all([doc, ae])
    db_session.flush()
    ev = SourceEvidence(document_id=doc.id, quoted_text="q", review_status="human_verified")
    db_session.add(ev)
    db_session.flush()
    grey = ListDefinition(
        code="FATF_GREY",
        name="grey",
        family="aml_cft",
        publisher="FATF",
        update_cadence=None,
        source_evidence_id=ev.id,
    )
    aml = ListDefinition(
        code="EU_AML_HIGH_RISK",
        name="eu aml",
        family="aml_cft",
        publisher="European Commission",
        update_cadence=None,
        source_evidence_id=ev.id,
    )
    db_session.add_all([grey, aml])
    db_session.flush()
    db_session.add_all(
        [
            ListMembership(
                list_definition_id=grey.id,
                jurisdiction_id=ae.id,
                classification="increased_monitoring",
                announcement_date=date(2022, 3, 4),
                status="active",
                source_evidence_id=ev.id,
                valid_period=Range(date(2022, 3, 4), date(2024, 2, 23), bounds="[)"),
            ),
            ListMembership(
                list_definition_id=aml.id,
                jurisdiction_id=ae.id,
                classification="high_risk",
                announcement_date=date(2023, 3, 16),
                status="active",
                source_evidence_id=ev.id,
                valid_period=Range(date(2023, 3, 16), date(2025, 6, 10), bounds="[)"),
            ),
        ]
    )
    db_session.flush()
    return ae


def test_is_listed_as_of(db_session):
    _seed(db_session)
    repo = ListRepository(db_session)
    assert repo.is_listed("AE", "FATF_GREY", date(2023, 1, 1)) is not None  # during
    assert repo.is_listed("AE", "FATF_GREY", date(2024, 6, 1)) is None  # after removal
    assert repo.is_listed("AE", "FATF_GREY", date(2021, 1, 1)) is None  # before


def test_lists_for_returns_both_concurrent(db_session):
    _seed(db_session)
    repo = ListRepository(db_session)
    codes = {m.list_definition_id for m in repo.lists_for("AE", date(2023, 6, 1))}
    assert len(codes) == 2  # on FATF grey AND EU AML on this date


def test_members_of_list(db_session):
    _seed(db_session)
    repo = ListRepository(db_session)
    assert len(repo.members("FATF_GREY", date(2023, 1, 1))) == 1
    assert len(repo.members("FATF_GREY", date(2025, 1, 1))) == 0
