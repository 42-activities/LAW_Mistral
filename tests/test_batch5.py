"""Golden expectations for P8 batch 5 (PL, HU, SE, DK)."""

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
        # Poland: 2-year directive periods; treaty 5% tier needs 365 days.
        ("PL", "FR", "DIVIDEND", "10", 730, "19.000", "0.000", "0.000", "directive_exemption"),
        ("PL", "FR", "DIVIDEND", "10", 400, "19.000", "19.000", "5.000",
         "exemption_conditions_not_met"),
        ("PL", "AE", "ROYALTY", None, None, "20.000", "20.000", "5.000", None),
        ("FR", "PL", "ROYALTY", "10", 400, "25.000", "25.000", "10.000",
         "exemption_conditions_not_met"),
        # Hungary: no withholding; France caps dividends at 5% only from 25%.
        ("HU", "AE", "DIVIDEND", None, None, "0.000", "0.000", "0.000", None),
        ("FR", "HU", "DIVIDEND", "30", 730, "25.000", "0.000", "0.000", "directive_exemption"),
        ("FR", "HU", "DIVIDEND", "5", 400, "25.000", "25.000", "15.000",
         "treaty_threshold_not_met"),
        # Sweden: no treaty with the UAE.
        ("SE", "FR", "DIVIDEND", "10", None, "30.000", "0.000", "0.000", "directive_exemption"),
        ("SE", "AE", "DIVIDEND", "100", 730, "30.000", "30.000", "30.000", "no_treaty"),
        ("SE", "FR", "ROYALTY", None, None, "20.600", "20.600", "0.000", None),
        # Denmark: new 2022 treaty with France; no treaty with the UAE.
        ("DK", "FR", "DIVIDEND", "10", 400, "22.000", "0.000", "0.000", "directive_exemption"),
        ("DK", "AE", "DIVIDEND", "100", 730, "22.000", "22.000", "22.000", "no_treaty"),
        ("FR", "DK", "DIVIDEND", "5", 400, "25.000", "25.000", "15.000",
         "treaty_threshold_not_met"),
        ("FR", "DK", "ROYALTY", "10", 400, "25.000", "25.000", "0.000", None),
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


def test_poland_exempts_eu_dividends_only(s):
    calc = FlowCalculator(s)
    fr = calc.compute(Flow("DIVIDEND", "FR", "PL", "FR", Decimal("100"), 24), D)
    assert fr.legs[1].detail["participation_exemption"] == "applies"
    ae = calc.compute(Flow("DIVIDEND", "AE", "PL", "FR", Decimal("100"), 24), D)
    assert ae.legs[1].detail["participation_exemption"] == "not applied"
    assert "not in EU" in ae.legs[1].detail["exemption_reasons"]


def test_cfc_outcomes(s):
    profile = ScoringProfile(
        parent="FR", flows=(ProfileFlow("DIVIDEND", "FR"), ProfileFlow("ROYALTY", "FR"))
    )
    cards = {c.jurisdiction: c for c in Scorer(s).rank(profile, ["PL", "HU", "SE", "DK"], D)}
    cfc = {
        j: "cfc_exposure" in {f.code for f in c.factors["substance_burden"].flags}
        for j, c in cards.items()
    }
    assert cfc == {"PL": False, "HU": True, "SE": False, "DK": False}
    assert all(c.complete for c in cards.values())


def test_data_quality_checks_pass(s):
    assert run_checks(s) == []
