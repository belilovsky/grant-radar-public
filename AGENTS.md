# QAZ.FUND development contract

## Product boundary

This repository is the canonical public source for `qaz-fund` at
`https://qaz.fund`. QAZ.FUND is a public navigator for grants and support
programmes relevant to Kazakhstan. The primary journey is:

`find -> verify at the official source -> compare -> prepare locally -> export/share`

QAZ.FUND is not a grant maker, an eligibility authority, a legal adviser, or
an application-submission portal. Do not add accounts, server-side applicant
profiles, document uploads, personal notifications, or submission APIs unless
the owner explicitly changes that product boundary. Saved selections and
application drafts stay in the browser.

Russian is the primary editorial locale. Kazakh and English routes must remain
compatible and honest about translation availability; never present a fallback
as an approved translation. Relevance supports ordering and shortlisting only.
Only the programme owner can confirm eligibility, current terms, and receipt of
an application.

## Canonical owners

- `qdev-project.json`: project identity, lifecycle, capabilities, privacy and
  quality commands.
- `api/main.py`: FastAPI route registration and public machine contracts.
- `api/*_page.py`, `api/dashboard.py`, `api/dashboard_copy.py`, and
  `api/dashboard_style.py`: server-rendered public UI, localization and shared
  presentation.
- `core/`: normalization, persistence, ranking, provenance, public contracts,
  browser-only workbench data and scheduler behavior.
- `sources/`: upstream adapters and parsers. Repair the earliest broken parser
  or mapping; do not hand-edit database rows or generated exports.
- `alembic/`: schema migrations. Preserve forward/backward compatibility and
  add migration tests.
- `tests/`: characterization and regression contracts.
- `docs/qazstack/consumer-contract.json`, `qazstack-reuse.json`, and the
  `.well-known` builders in `api/`: Platform/QazStack/AVDS projections. Change
  their canonical source and regenerate; do not patch deployed JSON.
- `deploy/`, `docker-compose*.yml`, `Dockerfile*`, and deployment scripts:
  runtime and release contracts. Production changes require an explicit deploy
  request and the guarded project runbook.

## Supported local workflow

Use Python 3.12 and the repository virtual environment.

```bash
make bootstrap BOOTSTRAP_PYTHON=python3.12
make lint
make ci-fast
```

Run the narrow test for the touched behavior first, then `make lint` and
`make ci-fast`. Useful additional gates:

- public content: `make content-audit ARGS="--base-url <candidate-url>"`;
- browser matrix: `scripts/browser_matrix.py` and
  `scripts/browser_targeted_acceptance.py` against a deterministic candidate;
- production-like latency: `python -m scripts.performance_smoke --base-url <candidate-url>`;
- migrations: focused tests in `tests/test_alembic_migrations.py` before any
  database upgrade;
- deployment contracts: `tests/test_deploy_contract.py`,
  `tests/test_prod_image_contract.py`, and `tests/test_production_smoke.py`.

`make ci-fast` is the normal source gate. `make ci` is the Docker-based gate
and may create local containers; do not treat either as deployment evidence.

## Change safety

- Preserve unrelated dirty work. Never reset, clean, rewrite history, or prune
  Docker data to make a check green.
- Keep source, local candidate, artifact, runtime, and public evidence separate.
- Preserve existing public routes and JSON fields. Additive fields are allowed;
  incompatible contracts require a new version or endpoint.
- Keep unknown source facts unknown. Retain the source URL, observation time,
  freshness and uncertainty instead of guessing amounts, deadlines, eligibility
  or application steps.
- Public GET/read surfaces and the token-protected operator/refresh boundary are
  different contracts. Never expose the admin token in HTML, logs, fixtures or
  command output.
- No third-party analytics or session replay is part of the current public
  product. Restricted server request logs follow the retention stated in the
  data policy.
- Generated reports, release markers, browser screenshots, local databases,
  caches and task evidence are not canonical source inputs. Store temporary
  audit evidence outside the repository unless an established project contract
  explicitly owns it.
- Do not commit, push, publish, deploy, restart production, mutate providers or
  run active security tests without the corresponding explicit owner request.

## Full-surface checks

For shared UI or copy changes, cover the home/catalog, opportunity detail,
comparison, preparation, funder, insights, media, status/policy pages, docs,
real 404, locales, empty/degraded states and compact-to-wide viewports. For
data changes, trace `official source -> parser -> normalization -> storage and
history -> API/export -> public UI`. For release work, use the repository-native
guarded deployment and verify exact SHA, readiness, worker heartbeat, semantic
service, critical routes, rollback and public browser behavior.
