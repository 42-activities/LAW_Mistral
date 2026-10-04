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

## Analysis API (P3 engines)

All endpoints take an `X-API-Key` header. Rates are percentages; every result lists the
`source_evidence` ids it was derived from and flags any assumption or missing data.

- `POST /v1/analyze/withholding-tax` — domestic rate, list-triggered consequence, treaty cap,
  amount withheld at payment and final rate for one payment.
- `GET /v1/analyze/jurisdiction-risk?jurisdiction=AE&on_date=2024-06-30` — list memberships.
- `POST /v1/analyze/flow` — tax leakage per 100 of income along source → holding → parent.
- `POST /v1/analyze/holding-recommendation` — ranked ScoreCards (tax efficiency, compliance,
  treaty breadth, substance burden) for a profile; guardrails cap FATF-black and
  counterparty-ETNC jurisdictions; every run is stored in `recommender.scoring_run`.

Seed the France–UAE golden data with `docker compose exec app python -m app.cli seed-france-uae`.
