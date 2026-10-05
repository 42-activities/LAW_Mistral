"""Golden expectations for P8 batch 1 (LU, NL, CY + France's directive exemptions)."""

from datetime import date
from decimal import Decimal

import pytest

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


def wht(s, src, dst, cat, pct=None, days=None, on=D):
    return WithholdingEngine(s).compute(src, dst, cat, on, pct, days)


def codes(r):
    return {f.code for f in r.flags}


@pytest.mark.parametrize(
    ("src", "dst", "cat", "pct", "days", "domestic", "final", "flag"),
    [
        # France → EU: directive exemptions take the domestic rate to 0.
        ("FR", "LU", "DIVIDEND", "100", 730, "25.000", "0.000", "directive_exemption"),
        ("FR", "NL", "DIVIDEND", "30", 730, "25.000", "0.000", "directive_exemption"),
        ("FR", "CY", "DIVIDEND", "10", 730, "25.000", "0.000", "directive_exemption"),
        ("FR", "LU", "ROYALTY", "100", 730, "25.000", "0.000", "directive_exemption"),
        # Below the directive thresholds the treaty tiers decide.
        ("FR", "LU", "DIVIDEND", "7", 400, "25.000", "0.000", "exemption_conditions_not_met"),
        ("FR", "LU", "DIVIDEND", "3", 400, "25.000", "15.000", "treaty_threshold_not_met"),
        ("FR", "LU", "ROYALTY", "10", 730, "25.000", "5.000", "exemption_conditions_not_met"),
        ("FR", "CY", "DIVIDEND", "5", 400, "25.000", "15.000", "treaty_threshold_not_met"),
        ("FR", "NL", "DIVIDEND", "8", 400, "25.000", "15.000", "treaty_threshold_not_met"),
        # Outbound from the EU candidates.
        ("LU", "FR", "DIVIDEND", "100", 730, "15.000", "0.000", "directive_exemption"),
        ("NL", "FR", "DIVIDEND", "100", 730, "15.000", "0.000", "directive_exemption"),
        ("NL", "AE", "DIVIDEND", "100", 730, "15.000", "0.000", "directive_exemption"),
        ("LU", "AE", "DIVIDEND", "100", 730, "15.000", "5.000", None),
        ("CY", "AE", "DIVIDEND", None, None, "0.000", "0.000", None),
        ("CY", "FR", "ROYALTY", "100", 730, "10.000", "0.000", "directive_exemption"),
        ("CY", "FR", "ROYALTY", "10", 730, "10.000", "0.000", "exemption_conditions_not_met"),
    ],
)
def test_corridors(s, src, dst, cat, pct, days, domestic, final, flag):
    r = wht(s, src, dst, cat, None if pct is None else Decimal(pct), days)
    assert r.complete, r.flags
    assert str(r.domestic_rate) == domestic
    if "directive_exemption" in codes(r):
        assert r.effective_domestic_rate == Decimal("0.000")
    assert str(r.final_rate) == final
    if flag:
        assert flag in codes(r)
    assert r.citations


def test_dutch_conditional_wht_on_listed_jurisdictions(s):
    interest = wht(s, "NL", "VU", "INTEREST")
    assert interest.effective_domestic_rate == Decimal("25.800")
    assert interest.consequences[0].list_code == "NL_LOW_TAX"
    dividend = wht(s, "NL", "PA", "DIVIDEND")
    assert dividend.domestic_rate == Decimal("15.000")
    assert dividend.final_rate == Decimal("25.800")
    # the 2026 list does not reach back into 2025
    assert wht(s, "NL", "VU", "INTEREST", on=date(2025, 6, 30)).final_rate == Decimal("0.000")


def test_cyprus_rate_change_is_dated(s):
    tax = TaxEngine(s)
    assert tax.cit("CY", D).rate == Decimal("15")
    assert tax.cit("CY", date(2025, 6, 30)).rate is None  # pre-2026 rate not seeded
    assert tax.cit("LU", D).rate == Decimal("23.87")
    assert tax.cit("NL", D, Decimal("1000000")).rate == Decimal("24.440")


def test_participation_exemptions(s):
    tax = TaxEngine(s)
    lu = tax.participation_exemption("LU", "DIVIDEND", D, Decimal("10"), 12, Decimal("25"))
    assert lu.applies
    assert not tax.participation_exemption(
        "LU", "DIVIDEND", D, Decimal("10"), 12, Decimal("7")
    ).applies  # payer taxed below 8%
    assert tax.participation_exemption("NL", "DIVIDEND", D, Decimal("5"), 0, None).applies
    assert tax.participation_exemption("CY", "DIVIDEND", D, Decimal("1"), 0, None).applies


def test_recommendation_ranks_all_five_completely(s):
    profile = ScoringProfile(
        parent="FR", flows=(ProfileFlow("DIVIDEND", "FR"), ProfileFlow("ROYALTY", "FR"))
    )
    cards = Scorer(s).rank(profile, ["AE", "FR", "LU", "NL", "CY"], D)
    assert all(c.complete for c in cards), [(c.jurisdiction, c.factors) for c in cards]
    by = {c.jurisdiction: c for c in cards}
    # French CFC: a holding taxed at or below 60% of France's 25% (i.e. ≤15%) is caught.
    sub = {j: {f.code for f in by[j].factors["substance_burden"].flags} for j in by}
    assert "cfc_exposure" in sub["AE"]
    assert "cfc_exposure" not in sub["LU"] and "cfc_exposure" not in sub["NL"]
    # 15% is exactly 40% below France's 25%: "inférieur de 40 % ou plus" is inclusive.
    assert "cfc_exposure" in sub["CY"]


def test_data_quality_checks_pass(s):
    assert run_checks(s) == []
