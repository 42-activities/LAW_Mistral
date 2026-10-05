"""Golden expectations for P8 batch 4 (HK, AT, PT, IT)."""

from datetime import date
from decimal import Decimal

import pytest

from app.modules.engine.flow import Flow, FlowCalculator
from app.modules.engine.tax import TaxEngine
from app.modules.engine.withholding import WithholdingEngine
from app.modules.scoring.scorer import Scorer
from app.modules.scoring.types import ProfileFlow, ScoringProfile
from app.modules.seed.france_uae import seed
from app.modules.seed.quality import run_checks

D = date(2026, 6, 30)


@pytest.fixture
def s(db_session):
    seed(db_session)
    db_session.flush()
    return db_session


def codes(r):
    return {f.code for f in r.flags}


@pytest.mark.parametrize(
    ("src", "dst", "cat", "pct", "days", "domestic", "effective", "final", "flag"),
    [
        # Hong Kong: deemed-profit royalty rate below the treaty caps.
        ("HK", "FR", "ROYALTY", None, None, "4.950", "4.950", "4.950", None),
        ("HK", "AE", "DIVIDEND", None, None, "0.000", "0.000", "0.000", None),
        ("FR", "HK", "ROYALTY", None, None, "25.000", "25.000", "10.000", None),
        ("FR", "HK", "DIVIDEND", "100", 730, "25.000", "25.000", "10.000", None),
        # Austria: EU directives; 2023 protocol with the UAE.
        ("AT", "FR", "DIVIDEND", "10", 400, "27.500", "0.000", "0.000", "directive_exemption"),
        ("AT", "FR", "DIVIDEND", "5", 400, "27.500", "27.500", "15.000",
         "treaty_threshold_not_met"),
        ("AT", "AE", "DIVIDEND", "10", None, "27.500", "27.500", "0.000", None),
        ("AT", "AE", "ROYALTY", None, None, "20.000", "20.000", "0.000", None),
        ("AT", "FR", "ROYALTY", "25", 400, "20.000", "0.000", "0.000", "directive_exemption"),
        # Portugal: 25% final WHT; royalty directive needs 2 years.
        ("PT", "FR", "DIVIDEND", "10", 400, "25.000", "0.000", "0.000", "directive_exemption"),
        ("PT", "FR", "ROYALTY", "25", 400, "25.000", "25.000", "5.000",
         "exemption_conditions_not_met"),
        ("PT", "FR", "ROYALTY", "25", 800, "25.000", "0.000", "0.000", "directive_exemption"),
        ("PT", "AE", "DIVIDEND", "10", None, "25.000", "25.000", "5.000", None),
        ("PT", "AE", "INTEREST", None, None, "25.000", "25.000", "10.000", None),
        # Italy: 1.2% for EU companies, 0% under the directive, no MLI.
        ("IT", "FR", "DIVIDEND", None, None, "26.000", "1.200", "1.200", "directive_exemption"),
        ("IT", "FR", "DIVIDEND", "10", 400, "26.000", "0.000", "0.000", "directive_exemption"),
        ("IT", "AE", "DIVIDEND", "30", None, "26.000", "26.000", "5.000", None),
        ("IT", "AE", "ROYALTY", None, None, "30.000", "30.000", "10.000", None),
        ("FR", "IT", "ROYALTY", "10", 400, "25.000", "25.000", "5.000",
         "exemption_conditions_not_met"),
    ],
)
def test_corridors(s, src, dst, cat, pct, days, domestic, effective, final, flag):
    r = WithholdingEngine(s).compute(
        src, dst, cat, D, None if pct is None else Decimal(pct), days
    )
    assert r.complete, r.flags
    assert (str(r.domestic_rate), str(r.effective_domestic_rate), str(r.final_rate)) == (
        domestic, effective, final
    )
    if flag:
        assert flag in codes(r)
    assert r.citations


def test_cit_bands(s):
    tax = TaxEngine(s)
    assert tax.cit("HK", D, Decimal("1000000")).rate == Decimal("8.250")
    assert tax.cit("HK", D).rate == Decimal("16.5")  # top band without an amount
    assert tax.cit("AT", D).rate == Decimal("23")
    assert tax.cit("AT", date(2028, 6, 30), Decimal("2000000")).rate == Decimal("23.500")
    assert tax.cit("PT", D, Decimal("1000000")).rate == Decimal("20.500")
    assert tax.cit("PT", D).rate == Decimal("29.5")  # conservative top band
    assert tax.cit("PT", date(2027, 6, 30)).rate is None  # 2027 rate not seeded yet
    assert tax.cit("IT", D, income_category="ROYALTY").rate == Decimal("27.9")
    assert tax.cit("IT", D, income_category="DIVIDEND").rate == Decimal("24")


def test_portugal_participation_needs_11_4pct_payer_tax(s):
    calc = FlowCalculator(s)
    fr = calc.compute(Flow("DIVIDEND", "FR", "PT", "FR", Decimal("100"), 24), D)
    assert fr.legs[1].detail["participation_exemption"] == "applies"
    ae = calc.compute(Flow("DIVIDEND", "AE", "PT", "FR", Decimal("100"), 24), D)
    assert ae.legs[1].detail["participation_exemption"] == "not applied"


def test_rankings_complete(s):
    profile = ScoringProfile(
        parent="FR", flows=(ProfileFlow("DIVIDEND", "FR"), ProfileFlow("ROYALTY", "FR"))
    )
    cards = Scorer(s).rank(profile, ["HK", "AT", "PT", "IT"], D)
    assert all(c.complete for c in cards)


def test_data_quality_checks_pass(s):
    assert run_checks(s) == []
