"""Merge matrix_A..D into treaties_merged.json; report disagreements between agents."""
import collections
import json

M = {f: json.load(open(f"matrix_{f}.json")) for f in "ABCD"}
by = collections.defaultdict(dict)
for f, rows in M.items():
    for r in rows:
        by[frozenset((r["a"], r["b"]))][f] = r

# Manual resolutions (reasoned in the session):
OVERRIDE = {
    frozenset(("BE", "QA")): "D",  # A misread the 2015 amending-instrument signature as EIF
    frozenset(("SG", "JO")): "C",  # IRAS list shows it in force; D inferred absence from MLI lists
    frozenset(("GR", "SG")): "C",  # IRAS list: in force 2022-03-14; B inferred absence
    frozenset(("GR", "SE")): "C",  # Sweden repealed its implementing law from 2022-01-01
    frozenset(("LU", "OM")): "B",  # Oman ratified; Luxembourg has not published entry into force
}
# Treated as unknown (not applied): LU–OM entry into force unpublished; ES–SE no Swedish law.
PENDING = {frozenset(("LU", "OM")), frozenset(("ES", "SE"))}

def score(r):
    # prefer: decided in_force > has entry date > has quote
    return (r["in_force"] is not None, r["in_force"] is True and bool(r.get("entry_into_force")),
            bool(r.get("quote")))

merged, conflicts = [], []
for k, recs in by.items():
    vals = {f: r["in_force"] for f, r in recs.items()}
    decided = {v for v in vals.values() if v is not None}
    if k in OVERRIDE:
        best = recs[OVERRIDE[k]]
    else:
        best = max(recs.values(), key=score)
        if len(decided) > 1:
            conflicts.append((sorted(k), vals))
    row = {**best, "agents": sorted(recs)}
    if k in PENDING:
        row["in_force"] = None
    merged.append(row)
json.dump(sorted(merged, key=lambda r: (r["a"], r["b"])), open("treaties_merged.json", "w"),
          ensure_ascii=False, indent=1)
c = collections.Counter(r["in_force"] for r in merged)
mli = sum(1 for r in merged if r.get("mli_covered_both"))
print(len(merged), "pairs;", dict(c), "; MLI both:", mli)
print("unresolved conflicts:", conflicts)
no_eif = sum(1 for r in merged if r["in_force"] and not r.get("entry_into_force"))
print("in force without entry date:", no_eif)
