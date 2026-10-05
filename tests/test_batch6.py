"""Golden expectations for P8 batch 6 (US, CZ, MU, QA)."""

from datetime import date
from decimal import Decimal

import pytest

from app.modules.engine.flow import Flow, FlowCalculator
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
    ("src", "dst", "cat", "pct", "days", "domestic", "effective", "final", "flag"),
    [
        # United States: 30% FDAP; treaty tiers 15 / 5 / 0 (≥80%, 12 months).
        ("US", "FR", "DIVIDEND", "5", None, "30.000", "30.000", "15.000",
         "treaty_threshold_not_met"),
        ("US", "FR", "DIVIDEND", "50", None, "30.000", "30.000", "5.000", None),
        ("US", "FR", "DIVIDEND", "100", 400, "30.000", "30.000", "0.000", None),
        ("US", "AE", "ROYALTY", None, None, "30.000", "30.000", "30.000", "no_treaty"),
        # Czech Republic: new 2023 treaty with the UAE from 2025.
        ("CZ", "FR", "DIVIDEND", "10", 400, "15.000", "0.000", "0.000", "directive_exemption"),
        ("CZ", "AE", "DIVIDEND", None, None, "15.000", "15.000", "5.000", None),
        ("CZ", "AE", "ROYALTY", None, None, "15.000", "15.000", "10.000", None),
        ("FR", "CZ", "ROYALTY", "10", 400, "25.000", "25.000", "10.000",
         "exemption_conditions_not_met"),
        # Mauritius.
        ("MU", "FR", "ROYALTY", None, None, "15.000", "15.000", "15.000", None),
        ("MU", "AE", "INTEREST", None, None, "15.000", "15.000", "0.000", None),
        ("FR", "MU", "DIVIDEND", "10", None, "25.000", "25.000", "5.000", None),
        # Qatar: 5% WHT, 0% under the France treaty, no UAE treaty.
        ("QA", "FR", "ROYALTY", None, None, "5.000", "5.000", "0.000", None),
        ("QA", "AE", "INTEREST", None, None, "5.000", "5.000", "5.000", "no_treaty"),
        ("FR", "QA", "DIVIDEND", None, None, "25.000", "25.000", "0.000", None),
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


def test_holding_taxation(s):
    calc = FlowCalculator(s)
    mu = calc.compute(Flow("DIVIDEND", "FR", "MU", "FR", Decimal("100"), 24), D)
    assert mu.legs[1].rate == Decimal("3.000")  # 80% exempt × 15%
    mu_int = calc.compute(Flow("INTEREST", "FR", "MU", "FR", Decimal("100"), 24), D)
    assert mu_int.legs[1].rate == Decimal("3.000")
    qa = calc.compute(Flow("DIVIDEND", "FR", "QA", "FR", Decimal("100"), 24), D)
    assert qa.legs[1].rate == Decimal("10.000")
    assert "holding_regime_not_recorded" in {f.code for f in qa.flags}


def test_cfc_outcomes(s):
    profile = ScoringProfile(
        parent="FR", flows=(ProfileFlow("DIVIDEND", "FR"), ProfileFlow("ROYALTY", "FR"))
    )
    cards = {c.jurisdiction: c for c in Scorer(s).rank(profile, ["US", "CZ", "MU", "QA"], D)}
    cfc = {
        j: "cfc_exposure" in {f.code for f in c.factors["substance_burden"].flags}
        for j, c in cards.items()
    }
    assert cfc == {"US": False, "CZ": False, "MU": True, "QA": True}
    assert all(c.complete for c in cards.values())


def test_data_quality_checks_pass(s):
    assert run_checks(s) == []
