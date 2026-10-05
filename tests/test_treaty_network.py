"""Golden corridors from treaty rates extracted from official texts (hub treaty network)."""

from datetime import date
from decimal import Decimal

import pytest

from app.modules.engine.withholding import WithholdingEngine
from app.modules.seed.france_uae import seed
from app.modules.seed.quality import run_checks

D = date(2026, 6, 30)


@pytest.fixture
def s(db_session):
    seed(db_session)
    db_session.flush()
    return db_session


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
