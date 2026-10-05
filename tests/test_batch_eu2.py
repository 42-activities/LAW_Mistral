"""Golden expectations for P8 batch 2 (DE, IE, MT, BE)."""

from datetime import date
from decimal import Decimal

import pytest

from app.modules.engine.flow import Flow, FlowCalculator
from app.modules.engine.tax import TaxEngine
from app.modules.engine.withholding import WithholdingEngine
from app.modules.scoring.scorer import Scorer
from app.modules.scoring.types import ProfileFlow, ScoringProfile
from app.modules.seed.quality import run_checks

D = date(2026, 6, 30)


@pytest.fixture
def s(seeded_session):
    return seeded_session


def codes(r):
    return {f.code for f in r.flags}


@pytest.mark.parametrize(
    ("src", "dst", "cat", "pct", "days", "domestic", "final", "flag"),
    [
        # France–Germany caps differ by direction (art. 9(3) vs 9(5)).
        ("FR", "DE", "DIVIDEND", "100", 730, "25.000", "0.000", "directive_exemption"),
        ("FR", "DE", "DIVIDEND", "5", 400, "25.000", "15.000", "treaty_threshold_not_met"),
        ("DE", "FR", "DIVIDEND", "20", 400, "15.825", "0.000", "directive_exemption"),
        ("DE", "FR", "DIVIDEND", "20", 200, "15.825", "15.000", "exemption_conditions_not_met"),
        ("DE", "FR", "DIVIDEND", "5", 400, "15.825", "15.000", "treaty_threshold_not_met"),
        ("DE", "AE", "DIVIDEND", "100", 730, "15.825", "15.825", "no_treaty"),
        ("DE", "FR", "ROYALTY", "25", None, "15.825", "0.000", "directive_exemption"),
        # Ireland: DWT exempt for EU companies; treaty 0% with the UAE.
        ("IE", "FR", "DIVIDEND", "100", 730, "25.000", "0.000", "directive_exemption"),
        ("IE", "AE", "DIVIDEND", "100", 730, "25.000", "0.000", None),
        ("FR", "IE", "DIVIDEND", "60", 400, "25.000", "10.000", "exemption_conditions_not_met"),
        ("FR", "IE", "DIVIDEND", "60", 200, "25.000", "15.000", "treaty_holding_period_not_met"),
        # Malta: no withholding outbound; France caps royalties at 10% under the treaty.
        ("MT", "FR", "DIVIDEND", None, None, "0.000", "0.000", None),
        ("FR", "MT", "ROYALTY", "10", 100, "25.000", "10.000", "exemption_conditions_not_met"),
        ("FR", "MT", "DIVIDEND", "10", 100, "25.000", "0.000", None),
        # Belgium: 30% précompte, EU directive exemptions, 1964 treaty with France.
        ("BE", "FR", "DIVIDEND", "100", 730, "30.000", "0.000", "directive_exemption"),
        ("BE", "FR", "DIVIDEND", "12", 400, "30.000", "0.000", "directive_exemption"),
        ("BE", "FR", "DIVIDEND", "5", 400, "30.000", "15.000", "treaty_threshold_not_met"),
        ("BE", "FR", "INTEREST", "10", 400, "30.000", "15.000", "exemption_conditions_not_met"),
        ("BE", "FR", "ROYALTY", "30", 400, "30.000", "0.000", "directive_exemption"),
        ("BE", "AE", "DIVIDEND", "30", 400, "30.000", "5.000", None),
        ("BE", "AE", "ROYALTY", None, None, "30.000", "5.000", None),
    ],
)
def test_corridors(s, src, dst, cat, pct, days, domestic, final, flag):
    r = WithholdingEngine(s).compute(
        src, dst, cat, D, None if pct is None else Decimal(pct), days
    )
    assert r.complete, r.flags
    assert str(r.domestic_rate) == domestic
    assert str(r.final_rate) == final
    if flag:
        assert flag in codes(r)
    assert r.citations


def test_category_cit_and_refunds(s):
    tax = TaxEngine(s)
    assert tax.cit("IE", D).rate == Decimal("12.5")
    assert tax.cit("IE", D, income_category="ROYALTY").rate == Decimal("25")
    assert tax.cit("IE", D, income_category="DIVIDEND").rate == Decimal("12.5")  # fallback
    assert tax.cit("DE", D).rate == Decimal("32.975")
    assert tax.cit("DE", date(2028, 1, 1)).rate is None  # rate path after 2027 not seeded

    calc = FlowCalculator(s)
    malta = calc.compute(Flow("ROYALTY", "FR", "MT", "FR", Decimal("100"), 24), D)
    leg = malta.legs[1]
    assert leg.rate == Decimal("10.000")  # 35% less the 5/7 shareholder refund
    assert leg.detail["cit_before_refund"] == "35.000"
    assert "shareholder_refund" in {f.code for f in leg.flags}
    germany = calc.compute(Flow("DIVIDEND", "FR", "DE", "FR", Decimal("100"), 24), D)
    assert germany.legs[1].rate == Decimal("1.649")  # 5% of 32.975% (§8b(5) KStG)


def test_cfc_uses_effective_rate_after_refunds(s):
    profile = ScoringProfile(
        parent="FR", flows=(ProfileFlow("DIVIDEND", "FR"), ProfileFlow("ROYALTY", "FR"))
    )
    cards = {c.jurisdiction: c for c in Scorer(s).rank(profile, ["MT", "DE", "IE"], D)}

    def cfc(j):
        return "cfc_exposure" in {f.code for f in cards[j].factors["substance_burden"].flags}

    assert cfc("MT")  # 35% headline, 10% after refund ≤ 15%
    assert cfc("IE")  # 12.5% trading rate ≤ 15%
    assert not cfc("DE")
    assert all(c.complete for c in cards.values())


def test_data_quality_checks_pass(s):
    assert run_checks(s) == []
