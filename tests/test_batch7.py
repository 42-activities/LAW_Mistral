"""Golden expectations for P8 batch 7 (BG, RO, GR) and the Middle East waves 1-2."""

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


@pytest.mark.parametrize(
    ("src", "dst", "cat", "pct", "days", "final"),
    [
        ("EG", "FR", "DIVIDEND", "100", 730, "0.000"),
        ("EG", "FR", "INTEREST", None, None, "15.000"),
        # Egypt–UAE: entry-into-force date unverified, so the treaty is not applied.
        ("EG", "AE", "DIVIDEND", "10", 400, "10.000"),
        ("JO", "FR", "ROYALTY", None, None, "10.000"),  # domestic 10% below the 15% cap
        ("FR", "JO", "DIVIDEND", "10", 400, "5.000"),
        ("FR", "JO", "DIVIDEND", "10", 100, "15.000"),
        ("JO", "AE", "INTEREST", None, None, "7.000"),
        ("LB", "FR", "DIVIDEND", None, None, "0.000"),
        ("LB", "FR", "ROYALTY", None, None, "8.500"),  # no treaty cap on royalties
        ("LB", "AE", "ROYALTY", None, None, "5.000"),
        ("IQ", "FR", "INTEREST", None, None, "15.000"),
        ("TR", "FR", "DIVIDEND", "10", 400, "15.000"),
        ("TR", "FR", "ROYALTY", None, None, "10.000"),
        ("TR", "AE", "DIVIDEND", "30", None, "10.000"),
        ("TR", "AE", "DIVIDEND", "5", None, "12.000"),
    ],
)
def test_wave2_corridors(s, src, dst, cat, pct, days, final):
    r = WithholdingEngine(s).compute(
        src, dst, cat, D, None if pct is None else Decimal(pct), days
    )
    assert r.complete, r.flags
    assert str(r.final_rate) == final


def test_egypt_drops_dividend_add_back_from_29_july_2026(s):
    calc = FlowCalculator(s)
    flow = Flow("DIVIDEND", "FR", "EG", "FR", Decimal("100"), 24)
    before = calc.compute(flow, D).legs[1]
    after = calc.compute(flow, date(2026, 9, 1)).legs[1]
    assert before.detail["participation_exemption"] == "applies"
    assert before.tax_per_100 > after.tax_per_100 == Decimal("0")


def test_wave2_rankings_complete(s):
    profile = ScoringProfile(
        parent="FR", flows=(ProfileFlow("DIVIDEND", "FR"), ProfileFlow("ROYALTY", "FR"))
    )
    cards = Scorer(s).rank(profile, ["EG", "JO", "TR", "LB", "IQ"], D)
    assert all(c.complete for c in cards), [(c.jurisdiction, c.flags) for c in cards]
    comp = {c.jurisdiction: c.factors["compliance"].score for c in cards}
    assert comp["LB"] < comp["IQ"] < comp["EG"]  # grey + EU AML < grey < Global Forum PC


def test_listed_jurisdictions_keep_guardrails(s):
    profile = ScoringProfile(parent="FR", flows=(ProfileFlow("DIVIDEND", "FR"),))
    cards = Scorer(s).rank(profile, ["IR", "SY", "YE", "AE"], D)
    by = {c.jurisdiction: c for c in cards}
    # Iran, Syria and Yemen now have tax data (batch 9) but keep their list flags; Iran's
    # FATF call-for-action guardrail caps its score.
    assert {f.code for f in by["IR"].guardrail_flags} == {"guardrail_fatf_black"}
    assert by["AE"].rank < by["IR"].rank


def test_turkiye_participation_needs_15pct_payer_tax(s):
    calc = FlowCalculator(s)
    fr = calc.compute(Flow("DIVIDEND", "FR", "TR", "FR", Decimal("100"), 24), D)
    assert fr.legs[1].detail["participation_exemption"] == "applies"
    ae = calc.compute(Flow("DIVIDEND", "AE", "TR", "FR", Decimal("100"), 24), D)
    assert ae.legs[1].detail["participation_exemption"] == "not applied"


def test_no_treaty_flag_is_a_data_gap_and_notes_zero_domestic_rate(s):
    r = WithholdingEngine(s).compute("BH", "US", "DIVIDEND", D, Decimal("100"), 730)
    msg = next(f.message for f in r.flags if f.code == "no_treaty")
    assert "recorded in the database" in msg and "not a finding" in msg
    assert "domestic rate is already 0%" in msg


@pytest.mark.parametrize(
    ("src", "dst", "cat", "final", "ppt"),
    [
        ("QA", "CY", "DIVIDEND", "0.000", True),
        ("QA", "CY", "ROYALTY", "5.000", True),
        ("QA", "AT", "DIVIDEND", "0.000", False),
        ("AT", "QA", "ROYALTY", "5.000", False),  # Austria 20% domestic, treaty cap 5%
        ("CY", "QA", "INTEREST", "0.000", True),
    ],
)
def test_qatar_cyprus_and_austria_treaties(s, src, dst, cat, final, ppt):
    r = WithholdingEngine(s).compute(src, dst, cat, D, Decimal("100"), 730)
    assert r.complete, r.flags
    assert str(r.final_rate) == final
    assert "no_treaty" not in codes(r)
    assert ("mli_ppt" in codes(r)) is ppt
