# Deployment Guide

This repository keeps a public-safe deployment guide. Private server inventory,
hostnames, SSH targets, backup paths, and incident history should live in a
separate operator runbook.

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
starts. Disable that behavior for one-off jobs with
`GRANT_RADAR_SKIP_MIGRATIONS=1`.

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
```

After deploy:

```bash
curl -fsS https://example.org/health
curl -fsS https://example.org/ready
curl -fsSI https://example.org/favicon.ico
curl -fsS 'https://example.org/opportunities?limit=3'
```

If Russian localization is enabled in your storage backend, you can also run:

```bash
PYTHONPATH=. ./.venv/bin/python -m scripts.nlp_quality_audit --base-url https://example.org --lang ru --limit 150
```

## Automation

The repository includes helper scripts such as `scripts/deploy_qaz_fund.sh` and
`scripts/qaz_fund_cutover.sh`, but they intentionally require explicit host and
certificate configuration through environment variables. Do not hardcode live
infrastructure details into the public repository.
