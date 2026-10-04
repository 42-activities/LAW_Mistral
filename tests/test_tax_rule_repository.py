from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.dialects.postgresql import Range

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import IncomeCategory, TaxType
from app.modules.source.models import SourceDocument, SourceEvidence
from app.modules.tax.models import DomesticTaxRule, TaxBracket
from app.modules.tax.repository import TaxRuleRepository, resolve_bracket_rate


def _evidence(db_session):
    doc = SourceDocument(
        title="d", url="https://x", retrieved_at=datetime.now(UTC), content_hash="h"
    )
    db_session.add(doc)
    db_session.flush()
    ev = SourceEvidence(document_id=doc.id, quoted_text="q", review_status="human_verified")
    db_session.add(ev)
    db_session.flush()
    return ev


def test_as_of_resolution(db_session):
    ev = _evidence(db_session)
    ae = Jurisdiction(code="AE", name="UAE")
    tt = TaxType(code="WHT_ROYALTY", name="roy")
    ic = IncomeCategory(code="ROYALTY", name="Royalty")
    db_session.add_all([ae, tt, ic])
    db_session.flush()
    db_session.add(
        DomesticTaxRule(
            jurisdiction_id=ae.id,
            tax_type_id=tt.id,
            income_category_id=ic.id,
            taxpayer_type="any",
            rate=Decimal("0"),
            is_bracketed=False,
            source_evidence_id=ev.id,
            valid_period=Range(date(2023, 6, 1), None, bounds="[)"),
        )
    )
    db_session.flush()
    repo = TaxRuleRepository(db_session)
    rule = repo.get_rule("AE", "WHT_ROYALTY", "ROYALTY", date(2024, 1, 1))
    assert rule is not None and rule.rate == Decimal("0")
    assert repo.get_rule("AE", "WHT_ROYALTY", "ROYALTY", date(2023, 1, 1)) is None


def test_bracket_resolution(db_session):
    ev = _evidence(db_session)
    ae = Jurisdiction(code="AE", name="UAE")
    tt = TaxType(code="CIT", name="cit")
    ic = IncomeCategory(code="CORPORATE_PROFIT", name="Corporate profit")
    db_session.add_all([ae, tt, ic])
    db_session.flush()
    rule = DomesticTaxRule(
        jurisdiction_id=ae.id,
        tax_type_id=tt.id,
        income_category_id=ic.id,
        taxpayer_type="company",
        rate=None,
        is_bracketed=True,
        source_evidence_id=ev.id,
        valid_period=Range(date(2023, 6, 1), None, bounds="[)"),
    )
    rule.brackets = [
        TaxBracket(
            lower_bound=Decimal("0"), upper_bound=Decimal("375000"), rate=Decimal("0"), position=0
        ),
        TaxBracket(lower_bound=Decimal("375000"), upper_bound=None, rate=Decimal("9"), position=1),
    ]
    db_session.add(rule)
    db_session.flush()
    assert resolve_bracket_rate(rule, Decimal("0")) == Decimal("0")
    assert resolve_bracket_rate(rule, Decimal("100000")) == Decimal("0")
    assert resolve_bracket_rate(rule, Decimal("374999.99")) == Decimal("0")
    assert resolve_bracket_rate(rule, Decimal("375000")) == Decimal("9")
    assert resolve_bracket_rate(rule, Decimal("1000000")) == Decimal("9")
