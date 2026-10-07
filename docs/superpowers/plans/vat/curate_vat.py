"""Copies researched VAT files (one <CC>.json per jurisdiction) into the seed data.

    python curate_vat.py <research VAT/out dir>

`future_changes` must change the STANDARD rate. Where research recorded a reduced-rate change
there, it is moved into `notes` so the loader does not mistake it for a new standard rate."""

import json
import sys
from pathlib import Path

DEST = Path(__file__).resolve().parents[4] / "app" / "modules" / "seed" / "data" / "vat"

# Future changes that concern reduced rates only (checked by hand).
REDUCED_ONLY = {"KZ", "LV", "SE"}


def curate(d: dict) -> dict:
    moved = []
    kept = []
    for ch in d.get("future_changes") or []:
        std = d.get("standard_rate")
        same = std is not None and float(ch["rate"]) == float(std)
        if d["code"] in REDUCED_ONLY or same:
            moved.append(ch)
        else:
            kept.append(ch)
    if moved:
        extra = "; ".join(f"from {c['valid_from']}: {c['quote'].split(' — ')[-1]}" for c in moved)
        prefix = f"{d['notes']} " if d.get("notes") else ""
        d["notes"] = f"{prefix}Scheduled: {extra}"
    d["future_changes"] = kept
    return d


def main(src: str) -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in sorted(Path(src).glob("[A-Z][A-Z].json")):
        d = curate(json.loads(p.read_text(encoding="utf-8")))
        out = json.dumps(d, ensure_ascii=False, indent=1) + "\n"
        (DEST / p.name).write_text(out, encoding="utf-8")
        n += 1
    print(f"{n} files curated")


if __name__ == "__main__":
    main(sys.argv[1])
