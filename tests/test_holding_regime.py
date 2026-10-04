from datetime import UTC, date, datetime

from sqlalchemy.dialects.postgresql import Range

from app.modules.core.models import Jurisdiction
from app.modules.source.models import SourceDocument, SourceEvidence
from app.modules.tax.models import HoldingRegime
from app.modules.tax.repository import HoldingRegimeRepository


def test_holding_regime_as_of(db_session):
    doc = SourceDocument(
        title="FR CGI", url="https://bofip", retrieved_at=datetime.now(UTC), content_hash="h"
    )
    fr = Jurisdiction(code="FR", name="France")
    db_session.add_all([doc, fr])
    db_session.flush()
    ev = SourceEvidence(
        document_id=doc.id, quoted_text="régime mère-fille", review_status="human_verified"
    )
    db_session.add(ev)
    db_session.flush()
    db_session.add(
        HoldingRegime(
            jurisdiction_id=fr.id,
            participation_exemption_dividends=True,
            participation_exemption_capgains=True,
            min_holding_pct=5,
            min_holding_period_months=24,
            subject_to_tax_condition=True,
            notes="régime mère-fille",
            source_evidence_id=ev.id,
            valid_period=Range(date(2020, 1, 1), None, bounds="[)"),
        )
    )
    db_session.flush()
    repo = HoldingRegimeRepository(db_session)
    got = repo.get("FR", date(2024, 1, 1))
    assert got is not None and got.participation_exemption_dividends is True
    assert repo.get("FR", date(2019, 1, 1)) is None
