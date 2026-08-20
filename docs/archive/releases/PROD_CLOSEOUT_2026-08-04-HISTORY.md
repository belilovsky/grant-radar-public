# QAZ.FUND production closeout – opportunity history.v1

## Release identity

- Checkout: `/Users/belilovsky/Documents/Codex/2026-05-21/grant-radar-public`
- Branch: `codex/qaz-fund-reuse-boundary-20260728`
- Runtime: `root@148.230.117.131:/opt/grant-radar`
- Public domain: `https://qaz.fund`
- Deployed revision: `51419e0f4ac9437d420b8c50435519388f633c6c`
- Release marker: `/.well-known/release.json`

## Delivered slice

The public opportunity history contract is now live:

`GET /opportunities/{id}/history.json?lang=kk|ru|en&limit={n}`

- Schema: `history.v1`.
- A record contains only normalized public fields, a content hash, the
  observed timestamp, version number and changed-field list.
- Raw HTML, parser payloads, operator notes and subscriber data are excluded.
- Existing production migration lineage is preserved:
  `0005_opportunity_observations -> 0006_opportunity_versions`.
- The migration is idempotent for a table created by an earlier partial release:
  it keeps existing rows, creates only missing indexes and backfills only cards
  that have no history yet.
- The endpoint is linked from site discovery, `llms.txt`, the ecosystem
  manifest and the public AI-consumption template.

## Verification

- `PYTHONPATH=. .venv/bin/pytest -q`: **484 passed**.
- `make lint`: Black, isort, flake8, mypy and vulture passed.
- `git diff --check`: passed; working tree clean.
- `make smoke-prod`: passed on `https://qaz.fund`.
- `make content-audit`: passed; 26 sources, 393 relevant open cards, 0 stale
  sources, 0 unknown-freshness sources, no content issues.
- Public `/health`: 1,280 records; `/ready`: database backend.
- Production database: 1,792 history rows covering all 1,280 opportunity IDs;
  Alembic reports one head, `0006_opportunity_versions`.
- Public sample verified with a real opportunity ID: `schema_version=history.v1`,
  `status=ready`, at least one version, initial change marker, and no `raw`
  field in the public snapshot.
- All discovery, AVDS4, QazStack, comparison and notification-contract markers
  remain green in the smoke result.

## Remaining boundary

History is a read-only evidence surface. It does not infer eligibility, verify
the source independently, or activate notifications. Notification delivery
remains explicitly disabled until identity, consent, unsubscribe and delivery
observability contracts are implemented and tested.

## Rollback

Redeploy the previous verified revision with `scripts/deploy_qaz_fund.sh`.
Do not drop `opportunity_versions`; the migration is additive and preserves
the public evidence trail.
