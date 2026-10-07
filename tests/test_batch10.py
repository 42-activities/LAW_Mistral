"""Golden expectations for P8 batch 10 (Norway, Canada, Western Balkans, India, China)."""

from datetime import date
from decimal import Decimal

import pytest

from app.modules.engine.withholding import WithholdingEngine
from app.modules.risk.repository import ListRepository
from app.modules.scoring.scorer import Scorer
from app.modules.scoring.types import ProfileFlow, ScoringProfile
from app.modules.seed.quality import run_checks

D = date(2026, 6, 30)
BATCH = ["NO", "CA", "AL", "BA", "ME", "MK", "XK", "IN", "CN"]


@pytest.fixture
def s(seeded_session):
    return seeded_session


@pytest.mark.parametrize(
    ("src", "dst", "cat", "pct", "days", "final"),
    [
        # Norway: 25% dividends, exempt for a genuine EU/EEA company; no UAE treaty; no general
        # interest WHT. France-source dividends to a ≥10% Norwegian parent: residence-only.
        ("NO", "FR", "DIVIDEND", "10", 730, "0.000"),
        ("NO", "AE", "DIVIDEND", "100", 730, "25.000"),
        ("NO", "AE", "INTEREST", None, None, "0.000"),
        ("FR", "NO", "DIVIDEND", "10", 730, "0.000"),
        # Canada: Part XIII 25%; France and UAE 5% at 10% (voting power), interest 10%.
        ("CA", "FR", "DIVIDEND", "10", None, "5.000"),
        ("CA", "FR", "DIVIDEND", "5", None, "15.000"),
        ("CA", "FR", "INTEREST", None, None, "10.000"),
        ("CA", "AE", "ROYALTY", None, None, "10.000"),
        # Albania: 8% dividends; France 5% at 25% only after 365 days (MLI art. 8).
        ("AL", "FR", "DIVIDEND", "25", 400, "5.000"),
        ("AL", "FR", "DIVIDEND", "25", 100, "8.000"),
        ("AL", "FR", "ROYALTY", None, None, "5.000"),
        ("AL", "AE", "INTEREST", None, None, "0.000"),
        # Bosnia (FBiH): France 1974 convention 5% at 25%, interest residence-only; UAE treaty
        # not applied (no entry-into-force date).
        ("BA", "FR", "DIVIDEND", "25", None, "5.000"),
        ("BA", "FR", "INTEREST", None, None, "0.000"),
        ("BA", "AE", "ROYALTY", None, None, "10.000"),
        # Montenegro: 15% WHT; France royalties residence-only; UAE 5% dividends at 5%.
        ("ME", "FR", "ROYALTY", None, None, "0.000"),
        ("ME", "FR", "DIVIDEND", "10", None, "15.000"),
        ("ME", "AE", "DIVIDEND", "5", None, "5.000"),
        ("ME", "AE", "ROYALTY", None, None, "10.000"),
        # North Macedonia: 10% WHT; France dividends residence-only at 10%; UAE 5% flat.
        ("MK", "FR", "DIVIDEND", "10", None, "0.000"),
        ("MK", "FR", "DIVIDEND", "5", None, "10.000"),
        ("MK", "AE", "INTEREST", None, None, "5.000"),
        # Kosovo: no dividend WHT; UAE interest 5%; royalties: higher 10% stored.
        ("XK", "FR", "DIVIDEND", "100", None, "0.000"),
        ("XK", "FR", "ROYALTY", None, None, "0.000"),
        ("XK", "AE", "INTEREST", None, None, "5.000"),
        ("XK", "AE", "ROYALTY", None, None, "10.000"),
        # India: 21.84% effective domestic; France treaty-text caps (MFN not applied).
        ("IN", "FR", "DIVIDEND", "100", None, "15.000"),
        ("IN", "FR", "INTEREST", "10", None, "10.000"),
        ("IN", "FR", "INTEREST", None, None, "15.000"),
        ("IN", "FR", "ROYALTY", None, None, "20.000"),
        ("IN", "AE", "DIVIDEND", "10", None, "5.000"),
        ("IN", "AE", "INTEREST", None, None, "12.500"),
        # China: 10% WHT; France 5% at 25% with 365 days; UAE treaty not applied.
        ("CN", "FR", "DIVIDEND", "25", 400, "5.000"),
        ("CN", "FR", "DIVIDEND", "25", 100, "10.000"),
        ("CN", "FR", "ROYALTY", None, None, "10.000"),
        ("CN", "AE", "DIVIDEND", "100", None, "10.000"),
    ],
)
def test_corridors(s, src, dst, cat, pct, days, final):
    r = WithholdingEngine(s).compute(
        src, dst, cat, D, None if pct is None else Decimal(pct), days
    )
    assert str(r.final_rate) == final, r.flags
    assert r.citations


@pytest.mark.parametrize("src", ["BA", "CN"])
def test_uae_treaty_not_applied_without_entry_into_force(s, src):
    r = WithholdingEngine(s).compute(src, "AE", "DIVIDEND", D, Decimal("100"), 730)
    assert "treaty_in_force_unknown" in {f.code for f in r.flags}


def test_norway_eea_dividend_exemption_flagged(s):
    r = WithholdingEngine(s).compute("NO", "FR", "DIVIDEND", D, Decimal("10"), 730)
    assert str(r.domestic_rate) == "25.000"
    assert "directive_exemption" in {f.code for f in r.flags}


def test_india_france_mfn_flagged_not_applied(s):
    r = WithholdingEngine(s).compute("IN", "FR", "DIVIDEND", D, Decimal("100"), None)
    codes = {f.code for f in r.flags}
    assert "mfn_clause" in codes and "mli_ppt" in codes
    assert str(r.final_rate) == "15.000"


def test_lists(s):
    repo = ListRepository(s)
    assert repo.is_listed("BA", "FATF_GREY", D) is not None
    assert repo.is_listed("BA", "FATF_GREY", date(2026, 6, 18)) is None
    assert repo.is_listed("ME", "EU_TAX_ANNEX_II", D) is not None
    for code in ("NO", "CA", "AL", "MK", "XK", "IN", "CN"):
        assert repo.is_listed(code, "FATF_GREY", D) is None


def test_rankings_complete(s):
    profile = ScoringProfile(
        parent="FR", flows=(ProfileFlow("DIVIDEND", "FR"), ProfileFlow("ROYALTY", "FR"))
    )
    cards = Scorer(s).rank(profile, BATCH, D)
    assert all(c.complete for c in cards), [
        (c.jurisdiction, {k: [f.code for f in v.flags] for k, v in c.factors.items()})
        for c in cards if not c.complete
    ]
    assert not any(c.guardrail_flags for c in cards)
    comp = {c.jurisdiction: c.factors["compliance"].score for c in cards}
    assert comp["BA"] < comp["ME"] < comp["NO"]  # FATF grey < EU Annex II < unlisted


def test_data_quality_checks_pass(s):
    assert run_checks(s) == []
