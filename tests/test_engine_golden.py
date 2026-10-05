"""France–UAE golden expectations (docs/superpowers/plans/2026-10-04-p3-engines.md)."""

from datetime import date
from decimal import Decimal

import pytest

from app.modules.engine.flow import Flow, FlowCalculator
from app.modules.engine.withholding import WithholdingEngine

D = date(2024, 6, 30)
POST_ETNC = date(2025, 6, 1)


@pytest.fixture
def seeded(seeded_session):
    return seeded_session


def codes(result):
    return {f.code for f in result.flags}


def test_fr_to_ae_dividend_refund(seeded):
    r = WithholdingEngine(seeded).compute("FR", "AE", "DIVIDEND", D, Decimal("100"), 730)
    assert r.domestic_rate == Decimal("25")
    assert r.treaty_cap == Decimal("0")
    assert r.withheld_at_payment == Decimal("25")
    assert r.final_rate == Decimal("0")
    assert r.relief_mechanism == "refund"
    assert "refund_cash_flow" in codes(r)
    assert r.treaty_name.endswith("Article 8")
    assert len(r.citations) >= 3  # domestic rule, treaty, treaty article


def test_fr_to_ae_royalty_relief_unknown(seeded):
    r = WithholdingEngine(seeded).compute("FR", "AE", "ROYALTY", D)
    assert (r.domestic_rate, r.treaty_cap) == (Decimal("25"), Decimal("0"))
    assert r.withheld_at_payment == Decimal("25")
    assert r.final_rate == Decimal("0")
    assert "relief_mechanism_unknown" in codes(r)
    assert r.treaty_name.endswith("Article 10")


def test_fr_to_ae_interest(seeded):
    r = WithholdingEngine(seeded).compute("FR", "AE", "INTEREST", D)
    assert r.final_rate == Decimal("0")
    assert r.withheld_at_payment == Decimal("0")


def test_ae_to_fr_dividend(seeded):
    r = WithholdingEngine(seeded).compute("AE", "FR", "DIVIDEND", D)
    assert r.domestic_rate == Decimal("0")
    assert r.final_rate == Decimal("0")


def test_fr_to_etnc_full_measures_gets_consequence_rate(seeded):
    r = WithholdingEngine(seeded).compute("FR", "VU", "DIVIDEND", POST_ETNC)
    assert r.domestic_rate == Decimal("25")
    assert r.effective_domestic_rate == Decimal("75")
    assert r.final_rate == Decimal("75")
    assert "consequence_applied" in codes(r)
    assert r.consequences[0].list_code == "FR_ETNC"


def test_fr_to_etnc_certain_measures_no_wht_consequence(seeded):
    r = WithholdingEngine(seeded).compute("FR", "PA", "DIVIDEND", POST_ETNC)
    assert r.final_rate == Decimal("25")
    assert r.consequences == ()


def test_etnc_consequence_not_applied_before_listing(seeded):
    r = WithholdingEngine(seeded).compute("FR", "VU", "DIVIDEND", D)
    assert r.final_rate == Decimal("25")


def test_flow_dividend_fully_exempt(seeded):
    f = Flow("DIVIDEND", "FR", "AE", "FR", Decimal("100"), 24)
    r = FlowCalculator(seeded).compute(f, D)
    assert r.total_leakage_pct == Decimal("0.000")
    cit_leg = r.legs[1]
    assert cit_leg.detail["participation_exemption"] == "applies"
    assert r.complete


def test_flow_dividend_small_holding_taxed_in_uae(seeded):
    f = Flow("DIVIDEND", "FR", "AE", "FR", Decimal("3"), 24)
    r = FlowCalculator(seeded).compute(f, D)
    assert r.legs[1].rate == Decimal("9.000")
    assert r.total_leakage_pct == Decimal("9.000")
    assert "cit_top_bracket_assumed" in codes(r)


def test_flow_royalty_taxed_in_uae(seeded):
    f = Flow("ROYALTY", "FR", "AE", "FR")
    r = FlowCalculator(seeded).compute(f, D)
    assert r.total_leakage_pct == Decimal("9.000")


def test_flow_royalty_average_cit_with_amount(seeded):
    f = Flow("ROYALTY", "FR", "AE", "FR", amount=Decimal("1000000"))
    r = FlowCalculator(seeded).compute(f, D)
    # (1,000,000 - 375,000) × 9% / 1,000,000 = 5.625%
    assert r.total_leakage_pct == Decimal("5.625")


def test_flow_via_france_applies_quote_part(seeded):
    # AE subsidiary pays FR holding: 0% UAE WHT, French 95% exemption → 5% × 25% = 1.25%
    f = Flow("DIVIDEND", "AE", "FR", "FR", Decimal("100"), 24)
    r = FlowCalculator(seeded).compute(f, D)
    assert r.total_leakage_pct == Decimal("1.250")


def test_flow_incomplete_when_data_missing(seeded):
    f = Flow("DIVIDEND", "FR", "VU", "FR", Decimal("100"), 24)
    r = FlowCalculator(seeded).compute(f, POST_ETNC)
    assert r.total_leakage_pct is None  # no Vanuatu CIT rule recorded
    assert "missing_cit_rule" in codes(r)


def test_flow_is_reproducible(seeded):
    f = Flow("DIVIDEND", "FR", "AE", "FR", Decimal("100"), 24)
    calc = FlowCalculator(seeded)
    assert calc.compute(f, D) == calc.compute(f, D)
