# Production Checklist

This checklist is safe to keep in a public repository. It is intentionally
limited to repeatable validation steps and excludes live host inventory,
historic backup filenames, and maintainer-only evidence.

## Secrets and environment

- `.env*` files are local or server-only.
- `.env.example` is the only tracked environment template.
- Rotate any token or password immediately if it was ever committed.
- Keep `GRANT_RADAR_ADMIN_TOKEN` set for mutation endpoints.
- Store server env files with `chmod 600`.

## Public API expectations

- `GET` and `HEAD /health` are public.
- `GET` and `HEAD /ready` are public and must not expose secrets.
- `GET /coverage`, `GET /opportunities`, and `GET /digest` are public.
- `GET` and `HEAD /robots.txt`, `/sitemap.xml`, `/llms.txt`, and `/site-discovery.json` are public.
- `GET /docs` and `GET /openapi.json` must stay reachable for public API consumers.
- `llms.txt` and `site-discovery.json` should expose the read-only data endpoints
  and stable query templates for machine consumers.
- `POST /refresh` must require `GRANT_RADAR_ADMIN_TOKEN`.
- The production compose file must not start without `POSTGRES_PASSWORD`.
- The API container must report healthy through `GET /ready`.

## Pre-release checks

```bash
make lint
make ci-fast
PYTHONPATH=. ./.venv/bin/python -m scripts.production_smoke --base-url https://example.org
PYTHONPATH=. ./.venv/bin/python -m scripts.content_audit --base-url https://example.org
PYTHONPATH=. ./.venv/bin/python -m scripts.nlp_quality_audit --base-url https://example.org --lang ru --limit 150
PYTHONPATH=. ./.venv/bin/python -m scripts.nlp_quality_audit --base-url https://example.org --lang en --limit 150
```

## Post-release checks

```bash
curl -fsS https://example.org/health
curl -fsS https://example.org/ready
curl -fsSI https://example.org/ready
curl -fsSI https://example.org/favicon.ico
curl -fsS https://example.org/llms.txt
curl -fsS https://example.org/site-discovery.json
curl -fsSI https://example.org/docs
curl -fsS 'https://example.org/opportunities?limit=3&min_score=0.5'
curl -fsS 'https://example.org/digest?limit=5&tag=ai'
```

## Operational notes

- Run Alembic migrations before serving traffic.
- Keep database backups outside the repository and verify restore regularly.
- Create encrypted host-side dumps with `BACKUP_DIR=/var/backups/grant-radar ./scripts/backup_postgres.sh`.
- Schedule the backup script from the private maintainer runbook only after a restore drill.
- Monitor freshness in `/coverage`, especially zero-item and stale sources.
- Keep deploy hosts, paths, backup archives, and incident history in a private
  maintainer runbook.
