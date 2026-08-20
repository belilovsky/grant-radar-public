# QAZ.FUND production closeout – enabled-source freshness counts

## Release identity

- Checkout: `/Users/belilovsky/Documents/Codex/2026-05-21/grant-radar-public`
- Branch: `codex/qaz-fund-reuse-boundary-20260728`
- Runtime: `root@148.230.117.131:/opt/grant-radar`
- Public domain: `https://qaz.fund`
- Deployed revision: `26ac3539d01bf8f3a4af313592c1ee54d85302a6`
- Release marker: `/.well-known/release.json`

## Delivered

Coverage summary counters now use the same enabled-source boundary as the
catalog. Disabled historical sources may remain in the detailed registry, but
they no longer inflate the public fresh, stale, or unknown totals. The
protected operator summary uses the same rule for its stale-source list.

## Verification

- `PYTHONPATH=. .venv/bin/pytest -q`: **495 passed**.
- `make lint`: Black, isort, flake8, mypy and vulture passed.
- `make smoke-prod`: passed on the exact public revision; 26 connected sources,
  26 fresh sources, 0 stale and 0 unknown-freshness sources.
- `make content-audit`: passed with no issues.
- Public `/status?lang=ru`: metrics render `26 / 26 / 0 / 0`, the source names
  remain editorially localized, and horizontal overflow is zero.

## Boundary

This is a read-model consistency fix. It does not enable a source, change
collector scheduling, alter opportunity records, or start a new background
process.
