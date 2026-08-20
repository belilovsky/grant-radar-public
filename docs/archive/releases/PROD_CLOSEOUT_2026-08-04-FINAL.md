# QAZ.FUND production closeout – benchmark plan and contract hardening

## Release identity

- Canonical checkout: `/Users/belilovsky/Documents/Codex/2026-05-21/grant-radar-public`
- Branch: `codex/qaz-fund-reuse-boundary-20260728`
- Runtime: `root@148.230.117.131:/opt/grant-radar`
- Public domain: `https://qaz.fund`
- Final deployed revision: `c55b2c860384030c0cae717916bb9b21a0aa47b5`
- Public marker: `/.well-known/release.json`

## What is closed in this pass

- External benchmark and upgrade plan is maintained in
  [`PRODUCT_BENCHMARK_2026-08-04.md`](../../PRODUCT_BENCHMARK_2026-08-04.md),
  with official analogues, admission gates and measurable success criteria.
- `insights.v1`, `comparison.v1` and `history.v1` provide bounded machine and
  AVDS4 human read models without inventing eligibility or verification.
- `source-onboarding.v1` makes active, gated and deferred sources explicit;
  no credentials or private responses enter the public contract.
- `qazfund-workbench.v1` gives editors a reproducible local JSON/CSV/README
  handoff with a stable selection hash and no `raw` payload.
- `notification-v1` now explicitly covers identity, consent, local-only saves,
  synchronization and delivery. Accounts, workers, subscriptions and
  background processes remain disabled.
- Documentation, tests and production smoke now enforce these boundaries.

## Final verification

- `PYTHONPATH=. .venv/bin/pytest -q`: **491 passed**.
- `make lint`: Black, isort, flake8, mypy and vulture passed.
- `git diff --check`: passed; working tree clean.
- RU NLP audit: 150 records, 0 issues.
- EN NLP audit: 150 records, 0 issues.
- `make smoke-prod`: passed on the exact public revision; 1,280 health records,
  26 sources, 393 relevant open records, 0 stale sources, 0 unknown-freshness
  sources, 20 NDJSON records and 5 digest items. All AVDS4, QazStack,
  comparison, history, source-onboarding and identity/consent markers passed.
- `make content-audit`: passed with no issues.
- Public notification contract verified with `status=not_enabled`, no account,
  no cross-device synchronization and no consent collection.

## Remaining product roadmap

The benchmark plan remains the roadmap for future product work: authenticated
saved work, consented notifications, funder/recipient graph, richer source
enrichment and interactive analytics. Each item requires its own data-license,
privacy, provenance and release gate; no gated source or delivery process is
implicitly activated by this release.
