"""Loader for treaty rates extracted from official texts."""

import json
from datetime import date
from decimal import Decimal

import pytest

from app.modules.engine.withholding import WithholdingEngine
from app.modules.seed.france_uae import seed
from app.modules.seed.quality import run_checks
from app.modules.seed.treaty_rates import current_tiers, seed_treaty_rates

D = date(2026, 6, 30)


def _file(tmp_path, name, body):
    folder = tmp_path / "CH"
    folder.mkdir(exist_ok=True)
    (folder / name).write_text(json.dumps(body), encoding="utf-8")


BASE = {
    "a": "CH", "b": "IL", "treaty_name": "Test convention CH–IL", "signed": "2003-07-02",
    "entry_into_force": "2004-12-24", "source_title": "Test text", "source_url": "https://x",
    "eif_quote": "in force 24 Dec 2004",
    "rates": [
        {"category": "DIVIDEND", "article": "Article 10(2)(b)", "valid_from": "2005-01-01",
         "max_rate": "15", "exclusive": False, "ownership_threshold": None,
         "min_holding_days": None, "source_state": None, "quote": "15 per cent"},
        {"category": "DIVIDEND", "article": "Article 10(2)(a)", "valid_from": "2005-01-01",
         "max_rate": "5", "exclusive": False, "ownership_threshold": "10",
         "min_holding_days": None, "source_state": None, "quote": "5 per cent at 10%"},
        {"category": "DIVIDEND", "article": "Article 10(2)(a)", "valid_from": "1990-01-01",
         "max_rate": "7", "exclusive": False, "ownership_threshold": "10",
         "min_holding_days": None, "source_state": None, "quote": "superseded tier"},
    ],
    "ppt": {"applies": True, "from": "2020-01-01", "basis": "MLI art. 7(1)",
            "source_url": "https://y", "quote": "principal purposes"},
}


@pytest.fixture
def s(seeded_session):
    return seeded_session


def test_current_tiers_keeps_latest_and_skips_uncapped():
    tiers = current_tiers(BASE["rates"] + [
        {"category": "ROYALTY", "article": "Art 12", "valid_from": "2005-01-01",
         "max_rate": None, "exclusive": False, "quote": "no cap"},
    ])
    assert sorted(t["max_rate"] for t in tiers) == ["15", "5"]


def test_future_treaty_tier_does_not_hide_todays_rate(s, tmp_path):
    later = {"category": "DIVIDEND", "article": "Art 10(2)", "valid_from": "2099-01-01",
             "max_rate": "7", "exclusive": False, "quote": "new treaty"}
    tiers = current_tiers(BASE["rates"] + [later], today=D)
    general = sorted((t["valid_from"], t["_end"]) for t in tiers
                     if t["category"] == "DIVIDEND" and t.get("ownership_threshold") is None)
    assert general[-1] == ("2099-01-01", None) and general[0][1] == "2099-01-01"
    _file(tmp_path, "CH-IL.json", {**BASE, "rates": BASE["rates"] + [later]})
    seed_treaty_rates(s, tmp_path)
    s.flush()
    engine = WithholdingEngine(s)
    assert str(engine.compute("CH", "IL", "DIVIDEND", D, Decimal("5"), 400).final_rate) == "15.000"
    future = engine.compute("CH", "IL", "DIVIDEND", date(2099, 6, 1), Decimal("5"), 400)
    assert str(future.final_rate) == "7.000"


def test_loader_seeds_tiers_and_ppt(s, tmp_path):
    _file(tmp_path, "CH-IL.json", BASE)
    _file(tmp_path, "CH-XX.json", {**BASE, "b": "XX"})  # unknown jurisdiction: skipped
    _file(tmp_path, "CH-SA.json", {**BASE, "b": "SA", "entry_into_force": None})  # skipped
    assert seed_treaty_rates(s, tmp_path) == 1
    s.flush()
    engine = WithholdingEngine(s)
    big = engine.compute("CH", "IL", "DIVIDEND", D, Decimal("10"), 400)
    small = engine.compute("CH", "IL", "DIVIDEND", D, Decimal("5"), 400)
    assert (str(big.final_rate), str(small.final_rate)) == ("5.000", "15.000")
    assert "mli_ppt" in {f.code for f in big.flags}
    assert run_checks(s) == []


def test_reseed_is_idempotent(s):
    from sqlalchemy import func, select

    from app.modules.treaty.models import MliApplication, Treaty, TreatyRate

    def counts():
        return [s.scalar(select(func.count()).select_from(m)) for m in (Treaty, TreatyRate,
                                                                          MliApplication)]

    before = counts()
    seed(s)
    s.flush()
    assert counts() == before


def test_reseed_replaces_corrected_rates(db_session, tmp_path):
    from app.modules.seed.builder import Seeder

    sd = Seeder(db_session)
    sd.jurisdiction("CH", "Switzerland")
    sd.jurisdiction("IL", "Israel")
    db_session.flush()
    _file(tmp_path, "CH-IL.json", BASE)
    seed_treaty_rates(db_session, tmp_path)
    fixed = {**BASE, "rates": [{**BASE["rates"][0], "max_rate": "10"}, BASE["rates"][1]]}
    _file(tmp_path, "CH-IL.json", fixed)
    seed_treaty_rates(db_session, tmp_path)
    db_session.flush()
    from app.modules.treaty.repository import TreatyRepository

    repo = TreatyRepository(db_session)
    t = repo.find_by_parties("CH", "IL")
    caps = sorted(str(r.max_rate) for r in repo.get_rates(t.id, "DIVIDEND", D))
    assert caps == ["10.000", "5.000"]


def test_no_cap_treaty_is_stored_without_rates(db_session, tmp_path):
    from app.modules.seed.builder import Seeder

    sd = Seeder(db_session)
    sd.jurisdiction("CH", "Switzerland")
    sd.jurisdiction("IL", "Israel")
    db_session.flush()
    _file(tmp_path, "CH-IL.json", {**BASE, "rates": [], "no_cap": True})
    assert seed_treaty_rates(db_session, tmp_path) == 1
    from app.modules.treaty.repository import TreatyRepository

    assert TreatyRepository(db_session).find_by_parties("CH", "IL") is not None
