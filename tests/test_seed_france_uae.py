from datetime import date
from decimal import Decimal

from app.modules.seed.france_uae import seed
from app.modules.tax.repository import TaxRuleRepository, resolve_bracket_rate
from app.modules.treaty.repository import TreatyRepository


def test_seed_is_idempotent_and_resolves(db_session):
    seed(db_session)
    seed(db_session)  # second run must not duplicate or error
    db_session.flush()

    tax = TaxRuleRepository(db_session)
    # UAE 0% WHT royalty
    assert tax.get_rule("AE", "WHT_ROYALTY", "ROYALTY", date(2024, 1, 1)).rate == Decimal("0")
    # France 25% company dividend WHT
    fr_div = tax.get_rule(
        "FR", "WHT_DIVIDEND", "DIVIDEND", date(2024, 1, 1), taxpayer_type="company"
    )
    assert fr_div.rate == Decimal("25")
    # UAE CIT brackets
    cit = tax.get_rule("AE", "CIT", "CORPORATE_PROFIT", date(2024, 1, 1), taxpayer_type="company")
    assert resolve_bracket_rate(cit, Decimal("100000")) == Decimal("0")
    assert resolve_bracket_rate(cit, Decimal("1000000")) == Decimal("9")

    treaty = TreatyRepository(db_session)
    t = treaty.find_by_parties("FR", "AE")
    assert t is not None
    rate = treaty.get_rate(t.id, "DIVIDEND", date(2024, 1, 1))
    assert rate.exclusive_residence_taxation is True and rate.relief_mechanism == "refund"
    assert treaty.get_article(t.id, "DIVIDENDS").article_ref == "Article 8"


def test_every_seeded_figure_has_evidence(db_session):
    seed(db_session)
    db_session.flush()
    from app.modules.tax.models import DomesticTaxRule, HoldingRegime
    from app.modules.treaty.models import Treaty, TreatyProtocol, TreatyRate

    for model in (DomesticTaxRule, HoldingRegime, TreatyRate, Treaty, TreatyProtocol):
        rows = db_session.query(model).all()
        assert rows, f"no {model.__name__} rows seeded"
        assert all(r.source_evidence_id is not None for r in rows)
