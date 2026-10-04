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
