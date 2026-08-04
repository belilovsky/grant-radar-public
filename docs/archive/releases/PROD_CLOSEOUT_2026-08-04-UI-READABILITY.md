# QAZ.FUND production closeout – readability and source-status slice

## Release identity

- Checkout: `/Users/belilovsky/Documents/Codex/2026-05-21/grant-radar-public`
- Branch: `codex/qaz-fund-reuse-boundary-20260728`
- Runtime: `root@148.230.117.131:/opt/grant-radar`
- Public domain: `https://qaz.fund`
- Deployed revision: `44765a1460137b201cb31184a7d98b0300292cd5`
- Release marker: `/.well-known/release.json`

## Delivered

- Added restrained alternating AVDS4 row surfaces to the public source-status
  table so long lists scan as groups without becoming visually heavy.
- Reused the curated source-label map on the status page; when a slug has no
  editorial label, the official registry name is preserved instead of exposing
  an adapter identifier such as `grants gov`.
- Kept the existing three-language shell and source links unchanged.

## Verification

- `PYTHONPATH=. .venv/bin/pytest -q`: **495 passed**.
- `make lint`: Black, isort, flake8, mypy and vulture passed.
- `make smoke-prod`: passed on the exact public revision; 1,283 health
  records, 26 sources, 394 relevant open records, 0 stale sources and 0
  unknown-freshness sources.
- `make content-audit`: passed with no issues.
- Public browser matrix: 11 routes at 390, 1,024 and 2,560 px; 30 expected
  200 responses and 3 intentional 404 responses, zero horizontal overflow and
  zero page errors. RU, KAZ and EN status shells were checked separately.

## Boundary

This is a presentation and labeling change only. It does not start collectors,
workers, subscriptions or background delivery processes and does not alter the
public data contract.
