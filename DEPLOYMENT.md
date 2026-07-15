# Deployment Guide

This repository keeps a public-safe deployment guide. Server inventory,
hostnames, SSH targets, backup paths, and incident history should live in a
separate maintainer runbook.

## Prerequisites

- Docker and Docker Compose
- Python 3.12+
- A PostgreSQL database
- A Redis instance
- A public base URL for the dashboard

## Environment

Start from `.env.example` and create a server-local `.env.prod`:

```bash
cp .env.example .env.prod
chmod 600 .env.prod
```

Set at minimum:

- `POSTGRES_PASSWORD`
- `DATABASE_URL` or `GRANT_RADAR_DB_URL`
- `PUBLIC_BASE_URL`
- `GRANT_RADAR_ADMIN_TOKEN`

Optional integrations such as Telegram or Sentry can stay empty until needed.

## Container deployment

Build and run:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

The production image uses `requirements-prod.txt` and runs
`scripts/entrypoint.sh`, which applies Alembic migrations before uvicorn
starts. In the standard Compose layout the API is the single migration owner;
the worker skips migrations to avoid a concurrent Alembic run. Disable the
behavior for other one-off jobs with `GRANT_RADAR_SKIP_MIGRATIONS=1`.

The worker records one `runs` row per source cycle using the existing schema.
This is also the freshness evidence for sources that return no records. Do not
seed or update these rows manually: a successful real fetch cycle is the gate.

## Reverse proxy

Put the API behind a reverse proxy that forwards the public host to the
container port configured by `docker-compose.prod.yml`. Keep TLS termination,
rate limits, and logging in the reverse proxy layer.

Recommended forwarded headers:

- `Host`
- `X-Real-IP`
- `X-Forwarded-For`
- `X-Forwarded-Proto`

## Release checks

Before deploy:

```bash
make lint
make ci-fast
PYTHONPATH=. ./.venv/bin/python -m scripts.production_smoke --base-url https://example.org
PYTHONPATH=. ./.venv/bin/python -m scripts.content_audit --base-url https://example.org
PYTHONPATH=. ./.venv/bin/python -m scripts.nlp_quality_audit --base-url https://example.org --lang ru --limit 150
PYTHONPATH=. ./.venv/bin/python -m scripts.nlp_quality_audit --base-url https://example.org --lang en --limit 150
```

For a production release, set both the private deployment target and the public
URL. The deploy helper refuses to claim success until the public route reports
the exact Git revision that was just built:

```bash
DEPLOY_HOST=deploy@example.org \
PUBLIC_URL=https://example.org \
bash scripts/deploy_qaz_fund.sh
```

Use `REQUIRE_PUBLIC_VERIFY=0` only for an intentionally private staging target.
It must not be used for the public QAZ.FUND release. This distinction matters
when TLS/edge and application origin are separate hosts.

After deploy:

```bash
curl -fsS https://example.org/health
curl -fsS https://example.org/ready
curl -fsSI https://example.org/ready
curl -fsSI https://example.org/favicon.ico
curl -fsS 'https://example.org/opportunities?limit=3'
```

## Backups

Create encrypted database dumps outside the repository and verify a restore
regularly. The helper retains the newest fourteen archives by default:

```bash
BACKUP_DIR=/var/backups/grant-radar ./scripts/backup_postgres.sh
```

Schedule this command from the private maintainer runbook only after a restore
drill. Do not commit dump files or host-specific backup paths.

## Automation

The repository includes helper scripts such as `scripts/deploy_qaz_fund.sh` and
`scripts/qaz_fund_cutover.sh`, but they intentionally require explicit host and
certificate configuration through environment variables. Do not hardcode live
infrastructure details into the public repository.

`scripts/deploy_qaz_fund.sh` is conservative by default: it syncs the tree
without `--delete`. If you intentionally want rsync to remove files on the
target, opt in explicitly with `RSYNC_DELETE=1`. The script also waits for the
API container to answer `GET /ready` before it prints a successful deploy
result; tune this with `READY_URL`, `READY_ATTEMPTS`, and `READY_DELAY` if the
runtime shape changes. It also injects `APP_REVISION` and `APP_DEPLOYED_AT` into
the containers and verifies `/.well-known/release.json` through `PUBLIC_URL`.
That endpoint is also linked from `site-discovery.json` for machine consumers.
