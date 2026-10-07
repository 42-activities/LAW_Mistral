"""Loads VAT / GST data from data/vat/<CC>.json (one file per jurisdiction, researched from
official sources; see docs/superpowers/plans/2026-10-07-vat.md for the file shape).

A file gives the rate in force and any enacted future change; each becomes one period. On a
re-seed a jurisdiction's stored periods are replaced when the file no longer matches them."""

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.orm import Session

from app.modules.core.repository import JurisdictionRepository
from app.modules.seed.builder import Seeder, Src
from app.modules.tax.models import VatRule

DATA_DIR = Path(__file__).parent / "data" / "vat"


def _cut(text: str | None, n: int) -> str | None:
    return None if text is None else (text if len(text) <= n else text[: n - 1] + "…")


def _periods(data: dict[str, Any]) -> list[dict[str, Any]]:
    """(start, rate, quote, url) per period, oldest first."""
    # No start date (no VAT at all, or the rate's commencement was not found): open-ended period.
    rows: list[dict[str, Any]] = [{
        "start": date.fromisoformat(data["valid_from"]) if data.get("valid_from") else None,
        "rate": data.get("standard_rate"),
        "quote": data["quote"],
        "url": data["source_url"],
        "title": data["source_title"] + (" (secondary source)" if data.get("secondary") else ""),
        "article": data.get("legal_ref"),
    }]
    for ch in data.get("future_changes") or []:
        rows.append({
            "start": date.fromisoformat(ch["valid_from"]),
            "rate": ch["rate"],
            "quote": ch["quote"],
            "url": ch.get("source_url") or data["source_url"],
            "title": data["source_title"],
            "article": data.get("legal_ref"),
        })
    rows.sort(key=lambda r: r["start"] or date.min)
    for i, r in enumerate(rows):
        r["end"] = rows[i + 1]["start"] if i + 1 < len(rows) else None
    return rows


def load_file(sd: Seeder, path: Path) -> bool:
    data = json.loads(path.read_text(encoding="utf-8"))
    j = JurisdictionRepository(sd.s).get_by_code(data["code"])
    if j is None:
        return False
    reduced = [
        {"rate": str(r["rate"]), "scope": _cut(str(r.get("scope", "")), 200) or ""}
        for r in data.get("reduced_rates") or []
    ]
    notes = _cut(data.get("notes") or None, 1000)
    wanted = [
        (p["start"], p["end"], None if p["rate"] is None else Decimal(str(p["rate"])))
        for p in _periods(data)
    ]
    stored = sd.s.scalars(
        select(VatRule).where(VatRule.jurisdiction_id == j.id).order_by(VatRule.valid_period)
    ).all()
    current = [(r.valid_period.lower, r.valid_period.upper, r.standard_rate) for r in stored]
    if current == wanted and all(r.reduced_rates == reduced and r.notes == notes for r in stored):
        return False
    sd.s.execute(delete(VatRule).where(VatRule.jurisdiction_id == j.id))
    for p in _periods(data):
        src = Src(_cut(p["title"], 500) or "", p["url"], _cut(p["article"], 50), p["quote"])
        sd.s.add(VatRule(
            jurisdiction_id=j.id,
            has_vat=bool(data["has_vat"]),
            tax_name=_cut(data.get("tax_name") or "VAT", 200) or "VAT",
            standard_rate=None if p["rate"] is None else Decimal(str(p["rate"])),
            reduced_rates=reduced,
            notes=notes,
            source_evidence_id=sd.ev(src),
            valid_period=Range(p["start"], p["end"], bounds="[)"),
        ))
    sd.s.flush()
    return True


def seed_vat(session: Session, data_dir: Path = DATA_DIR) -> int:
    sd = Seeder(session)
    return sum(load_file(sd, p) for p in sorted(data_dir.glob("*.json")))
