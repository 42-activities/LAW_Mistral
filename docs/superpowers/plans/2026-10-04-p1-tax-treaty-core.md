# P1 Tax & Treaty Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the versioned, source-backed data layer for domestic tax rules, holding regimes, and tax treaties — bitemporal validity enforced by `btree_gist` exclusion constraints, every figure linked to official `source_evidence`, with as-of read repositories, and seed the verified **France–UAE golden fixture**.

**Architecture:** Extends the P0 modular monolith. New reference data under `core`; versioned rule/treaty tables under `tax` and `treaty` (created empty in P0). Each versioned row carries a `valid_period daterange` (valid time) and a mandatory `source_evidence_id` FK (no figure without a source). Repositories expose as-of resolution only — composing `min(domestic, treaty)` into an answer is **P3 (engines)**, out of scope here.

**Tech Stack:** Python 3.12 · FastAPI · SQLAlchemy 2.0 sync + psycopg3 · Alembic · PostgreSQL 16 (`btree_gist`, `daterange`, `ExcludeConstraint`) · pytest · ruff · mypy.

**Spec:** `docs/superpowers/specs/2026-10-04-tax-jurisdiction-recommender-design.md`

## Global Constraints

- Python **3.12**; uv; SQLAlchemy **2.0 sync** (`Mapped`, `mapped_column`); psycopg v3; Alembic.
- All new tables live under the existing schemas `core`, `tax`, `treaty` (created in P0 migration 0001). Migrations continue the chain from **0004** (next is **0005**).
- **Bitemporal:** every versioned rule/rate row has `valid_period daterange NOT NULL`; overlaps for the same logical key are rejected at write time via a `btree_gist` `ExcludeConstraint` (spec §6).
- **Source-backing (spec core principle):** every stored figure row (`domestic_tax_rule`, `holding_regime`, `treaty_rate`, `treaty`, `treaty_protocol`) has a **NOT NULL** `source_evidence_id` FK → `source.source_evidence`. (P1 uses one primary source per figure; multi-source M2M is a later enhancement.)
- **Join treaty data on `article_category`, never on article number** (spec §2.4 / review §2.4).
- **`treaty_party` only** (no `jurisdiction_a/b`); treaties may have ≥2 parties (spec §3.1).
- `ruff` + `mypy app` clean; `pytest` clean. No committed bytecode (`.gitignore` from P0 covers it).
- Rates are decimals in **percent**, range 0–100, stored `Numeric(6,3)`.
- All figures seeded in the fixture must be **verified against the cited official source** before the task is considered done (spec §5 bottom line).

## Review Focus

- **Overlapping validity for the same logical key** (same jurisdiction+tax_type+taxpayer+income_category, overlapping `valid_period`) → rejected by the exclusion constraint at write time, not silently accepted. (Task 2 tests.)
- **As-of query on a date outside every `valid_period`** → returns `None`, not a stale or arbitrary row. (Task 3 tests.)
- **A figure row inserted without a source** → impossible: `source_evidence_id` is NOT NULL and FK-enforced. (Tasks 2/4/6 schema + tests.)
- **Treaty lookup by the two parties in either order** (`find_by_parties("FR","AE")` == `("AE","FR")`) → same treaty. (Task 6 tests.)
- **CIT resolved for an amount that straddles a bracket boundary** (e.g. exactly AED 375,000) → the correct bracket's rate, boundary handled consistently. (Task 3 tests.)

---

## File Structure

```
app/modules/core/reference.py        # Currency, TaxType, IncomeCategory models
app/modules/core/reference_repo.py   # lookups by code (cached-ish helpers)
app/modules/tax/__init__.py
app/modules/tax/models.py            # DomesticTaxRule, TaxBracket, HoldingRegime
app/modules/tax/repository.py        # TaxRuleRepository, HoldingRegimeRepository, resolve_bracket_rate
app/modules/treaty/__init__.py
app/modules/treaty/models.py         # Treaty, TreatyParty, TreatyArticle, TreatyProtocol, TreatyRate
app/modules/treaty/repository.py     # TreatyRepository
app/modules/seed/__init__.py
app/modules/seed/sources.py          # helper to upsert SourceDocument + SourceEvidence
app/modules/seed/france_uae.py       # the verified France–UAE golden fixture
app/cli.py                           # `python -m app.cli seed-france-uae`
migrations/versions/0005_core_reference.py
migrations/versions/0006_tax_domestic_rule.py
migrations/versions/0007_tax_holding_regime.py
migrations/versions/0008_treaty_core.py
migrations/versions/0009_treaty_rate.py
tests/test_core_reference.py
tests/test_domestic_tax_rule.py
tests/test_tax_rule_repository.py
tests/test_holding_regime.py
tests/test_treaty_core.py
tests/test_treaty_rate_repository.py
tests/test_seed_france_uae.py
tests/test_data_quality.py
```

Every task that adds a model MUST also add its module to the import block in `migrations/env.py` (the P0 pattern: `from app.modules.<ctx> import models as _<ctx>_models  # noqa: F401`).

---

### Task 1: Core reference data (currency, tax_type, income_category)

**Files:**
- Create: `app/modules/core/reference.py`, `app/modules/core/reference_repo.py`
- Create: `migrations/versions/0005_core_reference.py`
- Modify: `migrations/env.py` (import reference models)
- Test: `tests/test_core_reference.py`

**Interfaces:**
- Consumes: `app.db.Base`, `db_session`.
- Produces (schema `core`):
  - `Currency(id:int, code:str unique, name:str)` (e.g. "EUR","AED").
  - `TaxType(id:int, code:str unique, name:str)` (e.g. "CIT","WHT_DIVIDEND","WHT_INTEREST","WHT_ROYALTY","VAT").
  - `IncomeCategory(id:int, code:str unique, name:str)` (e.g. "DIVIDEND","INTEREST","ROYALTY","CORPORATE_PROFIT").
  - `ReferenceRepository(session)` with `currency(code)->Currency|None`, `tax_type(code)->TaxType|None`, `income_category(code)->IncomeCategory|None`, and `get_or_create_*` variants returning the row (used by seeds).

- [ ] **Step 1: Write the failing test**

`tests/test_core_reference.py`:
```python
from app.modules.core.reference import Currency, IncomeCategory, TaxType
from app.modules.core.reference_repo import ReferenceRepository


def test_lookup_by_code(db_session):
    db_session.add_all([
        Currency(code="EUR", name="Euro"),
        TaxType(code="CIT", name="Corporate income tax"),
        IncomeCategory(code="DIVIDEND", name="Dividend"),
    ])
    db_session.flush()
    repo = ReferenceRepository(db_session)
    assert repo.currency("EUR").name == "Euro"
    assert repo.tax_type("CIT").name == "Corporate income tax"
    assert repo.income_category("DIVIDEND").code == "DIVIDEND"
    assert repo.currency("USD") is None


def test_get_or_create_is_idempotent(db_session):
    repo = ReferenceRepository(db_session)
    a = repo.get_or_create_tax_type("VAT", "Value added tax")
    db_session.flush()
    b = repo.get_or_create_tax_type("VAT", "Value added tax")
    db_session.flush()
    assert a.id == b.id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_core_reference.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the models**

`app/modules/core/reference.py`:
```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Currency(Base):
    __tablename__ = "currency"
    __table_args__ = {"schema": "core"}

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(3), unique=True)
    name: Mapped[str] = mapped_column(String(100))


class TaxType(Base):
    __tablename__ = "tax_type"
    __table_args__ = {"schema": "core"}

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(100))


class IncomeCategory(Base):
    __tablename__ = "income_category"
    __table_args__ = {"schema": "core"}

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(100))
```

- [ ] **Step 4: Write the repository**

`app/modules/core/reference_repo.py`:
```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.core.reference import Currency, IncomeCategory, TaxType


class ReferenceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def currency(self, code: str) -> Currency | None:
        return self.session.scalar(select(Currency).where(Currency.code == code))

    def tax_type(self, code: str) -> TaxType | None:
        return self.session.scalar(select(TaxType).where(TaxType.code == code))

    def income_category(self, code: str) -> IncomeCategory | None:
        return self.session.scalar(select(IncomeCategory).where(IncomeCategory.code == code))

    def get_or_create_currency(self, code: str, name: str) -> Currency:
        row = self.currency(code)
        if row is None:
            row = Currency(code=code, name=name)
            self.session.add(row)
        return row

    def get_or_create_tax_type(self, code: str, name: str) -> TaxType:
        row = self.tax_type(code)
        if row is None:
            row = TaxType(code=code, name=name)
            self.session.add(row)
        return row

    def get_or_create_income_category(self, code: str, name: str) -> IncomeCategory:
        row = self.income_category(code)
        if row is None:
            row = IncomeCategory(code=code, name=name)
            self.session.add(row)
        return row
```

- [ ] **Step 5: Write the migration + env import**

`migrations/versions/0005_core_reference.py` (revision "0005", down_revision "0004"): create the three tables under schema `core`, each with `id` PK and a unique `code`. Follow the exact column types in the models (`String(3)` for currency code, `String(32)` for the others, `String(100)` for names). Add to `migrations/env.py`:
```python
from app.modules.core import reference as _core_reference  # noqa: F401
```

- [ ] **Step 6: Run tests + checks; commit**

Run: `uv run pytest tests/test_core_reference.py -v` (PASS), then `uv run pytest`, `uv run ruff check .`, `uv run mypy app` (all clean).
```bash
git add app/modules/core/reference.py app/modules/core/reference_repo.py migrations/versions/0005_core_reference.py migrations/env.py tests/test_core_reference.py
git commit -m "feat: core reference data (currency, tax_type, income_category)"
```

---

### Task 2: `tax.domestic_tax_rule` + `tax.tax_bracket` with exclusion constraint

**Files:**
- Create: `app/modules/tax/__init__.py`, `app/modules/tax/models.py`
- Create: `migrations/versions/0006_tax_domestic_rule.py`
- Modify: `migrations/env.py`
- Test: `tests/test_domestic_tax_rule.py`

**Interfaces:**
- Consumes: `core.Jurisdiction` (P0), `core.TaxType`/`IncomeCategory` (Task 1), `source.SourceEvidence` (P0), `db_session`.
- Produces (schema `tax`):
  - `DomesticTaxRule(id, jurisdiction_id FK core.jurisdiction, tax_type_id FK core.tax_type, income_category_id FK core.income_category (NOT NULL; use CORPORATE_PROFIT for CIT), taxpayer_type:str ('company'|'individual'|'any'), rate:Decimal|None (percent; NULL when bracketed), is_bracketed:bool, source_evidence_id FK source.source_evidence NOT NULL, valid_period:DATERANGE NOT NULL)` with an `ExcludeConstraint` over `(jurisdiction_id '=', tax_type_id '=', income_category_id '=', taxpayer_type '=', valid_period '&&')` using gist, named `no_overlap_domestic_rule`; `brackets` relationship.
  - `TaxBracket(id, domestic_tax_rule_id FK, lower_bound:Decimal, upper_bound:Decimal|None (NULL = ∞), rate:Decimal (percent), position:int)`.

- [ ] **Step 1: Write the failing test**

`tests/test_domestic_tax_rule.py`:
```python
from datetime import date

import pytest
from sqlalchemy import Range
from sqlalchemy.exc import IntegrityError

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import IncomeCategory, TaxType
from app.modules.source.models import SourceDocument, SourceEvidence
from app.modules.tax.models import DomesticTaxRule


def _seed_minimal(db_session):
    j = Jurisdiction(code="AE", name="United Arab Emirates")
    tt = TaxType(code="WHT_ROYALTY", name="WHT on royalties")
    ic = IncomeCategory(code="ROYALTY", name="Royalty")
    doc = SourceDocument(title="UAE CT Law", url="https://mof.gov.ae/corporate-tax/",
                         retrieved_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
                         content_hash="x")
    db_session.add_all([j, tt, ic, doc])
    db_session.flush()
    ev = SourceEvidence(document_id=doc.id, article="FDL 47", page=1,
                        quoted_text="0% WHT", review_status="human_verified")
    db_session.add(ev)
    db_session.flush()
    return j, tt, ic, ev


def test_create_rule_with_validity(db_session):
    j, tt, ic, ev = _seed_minimal(db_session)
    rule = DomesticTaxRule(
        jurisdiction_id=j.id, tax_type_id=tt.id, income_category_id=ic.id,
        taxpayer_type="any", rate=0, is_bracketed=False, source_evidence_id=ev.id,
        valid_period=Range(date(2023, 6, 1), None, bounds="[)"),
    )
    db_session.add(rule)
    db_session.flush()
    assert rule.id is not None


def test_overlapping_validity_is_rejected(db_session):
    j, tt, ic, ev = _seed_minimal(db_session)
    common = dict(jurisdiction_id=j.id, tax_type_id=tt.id, income_category_id=ic.id,
                  taxpayer_type="any", rate=0, is_bracketed=False, source_evidence_id=ev.id)
    db_session.add(DomesticTaxRule(**common, valid_period=Range(date(2023, 6, 1), None, bounds="[)")))
    db_session.flush()
    db_session.add(DomesticTaxRule(**common, valid_period=Range(date(2024, 1, 1), None, bounds="[)")))
    with pytest.raises(IntegrityError):
        db_session.flush()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_domestic_tax_rule.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the models**

`app/modules/tax/models.py`:
```python
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import DATERANGE, ExcludeConstraint, Range
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class DomesticTaxRule(Base):
    __tablename__ = "domestic_tax_rule"
    __table_args__ = (
        ExcludeConstraint(
            ("jurisdiction_id", "="),
            ("tax_type_id", "="),
            ("income_category_id", "="),
            ("taxpayer_type", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_domestic_rule",
        ),
        CheckConstraint("rate IS NULL OR (rate >= 0 AND rate <= 100)", name="rate_pct_range"),
        {"schema": "tax"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    jurisdiction_id: Mapped[int] = mapped_column(ForeignKey("core.jurisdiction.id"))
    tax_type_id: Mapped[int] = mapped_column(ForeignKey("core.tax_type.id"))
    income_category_id: Mapped[int] = mapped_column(ForeignKey("core.income_category.id"))
    taxpayer_type: Mapped[str] = mapped_column(String(16), default="any")
    rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    is_bracketed: Mapped[bool] = mapped_column(Boolean, default=False)
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))
    valid_period: Mapped[Range[date]] = mapped_column(DATERANGE)

    brackets: Mapped[list["TaxBracket"]] = relationship(
        back_populates="rule", order_by="TaxBracket.position"
    )


class TaxBracket(Base):
    __tablename__ = "tax_bracket"
    __table_args__ = {"schema": "tax"}

    id: Mapped[int] = mapped_column(primary_key=True)
    domestic_tax_rule_id: Mapped[int] = mapped_column(ForeignKey("tax.domestic_tax_rule.id"))
    lower_bound: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    upper_bound: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(6, 3))
    position: Mapped[int] = mapped_column(Integer)

    rule: Mapped[DomesticTaxRule] = relationship(back_populates="brackets")
```

> Note on ranges: `sqlalchemy.dialects.postgresql.Range` is the SQLAlchemy 2.0 range value object for psycopg3. If import or binding fails in this environment, report it (do not silently swap drivers); the fallback is `from sqlalchemy import Range` (top-level in SQLAlchemy 2.0.x). Use `bounds="[)"` (inclusive lower, exclusive upper) consistently everywhere in P1.

- [ ] **Step 4: Write the migration**

`migrations/versions/0006_tax_domestic_rule.py` (revision "0006", down_revision "0005"). It MUST:
1. `op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")` first.
2. Create `tax.domestic_tax_rule` with the columns above, the FKs, the `CheckConstraint` `rate_pct_range`, and the `ExcludeConstraint` (use `from sqlalchemy.dialects.postgresql import ExcludeConstraint` and pass it in `op.create_table(..., postgresql_...)` or add via `op.create_table` `*args`; simplest is to build the table with `sa.Column`s and include `postgresql.ExcludeConstraint(...)` plus `sa.CheckConstraint(...)` in the `op.create_table` constraint args, with `schema="tax"`).
3. Create `tax.tax_bracket` with its FK to `tax.domestic_tax_rule.id`.
4. `downgrade`: drop `tax_bracket` then `domestic_tax_rule` (leave the extension in place).

Add to `migrations/env.py`:
```python
from app.modules.tax import models as _tax_models  # noqa: F401
```

- [ ] **Step 5: Run tests + checks; commit**

Run: `uv run pytest tests/test_domestic_tax_rule.py -v` (both pass — the overlap test proves the exclusion constraint fires), then full suite + ruff + mypy clean.
```bash
git add app/modules/tax migrations/versions/0006_tax_domestic_rule.py migrations/env.py tests/test_domestic_tax_rule.py
git commit -m "feat: tax.domestic_tax_rule + tax_bracket with btree_gist no-overlap constraint"
```

---

### Task 3: `TaxRuleRepository` with as-of resolution + bracket helper

**Files:**
- Create: `app/modules/tax/repository.py`
- Test: `tests/test_tax_rule_repository.py`

**Interfaces:**
- Consumes: `DomesticTaxRule`, `TaxBracket` (Task 2), `ReferenceRepository` (Task 1), `core.Jurisdiction`.
- Produces:
  - `TaxRuleRepository(session)` with `get_rule(jurisdiction_code: str, tax_type_code: str, income_category_code: str, on_date: date, taxpayer_type: str = "any") -> DomesticTaxRule | None` — returns the rule whose `valid_period` contains `on_date`, else None.
  - `resolve_bracket_rate(rule: DomesticTaxRule, amount: Decimal) -> Decimal` — module-level function: for a bracketed rule returns the rate of the bracket containing `amount` (lower inclusive, upper exclusive; the open-ended top bracket has `upper_bound=None`); for a flat rule returns `rule.rate`. Raises `ValueError` if a bracketed rule has no bracket covering `amount`.

- [ ] **Step 1: Write the failing test**

`tests/test_tax_rule_repository.py`:
```python
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import Range

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import IncomeCategory, TaxType
from app.modules.source.models import SourceDocument, SourceEvidence
from app.modules.tax.models import DomesticTaxRule, TaxBracket
from app.modules.tax.repository import TaxRuleRepository, resolve_bracket_rate


def _evidence(db_session):
    doc = SourceDocument(title="d", url="https://x", retrieved_at=__import__("datetime").datetime.now(__import__("datetime").UTC), content_hash="h")
    db_session.add(doc); db_session.flush()
    ev = SourceEvidence(document_id=doc.id, quoted_text="q", review_status="human_verified")
    db_session.add(ev); db_session.flush()
    return ev


def test_as_of_resolution(db_session):
    ev = _evidence(db_session)
    ae = Jurisdiction(code="AE", name="UAE")
    tt = TaxType(code="WHT_ROYALTY", name="roy")
    ic = IncomeCategory(code="ROYALTY", name="Royalty")
    db_session.add_all([ae, tt, ic]); db_session.flush()
    db_session.add(DomesticTaxRule(
        jurisdiction_id=ae.id, tax_type_id=tt.id, income_category_id=ic.id,
        taxpayer_type="any", rate=Decimal("0"), is_bracketed=False, source_evidence_id=ev.id,
        valid_period=Range(date(2023, 6, 1), None, bounds="[)"),
    ))
    db_session.flush()
    repo = TaxRuleRepository(db_session)
    assert repo.get_rule("AE", "WHT_ROYALTY", "ROYALTY", date(2024, 1, 1)).rate == Decimal("0")
    assert repo.get_rule("AE", "WHT_ROYALTY", "ROYALTY", date(2023, 1, 1)) is None  # before validity


def test_bracket_resolution(db_session):
    ev = _evidence(db_session)
    ae = Jurisdiction(code="AE", name="UAE")
    tt = TaxType(code="CIT", name="cit")
    ic = IncomeCategory(code="CORPORATE_PROFIT", name="Corporate profit")
    db_session.add_all([ae, tt, ic]); db_session.flush()
    rule = DomesticTaxRule(
        jurisdiction_id=ae.id, tax_type_id=tt.id, income_category_id=ic.id,
        taxpayer_type="company", rate=None, is_bracketed=True, source_evidence_id=ev.id,
        valid_period=Range(date(2023, 6, 1), None, bounds="[)"),
    )
    rule.brackets = [
        TaxBracket(lower_bound=Decimal("0"), upper_bound=Decimal("375000"), rate=Decimal("0"), position=0),
        TaxBracket(lower_bound=Decimal("375000"), upper_bound=None, rate=Decimal("9"), position=1),
    ]
    db_session.add(rule); db_session.flush()
    assert resolve_bracket_rate(rule, Decimal("100000")) == Decimal("0")
    assert resolve_bracket_rate(rule, Decimal("375000")) == Decimal("9")   # boundary -> upper bracket
    assert resolve_bracket_rate(rule, Decimal("1000000")) == Decimal("9")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tax_rule_repository.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the repository + helper**

`app/modules/tax/repository.py`:
```python
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import IncomeCategory, TaxType
from app.modules.tax.models import DomesticTaxRule


class TaxRuleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_rule(
        self,
        jurisdiction_code: str,
        tax_type_code: str,
        income_category_code: str,
        on_date: date,
        taxpayer_type: str = "any",
    ) -> DomesticTaxRule | None:
        stmt = (
            select(DomesticTaxRule)
            .join(Jurisdiction, DomesticTaxRule.jurisdiction_id == Jurisdiction.id)
            .join(TaxType, DomesticTaxRule.tax_type_id == TaxType.id)
            .join(IncomeCategory, DomesticTaxRule.income_category_id == IncomeCategory.id)
            .where(
                Jurisdiction.code == jurisdiction_code,
                TaxType.code == tax_type_code,
                IncomeCategory.code == income_category_code,
                DomesticTaxRule.taxpayer_type == taxpayer_type,
                DomesticTaxRule.valid_period.contains(on_date),
            )
        )
        return self.session.scalar(stmt)


def resolve_bracket_rate(rule: DomesticTaxRule, amount: Decimal) -> Decimal:
    if not rule.is_bracketed:
        if rule.rate is None:
            raise ValueError("flat rule has no rate")
        return rule.rate
    for bracket in rule.brackets:
        upper_ok = bracket.upper_bound is None or amount < bracket.upper_bound
        if amount >= bracket.lower_bound and upper_ok:
            return bracket.rate
    raise ValueError(f"no bracket covers amount {amount}")
```

> Note: `DATERANGE.contains(on_date)` emits the PostgreSQL `@>` operator. If the column's comparator does not expose `.contains` in this SQLAlchemy version, use `DomesticTaxRule.valid_period.op("@>")(on_date)` and report the substitution.

- [ ] **Step 4: Run tests + checks; commit**

Run: `uv run pytest tests/test_tax_rule_repository.py -v` (PASS), then full suite + ruff + mypy clean.
```bash
git add app/modules/tax/repository.py tests/test_tax_rule_repository.py
git commit -m "feat: TaxRuleRepository as-of resolution + bracket rate helper"
```

---

### Task 4: `tax.holding_regime`

**Files:**
- Modify: `app/modules/tax/models.py` (add `HoldingRegime`), `app/modules/tax/repository.py` (add `HoldingRegimeRepository`)
- Create: `migrations/versions/0007_tax_holding_regime.py`
- Test: `tests/test_holding_regime.py`

**Interfaces:**
- Produces (schema `tax`):
  - `HoldingRegime(id, jurisdiction_id FK, participation_exemption_dividends:bool, participation_exemption_capgains:bool, min_holding_pct:Decimal|None, min_holding_period_months:int|None, subject_to_tax_condition:bool, notes:str|None, source_evidence_id FK NOT NULL, valid_period:DATERANGE)` with `ExcludeConstraint((jurisdiction_id '='),(valid_period '&&'), using gist, name='no_overlap_holding_regime')`.
  - `HoldingRegimeRepository(session).get(jurisdiction_code: str, on_date: date) -> HoldingRegime | None` (as-of).

- [ ] **Step 1: Write the failing test**

`tests/test_holding_regime.py`:
```python
from datetime import date

from sqlalchemy import Range

from app.modules.core.models import Jurisdiction
from app.modules.source.models import SourceDocument, SourceEvidence
from app.modules.tax.models import HoldingRegime
from app.modules.tax.repository import HoldingRegimeRepository


def test_holding_regime_as_of(db_session):
    doc = SourceDocument(title="FR CGI", url="https://bofip", retrieved_at=__import__("datetime").datetime.now(__import__("datetime").UTC), content_hash="h")
    fr = Jurisdiction(code="FR", name="France")
    db_session.add_all([doc, fr]); db_session.flush()
    ev = SourceEvidence(document_id=doc.id, quoted_text="régime mère-fille", review_status="human_verified")
    db_session.add(ev); db_session.flush()
    db_session.add(HoldingRegime(
        jurisdiction_id=fr.id, participation_exemption_dividends=True,
        participation_exemption_capgains=True, min_holding_pct=5, min_holding_period_months=24,
        subject_to_tax_condition=True, notes="régime mère-fille", source_evidence_id=ev.id,
        valid_period=Range(date(2020, 1, 1), None, bounds="[)"),
    ))
    db_session.flush()
    repo = HoldingRegimeRepository(db_session)
    got = repo.get("FR", date(2024, 1, 1))
    assert got is not None and got.participation_exemption_dividends is True
    assert repo.get("FR", date(2019, 1, 1)) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_holding_regime.py -v`
Expected: FAIL — `HoldingRegime` not defined.

- [ ] **Step 3: Add the model**

Append to `app/modules/tax/models.py`:
```python
class HoldingRegime(Base):
    __tablename__ = "holding_regime"
    __table_args__ = (
        ExcludeConstraint(
            ("jurisdiction_id", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_holding_regime",
        ),
        {"schema": "tax"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    jurisdiction_id: Mapped[int] = mapped_column(ForeignKey("core.jurisdiction.id"))
    participation_exemption_dividends: Mapped[bool] = mapped_column(Boolean, default=False)
    participation_exemption_capgains: Mapped[bool] = mapped_column(Boolean, default=False)
    min_holding_pct: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    min_holding_period_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subject_to_tax_condition: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))
    valid_period: Mapped[Range[date]] = mapped_column(DATERANGE)
```

- [ ] **Step 4: Add the repository method**

Append to `app/modules/tax/repository.py`:
```python
from app.modules.tax.models import HoldingRegime  # add to existing imports


class HoldingRegimeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, jurisdiction_code: str, on_date: date) -> HoldingRegime | None:
        stmt = (
            select(HoldingRegime)
            .join(Jurisdiction, HoldingRegime.jurisdiction_id == Jurisdiction.id)
            .where(
                Jurisdiction.code == jurisdiction_code,
                HoldingRegime.valid_period.contains(on_date),
            )
        )
        return self.session.scalar(stmt)
```

- [ ] **Step 5: Write migration + run + commit**

`migrations/versions/0007_tax_holding_regime.py` (revision "0007", down_revision "0006"): create `tax.holding_regime` with the columns above, FK to `core.jurisdiction` and `source.source_evidence`, and the `ExcludeConstraint` (btree_gist already created in 0006). downgrade drops the table.
Run focused test (PASS), full suite + ruff + mypy clean.
```bash
git add app/modules/tax/models.py app/modules/tax/repository.py migrations/versions/0007_tax_holding_regime.py tests/test_holding_regime.py
git commit -m "feat: tax.holding_regime with as-of repository"
```

---

### Task 5: Treaty core tables (`treaty`, `treaty_party`, `treaty_article`, `treaty_protocol`)

**Files:**
- Create: `app/modules/treaty/__init__.py`, `app/modules/treaty/models.py`
- Create: `migrations/versions/0008_treaty_core.py`
- Modify: `migrations/env.py`
- Test: `tests/test_treaty_core.py`

**Interfaces:**
- Produces (schema `treaty`):
  - `Treaty(id, name:str, signature_date:date, entry_into_force_date:date|None, source_evidence_id FK NOT NULL)`.
  - `TreatyParty(id, treaty_id FK, jurisdiction_id FK core.jurisdiction)`.
  - `TreatyArticle(id, treaty_id FK, article_category:str, article_ref:str)` — e.g. category "DIVIDENDS", ref "Article 8".
  - `TreatyProtocol(id, treaty_id FK, signature_date:date, entry_into_force_date:date|None, description:str, source_evidence_id FK NOT NULL)`.

- [ ] **Step 1: Write the failing test**

`tests/test_treaty_core.py`:
```python
from datetime import date

from app.modules.core.models import Jurisdiction
from app.modules.source.models import SourceDocument, SourceEvidence
from app.modules.treaty.models import Treaty, TreatyArticle, TreatyParty, TreatyProtocol


def _ev(db_session):
    doc = SourceDocument(title="FR-UAE treaty", url="https://impots", retrieved_at=__import__("datetime").datetime.now(__import__("datetime").UTC), content_hash="h")
    db_session.add(doc); db_session.flush()
    ev = SourceEvidence(document_id=doc.id, quoted_text="t", review_status="human_verified")
    db_session.add(ev); db_session.flush()
    return ev


def test_treaty_with_two_parties_and_article(db_session):
    ev = _ev(db_session)
    fr = Jurisdiction(code="FR", name="France")
    ae = Jurisdiction(code="AE", name="UAE")
    db_session.add_all([fr, ae]); db_session.flush()
    t = Treaty(name="France-UAE", signature_date=date(1989, 7, 19),
               entry_into_force_date=date(1990, 7, 1), source_evidence_id=ev.id)
    db_session.add(t); db_session.flush()
    db_session.add_all([
        TreatyParty(treaty_id=t.id, jurisdiction_id=fr.id),
        TreatyParty(treaty_id=t.id, jurisdiction_id=ae.id),
        TreatyArticle(treaty_id=t.id, article_category="DIVIDENDS", article_ref="Article 8"),
        TreatyProtocol(treaty_id=t.id, signature_date=date(1993, 12, 6),
                       entry_into_force_date=None, description="1993 amendment", source_evidence_id=ev.id),
    ])
    db_session.flush()
    assert len(t.parties) == 2
    assert t.articles[0].article_category == "DIVIDENDS"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_treaty_core.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the models**

`app/modules/treaty/models.py`:
```python
from datetime import date

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Treaty(Base):
    __tablename__ = "treaty"
    __table_args__ = {"schema": "treaty"}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    signature_date: Mapped[date] = mapped_column()
    entry_into_force_date: Mapped[date | None] = mapped_column(nullable=True)
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))

    parties: Mapped[list["TreatyParty"]] = relationship(back_populates="treaty")
    articles: Mapped[list["TreatyArticle"]] = relationship(back_populates="treaty")
    protocols: Mapped[list["TreatyProtocol"]] = relationship(back_populates="treaty")


class TreatyParty(Base):
    __tablename__ = "treaty_party"
    __table_args__ = {"schema": "treaty"}

    id: Mapped[int] = mapped_column(primary_key=True)
    treaty_id: Mapped[int] = mapped_column(ForeignKey("treaty.treaty.id"))
    jurisdiction_id: Mapped[int] = mapped_column(ForeignKey("core.jurisdiction.id"))

    treaty: Mapped[Treaty] = relationship(back_populates="parties")


class TreatyArticle(Base):
    __tablename__ = "treaty_article"
    __table_args__ = {"schema": "treaty"}

    id: Mapped[int] = mapped_column(primary_key=True)
    treaty_id: Mapped[int] = mapped_column(ForeignKey("treaty.treaty.id"))
    article_category: Mapped[str] = mapped_column(String(32))
    article_ref: Mapped[str] = mapped_column(String(50))

    treaty: Mapped[Treaty] = relationship(back_populates="articles")


class TreatyProtocol(Base):
    __tablename__ = "treaty_protocol"
    __table_args__ = {"schema": "treaty"}

    id: Mapped[int] = mapped_column(primary_key=True)
    treaty_id: Mapped[int] = mapped_column(ForeignKey("treaty.treaty.id"))
    signature_date: Mapped[date] = mapped_column()
    entry_into_force_date: Mapped[date | None] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(String(500))
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))

    treaty: Mapped[Treaty] = relationship(back_populates="protocols")
```

- [ ] **Step 4: Migration + env import**

`migrations/versions/0008_treaty_core.py` (revision "0008", down_revision "0007"): create the four tables under schema `treaty` with the FKs above; downgrade drops them in dependency order (party/article/protocol before treaty). Add to `migrations/env.py`:
```python
from app.modules.treaty import models as _treaty_models  # noqa: F401
```

- [ ] **Step 5: Run + commit**

Focused test PASS; full suite + ruff + mypy clean.
```bash
git add app/modules/treaty migrations/versions/0008_treaty_core.py migrations/env.py tests/test_treaty_core.py
git commit -m "feat: treaty core tables (treaty, party, article, protocol)"
```

---

### Task 6: `treaty.treaty_rate` + `TreatyRepository`

**Files:**
- Modify: `app/modules/treaty/models.py` (add `TreatyRate`)
- Create: `app/modules/treaty/repository.py`
- Create: `migrations/versions/0009_treaty_rate.py`
- Test: `tests/test_treaty_rate_repository.py`

**Interfaces:**
- Produces (schema `treaty`):
  - `TreatyRate(id, treaty_id FK, treaty_article_id FK, income_category_id FK core.income_category, max_rate:Decimal|None, exclusive_residence_taxation:bool, relief_mechanism:str|None CHECK in ('at_source','refund','credit'), beneficial_owner_required:bool, ownership_threshold:Decimal|None, source_evidence_id FK NOT NULL, valid_period:DATERANGE)` with `ExcludeConstraint((treaty_id '='),(income_category_id '='),(valid_period '&&'), using gist, name='no_overlap_treaty_rate')`.
  - `TreatyRepository(session)` with:
    - `find_by_parties(code_a: str, code_b: str) -> Treaty | None` — order-independent (both parties present).
    - `get_rate(treaty_id: int, income_category_code: str, on_date: date) -> TreatyRate | None` (as-of).
    - `get_article(treaty_id: int, article_category: str) -> TreatyArticle | None`.

- [ ] **Step 1: Write the failing test**

`tests/test_treaty_rate_repository.py`:
```python
from datetime import date
from decimal import Decimal

from sqlalchemy import Range

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import IncomeCategory
from app.modules.source.models import SourceDocument, SourceEvidence
from app.modules.treaty.models import Treaty, TreatyArticle, TreatyParty, TreatyRate
from app.modules.treaty.repository import TreatyRepository


def _setup(db_session):
    doc = SourceDocument(title="t", url="https://impots", retrieved_at=__import__("datetime").datetime.now(__import__("datetime").UTC), content_hash="h")
    fr = Jurisdiction(code="FR", name="France"); ae = Jurisdiction(code="AE", name="UAE")
    ic = IncomeCategory(code="DIVIDEND", name="Dividend")
    db_session.add_all([doc, fr, ae, ic]); db_session.flush()
    ev = SourceEvidence(document_id=doc.id, quoted_text="art 8", review_status="human_verified")
    db_session.add(ev); db_session.flush()
    t = Treaty(name="France-UAE", signature_date=date(1989, 7, 19), source_evidence_id=ev.id)
    db_session.add(t); db_session.flush()
    art = TreatyArticle(treaty_id=t.id, article_category="DIVIDENDS", article_ref="Article 8")
    db_session.add_all([art, TreatyParty(treaty_id=t.id, jurisdiction_id=fr.id),
                        TreatyParty(treaty_id=t.id, jurisdiction_id=ae.id)])
    db_session.flush()
    db_session.add(TreatyRate(
        treaty_id=t.id, treaty_article_id=art.id, income_category_id=ic.id,
        max_rate=Decimal("0"), exclusive_residence_taxation=True, relief_mechanism="refund",
        beneficial_owner_required=True, ownership_threshold=None, source_evidence_id=ev.id,
        valid_period=Range(date(1994, 1, 1), None, bounds="[)"),
    ))
    db_session.flush()
    return t


def test_find_by_parties_is_order_independent(db_session):
    t = _setup(db_session)
    repo = TreatyRepository(db_session)
    assert repo.find_by_parties("FR", "AE").id == t.id
    assert repo.find_by_parties("AE", "FR").id == t.id


def test_get_rate_as_of_and_article(db_session):
    t = _setup(db_session)
    repo = TreatyRepository(db_session)
    rate = repo.get_rate(t.id, "DIVIDEND", date(2024, 1, 1))
    assert rate.exclusive_residence_taxation is True
    assert rate.relief_mechanism == "refund"
    assert repo.get_rate(t.id, "DIVIDEND", date(1990, 1, 1)) is None  # before protocol validity
    assert repo.get_article(t.id, "DIVIDENDS").article_ref == "Article 8"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_treaty_rate_repository.py -v`
Expected: FAIL — `TreatyRate`/`TreatyRepository` missing.

- [ ] **Step 3: Add the model**

Append to `app/modules/treaty/models.py` (extend imports with `CheckConstraint`, `Numeric`, `Boolean`, and the postgresql `DATERANGE`, `ExcludeConstraint`, `Range`; add `from decimal import Decimal`):
```python
class TreatyRate(Base):
    __tablename__ = "treaty_rate"
    __table_args__ = (
        ExcludeConstraint(
            ("treaty_id", "="),
            ("income_category_id", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_treaty_rate",
        ),
        CheckConstraint(
            "relief_mechanism IS NULL OR relief_mechanism IN ('at_source','refund','credit')",
            name="relief_mechanism_enum",
        ),
        CheckConstraint("max_rate IS NULL OR (max_rate >= 0 AND max_rate <= 100)", name="treaty_rate_pct_range"),
        {"schema": "treaty"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    treaty_id: Mapped[int] = mapped_column(ForeignKey("treaty.treaty.id"))
    treaty_article_id: Mapped[int] = mapped_column(ForeignKey("treaty.treaty_article.id"))
    income_category_id: Mapped[int] = mapped_column(ForeignKey("core.income_category.id"))
    max_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    exclusive_residence_taxation: Mapped[bool] = mapped_column(Boolean, default=False)
    relief_mechanism: Mapped[str | None] = mapped_column(String(16), nullable=True)
    beneficial_owner_required: Mapped[bool] = mapped_column(Boolean, default=False)
    ownership_threshold: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))
    valid_period: Mapped[Range[date]] = mapped_column(DATERANGE)
```

- [ ] **Step 4: Write the repository**

`app/modules/treaty/repository.py`:
```python
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import IncomeCategory
from app.modules.treaty.models import Treaty, TreatyArticle, TreatyParty, TreatyRate


class TreatyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_by_parties(self, code_a: str, code_b: str) -> Treaty | None:
        stmt = (
            select(Treaty)
            .where(
                Treaty.id.in_(
                    select(TreatyParty.treaty_id)
                    .join(Jurisdiction, TreatyParty.jurisdiction_id == Jurisdiction.id)
                    .where(Jurisdiction.code == code_a)
                ),
                Treaty.id.in_(
                    select(TreatyParty.treaty_id)
                    .join(Jurisdiction, TreatyParty.jurisdiction_id == Jurisdiction.id)
                    .where(Jurisdiction.code == code_b)
                ),
            )
        )
        return self.session.scalar(stmt)

    def get_rate(self, treaty_id: int, income_category_code: str, on_date: date) -> TreatyRate | None:
        stmt = (
            select(TreatyRate)
            .join(IncomeCategory, TreatyRate.income_category_id == IncomeCategory.id)
            .where(
                TreatyRate.treaty_id == treaty_id,
                IncomeCategory.code == income_category_code,
                TreatyRate.valid_period.contains(on_date),
            )
        )
        return self.session.scalar(stmt)

    def get_article(self, treaty_id: int, article_category: str) -> TreatyArticle | None:
        stmt = select(TreatyArticle).where(
            TreatyArticle.treaty_id == treaty_id,
            TreatyArticle.article_category == article_category,
        )
        return self.session.scalar(stmt)
```

- [ ] **Step 5: Migration + run + commit**

`migrations/versions/0009_treaty_rate.py` (revision "0009", down_revision "0008"): create `treaty.treaty_rate` with the columns, FKs, both `CheckConstraint`s, and the `ExcludeConstraint`. downgrade drops it.
Focused test PASS; full suite + ruff + mypy clean.
```bash
git add app/modules/treaty/models.py app/modules/treaty/repository.py migrations/versions/0009_treaty_rate.py tests/test_treaty_rate_repository.py
git commit -m "feat: treaty.treaty_rate + TreatyRepository (find-by-parties, as-of rate, article-by-category)"
```

---

### Task 7: France–UAE golden fixture seed

**Files:**
- Create: `app/modules/seed/__init__.py`, `app/modules/seed/sources.py`, `app/modules/seed/france_uae.py`, `app/cli.py`
- Test: `tests/test_seed_france_uae.py`

**Interfaces:**
- Consumes: all repositories and models above.
- Produces:
  - `app.modules.seed.sources.upsert_source(session, *, title, url, retrieved_at, content_hash, article, quoted_text, review_status="human_verified") -> SourceEvidence` — creates the document+evidence and returns the evidence row.
  - `app.modules.seed.france_uae.seed(session) -> None` — idempotent: seeds jurisdictions FR/AE, currencies EUR/AED, tax types, income categories, the verified domestic rules, UAE CIT brackets, one FR holding regime, and the France–UAE treaty with its 1993 protocol, article, and dividend rate. Re-running does not duplicate (guard via code lookups / get_or_create).
  - `app/cli.py`: `python -m app.cli seed-france-uae` opens a real `SessionLocal`, runs `seed`, commits.

**Verified figures to seed (each with the cited source — verify against the source before marking done):**

| Row | Value | Valid from | Source |
|---|---|---|---|
| UAE WHT dividend/interest/royalty | **0%** | 2023-06-01 | UAE Corporate Tax Law (FDL No. 47) — mof.gov.ae; PwC UAE WHT |
| UAE CIT | brackets **0%** ≤ AED 375,000, **9%** above | 2023-06-01 | FDL No. 47; mof.gov.ae/corporate-tax |
| France WHT dividend (company) | **25%** | 2023-01-01 | CGI art. 119 bis 2 / 187; PwC France WHT |
| France WHT royalty | **25%** | 2023-01-01 | CGI art. 182 B / 219 |
| France WHT interest | **0%** | 2023-01-01 | CGI (interest to non-residents exempt since 2018, ETNC excepted) |
| FR holding (régime mère-fille) | participation exemption dividends+capgains, min 5%, 24 months | 2020-01-01 | CGI art. 145 / 216 |
| France–UAE treaty | signed 1989-07-19; 1993-12-06 protocol | — | impots.gouv.fr treaty PDF |
| Treaty dividends | Article 8; exclusive residence taxation; max_rate 0; relief_mechanism **refund**; beneficial_owner_required true | 1994-01-01 | impots.gouv.fr; Art. 119 bis A II (2026 refund mechanism) |

- [ ] **Step 1: Write the failing test**

`tests/test_seed_france_uae.py`:
```python
from datetime import date
from decimal import Decimal

from app.modules.seed.france_uae import seed
from app.modules.tax.repository import TaxRuleRepository, resolve_bracket_rate
from app.modules.treaty.repository import TreatyRepository


def test_seed_is_idempotent_and_resolves(db_session):
    seed(db_session)
    seed(db_session)  # second run must not duplicate or error
    db_session.flush()

    tax = TaxRuleRepository(db_session)
    # UAE 0% WHT royalty
    assert tax.get_rule("AE", "WHT_ROYALTY", "ROYALTY", date(2024, 1, 1)).rate == Decimal("0")
    # France 25% company dividend WHT
    fr_div = tax.get_rule("FR", "WHT_DIVIDEND", "DIVIDEND", date(2024, 1, 1), taxpayer_type="company")
    assert fr_div.rate == Decimal("25")
    # UAE CIT brackets
    cit = tax.get_rule("AE", "CIT", "CORPORATE_PROFIT", date(2024, 1, 1), taxpayer_type="company")
    assert resolve_bracket_rate(cit, Decimal("100000")) == Decimal("0")
    assert resolve_bracket_rate(cit, Decimal("1000000")) == Decimal("9")

    treaty = TreatyRepository(db_session)
    t = treaty.find_by_parties("FR", "AE")
    assert t is not None
    rate = treaty.get_rate(t.id, "DIVIDEND", date(2024, 1, 1))
    assert rate.exclusive_residence_taxation is True and rate.relief_mechanism == "refund"
    assert treaty.get_article(t.id, "DIVIDENDS").article_ref == "Article 8"


def test_every_seeded_figure_has_evidence(db_session):
    seed(db_session)
    db_session.flush()
    from app.modules.tax.models import DomesticTaxRule, HoldingRegime
    from app.modules.treaty.models import TreatyRate
    for model in (DomesticTaxRule, HoldingRegime, TreatyRate):
        rows = db_session.query(model).all()
        assert rows, f"no {model.__name__} rows seeded"
        assert all(r.source_evidence_id is not None for r in rows)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_seed_france_uae.py -v`
Expected: FAIL — seed module missing.

- [ ] **Step 3: Implement `sources.py`**

`app/modules/seed/sources.py`:
```python
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.source.models import SourceDocument, SourceEvidence


def upsert_source(
    session: Session,
    *,
    title: str,
    url: str,
    retrieved_at: datetime,
    content_hash: str,
    article: str | None,
    quoted_text: str,
    review_status: str = "human_verified",
) -> SourceEvidence:
    doc = session.scalar(select(SourceDocument).where(SourceDocument.url == url))
    if doc is None:
        doc = SourceDocument(title=title, url=url, retrieved_at=retrieved_at, content_hash=content_hash)
        session.add(doc)
        session.flush()
    ev = session.scalar(
        select(SourceEvidence).where(
            SourceEvidence.document_id == doc.id, SourceEvidence.quoted_text == quoted_text
        )
    )
    if ev is None:
        ev = SourceEvidence(
            document_id=doc.id, article=article, quoted_text=quoted_text, review_status=review_status
        )
        session.add(ev)
        session.flush()
    return ev
```

- [ ] **Step 4: Implement `france_uae.py`**

`app/modules/seed/france_uae.py` — idempotent seeding using `ReferenceRepository.get_or_create_*`, a `get_or_create` for `Jurisdiction` by code, `upsert_source`, and existence guards before inserting rules/treaty (look up by the logical key; skip if a row already covers the period). Seed exactly the rows in the "Verified figures" table above, each pointing at the matching `upsert_source(...)` evidence. Use `Range(date(...), None, bounds="[)")` for every `valid_period`. (Full code is substantial; the implementer writes it from this spec and the table, mirroring the test's expectations. Every `rate`/`max_rate` is a `Decimal`. `retrieved_at` uses `datetime.now(datetime.UTC)` or a fixed date; `content_hash` may be a short placeholder string for the fixture.)

> Idempotency rule: before inserting a `DomesticTaxRule`, query for an existing rule with the same (jurisdiction, tax_type, income_category, taxpayer_type) whose `valid_period` contains the new lower bound; if present, skip. Same pattern for `HoldingRegime` (jurisdiction) and `TreatyRate` (treaty, income_category). For the `Treaty` itself, look up by `find_by_parties("FR","AE")`; create only if absent.

- [ ] **Step 5: Implement the CLI**

`app/cli.py`:
```python
import sys

from app.db import SessionLocal
from app.modules.seed.france_uae import seed


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] != "seed-france-uae":
        print("usage: python -m app.cli seed-france-uae", file=sys.stderr)
        return 2
    session = SessionLocal()
    try:
        seed(session)
        session.commit()
    finally:
        session.close()
    print("seeded France-UAE fixture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 6: Run tests + checks; commit**

Run: `uv run pytest tests/test_seed_france_uae.py -v` (PASS), full suite + ruff + mypy clean. Then prove the CLI runs against the live db:
```bash
docker compose up -d db
uv run alembic upgrade head
uv run python -m app.cli seed-france-uae   # prints "seeded France-UAE fixture"
uv run python -m app.cli seed-france-uae   # idempotent: runs again cleanly
```
```bash
git add app/modules/seed app/cli.py tests/test_seed_france_uae.py
git commit -m "feat: verified France-UAE golden fixture seed + CLI"
```

---

### Task 8: Data-quality checks

**Files:**
- Create: `app/modules/seed/quality.py`
- Test: `tests/test_data_quality.py`

**Interfaces:**
- Produces: `app.modules.seed.quality.run_checks(session) -> list[str]` — returns a list of human-readable violation strings (empty = healthy). Checks:
  1. every `Treaty` has ≥ 2 `TreatyParty` rows;
  2. every `DomesticTaxRule`, `HoldingRegime`, `TreatyRate`, `Treaty`, `TreatyProtocol` has a non-null `source_evidence_id` (schema already enforces, but the check documents the invariant and catches future nullable regressions);
  3. every flat `DomesticTaxRule` has a `rate`; every bracketed one has ≥ 1 `TaxBracket`;
  4. every `TreatyRate.relief_mechanism` is null or in the allowed set.

- [ ] **Step 1: Write the failing test**

`tests/test_data_quality.py`:
```python
from app.modules.seed.france_uae import seed
from app.modules.seed.quality import run_checks


def test_seeded_fixture_passes_quality_checks(db_session):
    seed(db_session)
    db_session.flush()
    violations = run_checks(db_session)
    assert violations == [], violations


def test_treaty_without_two_parties_is_flagged(db_session):
    from datetime import date

    from app.modules.source.models import SourceDocument, SourceEvidence
    from app.modules.treaty.models import Treaty, TreatyParty
    from app.modules.core.models import Jurisdiction
    doc = SourceDocument(title="t", url="https://x", retrieved_at=__import__("datetime").datetime.now(__import__("datetime").UTC), content_hash="h")
    fr = Jurisdiction(code="FR", name="France")
    db_session.add_all([doc, fr]); db_session.flush()
    ev = SourceEvidence(document_id=doc.id, quoted_text="q", review_status="human_verified")
    db_session.add(ev); db_session.flush()
    t = Treaty(name="lonely", signature_date=date(2000, 1, 1), source_evidence_id=ev.id)
    db_session.add(t); db_session.flush()
    db_session.add(TreatyParty(treaty_id=t.id, jurisdiction_id=fr.id))  # only one party
    db_session.flush()
    violations = run_checks(db_session)
    assert any("party" in v.lower() for v in violations)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_data_quality.py -v`
Expected: FAIL — module missing.

- [ ] **Step 3: Implement `quality.py`**

`app/modules/seed/quality.py`:
```python
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.tax.models import DomesticTaxRule
from app.modules.treaty.models import Treaty, TreatyParty, TreatyRate


def run_checks(session: Session) -> list[str]:
    violations: list[str] = []

    # 1. treaties need >= 2 parties
    for treaty in session.scalars(select(Treaty)):
        count = session.scalar(
            select(func.count()).select_from(TreatyParty).where(TreatyParty.treaty_id == treaty.id)
        )
        if (count or 0) < 2:
            violations.append(f"treaty {treaty.id} ({treaty.name}) has {count} party rows (< 2)")

    # 3. flat rules need a rate; bracketed rules need brackets
    for rule in session.scalars(select(DomesticTaxRule)):
        if rule.is_bracketed and not rule.brackets:
            violations.append(f"bracketed domestic_tax_rule {rule.id} has no brackets")
        if not rule.is_bracketed and rule.rate is None:
            violations.append(f"flat domestic_tax_rule {rule.id} has no rate")

    # 4. relief_mechanism within the allowed set
    allowed = {None, "at_source", "refund", "credit"}
    for tr in session.scalars(select(TreatyRate)):
        if tr.relief_mechanism not in allowed:
            violations.append(f"treaty_rate {tr.id} has invalid relief_mechanism {tr.relief_mechanism!r}")

    return violations
```

> Check 2 (source_evidence non-null) is enforced by NOT NULL columns; `run_checks` does not need to re-scan it, but note in a comment that the invariant lives in the schema.

- [ ] **Step 4: Run tests + checks; commit**

Focused test PASS; full suite + ruff + mypy clean.
```bash
git add app/modules/seed/quality.py tests/test_data_quality.py
git commit -m "feat: data-quality checks (>=2 treaty parties, rate/bracket integrity, relief enum)"
```

---

## Self-Review

**1. Spec coverage (P1 slice):**
- `holding_regime` (participation exemption + conditions) → Task 4 ✅ (spec §3 Factor 1, §4)
- Versioned `tax`/`treaty` tables + `btree_gist` exclusion constraints → Tasks 2,4,6 ✅ (spec §4, §6)
- `treaty_party`, `treaty_article` (join on category), `treaty_protocol`, `treaty_rate` with `relief_mechanism`/`exclusive_residence_taxation`/`beneficial_owner_required`/`ownership_threshold` → Tasks 5,6 ✅ (spec §2 ER, review §2–3)
- Every figure sourced (`source_evidence_id` NOT NULL) → Tasks 2,4,5,6 + Task 8 check ✅ (spec core principle)
- Verified France–UAE fixture → Task 7 ✅ (spec §9 P1, review §2)
- As-of reads (bitemporal valid time) → Tasks 3,4,6 ✅ (spec §6)
- Data-quality rules → Task 8 ✅ (spec §7)
- Deferred to later phases (correctly absent): `mli_position` + MLI matching and `treaty_applicability` nuance (P3 engine territory), multi-source M2M evidence, lists/`regulatory_consequence` (P2), the `min(domestic,treaty)` decision engine + Flow/Scoring (P3), `cfc_rule`/`substance_rule` depth (P1 seeds one holding regime; substance bands are P3/P4).

**2. Placeholder scan:** Task 7 Step 4 describes the seed module from an explicit figures table + idempotency rule rather than pasting ~150 lines; every other code step is literal. The seed's expected *outputs* are pinned by Task 7's test, so the implementation is constrained, not open-ended. No "TBD/TODO".

**3. Type consistency:** `valid_period: Range[date]` + `bounds="[)"` used identically across Tasks 2/4/6/7. Repo signatures (`get_rule`, `resolve_bracket_rate`, `find_by_parties`, `get_rate`, `get_article`, `HoldingRegimeRepository.get`) match between definition and use in Tasks 3/4/6/7/8. `source_evidence_id` spelled consistently. `relief_mechanism` allowed set identical in model CHECK (Task 6) and quality check (Task 8).

**4. Review Focus coverage:**
- Overlapping validity rejected → Task 2 `test_overlapping_validity_is_rejected` ✅
- As-of outside validity → `None` → Task 3 `test_as_of_resolution`, Task 6 `test_get_rate_as_of_and_article` ✅
- No figure without source → NOT NULL columns + Task 7 `test_every_seeded_figure_has_evidence` + Task 8 ✅
- Treaty lookup party-order-independent → Task 6 `test_find_by_parties_is_order_independent` ✅
- Bracket boundary (exactly 375,000) → Task 3 `test_bracket_resolution` ✅

---

## Known-fiddly areas for implementers (report, don't paper over)

- **PostgreSQL range types** (`DATERANGE`, `Range`, `bounds`, the `@>`/`&&` operators) and **`ExcludeConstraint`** in both models and Alembic are the highest-risk spots. If an import path or operator differs in the installed SQLAlchemy/psycopg versions, report the exact error and the substitution you made (the plan notes the known fallbacks). The overlap-rejection and as-of tests are the proof these work.
- The `btree_gist` extension must be created (migration 0006) before any gist exclusion constraint over scalar `=` columns.

## Next plans (not in this document)
P2 lists & review (EU/FATF/EU-AML/ETNC/Global Forum + `regulatory_consequence` precedence), then P3 engines (Tax/Treaty/Flow/Risk composing `min(domestic,treaty)` + MLI), P4 scoring, P5 UI, P6 LLM, P7 SaaS hardening, P8 scale.
