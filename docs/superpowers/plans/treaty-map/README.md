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

## Remaining treaties (seeded)

The other 235 in-force treaties (pairs without a hub) were extracted the same way and curated
into the same folder: 471 treaty files in total. `curate.py` now also turns "higher rate above
a holding threshold" tiers (Austrian royalty pattern, KW–IT dividends) into the general rate and
drops US–BE's certification-dependent 0% tier and PT–IL's conditional Israeli 10% tier.
Skipped by the loader: JO–KW (no text), OM–EG (no entry-into-force date).

## Gap pass

BE–DE (in force 1969-07-30), CY–DE (2011-12-16) and ES–SE (1976-12-21, still in force) added;
IE–DE entry into force (2012-11-28) and IE–GB 1998-protocol dividend start (1999-04-06) filled.
Still unresolved: JO–KW (no official text reachable), OM–EG (entry into force unpublished),
LU–OM (not in force per Luxembourg).

## Batch-8 network (EU completion, Serbia, CIS)

`treaties_merged_batch8.json` maps the 13 batch-8 jurisdictions against the 49-jurisdiction
universe (546 pairs, 424 in force); rates for 423 of them are in the seed folder. Curation adds:
investment-conditioned 0% dividend tiers (MD–GB, MD–NL) dropped; most-favoured-nation 0% rates
kept only where an official notice confirms them (EE via the Estonian MoF list; FI notices for LT
and LV; HMRC for EE–GB) and dropped for the other LT/LV partners; FI–BG Bulgarian-source dividend
reading, HR–IL reduced-rate tier and UZ–GB REIT tier dropped. Skipped: HR–SE (no text), RS–IL and
SI–DE (no entry-into-force date).

**Rebuild order.** `curate.py` overwrites files, so re-run it in this order when rebuilding the
seed folder: hub research → remaining-treaty research → gap pass → batch-8 research. Later folders
carry corrections (e.g. IE–DE entry into force) that earlier ones lack.
Investment-conditioned dividend tiers ("holds X% AND invested at least N") are dropped; "or"
conditions are kept because the percentage alone qualifies.
