# P2 Lists & Regulatory Consequences Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the versioned, source-backed data layer for tax-governance and AML/CFT **lists** (EU tax list, FATF grey/black, EU AML high-risk, Global Forum ratings, France ETNC) and the **regulatory consequences** a jurisdiction imposes from them — bitemporal, exclusion-constrained, with as-of repositories, seeded for the FR/UAE corridor with verified historical memberships.

**Architecture:** Extends the P0/P1 modular monolith. New tables under the `risk` schema (created empty in P0). Each list membership and consequence carries a `valid_period daterange` (valid time) and a mandatory `source_evidence_id`. Repositories expose as-of reads only — *applying* a consequence to override a treaty/domestic rate (consequence precedence) is the **P3 Risk engine**, out of scope here.

**Tech Stack:** Python 3.12 · FastAPI · SQLAlchemy 2.0 sync + psycopg3 · Alembic · PostgreSQL 16 (`btree_gist`, `daterange`, `ExcludeConstraint`) · pytest · ruff · mypy.

**Spec:** `docs/superpowers/specs/2026-10-04-tax-jurisdiction-recommender-design.md`

## Global Constraints

- Python **3.12**; uv; SQLAlchemy **2.0 sync**; psycopg v3; Alembic. Migrations continue the chain from **0009** (next is **0010**).
- New tables under schema `risk` (created in P0 migration 0001). `btree_gist` extension already created in P1 migration 0006.
- **Range value type** imports from `sqlalchemy.dialects.postgresql` — `from sqlalchemy.dialects.postgresql import DATERANGE, ExcludeConstraint, Range`. There is NO top-level `sqlalchemy.Range` in this project's SQLAlchemy (2.1.x). Use `Range(date(...), None, bounds="[)")` everywhere.
- **Bitemporal:** every `list_membership` and `regulatory_consequence` row has `valid_period daterange NOT NULL`; overlaps for the same logical key are rejected by a `btree_gist` `ExcludeConstraint`.
- **Source-backing:** every `list_membership` and `regulatory_consequence` row has a **NOT NULL** `source_evidence_id` FK → `source.source_evidence`. (`list_definition` also carries one for the list's authority document.)
- `ruff check` + `mypy app` clean; `pytest` clean. No committed bytecode (`.gitignore` covers `__pycache__`, `*.pyc`, `.DS_Store`).
- Rates `Numeric(6,3)`, 0–100.
- Seeded figures must match the verified table in Task 5; each cites an official source.
- The list families are kept distinct (spec §3): tax-governance (EU tax list, Global Forum, France ETNC) vs AML/CFT (FATF, EU AML). `family` column records which.

## Review Focus

- **As-of membership query when the jurisdiction's listing has expired** (e.g. UAE FATF grey after 2024-02-23) → returns not-listed, not a stale hit. (Task 3 tests.)
- **Overlapping membership of the same jurisdiction on the same list** → rejected by the exclusion constraint at write time. (Task 2 tests.)
- **A membership or consequence row without a source** → impossible: `source_evidence_id` NOT NULL + FK. (Tasks 2/4 schema + tests.)
- **The same jurisdiction listed on two different lists at once** (e.g. a jurisdiction on both FATF grey and EU AML) → both returned by `lists_for`, independently. (Task 3 tests.)
- **A consequence keyed to a classification tier** (ETNC full-measures vs certain-measures) → `consequences_triggered_by(list, classification, date)` returns only the matching tier. (Task 4 tests.)

---

## File Structure

```
app/modules/risk/__init__.py
app/modules/risk/models.py          # ListDefinition, ListMembership, RegulatoryConsequence
app/modules/risk/repository.py      # ListRepository, ConsequenceRepository
app/modules/seed/lists.py           # verified FR/UAE-corridor list memberships + ETNC consequence
migrations/versions/0010_risk_list_definition.py
migrations/versions/0011_risk_list_membership.py
migrations/versions/0012_risk_regulatory_consequence.py
tests/test_list_definition.py
tests/test_list_membership.py
tests/test_list_repository.py
tests/test_regulatory_consequence.py
tests/test_seed_lists.py
tests/test_data_quality_lists.py
```

Each model-adding task appends its module to `migrations/env.py` the first time (`from app.modules.risk import models as _risk_models  # noqa: F401`). Tasks 2 and 4 add models to the SAME `risk/models.py` created in Task 1, so only Task 1 edits `env.py`.

---

### Task 1: `risk.list_definition`

**Files:**
- Create: `app/modules/risk/__init__.py`, `app/modules/risk/models.py`, `app/modules/risk/repository.py`
- Create: `migrations/versions/0010_risk_list_definition.py`
- Modify: `migrations/env.py`
- Test: `tests/test_list_definition.py`

**Interfaces:**
- Consumes: `app.db.Base`, `source.SourceEvidence`, `db_session`.
- Produces (schema `risk`):
  - `ListDefinition(id, code:str unique, name:str, family:str ('tax_governance'|'aml_cft'), publisher:str, update_cadence:str|None, source_evidence_id FK source.source_evidence NOT NULL)`.
  - `ListDefinitionRepository(session)` with `get(code)->ListDefinition|None`, `get_or_create(code, *, name, family, publisher, update_cadence, source_evidence_id)->ListDefinition` (idempotent by code).

- [ ] **Step 1: Write the failing test**

`tests/test_list_definition.py`:
```python
from datetime import UTC, datetime

from app.modules.risk.models import ListDefinition
from app.modules.risk.repository import ListDefinitionRepository
from app.modules.source.models import SourceDocument, SourceEvidence


def _evidence(db_session):
    doc = SourceDocument(title="FATF", url="https://fatf-gafi.org", retrieved_at=datetime.now(UTC), content_hash="h")
    db_session.add(doc); db_session.flush()
    ev = SourceEvidence(document_id=doc.id, quoted_text="increased monitoring", review_status="human_verified")
    db_session.add(ev); db_session.flush()
    return ev


def test_create_and_lookup(db_session):
    ev = _evidence(db_session)
    repo = ListDefinitionRepository(db_session)
    created = repo.get_or_create(
        "FATF_GREY", name="FATF jurisdictions under increased monitoring",
        family="aml_cft", publisher="FATF", update_cadence="after each plenary", source_evidence_id=ev.id,
    )
    db_session.flush()
    assert created.id is not None
    assert repo.get("FATF_GREY").family == "aml_cft"
    assert repo.get("NOPE") is None


def test_get_or_create_idempotent(db_session):
    ev = _evidence(db_session)
    repo = ListDefinitionRepository(db_session)
    a = repo.get_or_create("EU_TAX_ANNEX_I", name="EU Annex I", family="tax_governance",
                           publisher="Council of the EU", update_cadence="twice a year", source_evidence_id=ev.id)
    db_session.flush()
    b = repo.get_or_create("EU_TAX_ANNEX_I", name="EU Annex I", family="tax_governance",
                           publisher="Council of the EU", update_cadence="twice a year", source_evidence_id=ev.id)
    db_session.flush()
    assert a.id == b.id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_list_definition.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the model**

`app/modules/risk/models.py`:
```python
from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ListDefinition(Base):
    __tablename__ = "list_definition"
    __table_args__ = (
        CheckConstraint("family IN ('tax_governance', 'aml_cft')", name="list_family_enum"),
        {"schema": "risk"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(48), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    family: Mapped[str] = mapped_column(String(16))
    publisher: Mapped[str] = mapped_column(String(120))
    update_cadence: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))
```

- [ ] **Step 4: Write the repository**

`app/modules/risk/repository.py`:
```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.risk.models import ListDefinition


class ListDefinitionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, code: str) -> ListDefinition | None:
        return self.session.scalar(select(ListDefinition).where(ListDefinition.code == code))

    def get_or_create(
        self,
        code: str,
        *,
        name: str,
        family: str,
        publisher: str,
        update_cadence: str | None,
        source_evidence_id: int,
    ) -> ListDefinition:
        row = self.get(code)
        if row is None:
            row = ListDefinition(
                code=code, name=name, family=family, publisher=publisher,
                update_cadence=update_cadence, source_evidence_id=source_evidence_id,
            )
            self.session.add(row)
        return row
```

- [ ] **Step 5: Migration + env import**

`migrations/versions/0010_risk_list_definition.py` (revision "0010", down_revision "0009"): create `risk.list_definition` with the columns, the FK, the unique `code`, and the `list_family_enum` CheckConstraint. downgrade drops the table. Add to `migrations/env.py`:
```python
from app.modules.risk import models as _risk_models  # noqa: F401
```

- [ ] **Step 6: Run + commit**

Focused test PASS; full suite + ruff + mypy clean.
```bash
git add app/modules/risk migrations/versions/0010_risk_list_definition.py migrations/env.py tests/test_list_definition.py
git commit -m "feat: risk.list_definition + repository"
```

---

### Task 2: `risk.list_membership` with exclusion constraint

**Files:**
- Modify: `app/modules/risk/models.py` (add `ListMembership`)
- Create: `migrations/versions/0011_risk_list_membership.py`
- Test: `tests/test_list_membership.py`

**Interfaces:**
- Produces (schema `risk`):
  - `ListMembership(id, list_definition_id FK risk.list_definition, jurisdiction_id FK core.jurisdiction, classification:str, announcement_date:date|None, status:str default 'active', source_evidence_id FK NOT NULL, valid_period DATERANGE)` with `ExcludeConstraint((list_definition_id '='),(jurisdiction_id '='),(valid_period '&&'), using gist, name='no_overlap_list_membership')`.

- [ ] **Step 1: Write the failing test**

`tests/test_list_membership.py`:
```python
from datetime import UTC, date, datetime

import pytest
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.exc import IntegrityError

from app.modules.core.models import Jurisdiction
from app.modules.risk.models import ListDefinition, ListMembership
from app.modules.source.models import SourceDocument, SourceEvidence


def _setup(db_session):
    doc = SourceDocument(title="FATF", url="https://fatf-gafi.org", retrieved_at=datetime.now(UTC), content_hash="h")
    ae = Jurisdiction(code="AE", name="UAE")
    db_session.add_all([doc, ae]); db_session.flush()
    ev = SourceEvidence(document_id=doc.id, quoted_text="grey", review_status="human_verified")
    db_session.add(ev); db_session.flush()
    ld = ListDefinition(code="FATF_GREY", name="grey", family="aml_cft", publisher="FATF",
                        update_cadence=None, source_evidence_id=ev.id)
    db_session.add(ld); db_session.flush()
    return ae, ld, ev


def test_create_membership(db_session):
    ae, ld, ev = _setup(db_session)
    m = ListMembership(
        list_definition_id=ld.id, jurisdiction_id=ae.id, classification="increased_monitoring",
        announcement_date=date(2022, 3, 4), status="active", source_evidence_id=ev.id,
        valid_period=Range(date(2022, 3, 4), date(2024, 2, 23), bounds="[)"),
    )
    db_session.add(m); db_session.flush()
    assert m.id is not None


def test_overlapping_membership_rejected(db_session):
    ae, ld, ev = _setup(db_session)
    common = dict(list_definition_id=ld.id, jurisdiction_id=ae.id, classification="increased_monitoring",
                  status="active", source_evidence_id=ev.id)
    db_session.add(ListMembership(**common, valid_period=Range(date(2022, 3, 4), None, bounds="[)")))
    db_session.flush()
    db_session.add(ListMembership(**common, valid_period=Range(date(2023, 1, 1), None, bounds="[)")))
    with pytest.raises(IntegrityError):
        db_session.flush()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_list_membership.py -v`
Expected: FAIL — `ListMembership` not defined.

- [ ] **Step 3: Add the model**

Append to `app/modules/risk/models.py` (extend imports to add `from datetime import date`; `Boolean` not needed; add `from sqlalchemy.dialects.postgresql import DATERANGE, ExcludeConstraint, Range`):
```python
class ListMembership(Base):
    __tablename__ = "list_membership"
    __table_args__ = (
        ExcludeConstraint(
            ("list_definition_id", "="),
            ("jurisdiction_id", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_list_membership",
        ),
        {"schema": "risk"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    list_definition_id: Mapped[int] = mapped_column(ForeignKey("risk.list_definition.id"))
    jurisdiction_id: Mapped[int] = mapped_column(ForeignKey("core.jurisdiction.id"))
    classification: Mapped[str] = mapped_column(String(48))
    announcement_date: Mapped[date | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))
    valid_period: Mapped[Range[date]] = mapped_column(DATERANGE)
```

- [ ] **Step 4: Migration + run + commit**

`migrations/versions/0011_risk_list_membership.py` (revision "0011", down_revision "0010"): create `risk.list_membership` with the columns, FKs, and the `ExcludeConstraint` (btree_gist exists from 0006). downgrade drops it.
Focused test PASS (incl. overlap rejection); full suite + ruff + mypy clean.
```bash
git add app/modules/risk/models.py migrations/versions/0011_risk_list_membership.py tests/test_list_membership.py
git commit -m "feat: risk.list_membership with no-overlap exclusion constraint"
```

---

### Task 3: `ListRepository` as-of queries

**Files:**
- Modify: `app/modules/risk/repository.py` (add `ListRepository`)
- Test: `tests/test_list_repository.py`

**Interfaces:**
- Produces:
  - `ListRepository(session)` with:
    - `is_listed(jurisdiction_code: str, list_code: str, on_date: date) -> ListMembership | None` (as-of; None if not currently in a valid membership window).
    - `members(list_code: str, on_date: date) -> list[ListMembership]` (all jurisdictions on that list, valid on date).
    - `lists_for(jurisdiction_code: str, on_date: date) -> list[ListMembership]` (all lists a jurisdiction is on, valid on date).

- [ ] **Step 1: Write the failing test**

`tests/test_list_repository.py`:
```python
from datetime import UTC, date, datetime

from sqlalchemy.dialects.postgresql import Range

from app.modules.core.models import Jurisdiction
from app.modules.risk.models import ListDefinition, ListMembership
from app.modules.risk.repository import ListRepository
from app.modules.source.models import SourceDocument, SourceEvidence


def _seed(db_session):
    doc = SourceDocument(title="s", url="https://s", retrieved_at=datetime.now(UTC), content_hash="h")
    ae = Jurisdiction(code="AE", name="UAE")
    db_session.add_all([doc, ae]); db_session.flush()
    ev = SourceEvidence(document_id=doc.id, quoted_text="q", review_status="human_verified")
    db_session.add(ev); db_session.flush()
    grey = ListDefinition(code="FATF_GREY", name="grey", family="aml_cft", publisher="FATF", update_cadence=None, source_evidence_id=ev.id)
    aml = ListDefinition(code="EU_AML_HIGH_RISK", name="eu aml", family="aml_cft", publisher="European Commission", update_cadence=None, source_evidence_id=ev.id)
    db_session.add_all([grey, aml]); db_session.flush()
    db_session.add_all([
        ListMembership(list_definition_id=grey.id, jurisdiction_id=ae.id, classification="increased_monitoring",
                       announcement_date=date(2022, 3, 4), status="active", source_evidence_id=ev.id,
                       valid_period=Range(date(2022, 3, 4), date(2024, 2, 23), bounds="[)")),
        ListMembership(list_definition_id=aml.id, jurisdiction_id=ae.id, classification="high_risk",
                       announcement_date=date(2023, 3, 16), status="active", source_evidence_id=ev.id,
                       valid_period=Range(date(2023, 3, 16), date(2025, 6, 10), bounds="[)")),
    ])
    db_session.flush()
    return ae


def test_is_listed_as_of(db_session):
    _seed(db_session)
    repo = ListRepository(db_session)
    assert repo.is_listed("AE", "FATF_GREY", date(2023, 1, 1)) is not None       # during
    assert repo.is_listed("AE", "FATF_GREY", date(2024, 6, 1)) is None           # after removal
    assert repo.is_listed("AE", "FATF_GREY", date(2021, 1, 1)) is None           # before


def test_lists_for_returns_both_concurrent(db_session):
    _seed(db_session)
    repo = ListRepository(db_session)
    codes = {m.list_definition_id for m in repo.lists_for("AE", date(2023, 6, 1))}
    assert len(codes) == 2   # on FATF grey AND EU AML on this date


def test_members_of_list(db_session):
    _seed(db_session)
    repo = ListRepository(db_session)
    assert len(repo.members("FATF_GREY", date(2023, 1, 1))) == 1
    assert len(repo.members("FATF_GREY", date(2025, 1, 1))) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_list_repository.py -v`
Expected: FAIL — `ListRepository` not defined.

- [ ] **Step 3: Write the repository**

Append to `app/modules/risk/repository.py` (extend imports: `from datetime import date`; `from app.modules.core.models import Jurisdiction`; `from app.modules.risk.models import ListMembership`):
```python
class ListRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def is_listed(self, jurisdiction_code: str, list_code: str, on_date: date) -> ListMembership | None:
        stmt = (
            select(ListMembership)
            .join(Jurisdiction, ListMembership.jurisdiction_id == Jurisdiction.id)
            .join(ListDefinition, ListMembership.list_definition_id == ListDefinition.id)
            .where(
                Jurisdiction.code == jurisdiction_code,
                ListDefinition.code == list_code,
                ListMembership.valid_period.contains(on_date),
            )
        )
        return self.session.scalar(stmt)

    def members(self, list_code: str, on_date: date) -> list[ListMembership]:
        stmt = (
            select(ListMembership)
            .join(ListDefinition, ListMembership.list_definition_id == ListDefinition.id)
            .where(ListDefinition.code == list_code, ListMembership.valid_period.contains(on_date))
        )
        return list(self.session.scalars(stmt))

    def lists_for(self, jurisdiction_code: str, on_date: date) -> list[ListMembership]:
        stmt = (
            select(ListMembership)
            .join(Jurisdiction, ListMembership.jurisdiction_id == Jurisdiction.id)
            .where(Jurisdiction.code == jurisdiction_code, ListMembership.valid_period.contains(on_date))
        )
        return list(self.session.scalars(stmt))
```
(Ensure `ListDefinition` is imported in repository.py — it already is from Task 1.)

- [ ] **Step 4: Run + commit**

Focused test PASS; full suite + ruff + mypy clean.
```bash
git add app/modules/risk/repository.py tests/test_list_repository.py
git commit -m "feat: ListRepository as-of membership queries (is_listed, members, lists_for)"
```

---

### Task 4: `risk.regulatory_consequence` + `ConsequenceRepository`

**Files:**
- Modify: `app/modules/risk/models.py` (add `RegulatoryConsequence`), `app/modules/risk/repository.py` (add `ConsequenceRepository`)
- Create: `migrations/versions/0012_risk_regulatory_consequence.py`
- Test: `tests/test_regulatory_consequence.py`

**Interfaces:**
- Produces (schema `risk`):
  - `RegulatoryConsequence(id, applying_jurisdiction_id FK core.jurisdiction, list_definition_id FK risk.list_definition (NULLABLE), classification_trigger:str|None, consequence_type:str, rate:Decimal|None Numeric(6,3), legal_ref:str, description:str|None, source_evidence_id FK NOT NULL, valid_period DATERANGE)` with `ExcludeConstraint((applying_jurisdiction_id '='),(list_definition_id '='),(classification_trigger '='),(consequence_type '='),(valid_period '&&'), using gist, name='no_overlap_consequence')` and a CheckConstraint `rate IS NULL OR (rate BETWEEN 0 AND 100)` named `consequence_rate_pct_range`.
  - `ConsequenceRepository(session)` with:
    - `for_applying_jurisdiction(code: str, on_date: date) -> list[RegulatoryConsequence]`.
    - `triggered_by(list_code: str, classification: str | None, on_date: date) -> list[RegulatoryConsequence]` — consequences whose `list_definition` matches `list_code` and whose `classification_trigger` is NULL (applies to any classification) or equals `classification`.

> Note: `classification_trigger` is part of the exclusion key, so it must be NOT NULL for the constraint to catch duplicates. Use the empty string `''` to mean "any classification" rather than SQL NULL, and have `triggered_by` treat `''` as the wildcard. Document this in a comment.

- [ ] **Step 1: Write the failing test**

`tests/test_regulatory_consequence.py`:
```python
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.dialects.postgresql import Range

from app.modules.core.models import Jurisdiction
from app.modules.risk.models import ListDefinition, RegulatoryConsequence
from app.modules.risk.repository import ConsequenceRepository
from app.modules.source.models import SourceDocument, SourceEvidence


def _seed(db_session):
    doc = SourceDocument(title="CGI", url="https://legifrance", retrieved_at=datetime.now(UTC), content_hash="h")
    fr = Jurisdiction(code="FR", name="France")
    db_session.add_all([doc, fr]); db_session.flush()
    ev = SourceEvidence(document_id=doc.id, article="CGI 238-0 A", quoted_text="75%", review_status="human_verified")
    db_session.add(ev); db_session.flush()
    etnc = ListDefinition(code="FR_ETNC", name="ETNC", family="tax_governance", publisher="France",
                          update_cadence="per national law", source_evidence_id=ev.id)
    db_session.add(etnc); db_session.flush()
    db_session.add(RegulatoryConsequence(
        applying_jurisdiction_id=fr.id, list_definition_id=etnc.id, classification_trigger="full_measures",
        consequence_type="withholding_tax", rate=Decimal("75"), legal_ref="CGI art. 238-0 A",
        description="75% WHT on certain payments to ETNC (full measures)", source_evidence_id=ev.id,
        valid_period=Range(date(2010, 2, 12), None, bounds="[)"),
    ))
    db_session.flush()
    return fr, etnc


def test_for_applying_jurisdiction(db_session):
    _seed(db_session)
    repo = ConsequenceRepository(db_session)
    rows = repo.for_applying_jurisdiction("FR", date(2024, 1, 1))
    assert len(rows) == 1 and rows[0].rate == Decimal("75")


def test_triggered_by_classification(db_session):
    _seed(db_session)
    repo = ConsequenceRepository(db_session)
    assert len(repo.triggered_by("FR_ETNC", "full_measures", date(2024, 1, 1))) == 1
    assert len(repo.triggered_by("FR_ETNC", "certain_measures", date(2024, 1, 1))) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_regulatory_consequence.py -v`
Expected: FAIL — `RegulatoryConsequence` not defined.

- [ ] **Step 3: Add the model**

Append to `app/modules/risk/models.py` (extend imports: `CheckConstraint`, `Numeric` from sqlalchemy; `from decimal import Decimal`):
```python
class RegulatoryConsequence(Base):
    __tablename__ = "regulatory_consequence"
    __table_args__ = (
        ExcludeConstraint(
            ("applying_jurisdiction_id", "="),
            ("list_definition_id", "="),
            ("classification_trigger", "="),
            ("consequence_type", "="),
            ("valid_period", "&&"),
            using="gist",
            name="no_overlap_consequence",
        ),
        CheckConstraint("rate IS NULL OR (rate >= 0 AND rate <= 100)", name="consequence_rate_pct_range"),
        {"schema": "risk"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    applying_jurisdiction_id: Mapped[int] = mapped_column(ForeignKey("core.jurisdiction.id"))
    list_definition_id: Mapped[int] = mapped_column(ForeignKey("risk.list_definition.id"))
    # classification_trigger: '' means "any classification on the list" (wildcard); NOT NULL so the
    # exclusion constraint can key on it. See ConsequenceRepository.triggered_by.
    classification_trigger: Mapped[str] = mapped_column(String(48), default="")
    consequence_type: Mapped[str] = mapped_column(String(48))
    rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    legal_ref: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_evidence_id: Mapped[int] = mapped_column(ForeignKey("source.source_evidence.id"))
    valid_period: Mapped[Range[date]] = mapped_column(DATERANGE)
```

- [ ] **Step 4: Add the repository**

Append to `app/modules/risk/repository.py` (add `from app.modules.risk.models import RegulatoryConsequence` to imports; `date` already imported in Task 3):
```python
class ConsequenceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def for_applying_jurisdiction(self, code: str, on_date: date) -> list[RegulatoryConsequence]:
        stmt = (
            select(RegulatoryConsequence)
            .join(Jurisdiction, RegulatoryConsequence.applying_jurisdiction_id == Jurisdiction.id)
            .where(Jurisdiction.code == code, RegulatoryConsequence.valid_period.contains(on_date))
        )
        return list(self.session.scalars(stmt))

    def triggered_by(
        self, list_code: str, classification: str | None, on_date: date
    ) -> list[RegulatoryConsequence]:
        stmt = (
            select(RegulatoryConsequence)
            .join(ListDefinition, RegulatoryConsequence.list_definition_id == ListDefinition.id)
            .where(
                ListDefinition.code == list_code,
                RegulatoryConsequence.valid_period.contains(on_date),
                RegulatoryConsequence.classification_trigger.in_(["", classification or ""]),
            )
        )
        return list(self.session.scalars(stmt))
```

- [ ] **Step 5: Migration + run + commit**

`migrations/versions/0012_risk_regulatory_consequence.py` (revision "0012", down_revision "0011"): create `risk.regulatory_consequence` with the columns, FKs, the `consequence_rate_pct_range` CheckConstraint, and the `ExcludeConstraint`. downgrade drops it.
Focused test PASS; full suite + ruff + mypy clean.
```bash
git add app/modules/risk/models.py app/modules/risk/repository.py migrations/versions/0012_risk_regulatory_consequence.py tests/test_regulatory_consequence.py
git commit -m "feat: risk.regulatory_consequence + ConsequenceRepository"
```

---

### Task 5: List seed for the FR/UAE corridor

**Files:**
- Create: `app/modules/seed/lists.py`
- Modify: `app/modules/seed/france_uae.py` (call `seed_lists(session)` at the end of `seed`)
- Test: `tests/test_seed_lists.py`

**Interfaces:**
- Produces: `app.modules.seed.lists.seed_lists(session) -> None` — idempotent: upserts the 7 `list_definition` rows, the verified memberships, and the France ETNC consequence. `france_uae.seed` calls it after its existing work (so the golden fixture includes lists).

**Verified figures to seed (each cites its source — verify before done):**

| Row | Value | valid_period | Source |
|---|---|---|---|
| `FATF_GREY` def | FATF "increased monitoring", AML/CFT, publisher FATF, cadence "after each plenary (Feb/Jun/Oct)" | — | fatf-gafi.org |
| `FATF_BLACK` def | FATF "call for action", AML/CFT | — | fatf-gafi.org |
| `EU_TAX_ANNEX_I` / `EU_TAX_ANNEX_II` defs | tax-governance, publisher Council of the EU, cadence "twice a year" | — | consilium.europa.eu |
| `EU_AML_HIGH_RISK` def | AML/CFT, publisher European Commission, Reg (EU) 2016/1675 | — | finance.ec.europa.eu |
| `GLOBAL_FORUM_RATING` def | tax-governance, publisher OECD Global Forum, EOIR ratings | — | oecd.org |
| `FR_ETNC` def | tax-governance, publisher France, cadence "per national law" | — | legifrance / BOFiP |
| UAE on `FATF_GREY` (increased_monitoring) | — | **[2022-03-04, 2024-02-23)** | FATF plenary statements |
| UAE on `EU_AML_HIGH_RISK` (high_risk) | — | **[2023-03-16, 2025-06-10)** | Del. Reg (EU) 2023/410; removed by (EU) 2025/1184 |
| Vanuatu (VU) on `FR_ETNC` (full_measures) | — | **[2025-05-08, ∞)** | arrêté 18 Apr 2025 (JO 7 May 2025) |
| Panama (PA) on `FR_ETNC` (certain_measures) | — | **[2025-05-08, ∞)** | arrêté 18 Apr 2025 |
| FR ETNC consequence | 75% WHT, `classification_trigger='full_measures'`, `consequence_type='withholding_tax'`, `legal_ref='CGI art. 238-0 A'` | **[2010-02-12, ∞)** | CGI art. 238-0 A |

Seed jurisdictions VU and PA via the existing get-or-create-by-code helper. UAE/FR already exist from the P1 fixture.

- [ ] **Step 1: Write the failing test**

`tests/test_seed_lists.py`:
```python
from datetime import date
from decimal import Decimal

from app.modules.risk.repository import ConsequenceRepository, ListRepository
from app.modules.seed.france_uae import seed


def test_seed_lists_idempotent_and_resolves(db_session):
    seed(db_session)
    seed(db_session)  # idempotent
    db_session.flush()

    lists = ListRepository(db_session)
    # UAE FATF grey: listed during the window, not after removal
    assert lists.is_listed("AE", "FATF_GREY", date(2023, 1, 1)) is not None
    assert lists.is_listed("AE", "FATF_GREY", date(2024, 6, 1)) is None
    # UAE EU AML high-risk window
    assert lists.is_listed("AE", "EU_AML_HIGH_RISK", date(2024, 1, 1)) is not None
    assert lists.is_listed("AE", "EU_AML_HIGH_RISK", date(2026, 1, 1)) is None
    # Vanuatu currently on FR ETNC (full measures)
    vu = lists.is_listed("VU", "FR_ETNC", date(2026, 1, 1))
    assert vu is not None and vu.classification == "full_measures"

    cons = ConsequenceRepository(db_session)
    etnc = cons.triggered_by("FR_ETNC", "full_measures", date(2026, 1, 1))
    assert len(etnc) == 1 and etnc[0].rate == Decimal("75")


def test_every_list_row_has_evidence(db_session):
    seed(db_session)
    db_session.flush()
    from app.modules.risk.models import ListMembership, RegulatoryConsequence
    for model in (ListMembership, RegulatoryConsequence):
        rows = db_session.query(model).all()
        assert rows and all(r.source_evidence_id is not None for r in rows)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_seed_lists.py -v`
Expected: FAIL — `seed_lists` missing / lists not seeded by `seed`.

- [ ] **Step 3: Implement `lists.py`**

`app/modules/seed/lists.py` — build using `ListDefinitionRepository.get_or_create`, `upsert_source` (from `app/modules/seed/sources.py`), the existing jurisdiction get-or-create helper in `france_uae.py` (import or replicate), and existence guards before inserting memberships/consequence (query the as-of repositories; skip if a row already covers the window). Seed exactly the rows in the "Verified figures" table, each pointing at its `upsert_source(...)` evidence. Use `Range(date(...), end_or_None, bounds="[)")`. The function signature is `def seed_lists(session: Session) -> None:`.

> Idempotency: for each `list_definition`, `get_or_create` by code. For each membership, check `ListRepository.is_listed(jurisdiction, list, lower_bound)`; insert only if absent. For the consequence, check `ConsequenceRepository.triggered_by("FR_ETNC", "full_measures", 2010-02-12)`; insert only if absent.

- [ ] **Step 4: Wire into `france_uae.seed`**

In `app/modules/seed/france_uae.py`, import `from app.modules.seed.lists import seed_lists` and call `seed_lists(session)` as the last statement of `seed(session)` (after the treaty rows). This keeps one golden fixture that includes lists.

- [ ] **Step 5: Run tests + CLI; commit**

Run: `uv run pytest tests/test_seed_lists.py -v` (PASS), full suite + ruff + mypy clean. Then live:
```bash
uv run alembic downgrade base && uv run alembic upgrade head
uv run python -m app.cli seed-france-uae   # seeds tax + treaty + lists
uv run python -m app.cli seed-france-uae   # idempotent
```
```bash
git add app/modules/seed/lists.py app/modules/seed/france_uae.py tests/test_seed_lists.py
git commit -m "feat: seed verified FR/UAE-corridor list memberships + France ETNC consequence"
```

---

### Task 6: Data-quality checks for lists & consequences

**Files:**
- Modify: `app/modules/seed/quality.py` (extend `run_checks`)
- Test: `tests/test_data_quality_lists.py`

**Interfaces:**
- Extends `run_checks(session) -> list[str]` with:
  4. every `ListMembership` has a non-empty `classification`;
  5. every `RegulatoryConsequence` with `consequence_type == 'withholding_tax'` has a non-null `rate`;
  6. every `RegulatoryConsequence.list_definition_id` references an existing `ListDefinition` (FK guarantees it; the check documents the cross-entity invariant and catches a dangling wildcard consequence with no list).

- [ ] **Step 1: Write the failing test**

`tests/test_data_quality_lists.py`:
```python
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.dialects.postgresql import Range

from app.modules.core.models import Jurisdiction
from app.modules.risk.models import ListDefinition, RegulatoryConsequence
from app.modules.seed.france_uae import seed
from app.modules.seed.quality import run_checks
from app.modules.source.models import SourceDocument, SourceEvidence


def test_seeded_fixture_passes_quality_checks(db_session):
    seed(db_session)
    db_session.flush()
    assert run_checks(db_session) == [], run_checks(db_session)


def test_wht_consequence_without_rate_is_flagged(db_session):
    doc = SourceDocument(title="x", url="https://x", retrieved_at=datetime.now(UTC), content_hash="h")
    fr = Jurisdiction(code="FR", name="France")
    db_session.add_all([doc, fr]); db_session.flush()
    ev = SourceEvidence(document_id=doc.id, quoted_text="q", review_status="human_verified")
    db_session.add(ev); db_session.flush()
    ld = ListDefinition(code="FR_ETNC", name="ETNC", family="tax_governance", publisher="France",
                        update_cadence=None, source_evidence_id=ev.id)
    db_session.add(ld); db_session.flush()
    db_session.add(RegulatoryConsequence(
        applying_jurisdiction_id=fr.id, list_definition_id=ld.id, classification_trigger="full_measures",
        consequence_type="withholding_tax", rate=None, legal_ref="CGI 238-0 A", description=None,
        source_evidence_id=ev.id, valid_period=Range(date(2010, 2, 12), None, bounds="[)"),
    ))
    db_session.flush()
    assert any("rate" in v.lower() for v in run_checks(db_session))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_data_quality_lists.py -v`
Expected: FAIL — the WHT-rate check doesn't exist yet (second test), and/or the seeded fixture now contains list rows the old `run_checks` doesn't cover.

- [ ] **Step 3: Extend `run_checks`**

Append to `app/modules/seed/quality.py` `run_checks` (add imports `from app.modules.risk.models import ListMembership, RegulatoryConsequence`):
```python
    # 4. list memberships need a classification
    for m in session.scalars(select(ListMembership)):
        if not m.classification:
            violations.append(f"list_membership {m.id} has an empty classification")

    # 5. withholding-tax consequences need a rate
    for c in session.scalars(select(RegulatoryConsequence)):
        if c.consequence_type == "withholding_tax" and c.rate is None:
            violations.append(f"regulatory_consequence {c.id} (withholding_tax) has no rate")
```
(Keep the existing checks 1–3 unchanged.)

- [ ] **Step 4: Run tests + checks; commit**

Focused test PASS; full suite + ruff + mypy clean (the seeded fixture — now including lists — must still pass `run_checks` with zero violations).
```bash
git add app/modules/seed/quality.py tests/test_data_quality_lists.py
git commit -m "feat: data-quality checks for list classification and WHT consequence rate"
```

---

## Self-Review

**1. Spec coverage (P2 slice of spec §3, §4, §7):**
- List families kept distinct (`family` column) → Task 1 ✅ (spec §3)
- EU tax list, FATF grey/black, EU AML, Global Forum, France ETNC as list definitions → Task 5 seed ✅
- `list_membership` bitemporal + exclusion constraint → Task 2 ✅
- `regulatory_consequence` tied to the applying jurisdiction (France ETNC 75% as the first case) → Tasks 4, 5 ✅ (spec §3.5, review §3.5)
- As-of reads → Task 3 ✅
- Every list figure sourced → Tasks 2/4 schema + Task 5 test ✅
- Data-quality rules → Task 6 ✅ (spec §7)
- Deferred (correctly absent): the consequence-precedence composition that overrides a treaty/domestic rate (P3 Risk engine); `national_risk_rule` (deferred — ETNC is modeled via `regulatory_consequence`); modeling the EU as a publisher *organisation* row (P2 uses a `publisher` string per spec §3.8's intent without a separate `organisation` table — noted for a later refinement); automated list ingestion (P8).

**2. Placeholder scan:** Task 5 Step 3 describes the seed from an explicit figures table + idempotency rule (its outputs pinned by Task 5's test), like P1 Task 7. Every other code step is literal. No "TBD/TODO".

**3. Type consistency:** `valid_period: Range[date]` + `bounds="[)"` and the dialect `Range` import are used identically across Tasks 2/4/5. Repo signatures (`is_listed`, `members`, `lists_for`, `for_applying_jurisdiction`, `triggered_by`, `get_or_create`) match between definition and use in Tasks 3/4/5. `classification_trigger` wildcard `''` convention is consistent between the model default (Task 4), `triggered_by` (Task 4), and the seed (Task 5).

**4. Review Focus coverage:**
- Expired membership as-of → Task 3 `test_is_listed_as_of` + Task 5 ✅
- Overlapping membership rejected → Task 2 `test_overlapping_membership_rejected` ✅
- No row without a source → NOT NULL + Task 5 `test_every_list_row_has_evidence` ✅
- Concurrent membership on two lists → Task 3 `test_lists_for_returns_both_concurrent` ✅
- Classification-tiered consequence → Task 4 `test_triggered_by_classification` ✅

---

## Known-fiddly areas for implementers (report, don't paper over)
- Same as P1: PostgreSQL `DATERANGE`/`Range`/`ExcludeConstraint` and the `@>`/`&&` operators (`.contains(on_date)`, fallback `.op("@>")`). btree_gist already exists (migration 0006) — do NOT re-create it in a way that errors; `CREATE EXTENSION IF NOT EXISTS` is idempotent if you include it, but it is unnecessary here.
- The `classification_trigger=''` wildcard is deliberate (NULL can't participate in the `=` exclusion key, and two NULLs wouldn't conflict). Keep `''`, not NULL.

## Next plans (not in this document)
P3 engines (Tax/Treaty/Flow/Risk composing `min(domestic,treaty)` + MLI + **consequence precedence** overriding treaty rates), then P4 scoring, P5 UI, P6 LLM, P7 SaaS hardening, P8 scale.
