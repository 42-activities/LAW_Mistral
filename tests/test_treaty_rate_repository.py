from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.dialects.postgresql import Range

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import IncomeCategory
from app.modules.source.models import SourceDocument, SourceEvidence
from app.modules.treaty.models import Treaty, TreatyArticle, TreatyParty, TreatyRate
from app.modules.treaty.repository import TreatyRepository


def _setup(db_session):
    doc = SourceDocument(
        title="t", url="https://impots", retrieved_at=datetime.now(UTC), content_hash="h"
    )
    fr = Jurisdiction(code="FR", name="France")
    ae = Jurisdiction(code="AE", name="UAE")
    ic = IncomeCategory(code="DIVIDEND", name="Dividend")
    db_session.add_all([doc, fr, ae, ic])
    db_session.flush()
    ev = SourceEvidence(document_id=doc.id, quoted_text="art 8", review_status="human_verified")
    db_session.add(ev)
    db_session.flush()
    t = Treaty(name="France-UAE", signature_date=date(1989, 7, 19), source_evidence_id=ev.id)
    db_session.add(t)
    db_session.flush()
    art = TreatyArticle(treaty_id=t.id, article_category="DIVIDENDS", article_ref="Article 8")
    db_session.add_all(
        [
            art,
            TreatyParty(treaty_id=t.id, jurisdiction_id=fr.id),
            TreatyParty(treaty_id=t.id, jurisdiction_id=ae.id),
        ]
    )
    db_session.flush()
    db_session.add(
        TreatyRate(
            treaty_id=t.id,
            treaty_article_id=art.id,
            income_category_id=ic.id,
            max_rate=Decimal("0"),
            exclusive_residence_taxation=True,
            relief_mechanism="refund",
            beneficial_owner_required=True,
            ownership_threshold=None,
            source_evidence_id=ev.id,
            valid_period=Range(date(1994, 1, 1), None, bounds="[)"),
        )
    )
    db_session.flush()
    return t


def test_find_by_parties_is_order_independent(db_session):
    t = _setup(db_session)
    repo = TreatyRepository(db_session)
    assert repo.find_by_parties("FR", "AE").id == t.id
    assert repo.find_by_parties("AE", "FR").id == t.id


def test_get_rate_as_of_and_article(db_session):
    t = _setup(db_session)
    repo = TreatyRepository(db_session)
    rate = repo.get_rate(t.id, "DIVIDEND", date(2024, 1, 1))
    assert rate.exclusive_residence_taxation is True
    assert rate.relief_mechanism == "refund"
    assert repo.get_rate(t.id, "DIVIDEND", date(1990, 1, 1)) is None
    assert repo.get_article(t.id, "DIVIDENDS").article_ref == "Article 8"
