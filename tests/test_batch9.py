"""Golden expectations for P8 batch 9 (Middle East completion, North Africa, Kenya, Australia)."""

from datetime import date
from decimal import Decimal

import pytest

from app.modules.engine.withholding import WithholdingEngine
from app.modules.scoring.scorer import Scorer
from app.modules.scoring.types import ProfileFlow, ScoringProfile
from app.modules.seed.quality import run_checks

D = date(2026, 6, 30)


@pytest.fixture
def s(seeded_session):
    return seeded_session


@pytest.mark.parametrize(
    ("src", "dst", "cat", "pct", "days", "final"),
    [
        # Iran: no dividend WHT; France treaty caps royalties at 10% (domestic 7.5% lower).
        ("IR", "FR", "DIVIDEND", "100", 730, "0.000"),
        ("IR", "FR", "INTEREST", None, None, "15.000"),
        ("IR", "FR", "ROYALTY", None, None, "7.500"),
        # Australia: unfranked 30%; France 5% at 10% for 365 days; no UAE treaty.
        ("AU", "FR", "DIVIDEND", "10", 400, "5.000"),
        ("AU", "AE", "ROYALTY", None, None, "30.000"),
        ("AU", "FR", "ROYALTY", None, None, "5.000"),
        # Algeria: France interest 12% from Algeria; UAE treaty not applied (no EIF date).
        ("DZ", "FR", "INTEREST", None, None, "10.000"),
        ("DZ", "FR", "DIVIDEND", "10", None, "5.000"),
        ("DZ", "AE", "ROYALTY", None, None, "30.000"),
        # Libya: France 5% at 10%.
        ("LY", "FR", "DIVIDEND", "10", None, "0.000"),
        # Morocco: 11.25% dividends in 2026; UAE 5% at 10%.
        ("MA", "AE", "DIVIDEND", "10", None, "5.000"),
        ("MA", "FR", "ROYALTY", None, None, "10.000"),
        # Tunisia: UAE dividends exempt; France no dividend cap (domestic 10%).
        ("TN", "AE", "DIVIDEND", "100", None, "0.000"),
        ("TN", "FR", "DIVIDEND", "100", None, "10.000"),
        ("TN", "AE", "ROYALTY", None, None, "7.500"),
        # Kenya: France 8% at 25% (MFN); UAE 5%.
        ("KE", "FR", "DIVIDEND", "25", None, "8.000"),
        ("KE", "AE", "DIVIDEND", "5", None, "5.000"),
        # Syria: France 0% at 10%; UAE royalties 18%. Yemen: UAE dividends exempt.
        ("SY", "FR", "DIVIDEND", "10", None, "0.000"),
        ("SY", "AE", "ROYALTY", None, None, "10.000"),  # domestic 10% below the 18% cap
        ("YE", "AE", "DIVIDEND", "100", None, "0.000"),
        ("YE", "AE", "ROYALTY", None, None, "10.000"),
        ("PS", "FR", "ROYALTY", None, None, "10.000"),
        # Sudan: UAE royalties capped at 5%.
        ("SD", "AE", "DIVIDEND", None, None, "0.000"),
    ],
)
def test_corridors(s, src, dst, cat, pct, days, final):
    r = WithholdingEngine(s).compute(
        src, dst, cat, D, None if pct is None else Decimal(pct), days
    )
    assert str(r.final_rate) == final, r.flags
    assert r.citations


def test_algeria_uae_treaty_not_applied_without_entry_into_force(s):
    r = WithholdingEngine(s).compute("DZ", "AE", "DIVIDEND", D, Decimal("100"), 730)
    assert "treaty_in_force_unknown" in {f.code for f in r.flags}


def test_rankings_complete(s):
    profile = ScoringProfile(
        parent="FR", flows=(ProfileFlow("DIVIDEND", "FR"), ProfileFlow("ROYALTY", "FR"))
    )
    cards = Scorer(s).rank(profile, ["AU", "DZ", "MA", "TN", "KE", "IR", "SY", "YE", "PS"], D)
    assert all(c.complete for c in cards), [
        (c.jurisdiction, {k: [f.code for f in v.flags] for k, v in c.factors.items()})
        for c in cards if not c.complete
    ]
    iran = next(c for c in cards if c.jurisdiction == "IR")
    assert {f.code for f in iran.guardrail_flags} == {"guardrail_fatf_black"}
    comp = {c.jurisdiction: c.factors["compliance"].score for c in cards}
    assert comp["SY"] < comp["PS"] and comp["YE"] < comp["PS"]  # FATF grey + EU AML


def test_data_quality_checks_pass(s):
    assert run_checks(s) == []
