"""Golden expectations for P8 batch 3 (GB, ES, SG, CH)."""

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
        # UK: outside the EU since the directives; treaty 0% with France.
        ("FR", "GB", "DIVIDEND", "10", 100, "25.000", "25.000", "0.000", None),
        ("FR", "GB", "ROYALTY", "100", 730, "25.000", "25.000", "0.000", None),
        ("GB", "AE", "INTEREST", None, None, "20.000", "20.000", "20.000",
         "treaty_rate_not_recorded"),
        ("GB", "AE", "DIVIDEND", None, None, "0.000", "0.000", "0.000", None),
        # Spain: reduced 19% for EU royalties, 0% for associated companies, treaty 5%.
        ("ES", "FR", "ROYALTY", None, None, "24.000", "19.000", "5.000", "directive_exemption"),
        ("ES", "FR", "ROYALTY", "30", 400, "24.000", "0.000", "0.000", "directive_exemption"),
        ("ES", "FR", "DIVIDEND", "5", 400, "19.000", "0.000", "0.000", "directive_exemption"),
        ("ES", "AE", "DIVIDEND", "10", None, "19.000", "19.000", "5.000", None),
        ("FR", "ES", "DIVIDEND", "5", 400, "25.000", "25.000", "15.000",
         "treaty_threshold_not_met"),
        # Singapore.
        ("SG", "FR", "INTEREST", None, None, "15.000", "15.000", "0.000", None),
        ("SG", "AE", "ROYALTY", None, None, "10.000", "10.000", "5.000", None),
        ("FR", "SG", "DIVIDEND", "10", None, "25.000", "25.000", "5.000", None),
        # Switzerland: 35% Verrechnungssteuer, treaty or EU-agreement relief.
        ("CH", "FR", "DIVIDEND", "10", 100, "35.000", "35.000", "0.000", None),
        ("CH", "FR", "DIVIDEND", "30", 730, "35.000", "0.000", "0.000", "directive_exemption"),
        ("CH", "AE", "DIVIDEND", "10", None, "35.000", "35.000", "5.000", None),
        ("CH", "AE", "DIVIDEND", "5", None, "35.000", "35.000", "15.000",
         "treaty_threshold_not_met"),
        ("FR", "CH", "ROYALTY", "100", 730, "25.000", "25.000", "5.000", None),
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


def test_uk_marginal_relief_bands(s):
    tax = TaxEngine(s)
    assert tax.cit("GB", D, Decimal("40000")).rate == Decimal("19.000")
    assert tax.cit("GB", D, Decimal("100000")).rate == Decimal("22.750")
    assert tax.cit("GB", D, Decimal("250000")).rate == Decimal("25.000")
    assert tax.cit("GB", D, Decimal("1000000")).rate == Decimal("25.000")


def test_singapore_foreign_dividend_needs_15pct_headline_rate(s):
    calc = FlowCalculator(s)
    from_fr = calc.compute(Flow("DIVIDEND", "FR", "SG", "FR", Decimal("100"), 24), D)
    assert from_fr.legs[1].detail["participation_exemption"] == "applies"
    from_ae = calc.compute(Flow("DIVIDEND", "AE", "SG", "FR", Decimal("100"), 24), D)
    assert from_ae.legs[1].detail["participation_exemption"] == "not applied"
    assert from_ae.legs[1].rate == Decimal("17.000")


def test_cfc_outcomes(s):
    profile = ScoringProfile(
        parent="FR", flows=(ProfileFlow("DIVIDEND", "FR"), ProfileFlow("ROYALTY", "FR"))
    )
    cards = {c.jurisdiction: c for c in Scorer(s).rank(profile, ["GB", "ES", "SG", "CH"], D)}
    cfc = {
        j: "cfc_exposure" in {f.code for f in c.factors["substance_burden"].flags}
        for j, c in cards.items()
    }
    assert cfc == {"GB": False, "ES": False, "SG": False, "CH": True}  # Zug 11.71% ≤ 15%
    assert all(c.complete for c in cards.values())


def test_data_quality_checks_pass(s):
    assert run_checks(s) == []
