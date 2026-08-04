# QAZ.FUND production closeout – local workbench export

## Release identity

- Checkout: `/Users/belilovsky/Documents/Codex/2026-05-21/grant-radar-public`
- Branch: `codex/qaz-fund-reuse-boundary-20260728`
- Runtime: `root@148.230.117.131:/opt/grant-radar`
- Public domain: `https://qaz.fund`
- Deployed revision: `dff0b342dea71596d6faca5e4d1d7794ddf2af95`

## Delivered slice

The local `qazfund-workbench.v1` exporter reads the public Opportunities NDJSON
and produces a safe editorial handoff:

- `workbench.json` with filters, selected IDs, source links and a deterministic
  content hash;
- `opportunities.csv` for spreadsheet work;
- `README.md` with the handoff context and official-source reminder.

The projection excludes `raw` and unknown nested fields. Existing output files
are protected from accidental replacement unless `--force` is supplied. The
tool does not add a public route, persist user selections, create accounts or
enable notifications. The contract and examples live in
[`WORKBENCH_EXPORT.md`](../../WORKBENCH_EXPORT.md).

## Verification

- `PYTHONPATH=. .venv/bin/pytest -q`: **491 passed**.
- `make lint`: passed (Black, isort, flake8, mypy, vulture).
- `git diff --check`: passed before release.
- Real public export: 868 input rows, 5-row control selection, `raw` absent from
  `workbench.json`.
- `make smoke-prod`: passed; exact public revision, 26 sources, 393 relevant
  open cards, 0 stale sources, 0 unknown-freshness sources, 5 digest items and
  all AVDS4/discovery/source-onboarding markers green.
- `make content-audit`: passed with no issues.

## Boundary

This is a local content workflow, not a server-side workspace or notification
system. Any future account, synchronization or delivery feature needs an
explicit consent, deletion and delivery contract before implementation.
