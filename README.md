# grant-radar

Opportunity radar for grants, accelerators, cloud credits, tenders, and public
support programs relevant to Kazakhstan and Central Asia.

## What it does

- collects opportunities from public source adapters;
- normalizes, deduplicates, and scores them;
- serves a public FastAPI dashboard and JSON endpoints;
- supports localized Russian detail pages and public shareable permalinks.

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
- `GET /status?lang=ru|en`
- `GET /insights?lang=ru|en`
- `GET /funders`
- `GET /opportunities`
- `GET /opportunities.ndjson`
- `GET /opportunities/{opportunity_id}`
- `GET /opportunity/{opportunity_id}?lang=ru|en`
- `GET /opportunity/{opportunity_id}/prepare?lang=ru|en`
- `GET /funder/{funder_slug}?lang=ru|en`
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
- `GET /operator` (noindex operator shell; token is never embedded in HTML)
- `GET /operator/health` (requires `GRANT_RADAR_ADMIN_TOKEN`)
- `POST /refresh` (requires `GRANT_RADAR_ADMIN_TOKEN`)

For machine consumers, `llms.txt` and `site-discovery.json` publish the public
entry points, read-only JSON/NDJSON endpoints, and supported query templates.
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
