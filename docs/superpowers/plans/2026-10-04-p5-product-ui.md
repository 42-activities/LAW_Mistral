# P5 Product UI — implementation notes

**Goal (spec §6–7, §9):** demoable France–UAE recommendation in a web app: onboarding wizard,
profile builder, recommendation results with re-weighting and flow-by-flow citations,
browse / compare / lists / evidence drill-down, disclaimers throughout.

## Backend
- `recommender.question_definition` (migration 0015), seeded with the 3 system-owned questions
  (size → substance capacity, activity → proposed flows, flows + source jurisdictions + parent).
- Deterministic profile builder (`app/modules/recommender/builder.py`): validates against the
  offered options (disabled options such as capital gains are rejected) and expands
  flows × sources into the `ScoringProfile`.
- `GET /v1/onboarding/questions`, `POST /v1/profiles`, `GET /v1/profiles/{id}` (org-scoped),
  `holding-recommendation` accepts `profile_id`, `GET /v1/browse/jurisdictions/{code}`,
  `GET /v1/lists`, `GET /v1/evidence/{id}` — all as-of a date.

## Web (`web/`, Next.js 16, React 19, Tailwind 4)
- Server components call the API over the compose network with a server-side key
  (`WEB_API_KEY`); the browser never sees it. Next rewrites `/v1`, `/docs`, `/openapi.json` and
  `/health*` to the API, so the site is the single public entry point (`APP_BIND`) and the host
  nginx config is unchanged.
- Pages: `/`, `/analyze` (wizard, server action), `/analyze/[id]` (ScoreCards, re-weight via GET
  params, data-as-of date), `/jurisdictions`, `/jurisdictions/[code]`, `/compare`, `/lists`,
  `/evidence/[id]`.
- The AI summary slot is labelled as coming in P6.

## Deferred
User accounts/sessions (the site acts as one organisation — P7), rate limiting (P7),
a profile history page, capital-gains flows.
