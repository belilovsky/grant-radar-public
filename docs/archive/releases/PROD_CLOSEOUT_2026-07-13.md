# QAZ.FUND production closeout - 2026-07-13

## Release

- Deployed code revision: `f1919cdb7f0fe2c78e692b76c6d2f82c4767a9ed`
- Public site: `https://qaz.fund/`
- Deployment result: API, database and Redis healthy; worker running.

## Delivered

- Added a public bilingual source-status page at `/status`.
- Added a noindex, no-store operator shell at `/operator`.
- Kept the operator token out of HTML and URLs; it is sent only as a request
  header and retained in the current browser tab.
- Added server-side opportunity filters for `q`, `source`, `lifecycle` and
  `region`.
- Added `X-Total-Count` and `X-Result-Count` response headers for paginated
  catalog consumers.
- Linked the main workbench to the public status page.
- Updated `llms.txt`, `site-discovery.json`, README and the production
  checklist to match the real runtime contract.

## Verification

- `make lint`: passed (Black, isort, Flake8 and mypy).
- `PYTHONPATH=. .venv/bin/pytest -q`: `378 passed`.
- Operator JavaScript syntax check: passed with `node --check`.
- Desktop and 390px visual checks: public status and authenticated operator
  states render without page overflow or script errors.
- Production smoke: passed.
- Live counts at closeout:
  - health items: `770`;
  - enabled sources: `23`;
  - relevant open opportunities: `121`;
  - fresh sources: `22`;
  - stale content sources: `1`;
  - failed recent worker runs: `0`.
- Unauthenticated `/operator/health`: `401` as expected.
- Filtered production API returned count headers and a non-empty Astana Hub
  Kazakhstan result set.

## Known non-blocker

`kazakhstan_domestic_support` reports stale content because its latest newly
discovered record is older than 72 hours. Recent worker runs are successful,
so this is a content-freshness signal rather than a collector or deployment
failure. Keep it visible and review it on the documented weekly source cycle.

## Product boundary

Server-side accounts, cross-device synchronization and notifications remain
deliberately out of scope until authentication, privacy, retention and delivery
rules are approved. The current saved-work workflow remains browser-local.
