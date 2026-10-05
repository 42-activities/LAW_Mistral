"""Golden expectations for P8 batch 7 (BG, RO, GR) and the Middle East (SA, BH, OM, KW, IL)."""

from datetime import date
from decimal import Decimal

import pytest

from app.modules.engine.flow import Flow, FlowCalculator
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
        # Bulgaria: EU dividends exempt with no holding test; 2% interest to the UAE.
        ("BG", "FR", "DIVIDEND", None, None, "5.000", "0.000", "0.000", "directive_exemption"),
        ("BG", "AE", "INTEREST", None, None, "10.000", "10.000", "2.000", None),
        ("BG", "FR", "INTEREST", None, None, "10.000", "10.000", "0.000", None),
        ("BG", "FR", "ROYALTY", "25", 800, "10.000", "0.000", "0.000", "directive_exemption"),
        ("FR", "BG", "DIVIDEND", "10", 400, "25.000", "25.000", "15.000",
         "treaty_threshold_not_met"),
        # Romania: 16% from 2026; flat 10% treaty with France; 3% with the UAE.
        ("RO", "FR", "DIVIDEND", "10", 400, "16.000", "0.000", "0.000", "directive_exemption"),
        ("RO", "FR", "ROYALTY", None, None, "16.000", "16.000", "10.000", None),
        ("RO", "AE", "DIVIDEND", "100", 730, "16.000", "16.000", "3.000", None),
        # Greece: 2022 treaty, 0% dividends at 5% for 24 months.
        ("GR", "FR", "DIVIDEND", "10", 400, "5.000", "5.000", "5.000",
         "exemption_conditions_not_met"),
        ("GR", "FR", "DIVIDEND", "10", 800, "5.000", "0.000", "0.000", "directive_exemption"),
        ("FR", "GR", "DIVIDEND", "5", 800, "25.000", "25.000", "0.000", None),
        ("GR", "AE", "ROYALTY", None, None, "20.000", "20.000", "10.000", None),
        # Saudi Arabia: France treaty gives residence-only taxation.
        ("SA", "FR", "DIVIDEND", "100", 730, "5.000", "5.000", "0.000", None),
        ("SA", "FR", "ROYALTY", None, None, "15.000", "15.000", "0.000", None),
        ("SA", "AE", "ROYALTY", None, None, "15.000", "15.000", "10.000", None),
        ("SA", "AE", "INTEREST", None, None, "5.000", "5.000", "0.000", None),
        # Bahrain: no withholding.
        ("BH", "FR", "DIVIDEND", None, None, "0.000", "0.000", "0.000", None),
        # Oman: dividend WHT suspended; France treaty caps royalties at 7%.
        ("OM", "FR", "DIVIDEND", None, None, "0.000", "0.000", "0.000", None),
        ("OM", "FR", "ROYALTY", None, None, "10.000", "10.000", "7.000", None),
        ("OM", "AE", "ROYALTY", None, None, "10.000", "10.000", "10.000", "no_treaty"),
        # Kuwait: no withholding; France treaty without PPT (Kuwait has not ratified the MLI).
        ("KW", "FR", "ROYALTY", None, None, "0.000", "0.000", "0.000", None),
        ("FR", "KW", "DIVIDEND", "100", 730, "25.000", "25.000", "0.000", None),
        # Israel: 30% to substantial shareholders; France caps at 5% from 10%.
        ("IL", "FR", "DIVIDEND", "10", None, "30.000", "30.000", "5.000", None),
        ("IL", "FR", "ROYALTY", None, None, "23.000", "23.000", "10.000", None),
        ("IL", "AE", "DIVIDEND", "100", 730, "30.000", "30.000", "30.000", "no_treaty"),
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


def test_bulgaria_exempts_eu_dividends_only(s):
    calc = FlowCalculator(s)
    fr = calc.compute(Flow("DIVIDEND", "FR", "BG", "FR", Decimal("100"), 24), D)
    assert fr.legs[1].detail["participation_exemption"] == "applies"
    ae = calc.compute(Flow("DIVIDEND", "AE", "BG", "FR", Decimal("100"), 24), D)
    assert ae.legs[1].detail["participation_exemption"] == "not applied"


def test_israel_taxes_foreign_dividends(s):
    r = FlowCalculator(s).compute(Flow("DIVIDEND", "FR", "IL", "FR", Decimal("100"), 24), D)
    assert r.legs[1].detail["participation_exemption"] == "not applied"


def test_rankings_complete(s):
    profile = ScoringProfile(
        parent="FR", flows=(ProfileFlow("DIVIDEND", "FR"), ProfileFlow("ROYALTY", "FR"))
    )
    cards = Scorer(s).rank(profile, ["BG", "RO", "GR", "SA", "BH", "OM", "KW", "IL"], D)
    assert all(c.complete for c in cards), [(c.jurisdiction, c.flags) for c in cards]


def test_kuwait_fatf_grey_list_penalised(s):
    profile = ScoringProfile(parent="FR", flows=(ProfileFlow("DIVIDEND", "FR"),))
    cards = {c.jurisdiction: c for c in Scorer(s).rank(profile, ["KW", "BH"], D)}
    assert cards["KW"].factors["compliance"].score < cards["BH"].factors["compliance"].score


def test_data_quality_checks_pass(s):
    assert run_checks(s) == []
