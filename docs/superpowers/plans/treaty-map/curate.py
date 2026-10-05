"""Copy research rate files into the seed data folder, applying documented curation.

Usage: python curate.py <scratch rates dir>
Each override removes a tier the engine cannot condition correctly; the reason is appended to
the file's notes so the evidence trail stays complete.
"""

import json
import sys
from pathlib import Path

DEST = Path(__file__).resolve().parents[4] / "app/modules/seed/data/treaty_rates"

# (file stem, category, ownership_threshold or None, exclusive flag) → reason
DROP = {
    ("GB-US", "DIVIDEND", "80", False): "0% tier needs the LOB test (art. 23) — not modelled",
    ("GB-BH", "INTEREST", None, True): "exemption limited to qualifying recipients (art. 11(3))",
    ("LU-US", "DIVIDEND", "25", True): "LU-side 0% needs the active-business test — not modelled",
    ("LU-AT", "ROYALTY", None, True): "exempt only below a 50% holding; the 10% tier is the "
    "conservative general rate for group payments",
    ("NL-HK", "DIVIDEND", "10", True): "0% needs a listing, bank or HQ test or competent-authority "
    "approval — not modelled",
}


# (file stem, category, ownership_threshold) → field changes on the remaining tier
RETIER = {
    ("LU-AT", "ROYALTY", "50"): {"ownership_threshold": None},
}


def curate(src: Path) -> int:
    n = 0
    for p in sorted(src.glob("*/*-*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        kept = []
        for r in d.get("rates", []):
            key = (p.stem, r["category"], r.get("ownership_threshold"), bool(r.get("exclusive")))
            if key in DROP:
                d["notes"] = f"{d.get('notes', '')} [curated: dropped {key[1]} tier — {DROP[key]}]"
            else:
                change = RETIER.get((p.stem, r["category"], r.get("ownership_threshold")))
                kept.append({**r, **change} if change else r)
        d["rates"] = kept
        out = DEST / p.parent.name / p.name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        n += 1
    return n


if __name__ == "__main__":
    print(curate(Path(sys.argv[1])), "files curated")
