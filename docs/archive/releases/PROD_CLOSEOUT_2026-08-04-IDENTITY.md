# QAZ.FUND production closeout – identity and consent boundary

## Release identity

- Checkout: `/Users/belilovsky/Documents/Codex/2026-05-21/grant-radar-public`
- Branch: `codex/qaz-fund-reuse-boundary-20260728`
- Runtime: `root@148.230.117.131:/opt/grant-radar`
- Public domain: `https://qaz.fund`
- Deployed revision: `9e7eb2d647ada989bd7cf2fa5562a1c308fa5df7`

## Delivered slice

`notification-v1` now states the complete current boundary, not just delivery:

- anonymous read access is enabled, but there is no authenticated owner,
  server profile or cross-device synchronization;
- saved views remain browser-local and are not server-side subscriptions;
- consent collection is disabled, with no purpose, frequency, version or
  withdrawal record;
- account, sync and subscription UI remain disabled;
- activation requires an identity provider, versioned consent, verified channel,
  delivery receipts, idempotency, deletion and retention rules.

The contract stays at
`/.well-known/notification-contract.json` and remains linked from discovery,
`llms.txt` and the ecosystem manifest. No account, worker, database table or
background process was introduced.

## Verification

- `PYTHONPATH=. .venv/bin/pytest -q`: **491 passed**.
- `make lint`: passed (Black, isort, flake8, mypy, vulture).
- Focused API and production-smoke tests: **96 passed**.
- `make smoke-prod`: passed with the exact public revision, 26 sources, 393
  relevant open cards, no stale or unknown-freshness sources, and all discovery,
  AVDS4, QazStack, source-onboarding and identity/consent markers green.
- `make content-audit`: passed with no issues.

## Boundary

Local saves are a convenience for the current browser, not a promise of account
sync or notification delivery. Any future activation requires a separate
privacy, consent and delivery release gate.
