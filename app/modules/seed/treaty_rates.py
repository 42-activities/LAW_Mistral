"""Treaty rates extracted from official treaty texts (P8 treaty network).

One JSON file per treaty pair under `data/treaty_rates/<HUB>/`, produced by the research
agents described in docs/superpowers/plans/treaty-map/. A file is loaded only when the treaty
has an entry-into-force date and at least one rate; per (category, threshold, direction) only
the tier in force today is kept, so protocol histories never overlap. All evidence is
`unreviewed` until a named reviewer confirms it (spec §10).
"""

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import IncomeCategory
from app.modules.core.repository import JurisdictionRepository
from app.modules.seed.builder import ARTICLE_CATEGORY, RETRIEVED_AT, Seeder, Src, period
from app.modules.source.models import SourceDocument, SourceEvidence
from app.modules.treaty.models import (
    MliApplication,
    Treaty,
    TreatyArticle,
    TreatyParty,
    TreatyRate,
)
from app.modules.treaty.repository import TreatyRepository

DATA_DIR = Path(__file__).parent / "data" / "treaty_rates"
CATEGORIES = {"DIVIDEND", "INTEREST", "ROYALTY"}


def _d(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _rate(r: dict[str, Any]) -> float:
    return 0.0 if r.get("exclusive") else float(r["max_rate"])


def current_tiers(rates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Latest tier per (category, ownership threshold, source State)."""
    latest: dict[tuple[str, str | None, str | None], dict[str, Any]] = {}
    for r in rates:
        if r.get("category") not in CATEGORIES or not r.get("valid_from"):
            continue
        if r.get("max_rate") is None and not r.get("exclusive"):
            continue
        key = (r["category"], r.get("ownership_threshold"), r.get("source_state"))
        cur = latest.get(key)
        # Same key and start: the extra tier is conditional (e.g. "profits taxed at the full
        # rate") — keep the higher, conservative rate.
        if cur is None or r["valid_from"] > cur["valid_from"] or (
            r["valid_from"] == cur["valid_from"] and _rate(r) > _rate(cur)
        ):
            latest[key] = r
    return list(latest.values())


def _cut(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


def _name(data: dict[str, Any], a_name: str, b_name: str) -> str:
    """Official titles run long; the stored name is short, the full title stays in evidence."""
    year = (data.get("signed") or "")[:4]
    return _cut(f"Treaty between {a_name} and {b_name}" + (f" ({year})" if year else ""), 200)


class _Evidence:
    """Evidence rows for a batch of new treaties: one query to prefetch, few flushes."""

    def __init__(self, session: Session) -> None:
        self.s = session
        self.docs = {d.url: d for d in session.scalars(select(SourceDocument))}
        self.evs = {
            (e.document_id, e.quoted_text): e for e in session.scalars(select(SourceEvidence))
        }

    def ids(self, srcs: list[Src]) -> list[int]:
        new_docs = []
        for src in srcs:
            if src.url not in self.docs:
                doc = SourceDocument(title=src.title, url=src.url, retrieved_at=RETRIEVED_AT,
                                     content_hash="fixture-v1")
                self.docs[src.url] = doc
                new_docs.append(doc)
        if new_docs:
            self.s.add_all(new_docs)
            self.s.flush()
        out, new_evs = [], []
        for src in srcs:
            key = (self.docs[src.url].id, src.quote)
            if key not in self.evs:
                ev = SourceEvidence(document_id=key[0], article=src.article,
                                    quoted_text=src.quote, review_status=src.review_status)
                self.evs[key] = ev
                new_evs.append(ev)
            out.append(key)
        if new_evs:
            self.s.add_all(new_evs)
            self.s.flush()
        return [self.evs[k].id for k in out]


def _insert_new(
    sd: Seeder, evidence: _Evidence, data: dict[str, Any], a: Jurisdiction, b: Jurisdiction,
    in_force: date, tiers: list[dict[str, Any]], codes: dict[str, Jurisdiction],
) -> None:
    """Fast path for a treaty not yet in the database (fresh seeds, tests)."""
    ppt = data.get("ppt") or {}
    with_ppt = bool(ppt.get("applies") and ppt.get("from"))
    srcs = [_treaty_src(data, in_force)] + [_rate_src(data, r) for r in tiers]
    if with_ppt:
        srcs.append(_ppt_src(data, ppt))
    ids = evidence.ids(srcs)
    t = Treaty(name=_name(data, a.name, b.name), signature_date=_d(data.get("signed")) or in_force,
               entry_into_force_date=in_force, source_evidence_id=ids[0])
    sd.s.add(t)
    sd.s.flush()
    articles = {}
    for r in tiers:
        cat = ARTICLE_CATEGORY[r["category"]]
        if cat not in articles:
            articles[cat] = TreatyArticle(treaty_id=t.id, article_category=cat,
                                          article_ref=_article_ref(r))
    sd.s.add_all([TreatyParty(treaty_id=t.id, jurisdiction_id=a.id),
                  TreatyParty(treaty_id=t.id, jurisdiction_id=b.id), *articles.values()])
    sd.s.flush()
    for r, ev_id in zip(tiers, ids[1:], strict=False):
        src_state = codes.get(r["source_state"]) if r.get("source_state") else None
        threshold = r.get("ownership_threshold")
        sd.s.add(TreatyRate(
            treaty_id=t.id, treaty_article_id=articles[ARTICLE_CATEGORY[r["category"]]].id,
            income_category_id=sd._id("cat", r["category"]),
            max_rate=None if r.get("max_rate") is None else Decimal(r["max_rate"]),
            exclusive_residence_taxation=bool(r.get("exclusive")), relief_mechanism=None,
            beneficial_owner_required=True,
            ownership_threshold=None if threshold is None else Decimal(threshold),
            min_holding_days=r.get("min_holding_days"),
            source_jurisdiction_id=None if src_state is None else src_state.id,
            source_evidence_id=ev_id, valid_period=period(_d(r["valid_from"]) or in_force),
        ))
    if with_ppt:
        sd.s.add(MliApplication(treaty_id=t.id, ppt_applies=True, source_evidence_id=ids[-1],
                                valid_period=period(_d(ppt["from"]) or in_force)))
    sd.s.flush()


def _article_ref(r: dict[str, Any]) -> str:
    return _cut(r["article"].split("(")[0].strip() or r["category"], 50)


def _treaty_src(data: dict[str, Any], in_force: date) -> Src:
    return Src(_cut(f"{data['treaty_name']} — {data['source_title']}", 500),
               data.get("eif_source_url") or data["source_url"], None,
               data.get("eif_quote") or f"entry into force {in_force.isoformat()}")


def _rate_src(data: dict[str, Any], r: dict[str, Any]) -> Src:
    return Src(_cut(data["source_title"], 500), data["source_url"],
               _cut(r["article"], 100) if r.get("article") else None, r["quote"])


def _ppt_src(data: dict[str, Any], ppt: dict[str, Any]) -> Src:
    return Src(_cut(data["source_title"], 500), ppt.get("source_url") or data["source_url"],
               _cut(ppt["basis"], 100) if ppt.get("basis") else None,
               ppt.get("quote") or "principal purpose test applies")


def _dec(value: str | None) -> Decimal | None:
    return None if value is None else Decimal(value)


def _drop_stale_rates(
    session: Session, treaty_id: int, tiers: list[dict[str, Any]], codes: dict[str, Jurisdiction]
) -> None:
    """Corrected files must win over rows loaded earlier: when the stored rates differ from the
    file's current tiers, delete them so they are re-inserted from the file."""

    def src_id(code: str | None) -> int | None:
        j = codes.get(code) if code else None
        return None if j is None else j.id

    want = {
        (r["category"], _dec(r.get("ownership_threshold")), src_id(r.get("source_state")),
         None if r.get("exclusive") else _dec(r.get("max_rate")), bool(r.get("exclusive")),
         r.get("min_holding_days"), _d(r["valid_from"]))
        for r in tiers
    }
    rows = session.execute(
        select(TreatyRate, IncomeCategory.code)
        .join(IncomeCategory, TreatyRate.income_category_id == IncomeCategory.id)
        .where(TreatyRate.treaty_id == treaty_id)
    ).all()
    have = {
        (code, r.ownership_threshold, r.source_jurisdiction_id,
         None if r.exclusive_residence_taxation else r.max_rate, r.exclusive_residence_taxation,
         r.min_holding_days, r.valid_period.lower)
        for r, code in rows
    }
    if have != want:
        session.execute(delete(TreatyRate).where(TreatyRate.treaty_id == treaty_id))
        session.flush()


def load_file(
    sd: Seeder, path: Path, evidence: _Evidence | None = None,
    codes: dict[str, Jurisdiction] | None = None,
) -> bool:
    data = json.loads(path.read_text(encoding="utf-8"))
    in_force = _d(data.get("entry_into_force"))
    if in_force is None and data.get("effective_from_official"):
        # Entry into force unpublished; the official "applies from" date stands in (see eif_quote).
        in_force = _d(data["effective_from_official"])
    tiers = current_tiers(data.get("rates") or [])
    # A treaty in force that sets no source-State cap (curated "no_cap") is stored without rates
    # so the engine reports "no limit recorded" rather than "no treaty".
    if in_force is None or not (tiers or data.get("no_cap")):
        return False
    repo = JurisdictionRepository(sd.s)
    a, b = repo.get_by_code(data["a"]), repo.get_by_code(data["b"])
    if a is None or b is None:
        return False
    if evidence is not None and codes is not None and (
        TreatyRepository(sd.s).find_by_parties(a.code, b.code) is None
    ):
        _insert_new(sd, evidence, data, a, b, in_force, tiers, codes)
        return True
    # Treaty already present (re-seed): replace its rates if the file changed, else no-op.
    t = sd.treaty(
        a, b, name=_name(data, a.name, b.name), signed=_d(data.get("signed")) or in_force,
        in_force=in_force,
        src=_treaty_src(data, in_force),
    )
    _drop_stale_rates(sd.s, t.id, tiers, codes or {})
    for r in tiers:
        source = r.get("source_state")
        sd.treaty_rate(
            t, r["category"], _article_ref(r), _d(r["valid_from"]) or in_force,
            _rate_src(data, r),
            max_rate=r.get("max_rate"), exclusive=bool(r.get("exclusive")),
            ownership_threshold=r.get("ownership_threshold"),
            min_holding_days=r.get("min_holding_days"),
            source=repo.get_by_code(source) if source else None,
        )
    ppt = data.get("ppt") or {}
    if ppt.get("applies") and ppt.get("from"):
        sd.ppt(t, _d(ppt["from"]) or in_force, _ppt_src(data, ppt))
    return True


def seed_treaty_rates(session: Session, data_dir: Path = DATA_DIR) -> int:
    sd = Seeder(session)
    files = sorted(data_dir.glob("*/*.json"))
    if not files:
        return 0
    evidence = _Evidence(session)
    codes = {j.code: j for j in JurisdictionRepository(session).list()}
    return sum(load_file(sd, p, evidence, codes) for p in files)
