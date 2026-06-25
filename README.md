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
- `GET /coverage`
- `GET /opportunities`
- `GET /opportunities/{opportunity_id}`
- `GET /opportunity/{opportunity_id}?lang=ru|en`
- `GET /digest`

## Quick start

### Host-based setup

```bash
make bootstrap
cp .env.example .env.dev
make ci-fast
```

For a lightweight local setup, keep
`GRANT_RADAR_DB_URL=sqlite:///./data/grants.db` in `.env.dev`.

### Docker-based setup

```bash
cp .env.example .env.dev
make dev
```

Local surfaces:

- API: `http://localhost:8000`
- PostgreSQL: `localhost:5434`
- Redis: `localhost:6380`

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

GitHub Actions runs lint and tests on pushes and pull requests to `main`.
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

## License

MIT
