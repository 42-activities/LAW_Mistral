# P0 Foundations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the modular-monolith skeleton — a running, API-key-authenticated FastAPI service backed by a migrated PostgreSQL with `core`/`source`/`saas` schemas, an evidence-resolution stub, and green CI.

**Architecture:** FastAPI modular monolith with one Python package (`app`) split by bounded context (`app/modules/<context>`). Synchronous SQLAlchemy 2.0 ORM over psycopg3, versioned by Alembic. Each context owns its models and a thin repository; the API layer (`app/api/v1`) composes them. This is Phase P0 of the spec — foundations only; tax/treaty/recommender logic arrives in later plans.

**Tech Stack:** Python 3.12 · uv · FastAPI · Uvicorn · SQLAlchemy 2.0 (sync) · psycopg3 · Alembic · pydantic-settings · pytest + httpx · ruff · mypy · Docker Compose (PostgreSQL 16) · GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-04-tax-jurisdiction-recommender-design.md`

## Global Constraints

- Python **3.12**; dependency management with **uv** (`pyproject.toml`, `uv.lock`).
- **Modular monolith**: no microservices, no graph DB (spec §2). One package `app`, split by bounded context under `app/modules/`.
- **PostgreSQL 16**; all tables live under an explicit schema (`core`, `source`, `saas`, plus empty `tax`, `treaty`, `risk`, `recommender`, `workflow` created for later phases). Schema names are lowercase.
- SQLAlchemy **2.0 sync** style (`DeclarativeBase`, `Mapped[...]`, `mapped_column`). psycopg **v3** driver (`postgresql+psycopg://`).
- `ruff` and `mypy` must pass clean in CI; `pytest` must pass clean in CI.
- **Source-backing principle (spec core):** the evidence service is the only way the system links a stored fact to an official source; its interface is introduced here even though facts arrive later.
- API version prefix is `/v1`.

## Review Focus

- **Missing or invalid API key** on a protected route → `401 Unauthorized`, never a 500 or an open route. (Task 7 tests.)
- **Unknown jurisdiction id** on `GET /v1/jurisdictions/{id}` → `404 Not Found` with a JSON error body, not a stack trace. (Task 8 tests.)
- **Duplicate jurisdiction code** insert → surfaced as a handled integrity error, not a raw driver exception. (Task 5 tests.)
- **Database unreachable** → `/health` stays `200` (liveness) but `/health/ready` returns `503` (readiness), so an orchestrator can tell them apart. (Task 2 tests.)
- **Re-running migrations** (`alembic upgrade head` twice, schemas already present) → idempotent, no error. (Task 4 tests.)

---

## File Structure

```
pyproject.toml                      # project + tool config (uv, ruff, mypy, pytest)
docker-compose.yml                  # local Postgres 16
Dockerfile                          # app image
alembic.ini                         # Alembic config
.github/workflows/ci.yml            # CI: lint, type-check, test
README.md                           # quickstart
app/
  __init__.py
  main.py                           # FastAPI app factory + router wiring
  config.py                         # Settings (pydantic-settings)
  db.py                             # engine, SessionLocal, Base, get_session
  deps.py                           # shared FastAPI dependencies (auth)
  errors.py                         # error handlers / exceptions
  modules/
    core/
      __init__.py
      models.py                     # Jurisdiction, JurisdictionAlias
      repository.py                 # JurisdictionRepository
    source/
      __init__.py
      models.py                     # SourceDocument, SourceEvidence
      service.py                    # EvidenceService (stub)
    saas/
      __init__.py
      models.py                     # OrganisationAccount, User, ApiKey
      security.py                   # hash_api_key, verify_api_key
  api/
    __init__.py
    v1/
      __init__.py                   # v1 APIRouter aggregation
      health.py                     # /health, /health/ready
      jurisdictions.py              # /v1/jurisdictions
migrations/
  env.py
  script.py.mako
  versions/
    0001_create_schemas.py
    0002_core_jurisdiction.py
    0003_source_evidence.py
    0004_saas_auth.py
tests/
  conftest.py                       # DB fixtures, test client, migrations
  test_health.py
  test_jurisdiction_repository.py
  test_source_evidence.py
  test_auth.py
  test_jurisdictions_api.py
```

---

### Task 1: Project scaffolding & tooling

**Files:**
- Create: `pyproject.toml`
- Create: `app/__init__.py`, `tests/__init__.py`
- Create: `tests/test_smoke.py`

**Interfaces:**
- Consumes: nothing.
- Produces: a `uv`-managed project where `uv run pytest`, `uv run ruff check .`, and `uv run mypy app` all run.

- [ ] **Step 1: Write the failing test**

`tests/test_smoke.py`:
```python
def test_python_version_is_supported():
    import sys

    assert sys.version_info[:2] == (3, 12)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_smoke.py -v`
Expected: FAIL — `uv`/project not initialized yet (command errors or no pytest).

- [ ] **Step 3: Create the project config**

`pyproject.toml`:
```toml
[project]
name = "jurisdiction-recommender"
version = "0.0.0"
requires-python = "==3.12.*"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "sqlalchemy>=2.0",
    "psycopg[binary]>=3.2",
    "alembic>=1.13",
    "pydantic-settings>=2.5",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "httpx>=0.27",
    "ruff>=0.7",
    "mypy>=1.13",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
addopts = "-ra"
testpaths = ["tests"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["app"]
```

Create empty `app/__init__.py` and `tests/__init__.py`. Then run `uv sync` to create the environment and lockfile.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_smoke.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock app/__init__.py tests/__init__.py tests/test_smoke.py
git commit -m "chore: scaffold uv project with tooling"
```

---

### Task 2: App factory, config, and health endpoints

**Files:**
- Create: `app/config.py`, `app/main.py`, `app/api/__init__.py`, `app/api/v1/__init__.py`, `app/api/v1/health.py`
- Create: `app/db.py`
- Test: `tests/test_health.py`, `tests/conftest.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `app.config.Settings` with `database_url: str`, `api_key_header: str = "X-API-Key"`, `environment: str = "local"`; `get_settings() -> Settings` (cached).
  - `app.db.engine`, `app.db.SessionLocal`, `class Base(DeclarativeBase)`, `get_session() -> Iterator[Session]`, `check_database() -> bool`.
  - `app.main.create_app() -> FastAPI`.
  - Routes: `GET /health` → `{"status": "ok"}` (200, no DB), `GET /health/ready` → `{"status": "ready"}` (200) or `{"status": "unavailable"}` (503) depending on `check_database()`.

- [ ] **Step 1: Write the failing test**

`tests/conftest.py`:
```python
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
```

`tests/test_health.py`:
```python
from unittest.mock import patch

from fastapi.testclient import TestClient


def test_health_is_ok_without_db(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ready_returns_503_when_db_unreachable(client: TestClient):
    with patch("app.api.v1.health.check_database", return_value=False):
        resp = client.get("/health/ready")
    assert resp.status_code == 503
    assert resp.json() == {"status": "unavailable"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_health.py -v`
Expected: FAIL — `app.main` does not exist.

- [ ] **Step 3: Write minimal implementation**

`app/config.py`:
```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env")

    database_url: str = "postgresql+psycopg://app:app@localhost:5432/app"
    api_key_header: str = "X-API-Key"
    environment: str = "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

`app/db.py`:
```python
from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def check_database() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
```

`app/api/v1/health.py`:
```python
from fastapi import APIRouter, Response

from app.db import check_database

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def ready(response: Response) -> dict[str, str]:
    if check_database():
        return {"status": "ready"}
    response.status_code = 503
    return {"status": "unavailable"}
```

`app/api/v1/__init__.py`:
```python
from fastapi import APIRouter

from app.api.v1 import health

api_router = APIRouter()
api_router.include_router(health.router)
```

`app/api/__init__.py`: empty file.

`app/main.py`:
```python
from fastapi import FastAPI

from app.api.v1 import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="Jurisdiction Recommender", version="0.0.0")
    app.include_router(api_router)
    return app


app = create_app()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_health.py -v`
Expected: PASS (both tests).

- [ ] **Step 5: Commit**

```bash
git add app tests/conftest.py tests/test_health.py
git commit -m "feat: app factory, settings, and health/readiness endpoints"
```

---

### Task 3: Local Postgres & container image

**Files:**
- Create: `docker-compose.yml`, `Dockerfile`, `.env.example`, `.dockerignore`

**Interfaces:**
- Consumes: `app.main:app`.
- Produces: a local Postgres 16 reachable at `postgresql+psycopg://app:app@localhost:5432/app`, and a runnable app image. No new Python symbols.

- [ ] **Step 1: Write the compose and image files**

`docker-compose.yml`:
```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: app
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 5s
      timeout: 3s
      retries: 10
```

`Dockerfile`:
```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /srv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`.env.example`:
```bash
APP_DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/app
APP_ENVIRONMENT=local
```

`.dockerignore`:
```
.git
.venv
__pycache__
*.pyc
tests
```

- [ ] **Step 2: Bring up the database and verify readiness**

Run:
```bash
docker compose up -d db
sleep 5
APP_DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/app \
  uv run python -c "from app.db import check_database; assert check_database(); print('db ok')"
```
Expected: prints `db ok`.

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml Dockerfile .env.example .dockerignore
git commit -m "chore: local postgres compose and app dockerfile"
```

---

### Task 4: Alembic setup & schema creation migration

**Files:**
- Create: `alembic.ini`, `migrations/env.py`, `migrations/script.py.mako`, `migrations/versions/0001_create_schemas.py`
- Test: `tests/conftest.py` (extend), `tests/test_migrations.py`

**Interfaces:**
- Consumes: `app.db.Base`, `app.config.get_settings`.
- Produces:
  - Alembic configured to read `APP_DATABASE_URL` and target `Base.metadata`.
  - Migration `0001` creating schemas `core, source, saas, tax, treaty, risk, recommender, workflow` idempotently.
  - `tests/conftest.py` gains a session-scoped `_migrated_db` fixture (runs `alembic upgrade head`) and a function-scoped `db_session` fixture (transaction rolled back per test).

- [ ] **Step 1: Write the failing test**

`tests/test_migrations.py`:
```python
from sqlalchemy import text

from app.db import engine


def test_expected_schemas_exist(_migrated_db):
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT schema_name FROM information_schema.schemata")
        ).scalars().all()
    for schema in ["core", "source", "saas", "tax", "treaty", "risk", "recommender", "workflow"]:
        assert schema in rows


def test_migrations_are_idempotent(_migrated_db):
    # Running upgrade head twice must not raise.
    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_migrations.py -v`
Expected: FAIL — no Alembic config / `_migrated_db` fixture.

- [ ] **Step 3: Configure Alembic**

`alembic.ini` (minimal; URL comes from env via `env.py`):
```ini
[alembic]
script_location = migrations

[loggers]
keys = root

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
```

`migrations/env.py`:
```python
from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import get_settings
from app.db import Base

# Import model modules so their tables register on Base.metadata.
from app.modules.core import models as _core_models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
```

> Note: `app.modules.core.models` is created in Task 5. Until then, comment that import out; re-enable it in Task 5. Later model modules (source, saas) are added to this import list in their tasks.

`migrations/script.py.mako`:
```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
"""
from alembic import op
import sqlalchemy as sa

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

`migrations/versions/0001_create_schemas.py`:
```python
"""create schemas

Revision ID: 0001
Revises:
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SCHEMAS = ["core", "source", "saas", "tax", "treaty", "risk", "recommender", "workflow"]


def upgrade() -> None:
    for schema in SCHEMAS:
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")


def downgrade() -> None:
    for schema in SCHEMAS:
        op.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
```

- [ ] **Step 4: Add DB fixtures to conftest**

Extend `tests/conftest.py`:
```python
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from app.db import engine


@pytest.fixture(scope="session")
def _migrated_db():
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    yield


@pytest.fixture
def db_session(_migrated_db) -> Session:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_migrations.py -v`
Expected: PASS. (Requires `docker compose up -d db`.)

- [ ] **Step 6: Commit**

```bash
git add alembic.ini migrations tests/conftest.py tests/test_migrations.py
git commit -m "feat: alembic setup and schema-creation migration"
```

---

### Task 5: `core.jurisdiction` model, migration & repository

**Files:**
- Create: `app/modules/core/__init__.py`, `app/modules/core/models.py`, `app/modules/core/repository.py`
- Create: `migrations/versions/0002_core_jurisdiction.py`
- Modify: `migrations/env.py` (enable the `core.models` import)
- Test: `tests/test_jurisdiction_repository.py`

**Interfaces:**
- Consumes: `app.db.Base`, `db_session` fixture.
- Produces:
  - `Jurisdiction(id: int, code: str, name: str)` and `JurisdictionAlias(id: int, jurisdiction_id: int, alias: str)` ORM models in schema `core`; `code` is unique.
  - `JurisdictionRepository(session: Session)` with `create(code: str, name: str) -> Jurisdiction`, `get(id: int) -> Jurisdiction | None`, `get_by_code(code: str) -> Jurisdiction | None`, `list() -> list[Jurisdiction]`.
  - `DuplicateCodeError(Exception)` raised by `create` on a duplicate `code`.

- [ ] **Step 1: Write the failing test**

`tests/test_jurisdiction_repository.py`:
```python
import pytest

from app.modules.core.repository import DuplicateCodeError, JurisdictionRepository


def test_create_and_get_by_code(db_session):
    repo = JurisdictionRepository(db_session)
    created = repo.create(code="AE", name="United Arab Emirates")
    db_session.flush()
    assert created.id is not None
    assert repo.get_by_code("AE").name == "United Arab Emirates"


def test_duplicate_code_raises(db_session):
    repo = JurisdictionRepository(db_session)
    repo.create(code="FR", name="France")
    db_session.flush()
    with pytest.raises(DuplicateCodeError):
        repo.create(code="FR", name="France Again")
        db_session.flush()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_jurisdiction_repository.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the models**

`app/modules/core/__init__.py`: empty file.

`app/modules/core/models.py`:
```python
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Jurisdiction(Base):
    __tablename__ = "jurisdiction"
    __table_args__ = {"schema": "core"}

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))

    aliases: Mapped[list["JurisdictionAlias"]] = relationship(back_populates="jurisdiction")


class JurisdictionAlias(Base):
    __tablename__ = "jurisdiction_alias"
    __table_args__ = {"schema": "core"}

    id: Mapped[int] = mapped_column(primary_key=True)
    jurisdiction_id: Mapped[int] = mapped_column(ForeignKey("core.jurisdiction.id"))
    alias: Mapped[str] = mapped_column(String(200))

    jurisdiction: Mapped[Jurisdiction] = relationship(back_populates="aliases")
```

- [ ] **Step 4: Write the repository**

`app/modules/core/repository.py`:
```python
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction


class DuplicateCodeError(Exception):
    pass


class JurisdictionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, code: str, name: str) -> Jurisdiction:
        jurisdiction = Jurisdiction(code=code, name=name)
        self.session.add(jurisdiction)
        try:
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise DuplicateCodeError(code) from exc
        return jurisdiction

    def get(self, id: int) -> Jurisdiction | None:
        return self.session.get(Jurisdiction, id)

    def get_by_code(self, code: str) -> Jurisdiction | None:
        return self.session.scalar(select(Jurisdiction).where(Jurisdiction.code == code))

    def list(self) -> list[Jurisdiction]:
        return list(self.session.scalars(select(Jurisdiction).order_by(Jurisdiction.code)))
```

> Note: the test calls `db_session.flush()` after a failing `create`; because `create` already rolls back the nested state on `IntegrityError`, re-raising as `DuplicateCodeError`, the second `flush()` in the test is a no-op on an empty pending set. Keep the `raise` inside `create`.

- [ ] **Step 5: Write the migration and enable the model import**

`migrations/versions/0002_core_jurisdiction.py`:
```python
"""core.jurisdiction and alias

Revision ID: 0002
Revises: 0001
"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jurisdiction",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(8), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.UniqueConstraint("code", name="uq_jurisdiction_code"),
        schema="core",
    )
    op.create_table(
        "jurisdiction_alias",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("jurisdiction_id", sa.Integer, sa.ForeignKey("core.jurisdiction.id"), nullable=False),
        sa.Column("alias", sa.String(200), nullable=False),
        schema="core",
    )


def downgrade() -> None:
    op.drop_table("jurisdiction_alias", schema="core")
    op.drop_table("jurisdiction", schema="core")
```

In `migrations/env.py`, ensure the import is active:
```python
from app.modules.core import models as _core_models  # noqa: F401
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_jurisdiction_repository.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add app/modules/core migrations/versions/0002_core_jurisdiction.py migrations/env.py tests/test_jurisdiction_repository.py
git commit -m "feat: core.jurisdiction model, migration, and repository"
```

---

### Task 6: `source` models & evidence service stub

**Files:**
- Create: `app/modules/source/__init__.py`, `app/modules/source/models.py`, `app/modules/source/service.py`
- Create: `migrations/versions/0003_source_evidence.py`
- Modify: `migrations/env.py` (add source models import)
- Test: `tests/test_source_evidence.py`

**Interfaces:**
- Consumes: `app.db.Base`, `db_session`.
- Produces:
  - `SourceDocument(id: int, title: str, url: str, retrieved_at: datetime, content_hash: str)` in schema `source`.
  - `SourceEvidence(id: int, document_id: int, article: str | None, page: int | None, quoted_text: str, review_status: str)` in schema `source`.
  - `EvidenceService(session: Session)` with `get(evidence_id: int) -> EvidenceView | None` where `EvidenceView` is a dataclass `{id, document_title, document_url, article, quoted_text, review_status}`. This is the single interface later phases use to resolve any figure to its source.

- [ ] **Step 1: Write the failing test**

`tests/test_source_evidence.py`:
```python
from datetime import datetime, timezone

from app.modules.source.models import SourceDocument, SourceEvidence
from app.modules.source.service import EvidenceService


def test_evidence_resolves_to_document(db_session):
    doc = SourceDocument(
        title="UAE Corporate Tax Law",
        url="https://mof.gov.ae/corporate-tax/",
        retrieved_at=datetime.now(timezone.utc),
        content_hash="abc123",
    )
    db_session.add(doc)
    db_session.flush()
    ev = SourceEvidence(
        document_id=doc.id,
        article="Art. 16",
        page=12,
        quoted_text="Withholding tax ... 0%",
        review_status="human_verified",
    )
    db_session.add(ev)
    db_session.flush()

    view = EvidenceService(db_session).get(ev.id)
    assert view is not None
    assert view.document_title == "UAE Corporate Tax Law"
    assert view.article == "Art. 16"
    assert view.review_status == "human_verified"


def test_missing_evidence_returns_none(db_session):
    assert EvidenceService(db_session).get(999999) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_source_evidence.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the models**

`app/modules/source/__init__.py`: empty file.

`app/modules/source/models.py`:
```python
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SourceDocument(Base):
    __tablename__ = "source_document"
    __table_args__ = {"schema": "source"}

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(1000))
    retrieved_at: Mapped[datetime] = mapped_column()
    content_hash: Mapped[str] = mapped_column(String(64))


class SourceEvidence(Base):
    __tablename__ = "source_evidence"
    __table_args__ = {"schema": "source"}

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("source.source_document.id"))
    article: Mapped[str | None] = mapped_column(String(100), nullable=True)
    page: Mapped[int | None] = mapped_column(nullable=True)
    quoted_text: Mapped[str] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(32), default="unreviewed")
```

- [ ] **Step 4: Write the service**

`app/modules/source/service.py`:
```python
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.modules.source.models import SourceDocument, SourceEvidence


@dataclass(frozen=True)
class EvidenceView:
    id: int
    document_title: str
    document_url: str
    article: str | None
    quoted_text: str
    review_status: str


class EvidenceService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, evidence_id: int) -> EvidenceView | None:
        ev = self.session.get(SourceEvidence, evidence_id)
        if ev is None:
            return None
        doc = self.session.get(SourceDocument, ev.document_id)
        assert doc is not None  # FK guarantees presence
        return EvidenceView(
            id=ev.id,
            document_title=doc.title,
            document_url=doc.url,
            article=ev.article,
            quoted_text=ev.quoted_text,
            review_status=ev.review_status,
        )
```

- [ ] **Step 5: Write the migration and enable the import**

`migrations/versions/0003_source_evidence.py`:
```python
"""source document and evidence

Revision ID: 0003
Revises: 0002
"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "source_document",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        schema="source",
    )
    op.create_table(
        "source_evidence",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("document_id", sa.Integer, sa.ForeignKey("source.source_document.id"), nullable=False),
        sa.Column("article", sa.String(100), nullable=True),
        sa.Column("page", sa.Integer, nullable=True),
        sa.Column("quoted_text", sa.Text, nullable=False),
        sa.Column("review_status", sa.String(32), nullable=False, server_default="unreviewed"),
        schema="source",
    )


def downgrade() -> None:
    op.drop_table("source_evidence", schema="source")
    op.drop_table("source_document", schema="source")
```

Add to `migrations/env.py`:
```python
from app.modules.source import models as _source_models  # noqa: F401
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_source_evidence.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add app/modules/source migrations/versions/0003_source_evidence.py migrations/env.py tests/test_source_evidence.py
git commit -m "feat: source document/evidence models and evidence service stub"
```

---

### Task 7: `saas` auth — org/user/api-key & API-key dependency

**Files:**
- Create: `app/modules/saas/__init__.py`, `app/modules/saas/models.py`, `app/modules/saas/security.py`, `app/deps.py`
- Create: `migrations/versions/0004_saas_auth.py`
- Modify: `migrations/env.py` (add saas models import)
- Test: `tests/test_auth.py`

**Interfaces:**
- Consumes: `app.db.Base`, `get_session`, `app.config.get_settings`, `db_session`, `client`.
- Produces:
  - `OrganisationAccount(id, name)`, `User(id, org_id, email)`, `ApiKey(id, org_id, key_hash, active)` in schema `saas`.
  - `app.modules.saas.security.hash_api_key(raw: str) -> str` (sha256 hex), `generate_api_key() -> tuple[str, str]` returning `(raw, key_hash)`.
  - `app.deps.require_api_key` — a FastAPI dependency returning the authenticated `ApiKey`'s `org_id: int`, raising `HTTPException(401)` when the header is missing or the key is unknown/inactive.

- [ ] **Step 1: Write the failing test**

`tests/test_auth.py`:
```python
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.deps import require_api_key
from app.modules.saas.models import ApiKey, OrganisationAccount
from app.modules.saas.security import generate_api_key, hash_api_key


def test_hash_is_deterministic():
    assert hash_api_key("abc") == hash_api_key("abc")
    assert len(hash_api_key("abc")) == 64


def _app_with_protected_route() -> FastAPI:
    app = FastAPI()

    @app.get("/protected")
    def protected(org_id: int = Depends(require_api_key)) -> dict[str, int]:
        return {"org_id": org_id}

    return app


def test_missing_key_is_401():
    client = TestClient(_app_with_protected_route())
    assert client.get("/protected").status_code == 401


def test_valid_key_authenticates(db_session, monkeypatch):
    org = OrganisationAccount(name="Acme Tax")
    db_session.add(org)
    db_session.flush()
    raw, key_hash = generate_api_key()
    db_session.add(ApiKey(org_id=org.id, key_hash=key_hash, active=True))
    db_session.flush()

    # Route uses the same db_session via dependency override.
    from app.db import get_session

    app = _app_with_protected_route()
    app.dependency_overrides[get_session] = lambda: iter([db_session])
    client = TestClient(app)
    resp = client.get("/protected", headers={"X-API-Key": raw})
    assert resp.status_code == 200
    assert resp.json() == {"org_id": org.id}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_auth.py -v`
Expected: FAIL — modules not found.

- [ ] **Step 3: Write security helpers**

`app/modules/saas/__init__.py`: empty file.

`app/modules/saas/security.py`:
```python
import hashlib
import secrets


def hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def generate_api_key() -> tuple[str, str]:
    raw = secrets.token_urlsafe(32)
    return raw, hash_api_key(raw)
```

- [ ] **Step 4: Write the models**

`app/modules/saas/models.py`:
```python
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class OrganisationAccount(Base):
    __tablename__ = "organisation_account"
    __table_args__ = {"schema": "saas"}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))


class User(Base):
    __tablename__ = "user"
    __table_args__ = {"schema": "saas"}

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("saas.organisation_account.id"))
    email: Mapped[str] = mapped_column(String(320), unique=True)


class ApiKey(Base):
    __tablename__ = "api_key"
    __table_args__ = {"schema": "saas"}

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("saas.organisation_account.id"))
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
```

- [ ] **Step 5: Write the dependency**

`app/deps.py`:
```python
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.modules.saas.models import ApiKey
from app.modules.saas.security import hash_api_key


def require_api_key(
    x_api_key: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> int:
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required")
    key = session.scalar(
        select(ApiKey).where(ApiKey.key_hash == hash_api_key(x_api_key), ApiKey.active.is_(True))
    )
    if key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return key.org_id
```

- [ ] **Step 6: Write the migration and enable the import**

`migrations/versions/0004_saas_auth.py`:
```python
"""saas org, user, api key

Revision ID: 0004
Revises: 0003
"""
import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organisation_account",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        schema="saas",
    )
    op.create_table(
        "user",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, sa.ForeignKey("saas.organisation_account.id"), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.UniqueConstraint("email", name="uq_user_email"),
        schema="saas",
    )
    op.create_table(
        "api_key",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.Integer, sa.ForeignKey("saas.organisation_account.id"), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("key_hash", name="uq_api_key_hash"),
        schema="saas",
    )


def downgrade() -> None:
    op.drop_table("api_key", schema="saas")
    op.drop_table("user", schema="saas")
    op.drop_table("organisation_account", schema="saas")
```

Add to `migrations/env.py`:
```python
from app.modules.saas import models as _saas_models  # noqa: F401
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `uv run pytest tests/test_auth.py -v`
Expected: PASS (all three).

- [ ] **Step 8: Commit**

```bash
git add app/modules/saas app/deps.py migrations/versions/0004_saas_auth.py migrations/env.py tests/test_auth.py
git commit -m "feat: saas org/user/api-key models and api-key auth dependency"
```

---

### Task 8: `GET /v1/jurisdictions` endpoint (authenticated)

**Files:**
- Create: `app/api/v1/jurisdictions.py`, `app/errors.py`
- Modify: `app/api/v1/__init__.py` (include router), `app/main.py` (register error handler)
- Test: `tests/test_jurisdictions_api.py`

**Interfaces:**
- Consumes: `require_api_key`, `get_session`, `JurisdictionRepository`.
- Produces:
  - `GET /v1/jurisdictions` → `200` list of `{id, code, name}` (requires API key).
  - `GET /v1/jurisdictions/{id}` → `200` one `{id, code, name}` or `404 {"detail": "jurisdiction not found"}`.
  - `app.errors.NotFoundError` + handler returning `404` JSON.

- [ ] **Step 1: Write the failing test**

`tests/test_jurisdictions_api.py`:
```python
from fastapi.testclient import TestClient

from app.db import get_session
from app.deps import require_api_key
from app.main import create_app
from app.modules.core.models import Jurisdiction


def _client_with_session(db_session) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: iter([db_session])
    app.dependency_overrides[require_api_key] = lambda: 1
    return TestClient(app)


def test_list_requires_api_key():
    client = TestClient(create_app())
    assert client.get("/v1/jurisdictions").status_code == 401


def test_list_returns_jurisdictions(db_session):
    db_session.add(Jurisdiction(code="AE", name="United Arab Emirates"))
    db_session.flush()
    client = _client_with_session(db_session)
    resp = client.get("/v1/jurisdictions")
    assert resp.status_code == 200
    assert {"code": "AE", "name": "United Arab Emirates"} in [
        {"code": j["code"], "name": j["name"]} for j in resp.json()
    ]


def test_get_unknown_id_is_404(db_session):
    client = _client_with_session(db_session)
    resp = client.get("/v1/jurisdictions/999999")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "jurisdiction not found"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_jurisdictions_api.py -v`
Expected: FAIL — route/module missing.

- [ ] **Step 3: Write the error type and handler**

`app/errors.py`:
```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class NotFoundError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def _not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": exc.detail})
```

- [ ] **Step 4: Write the endpoint**

`app/api/v1/jurisdictions.py`:
```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import require_api_key
from app.errors import NotFoundError
from app.modules.core.repository import JurisdictionRepository

router = APIRouter(prefix="/v1/jurisdictions", tags=["jurisdictions"])


class JurisdictionOut(BaseModel):
    id: int
    code: str
    name: str


@router.get("", response_model=list[JurisdictionOut])
def list_jurisdictions(
    _org_id: int = Depends(require_api_key),
    session: Session = Depends(get_session),
) -> list[JurisdictionOut]:
    repo = JurisdictionRepository(session)
    return [JurisdictionOut(id=j.id, code=j.code, name=j.name) for j in repo.list()]


@router.get("/{jurisdiction_id}", response_model=JurisdictionOut)
def get_jurisdiction(
    jurisdiction_id: int,
    _org_id: int = Depends(require_api_key),
    session: Session = Depends(get_session),
) -> JurisdictionOut:
    repo = JurisdictionRepository(session)
    j = repo.get(jurisdiction_id)
    if j is None:
        raise NotFoundError("jurisdiction not found")
    return JurisdictionOut(id=j.id, code=j.code, name=j.name)
```

- [ ] **Step 5: Wire router and handler**

In `app/api/v1/__init__.py`:
```python
from fastapi import APIRouter

from app.api.v1 import health, jurisdictions

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(jurisdictions.router)
```

In `app/main.py`, register handlers inside `create_app` before `return app`:
```python
    from app.errors import register_error_handlers

    register_error_handlers(app)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_jurisdictions_api.py -v`
Expected: PASS (all three).

- [ ] **Step 7: Commit**

```bash
git add app/api app/errors.py app/main.py tests/test_jurisdictions_api.py
git commit -m "feat: authenticated /v1/jurisdictions endpoint with 404 handling"
```

---

### Task 9: CI pipeline & README quickstart

**Files:**
- Create: `.github/workflows/ci.yml`, `README.md`

**Interfaces:**
- Consumes: the whole project.
- Produces: a CI job that lints, type-checks, and tests against a Postgres service; a README that documents local setup.

- [ ] **Step 1: Write the CI workflow**

`.github/workflows/ci.yml`:
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: app
          POSTGRES_PASSWORD: app
          POSTGRES_DB: app
        ports:
          - "5432:5432"
        options: >-
          --health-cmd "pg_isready -U app"
          --health-interval 5s
          --health-timeout 3s
          --health-retries 10
    env:
      APP_DATABASE_URL: postgresql+psycopg://app:app@localhost:5432/app
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with:
          python-version: "3.12"
      - run: uv sync --frozen
      - run: uv run ruff check .
      - run: uv run mypy app
      - run: uv run pytest -v
```

- [ ] **Step 2: Write the README**

`README.md`:
```markdown
# Jurisdiction Recommender

Phase P0 foundations. See `docs/superpowers/specs/2026-10-04-tax-jurisdiction-recommender-design.md`.

## Local setup

```bash
uv sync
docker compose up -d db
cp .env.example .env
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Checks

```bash
uv run ruff check .
uv run mypy app
uv run pytest -v
```
```

- [ ] **Step 3: Verify the full suite locally**

Run:
```bash
docker compose up -d db
uv run ruff check . && uv run mypy app && uv run pytest -v
```
Expected: ruff clean, mypy clean, all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci.yml README.md
git commit -m "ci: lint, type-check, and test on postgres; add readme"
```

---

## Self-Review

**1. Spec coverage (P0 slice of spec §2, §4, §8):**
- Modular monolith + bounded-context packages → Tasks 2, 5, 6, 7 ✅
- PostgreSQL with all spec schemas provisioned → Task 4 ✅
- Evidence service as the single fact→source resolver → Task 6 ✅
- SaaS auth (org/user/API key) → Task 7 ✅
- `/v1` API surface (jurisdictions; health) → Tasks 2, 8 ✅
- Later-phase schemas (`tax`, `treaty`, `risk`, `recommender`, `workflow`) created empty now → Task 4 ✅
- Out of P0 scope (deferred to later plans): tax/treaty/scoring engines, LLM service, onboarding, metering/billing, ingestion. Documented in spec §9 build order.

**2. Placeholder scan:** No TBD/TODO; every code step contains runnable code. The one forward-reference (env.py importing `core.models` before Task 5) is called out explicitly with instructions to comment/uncomment. ✅

**3. Type consistency:** `JurisdictionRepository` methods (`create/get/get_by_code/list`) used identically in Tasks 5 and 8. `require_api_key` returns `int` (org_id) and is consumed as `int` in Task 8. `EvidenceView` fields match between service and test. `hash_api_key`/`generate_api_key` signatures consistent across Task 7. ✅

**4. Review Focus coverage:**
- Missing/invalid API key → Task 7 `test_missing_key_is_401`, and Task 8 `test_list_requires_api_key` ✅
- Unknown jurisdiction id → Task 8 `test_get_unknown_id_is_404` ✅
- Duplicate code → Task 5 `test_duplicate_code_raises` ✅
- DB unreachable readiness split → Task 2 `test_ready_returns_503_when_db_unreachable` ✅
- Migration idempotency → Task 4 `test_migrations_are_idempotent` ✅

---

## Next plans (not in this document)

Each later phase from spec §9 gets its own plan → implementation cycle:
P1 tax+treaty core (with the France–UAE golden fixture), P2 lists & review,
P3 engines, P4 scoring, P5 product UI, P6 LLM, P7 SaaS hardening, P8 scale.
