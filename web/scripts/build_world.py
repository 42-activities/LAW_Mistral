"""Builds public/world.json: Equal Earth SVG paths per country (ISO alpha-2) for the tax map.

Source: Natural Earth 1:50m admin-0 countries (public domain), v5.1.2:
https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_50m_admin_0_countries.geojson

    python scripts/build_world.py ne_50m_admin_0_countries.geojson public/world.json
"""

import json
import math
import sys

W = 1000.0
A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
M = math.sqrt(3) / 2


def equal_earth(lon: float, lat: float) -> tuple[float, float]:
    t = math.asin(M * math.sin(math.radians(lat)))
    t2 = t * t
    t6 = t2 * t2 * t2
    x = math.radians(lon) * math.cos(t) / (M * (A1 + 3 * A2 * t2 + t6 * (7 * A3 + 9 * A4 * t2)))
    y = t * (A1 + A2 * t2 + t6 * (A3 + A4 * t2))
    return x, y


XMAX = equal_earth(180, 0)[0]
SCALE = W / (2 * XMAX)
YTOP = equal_earth(0, 84)[1]
YBOT = equal_earth(0, -58)[1]  # Antarctica is dropped
H = (YTOP - YBOT) * SCALE


def proj(lon: float, lat: float) -> tuple[float, float]:
    x, y = equal_earth(lon, lat)
    return round((x + XMAX) * SCALE, 1), round((YTOP - y) * SCALE, 1)


def ring_path(ring: list[list[float]]) -> tuple[str, list[tuple[float, float]]]:
    pts: list[tuple[float, float]] = []
    for lon, lat in ring:
        p = proj(lon, lat)
        if not pts or abs(p[0] - pts[-1][0]) + abs(p[1] - pts[-1][1]) >= 0.4:
            pts.append(p)
    if len(pts) < 3:
        return "", pts
    return "M" + "L".join(f"{x:g},{y:g}" for x, y in pts) + "Z", pts


def main(src: str, dst: str) -> None:
    features = json.load(open(src, encoding="utf-8"))["features"]
    # Several Natural Earth features can share a code (e.g. Australia's Indian Ocean
    # territories), so parts are merged per code before the bounding box is taken.
    merged: dict[str, dict] = {}
    for f in features:
        p = f["properties"]
        code = p["ISO_A2_EH"]
        if code == "AQ" or not f["geometry"]:
            continue
        if code == "-99":  # no ISO code (e.g. Kosovo): drawn as uncovered background
            code = "_" + p["ADM0_A3"]
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        entry = merged.setdefault(code, {"name": p["NAME"], "parts": [], "pts": []})
        for poly in polys:
            for ring in poly:
                d, pts = ring_path(ring)
                if d:
                    entry["parts"].append(d)
                    entry["pts"] += pts
        if p.get("SOVEREIGNT") == p.get("ADMIN"):
            entry["name"] = p["NAME"]
    out = {}
    for code, e in merged.items():
        if not e["pts"]:
            continue
        xs, ys = [q[0] for q in e["pts"]], [q[1] for q in e["pts"]]
        box = (max(xs) - min(xs)) * (max(ys) - min(ys))
        out[code] = {
            "name": e["name"],
            "d": "".join(e["parts"]),
            # Where a country is too small to see, the page draws a dot at this point.
            "dot": [round((min(xs) + max(xs)) / 2, 1), round((min(ys) + max(ys)) / 2, 1)]
            if box < 30 else None,
        }
    json.dump({"width": W, "height": round(H, 1), "countries": out}, open(dst, "w"),
              separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
