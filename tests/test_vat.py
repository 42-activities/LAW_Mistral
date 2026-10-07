import json
from datetime import date

from app.modules.browse.overview import BrowseService
from app.modules.seed.builder import Seeder
from app.modules.seed.vat import seed_vat

BASE = {
    "code": "FR",
    "has_vat": True,
    "tax_name": "TVA",
    "standard_rate": "20",
    "valid_from": "2014-01-01",
    "legal_ref": "CGI art. 278",
    "quote": "Le taux normal de la taxe sur la valeur ajoutée est fixé à 20 %",
    "source_url": "https://www.legifrance.gouv.fr/",
    "source_title": "CGI",
    "reduced_rates": [{"rate": "10", "scope": "restaurants"}, {"rate": "5.5", "scope": "food"}],
    "future_changes": [],
    "notes": "zero rate on exports",
}


def _write(tmp_path, data):
    (tmp_path / f"{data['code']}.json").write_text(json.dumps(data), encoding="utf-8")


def test_vat_loads_and_shows_in_overview(db_session, tmp_path):
    Seeder(db_session).jurisdiction("FR", "France")
    db_session.flush()
    _write(tmp_path, {**BASE, "future_changes": [
        {"rate": "21", "valid_from": "2027-01-01", "quote": "porté à 21 %", "source_url": "https://x"}
    ]})
    assert seed_vat(db_session, tmp_path) == 1
    assert seed_vat(db_session, tmp_path) == 0  # unchanged file: nothing rewritten
    vat = BrowseService(db_session).jurisdiction("FR", date(2026, 10, 7))["vat"]
    assert vat["standard_rate"] == "20.000" and vat["reduced_rates"][0]["rate"] == "10"
    assert vat["next_change"]["standard_rate"] == "21.000"
    later = BrowseService(db_session).jurisdiction("FR", date(2027, 3, 1))["vat"]
    assert later["standard_rate"] == "21.000" and later["next_change"] is None


def test_corrected_file_replaces_stored_vat(db_session, tmp_path):
    Seeder(db_session).jurisdiction("FR", "France")
    db_session.flush()
    _write(tmp_path, BASE)
    seed_vat(db_session, tmp_path)
    _write(tmp_path, {**BASE, "standard_rate": "19.6", "valid_from": "2000-04-01"})
    assert seed_vat(db_session, tmp_path) == 1
    vat = BrowseService(db_session).jurisdiction("FR", date(2026, 10, 7))["vat"]
    assert vat["standard_rate"] == "19.600"


def test_no_vat_jurisdiction(db_session, tmp_path):
    Seeder(db_session).jurisdiction("KW", "Kuwait")
    db_session.flush()
    _write(tmp_path, {**BASE, "code": "KW", "has_vat": False, "standard_rate": None,
                      "valid_from": None, "tax_name": "none", "reduced_rates": []})
    seed_vat(db_session, tmp_path)
    vat = BrowseService(db_session).jurisdiction("KW", date(2026, 10, 7))["vat"]
    assert vat["has_vat"] is False and vat["standard_rate"] is None
    assert vat["valid"]["from"] is None


def test_seeded_vat_covers_every_jurisdiction(seeded_session):
    rows = {r["code"]: r for r in BrowseService(seeded_session).corporate_tax(date(2026, 10, 7))}
    assert all(r["summary"]["vat"] is not None for r in rows.values())
    assert rows["FR"]["summary"]["vat"]["rate"] == "20.000"
    assert rows["SE"]["summary"]["vat"]["rate"] == "25.000"  # food-rate change is not standard
    assert rows["US"]["summary"]["vat"]["has_vat"] is False
    assert rows["KZ"]["summary"]["vat"]["rate"] == "16.000"
