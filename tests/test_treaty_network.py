"""Golden corridors from treaty rates extracted from official texts (hub treaty network)."""

from datetime import date
from decimal import Decimal

import pytest

from app.modules.engine.withholding import WithholdingEngine
from app.modules.seed.quality import run_checks

D = date(2026, 6, 30)


@pytest.fixture
def s(seeded_session):
    return seeded_session


@pytest.mark.parametrize(
    ("src", "dst", "cat", "pct", "days", "final"),
    [
        # UK hub
        ("CZ", "GB", "ROYALTY", None, None, "10.000"),
        ("IT", "GB", "ROYALTY", None, None, "8.000"),
        ("TR", "GB", "DIVIDEND", "30", 400, "15.000"),
        ("TR", "GB", "DIVIDEND", "10", 400, "15.000"),  # domestic 15% below the 20% cap
        ("SA", "GB", "ROYALTY", None, None, "8.000"),
        ("IL", "GB", "DIVIDEND", "10", 400, "5.000"),
        ("IL", "GB", "DIVIDEND", "10", 100, "15.000"),  # 365-day holding not met
        ("US", "GB", "DIVIDEND", "100", 730, "5.000"),  # 0% tier needs LOB: curated out
        ("JO", "GB", "INTEREST", None, None, "10.000"),
        # Netherlands hub
        # (10%+ intra-EU holdings get 0% under the EU directives before any treaty applies)
        ("DE", "NL", "DIVIDEND", "5", 400, "15.000"),
        ("CH", "NL", "DIVIDEND", "10", 400, "0.000"),
        ("HK", "NL", "DIVIDEND", "100", 730, "0.000"),  # HK has no dividend WHT anyway
        # Singapore / Cyprus / Hong Kong hubs
        ("IL", "SG", "INTEREST", None, None, "7.000"),
        ("IT", "SG", "ROYALTY", None, None, "15.000"),
        ("US", "CY", "DIVIDEND", "10", 400, "5.000"),
        ("PT", "HK", "ROYALTY", None, None, "5.000"),
        # Luxembourg / Malta / Switzerland hubs
        ("AT", "LU", "ROYALTY", None, None, "10.000"),  # curated: 10% treaty rate (no directive)
        ("US", "LU", "DIVIDEND", "10", 400, "5.000"),
        ("DE", "LU", "DIVIDEND", "5", 400, "15.000"),
        ("PL", "MT", "INTEREST", None, None, "4.000"),  # 2020 protocol, from 2023
        ("IT", "MT", "ROYALTY", None, None, "10.000"),
        ("DE", "CH", "DIVIDEND", "10", 400, "0.000"),  # 2023 protocol, from 2026
        ("TR", "CH", "ROYALTY", None, None, "10.000"),
        # Non-hub network
        ("US", "DE", "DIVIDEND", "10", 400, "5.000"),
        ("US", "PL", "DIVIDEND", "5", 400, "15.000"),
        ("SA", "ES", "ROYALTY", None, None, "8.000"),
        ("EG", "SA", "INTEREST", None, None, "10.000"),
        ("IL", "US", "INTEREST", None, None, "17.500"),
        ("JO", "SA", "ROYALTY", None, None, "7.000"),
        ("RO", "KW", "DIVIDEND", "100", 730, "1.000"),
        ("IT", "SA", "DIVIDEND", "30", 400, "5.000"),
        ("DK", "KW", "DIVIDEND", "100", 400, "0.000"),
        ("AT", "IT", "ROYALTY", None, None, "10.000"),  # curated Austrian >50% pattern
        # Gap pairs
        ("DE", "CY", "DIVIDEND", "5", 400, "15.000"),  # below the 10% directive threshold
        ("DE", "BE", "INTEREST", None, None, "0.000"),  # German domestic: no interest WHT
        ("ES", "SE", "ROYALTY", None, None, "10.000"),
        ("DE", "IE", "DIVIDEND", "5", 400, "15.000"),
        # Batch-8 network
        ("KZ", "NL", "DIVIDEND", "10", 400, "5.000"),  # MLI 365-day holding met
        ("KZ", "NL", "DIVIDEND", "10", 100, "15.000"),
        ("UZ", "CH", "ROYALTY", None, None, "5.000"),
        ("RS", "AT", "DIVIDEND", "30", None, "5.000"),
        ("MD", "ES", "DIVIDEND", "60", None, "0.000"),
        ("MD", "GB", "DIVIDEND", "60", None, "5.000"),  # 0% needs GBP 1m — curated out
        ("AZ", "GB", "ROYALTY", None, None, "10.000"),  # higher of the 5%/10% tiers
        ("UZ", "GB", "DIVIDEND", "5", None, "10.000"),  # REIT-only 15% curated out
        # Investment-conditioned dividend tiers are curated out; "or" conditions are kept
        ("AT", "AZ", "DIVIDEND", "100", 730, "15.000"),  # 5% tier also needs USD 250k
        ("AM", "SG", "DIVIDEND", "30", None, "0.000"),  # 25% OR USD 300k
        # Batch-9 network
        ("AU", "NL", "DIVIDEND", "10", 400, "15.000"),  # franking-conditioned tiers in notes
        ("MA", "ES", "DIVIDEND", "30", None, "10.000"),
        ("TN", "BE", "ROYALTY", None, None, "11.000"),
        ("IR", "AT", "DIVIDEND", "30", None, "0.000"),  # Iran domestic 0%
        ("AT", "IR", "DIVIDEND", "30", None, "5.000"),
        ("SY", "DE", "ROYALTY", None, None, "10.000"),  # domestic 10% below the 12% cap
        ("KE", "QA", "DIVIDEND", "10", None, "5.000"),
        ("DZ", "AT", "DIVIDEND", "10", None, "5.000"),
        # Ireland hub
        ("CH", "IE", "DIVIDEND", "10", 400, "0.000"),
        ("CH", "IE", "DIVIDEND", "5", 400, "15.000"),
        ("TR", "IE", "ROYALTY", None, None, "10.000"),
        ("TR", "IE", "DIVIDEND", "30", 400, "10.000"),  # conditional 5% tier not applied
        ("SA", "IE", "DIVIDEND", "100", 730, "0.000"),
        ("EG", "IE", "INTEREST", None, None, "10.000"),
    ],
)
def test_corridors(s, src, dst, cat, pct, days, final):
    r = WithholdingEngine(s).compute(src, dst, cat, D, None if pct is None else Decimal(pct), days)
    assert r.complete, r.flags
    assert "no_treaty" not in {f.code for f in r.flags}
    assert str(r.final_rate) == final


def test_data_quality_checks_pass(s):
    assert run_checks(s) == []


def test_maghreb_union_treaty_has_no_cap(s):
    r = WithholdingEngine(s).compute("MA", "DZ", "DIVIDEND", D, Decimal("100"), 730)
    codes = {f.code for f in r.flags}
    assert "no_treaty" not in codes and "treaty_rate_not_recorded" in codes
    assert str(r.final_rate) == "11.250"  # Moroccan domestic rate
