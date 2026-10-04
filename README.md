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

## Deploy (map-tax.naurzalinov.me)

Runs on the Hetzner server from `~/projects/LAW_Mistral`, behind host nginx + certbot.
The server `.env` sets `POSTGRES_PASSWORD`, `DB_BIND=127.0.0.1:5435`, `APP_BIND=127.0.0.1:8600`,
`APP_ENVIRONMENT=production`. Migrations run on container start.

```bash
git pull && docker compose up -d --build
docker compose exec app python -m app.cli create-api-key "<org name>"
```
