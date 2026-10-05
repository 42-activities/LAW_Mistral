"""Golden expectations for P8 batch 8 (remaining EU members, Serbia, CIS)."""

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


def codes(r):
    return {f.code for f in r.flags}


@pytest.mark.parametrize(
    ("src", "dst", "cat", "pct", "days", "final"),
    [
        # Slovakia: dividends outside the tax base; France–Czechoslovakia treaty.
        ("SK", "AE", "DIVIDEND", None, None, "0.000"),
        ("SK", "FR", "ROYALTY", None, None, "5.000"),
        ("SK", "AE", "INTEREST", None, None, "10.000"),
        ("SK", "FR", "ROYALTY", "25", 800, "0.000"),  # Interest and Royalties Directive
        # Kazakhstan: 15% domestic; France 5% at 10% for 365 days.
        ("KZ", "FR", "DIVIDEND", "10", 400, "5.000"),
        ("KZ", "FR", "DIVIDEND", "10", 100, "15.000"),
        ("KZ", "AE", "DIVIDEND", "5", None, "15.000"),  # no general UAE cap
        ("KZ", "AE", "ROYALTY", None, None, "10.000"),
        # Uzbekistan: France royalties exclusive; UAE dividends 5% at 25%.
        ("UZ", "FR", "ROYALTY", None, None, "0.000"),
        ("UZ", "AE", "DIVIDEND", "30", None, "5.000"),
        ("UZ", "AE", "DIVIDEND", "10", None, "10.000"),  # domestic 10% below the 15% cap
        # Latvia: no WHT except to EU Annex I jurisdictions.
        ("LV", "AE", "INTEREST", None, None, "0.000"),
        ("LV", "PA", "ROYALTY", None, None, "20.000"),
        # Estonia: no dividend/interest WHT; royalties 10% (0% to France under MFN).
        ("EE", "AE", "ROYALTY", None, None, "0.000"),
        ("EE", "FR", "ROYALTY", None, None, "0.000"),
        ("EE", "US", "ROYALTY", None, None, "10.000"),
        # Finland: 20% domestic; 1970 France treaty until 2026.
        ("FI", "FR", "DIVIDEND", "5", None, "0.000"),
        ("FI", "AE", "ROYALTY", None, None, "0.000"),
        ("FI", "US", "INTEREST", None, None, "0.000"),
        # Moldova: 2022 France convention from 2025; UAE 5/6/6.
        ("MD", "FR", "DIVIDEND", "10", 400, "5.000"),
        ("MD", "FR", "ROYALTY", None, None, "6.000"),
        ("MD", "AE", "INTEREST", None, None, "6.000"),
        # Armenia: 5% domestic dividends; UAE 3%, interest exempt.
        ("AM", "AE", "DIVIDEND", "100", 730, "3.000"),
        ("AM", "AE", "INTEREST", None, None, "0.000"),
        ("AM", "FR", "ROYALTY", None, None, "10.000"),
        # Azerbaijan: 5% dividends; UAE interest 7%.
        ("AZ", "AE", "INTEREST", None, None, "7.000"),
        ("AZ", "FR", "ROYALTY", None, None, "10.000"),
        ("AZ", "AE", "DIVIDEND", "100", 730, "5.000"),  # domestic 5% below the 10% cap
        # Serbia: 20% domestic; France 5% at 25% for 365 days.
        ("RS", "FR", "DIVIDEND", "30", 400, "5.000"),
        ("RS", "FR", "ROYALTY", None, None, "0.000"),
        ("RS", "AE", "DIVIDEND", "5", None, "5.000"),
        # Croatia: 0% to France at 10%; 25% to EU-listed non-treaty states.
        ("HR", "FR", "DIVIDEND", "10", None, "0.000"),
        ("HR", "AE", "ROYALTY", None, None, "5.000"),
        ("HR", "PA", "ROYALTY", None, None, "25.000"),
        # Slovenia: 15% domestic; France 0% at 20%, else 5%.
        ("SI", "FR", "ROYALTY", "25", None, "0.000"),
        ("SI", "FR", "ROYALTY", "10", None, "5.000"),
        ("SI", "AE", "DIVIDEND", "100", 730, "5.000"),
        # Lithuania: 17% dividends, exempt at 10% for 12 months to EU parents.
        ("LT", "FR", "DIVIDEND", "10", 400, "0.000"),
        ("LT", "AE", "DIVIDEND", "10", 400, "0.000"),
        ("LT", "AE", "DIVIDEND", "5", 400, "5.000"),
    ],
)
def test_corridors(s, src, dst, cat, pct, days, final):
    r = WithholdingEngine(s).compute(
        src, dst, cat, D, None if pct is None else Decimal(pct), days
    )
    assert r.complete, r.flags
    assert str(r.final_rate) == final, r.flags
    assert r.citations


def test_rankings_complete(s):
    profile = ScoringProfile(
        parent="FR", flows=(ProfileFlow("DIVIDEND", "FR"), ProfileFlow("ROYALTY", "FR"))
    )
    batch = ["SK", "KZ", "UZ", "LV", "LT", "EE", "FI", "MD", "AM", "AZ", "RS", "HR", "SI"]
    cards = Scorer(s).rank(profile, batch, D)
    assert all(c.complete for c in cards), [(c.jurisdiction, c.flags) for c in cards]


def test_data_quality_checks_pass(s):
    assert run_checks(s) == []


def test_france_finland_switches_to_2023_convention_in_2027(s):
    engine = WithholdingEngine(s)
    old = engine.compute("FI", "FR", "INTEREST", D, None, None)
    new = engine.compute("FI", "FR", "DIVIDEND", date(2027, 6, 30), Decimal("5"), 400)
    portfolio = engine.compute("FI", "FR", "DIVIDEND", date(2027, 6, 30), Decimal("1"), 400)
    assert str(old.final_rate) == "0.000"  # domestic interest exemption
    assert (str(new.final_rate), str(portfolio.final_rate)) == ("0.000", "15.000")
