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
    ("PT-IL", "DIVIDEND", "25", False, "IL", "10"): "10% applies only to profits taxed at a "
    "reduced Israeli rate — not modelled",
    ("US-BE", "DIVIDEND", "80", True, "US", None): "US-source 0% needs the LOB test and a "
    "Treasury certification that could not be confirmed",
    # Batch-8 treaty network
    ("MD-GB", "DIVIDEND", "50", True): "0% also needs GBP 1m invested — not modelled",
    ("MD-NL", "DIVIDEND", "50", True): "0% also needs USD 300k invested — not modelled",
    ("FI-BG", "DIVIDEND", None, True): "Bulgarian-source dividends read as 'other income' — "
    "interpretation, not an express dividend cap",
    ("HR-IL", "DIVIDEND", "10", False, "IL", "10"): "10% only for profits taxed at a reduced "
    "Israeli rate — not modelled",
    ("UZ-GB", "DIVIDEND", None, False, None, "15"): "15% applies only to property investment "
    "vehicles",
    ("LT-BE", "ROYALTY", None, True): "MFN 0% (Lithuania–Japan) not confirmed by an official "
    "notice",
    ("LT-CH", "ROYALTY", None, True): "MFN 0% (Lithuania–Japan) not confirmed by an official "
    "notice",
    ("LT-DK", "ROYALTY", None, True): "MFN 0% (Lithuania–Japan) not confirmed by an official "
    "notice",
    ("LT-ES", "ROYALTY", None, True): "MFN 0% (Lithuania–Japan) not confirmed by an official "
    "notice",
    ("LT-HU", "ROYALTY", None, True): "MFN 0% (Lithuania–Japan) not confirmed by an official "
    "notice",
    ("LT-IE", "ROYALTY", None, True): "MFN 0% (Lithuania–Japan) not confirmed by an official "
    "notice",
    ("LT-IT", "ROYALTY", None, True): "MFN 0% (Lithuania–Japan) not confirmed by an official "
    "notice",
    ("LT-LU", "ROYALTY", None, True): "MFN 0% (Lithuania–Japan) not confirmed by an official "
    "notice",
    ("LT-NL", "ROYALTY", None, True): "MFN 0% (Lithuania–Japan) not confirmed by an official "
    "notice",
    ("LT-SE", "ROYALTY", None, True): "MFN 0% (Lithuania–Japan) not confirmed by an official "
    "notice",
    ("LV-BE", "ROYALTY", None, True): "MFN 0% (Latvia–Japan) not confirmed by an official "
    "notice",
    ("LV-ES", "ROYALTY", None, True): "MFN 0% (Latvia–Japan) not confirmed by an official "
    "notice",
    ("LV-HU", "ROYALTY", None, True): "MFN 0% (Latvia–Japan) not confirmed by an official "
    "notice",
    ("LV-IE", "ROYALTY", None, True): "MFN 0% (Latvia–Japan) not confirmed by an official "
    "notice",
    ("LV-IT", "ROYALTY", None, True): "MFN 0% (Latvia–Japan) not confirmed by an official "
    "notice",
    ("LV-LU", "ROYALTY", None, True): "MFN 0% (Latvia–Japan) not confirmed by an official "
    "notice",
    ("LV-NL", "ROYALTY", None, True): "MFN 0% (Latvia–Japan) not confirmed by an official "
    "notice",
    ("LV-CH", "ROYALTY", None, True): "MFN 0% (Latvia–Japan) not confirmed by an official "
    "notice",
    ("LV-ES", "INTEREST", None, True): "MFN interest exemption (Latvia–Japan) not confirmed "
    "by an official notice",
    ("LV-LU", "INTEREST", None, True): "MFN interest exemption (Latvia–Japan) not confirmed "
    "by an official notice",
    ("NL-HK", "DIVIDEND", "10", True): "0% needs a listing, bank or HQ test or competent-authority "
    "approval — not modelled",
}


# (file stem, category, ownership_threshold) → field changes on the remaining tier
RETIER = {
    ("LU-AT", "ROYALTY", "50"): {"ownership_threshold": None},
}


def _cap(r: dict) -> float:
    return 0.0 if r.get("exclusive") else float(r["max_rate"])


def _invert_upper_tiers(rates: list[dict], d: dict) -> list[dict]:
    """A threshold tier with a HIGHER rate than the general tier (e.g. Austrian treaties:
    royalties exempt, but 10% if the recipient holds >50%) cannot be expressed — the engine
    applies the lowest qualifying cap. Keep the higher rate as the general rate (correct for
    group payments, conservative for small holdings)."""
    out = list(rates)
    for r in rates:
        if r.get("ownership_threshold") in (None, "0") or r.get("max_rate") is None:
            continue
        general = [g for g in out if g["category"] == r["category"]
                   and g.get("ownership_threshold") is None
                   and g.get("source_state") == r.get("source_state")]
        if general and all(_cap(r) > _cap(g) for g in general):
            out = [g for g in out if g not in general and g is not r]
            out.append({**r, "ownership_threshold": None})
            d["notes"] = (f"{d.get('notes', '')} [curated: {r['category']} {r['max_rate']}% tier "
                          f"above {r['ownership_threshold']}% used as the general rate — a higher "
                          f"rate for larger holdings is not modelled]")
    return out


def curate(src: Path) -> int:
    n = 0
    for p in sorted(src.glob("*/*-*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        kept = []
        for r in d.get("rates", []):
            key = (p.stem, r["category"], r.get("ownership_threshold"), bool(r.get("exclusive")))
            long_key = (*key, r.get("source_state"), r.get("max_rate"))
            reason = DROP.get(key) or DROP.get(long_key)
            if reason:
                d["notes"] = f"{d.get('notes', '')} [curated: dropped {key[1]} tier — {reason}]"
            else:
                change = RETIER.get((p.stem, r["category"], r.get("ownership_threshold")))
                kept.append({**r, **change} if change else r)
        d["rates"] = _invert_upper_tiers(kept, d)
        out = DEST / p.parent.name / p.name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        n += 1
    return n


if __name__ == "__main__":
    print(curate(Path(sys.argv[1])), "files curated")
