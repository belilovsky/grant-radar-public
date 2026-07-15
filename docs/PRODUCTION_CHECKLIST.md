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
- `GET` and `HEAD /status` render public source freshness without run errors.
- `GET` and `HEAD /operator` render a noindex/no-store token entry shell.
- `GET /operator/health` must require `GRANT_RADAR_ADMIN_TOKEN`.
- `GET` and `HEAD /opportunity/{id}` render public opportunity pages.
- `GET` and `HEAD /funder/{slug}` render public funder pages.
- `GET` and `HEAD /opportunities/{id}` return public opportunity detail availability.
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

## Public UX expectations

- The public page follows a stable reading order: value proposition, live
  collections, compact audience/topic navigation, catalog, funder profiles,
  source coverage, and methodology.
- The catalog appears before funder profiles so a visitor reaches actionable
  results before secondary discovery content.
- Loading states use neutral skeletons. Public copy must not expose editorial
  notes, draft labels, implementation language, or promises that content will
  appear later.
- Funder profiles use the same Kazakhstan/Central Asia relevance scope as the
  public catalog. Domestic-only federal programs must not reappear through the
  funder index.
- Opportunity pages show source content and factual metadata before generic
  preparation guidance. Long source text is split into readable paragraphs.
- The catalog keeps primary filters visible and places lifecycle/deadline/source
  filters under "Additional filters" / "Дополнительные фильтры".
- Saved views and saved opportunity cards are browser-local only. They are not
  synchronized between devices or accounts.
- CSV export downloads the currently visible result set as
  `qazfund-opportunities.csv`.
- Calendar export downloads visible deadline items as `qazfund-deadlines.ics`.
- "Correct the data" / "Уточнить данные" links open the public GitHub Issues form with the
  opportunity page prefilled.
- The footer must state that QAZ.FUND does not award grants or process
  applications, and must link to qdev.run without turning the footer into a
  promotional block.

## Post-release checks

```bash
curl -fsS https://example.org/health
curl -fsS https://example.org/ready
curl -fsSI https://example.org/ready
curl -fsSI https://example.org/favicon.ico
curl -fsS https://example.org/llms.txt
curl -fsS https://example.org/site-discovery.json
curl -fsSI 'https://example.org/status?lang=ru'
curl -fsSI 'https://example.org/operator?lang=ru'
curl -fsSI https://example.org/docs
curl -fsS 'https://example.org/opportunities?limit=3&min_score=0.5'
curl -fsSI 'https://example.org/opportunities/<uuid>?lang=ru'
curl -fsSI 'https://example.org/opportunity/<uuid>?lang=ru'
curl -fsSI 'https://example.org/funder/<slug>?lang=ru'
curl -fsS 'https://example.org/digest?limit=5&tag=ai'
```

## Operational notes

- Run Alembic migrations before serving traffic.
- Keep database backups outside the repository and verify restore regularly.
- Create encrypted host-side dumps with `BACKUP_DIR=/var/backups/grant-radar ./scripts/backup_postgres.sh`.
- Schedule the backup script from the private maintainer runbook only after a restore drill.
- Monitor freshness in `/coverage`, especially zero-item and stale sources.
- Source freshness uses the newest successful per-source check or discovered
  record. After a first deployment of source-run recording, allow one real
  worker cycle before expecting a zero-item source to move from `unknown` to
  `fresh`; never backfill that timestamp manually.
- Keep deploy hosts, paths, backup archives, and incident history in a private
  maintainer runbook.
