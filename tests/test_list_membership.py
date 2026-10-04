from datetime import UTC, date, datetime

import pytest
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.exc import IntegrityError

from app.modules.core.models import Jurisdiction
from app.modules.risk.models import ListDefinition, ListMembership
from app.modules.source.models import SourceDocument, SourceEvidence


def _setup(db_session):
    doc = SourceDocument(
        title="FATF",
        url="https://fatf-gafi.org",
        retrieved_at=datetime.now(UTC),
        content_hash="h",
    )
    ae = Jurisdiction(code="AE", name="UAE")
    db_session.add_all([doc, ae])
    db_session.flush()
    ev = SourceEvidence(document_id=doc.id, quoted_text="grey", review_status="human_verified")
    db_session.add(ev)
    db_session.flush()
    ld = ListDefinition(
        code="FATF_GREY",
        name="grey",
        family="aml_cft",
        publisher="FATF",
        update_cadence=None,
        source_evidence_id=ev.id,
    )
    db_session.add(ld)
    db_session.flush()
    return ae, ld, ev


def test_create_membership(db_session):
    ae, ld, ev = _setup(db_session)
    m = ListMembership(
        list_definition_id=ld.id,
        jurisdiction_id=ae.id,
        classification="increased_monitoring",
        announcement_date=date(2022, 3, 4),
        status="active",
        source_evidence_id=ev.id,
        valid_period=Range(date(2022, 3, 4), date(2024, 2, 23), bounds="[)"),
    )
    db_session.add(m)
    db_session.flush()
    assert m.id is not None


def test_overlapping_membership_rejected(db_session):
    ae, ld, ev = _setup(db_session)
    common = dict(
        list_definition_id=ld.id,
        jurisdiction_id=ae.id,
        classification="increased_monitoring",
        status="active",
        source_evidence_id=ev.id,
    )
    first = Range(date(2022, 3, 4), None, bounds="[)")
    db_session.add(ListMembership(**common, valid_period=first))
    db_session.flush()
    second = Range(date(2023, 1, 1), None, bounds="[)")
    db_session.add(ListMembership(**common, valid_period=second))
    with pytest.raises(IntegrityError):
        db_session.flush()
