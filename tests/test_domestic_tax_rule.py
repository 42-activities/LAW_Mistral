from datetime import UTC, date, datetime

import pytest
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.exc import IntegrityError

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import IncomeCategory, TaxType
from app.modules.source.models import SourceDocument, SourceEvidence
from app.modules.tax.models import DomesticTaxRule


def _seed_minimal(db_session):
    j = Jurisdiction(code="AE", name="United Arab Emirates")
    tt = TaxType(code="WHT_ROYALTY", name="WHT on royalties")
    ic = IncomeCategory(code="ROYALTY", name="Royalty")
    doc = SourceDocument(title="UAE CT Law", url="https://mof.gov.ae/corporate-tax/",
                         retrieved_at=datetime.now(UTC), content_hash="x")
    db_session.add_all([j, tt, ic, doc])
    db_session.flush()
    ev = SourceEvidence(document_id=doc.id, article="FDL 47", page=1,
                        quoted_text="0% WHT", review_status="human_verified")
    db_session.add(ev)
    db_session.flush()
    return j, tt, ic, ev


def test_create_rule_with_validity(db_session):
    j, tt, ic, ev = _seed_minimal(db_session)
    rule = DomesticTaxRule(
        jurisdiction_id=j.id, tax_type_id=tt.id, income_category_id=ic.id,
        taxpayer_type="any", rate=0, is_bracketed=False, source_evidence_id=ev.id,
        valid_period=Range(date(2023, 6, 1), None, bounds="[)"),
    )
    db_session.add(rule)
    db_session.flush()
    assert rule.id is not None


def test_overlapping_validity_is_rejected(db_session):
    j, tt, ic, ev = _seed_minimal(db_session)
    common = dict(jurisdiction_id=j.id, tax_type_id=tt.id, income_category_id=ic.id,
                  taxpayer_type="any", rate=0, is_bracketed=False, source_evidence_id=ev.id)
    first = Range(date(2023, 6, 1), None, bounds="[)")
    db_session.add(DomesticTaxRule(**common, valid_period=first))
    db_session.flush()
    second = Range(date(2024, 1, 1), None, bounds="[)")
    db_session.add(DomesticTaxRule(**common, valid_period=second))
    with pytest.raises(IntegrityError):
        db_session.flush()
