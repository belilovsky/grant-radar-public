# grant-radar

QAZ.FUND is a public opportunity navigator for grants, accelerators, cloud
credits, tenders, and support programs relevant to Kazakhstan and Central Asia.
It helps people find a route, check the source, and keep the next step clear.

## What it does

- collects opportunities from public source adapters;
- normalizes, deduplicates, and scores them;
- serves a public FastAPI dashboard and JSON endpoints;
- supports localized Kazakh, Russian, and English detail pages and public
  shareable permalinks; original source language and translation availability
  remain explicit in each record.

The repository is structured for clean local development, reproducible
validation, and public-safe deployment documentation.

This is the primary development repository for the project.

## Repository map

- `grant-radar-public`
  - primary development repository
  - source of truth for code, tests, migrations, and contributor docs
- `grant-radar-ops`
  - private maintainer and operations context only
  - not a parallel product-code repository
- `grant-radar`
  - legacy transition checkout
  - kept only as historical local context after the repo split

The main public endpoints are:

- `GET /health`
- `GET /ready`
- `GET /sources`
- `GET /coverage`
- `GET /status?lang=kk|ru|en`
- `GET /funders`
- `GET /opportunities`
- `GET /opportunities.ndjson`
- `GET /opportunities/{opportunity_id}`
- `GET /opportunities/{opportunity_id}/history.json?lang=kk|ru|en`
- `GET /.well-known/source-onboarding.json` – machine-readable admission
  boundary for active and prospective sources
- `GET /opportunity/{opportunity_id}?lang=kk|ru|en`
- `GET /funder/{funder_slug}?lang=kk|ru|en`
- `GET /media?lang=kk|ru|en`
- `GET /media.json?lang=kk|ru|en`
- `GET /media/feed.json?lang=kk|ru|en` (JSON Feed 1.1)
- `GET /media/rss.xml?lang=kk|ru|en` (RSS 2.0)
- `GET /insights?lang=kk|ru|en`
- `GET /terms?lang=kk|ru|en`
- `GET /data-policy?lang=kk|ru|en`
- `GET /attribution?lang=kk|ru|en`
- `GET /digest`
- `GET /api/v1/insights`
- `GET /api/v1/changes`
- `GET /media/v1/digest/daily.json`
- `GET /media/v1/digest/daily.txt`
- `GET /docs`
- `GET /openapi.json`
- `GET /robots.txt`
- `GET /sitemap.xml`
- `GET /llms.txt`
- `GET /site-discovery.json`
- `GET /og-image.png` (crawler-safe social preview; `/og-image.svg` remains available)
- `GET /operator` (noindex operator shell; token is never embedded in HTML)
- `GET /operator/health` (requires `GRANT_RADAR_ADMIN_TOKEN`)
- `POST /refresh` (requires `GRANT_RADAR_ADMIN_TOKEN`)

For machine consumers, `llms.txt` and `site-discovery.json` publish the public
entry points, read-only JSON/NDJSON endpoints, and supported query templates.
The history endpoint exposes only normalized public field changes and returns an
explicit `not_available` status when no snapshot backend is configured.
Use `/opportunities.ndjson?compact=true` for bulk discovery; keep the full
`/opportunities.ndjson` export for consumers that explicitly need raw source
payloads.

`/insights` is the public data-centre view. It reports only values derived from
the current catalogue and observation ledger. The application workspace stores
draft content in the browser and never submits it to QAZ.FUND.

## Quick start

### Host-based setup

```bash
make bootstrap BOOTSTRAP_PYTHON=python3.12
cp .env.example .env.dev
make ci-fast
```

For a lightweight local setup, keep
`GRANT_RADAR_DB_URL=sqlite:///./data/grants.db` in `.env.dev`.

Local bootstrap expects Python 3.12+. On machines where `python3` still points
to 3.9 or 3.10, pass `BOOTSTRAP_PYTHON=python3.12` explicitly or use the Docker
workflow instead.

If you already have an older `.venv`, run:

```bash
make bootstrap-reset BOOTSTRAP_PYTHON=python3.12
```

### Docker-based setup

```bash
cp .env.example .env.dev
make dev
```

Local surfaces:

- API: `http://localhost:8000`
- PostgreSQL: `localhost:5434`

Useful commands:

- `make lint`
- `make ci-fast`
- `make ci`
- `make format`
- `make db-upgrade`
- `make show-runs`
- `python -m scripts.performance_smoke --base-url http://localhost:8000`

The local workbench export creates a safe editorial handoff from public
Opportunities NDJSON. It writes normalized `workbench.json`,
`opportunities.csv`, and `README.md` files without carrying the `raw` payload,
storing user selections, or enabling notifications. See
[docs/WORKBENCH_EXPORT.md](docs/WORKBENCH_EXPORT.md).

## Active source coverage

Current ingestion includes public programs and monitors such as:

- `grants_gov`
- `astana_hub`
- `internews`
- `isdb_project_procurement`
- `ebrd_ecepp_procurement`
- `erasmus_kazakhstan`
- `opportunity_desk`
- `fundsforngos`
- `kazakhstan_domestic_support`
- `kazakhstan_watch`
- `eeas_kazakhstan`
- `world_bank_kazakhstan`
- `world_bank_procurement_ca`
- `eu_funding_tenders_ca`
- `canada_cfli_ca`
- `undp_procurement`
- `adb_kazakhstan`
- `google_cloud_startup`
- `microsoft_founders_hub`
- `aws_activate`
- `nvidia_inception`
- `cloudflare_startups`
- `mongodb_startups`
- `unicef_kazakhstan`
- `google_org_ai_opportunity`
- `unesco_iite`
- `ungm_opportunities`
- `osce_procurement`
- `iom_kazakhstan_procurement`
- `edb_procurement`
- `daad_central_asia`
- `gef_sgp_kazakhstan`
- `global_innovation_fund`

See [docs/SOURCE_REGISTRY.md](docs/SOURCE_REGISTRY.md)
for source-specific notes and priorities.

## Project layout

```text
grant-radar/
├── api/         FastAPI app and server-rendered public pages
├── core/        ingestion, scoring, scheduling, repositories
├── sources/     source adapters and parsers
├── scripts/     maintenance and audit utilities
├── tests/       local verification suite
├── alembic/     database migrations
└── docs/        product, persistence, deploy, and release notes
```

## Quality checks

Run lint and tests before opening or updating a pull request.
The same checks are available locally:

```bash
make lint
make ci-fast
```

`make ci` runs the docker-based validation pass.

## Production notes

`Dockerfile.prod` runs `scripts/entrypoint.sh`, which applies
`alembic upgrade head` before starting uvicorn. Real `.env.dev`,
`.env.staging`, and `.env.prod` files must stay local to the machine or server.
Production defaults to two Uvicorn workers, bounded source-fetch concurrency,
and a Compose worker heartbeat; see the runtime guide before changing them.

Deployment guidance lives in [DEPLOYMENT.md](DEPLOYMENT.md) and
[docs/PRODUCTION_CHECKLIST.md](docs/PRODUCTION_CHECKLIST.md).

## Docs

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [docs/DEVELOPMENT_MODEL.md](docs/DEVELOPMENT_MODEL.md)
- [SECURITY.md](SECURITY.md)
- [SUPPORT.md](SUPPORT.md)
- [docs/README.md](docs/README.md)
- [docs/PERSISTENCE.md](docs/PERSISTENCE.md)
- [docs/QAZFUND_DATA_CENTRE_2026-07-27.md](docs/QAZFUND_DATA_CENTRE_2026-07-27.md)
- [docs/UX_CJM_2026-07-27.md](docs/UX_CJM_2026-07-27.md)
- [docs/REPRODUCIBILITY_AND_RUNTIME.md](docs/REPRODUCIBILITY_AND_RUNTIME.md)
- [docs/TELEGRAM_DIGEST.md](docs/TELEGRAM_DIGEST.md)

## License

MIT
