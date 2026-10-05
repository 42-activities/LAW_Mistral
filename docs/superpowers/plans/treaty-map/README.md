# Treaty map (2026-10-05)

`treaties_merged.json`: every pair among the 38 jurisdictions with tax data (France and UAE
pairs excluded — already seeded): 471 in force, 155 not in force, 4 unresolved (BE–DE, CY–DE:
official lists blocked; LU–OM: entry into force not yet published by Luxembourg; ES–SE: no
Swedish implementing law). 278 treaties are MLI-covered on both sides.

Each record cites an official source (national treaty list or OECD MLI position) with a quote.
Built by four research agents; `merge_all.py` merges their outputs and records the manual
resolutions (BE–QA, SG–JO, GR–SG, GR–SE, LU–OM, ES–SE).

Not seeded yet: treaties change engine results only once their dividend/interest/royalty rates
are recorded from the treaty texts. 14 in-force treaties still lack an entry-into-force date.

## Hub treaty rates (seeded)

236 treaties between the nine hubs (NL, LU, CY, MT, IE, CH, SG, HK, GB) and the other
jurisdictions, extracted from official treaty texts into `app/modules/seed/data/treaty_rates/`
and loaded by `app/modules/seed/treaty_rates.py`. `curate.py` copies research output into that
folder and drops tiers the engine cannot condition (LOB / listing / recipient tests) or makes
them conservative; each change is noted in the file's `notes`. The loader keeps only the tier
in force per (category, threshold, direction) and, on ties, the higher (conservative) rate.
Skipped: IE–DE (no entry-into-force date), IE–GB dividends (protocol start date unknown).
