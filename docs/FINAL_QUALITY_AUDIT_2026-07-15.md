# Final quality audit - 2026-07-15

## Scope

This pass reviewed application code, repository structure, dependency and
security state, tests, automation, and documentation. It intentionally avoided
feature work, data changes, schema changes, and broad architectural rewrites.

## Baseline

- `make lint`: green (Black, isort, Flake8, mypy; 63 typed source files).
- `pytest -q`: 409 passed before changes.
- `python -m compileall -q api core sources scripts alembic`: green.
- `pip check`: no broken requirements.
- Tracked duplicate-file and temporary-artifact scans: no deletion candidates.

Running pytest with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` is not a valid project
gate: this repository intentionally depends on `pytest-asyncio`. Use the normal
venv invocation documented in `Makefile` and CI.

## Changes made

- Updated Starlette from 1.0.1 to 1.3.1 to close four published advisories,
  including a high-severity denial-of-service issue.
- Made `requirements-prod.txt` the single runtime dependency source for both
  development and production installation paths.
- Added a regression test for the development image dependency contract and
  expanded the GitHub Actions dependency-cache key.
- Aligned the Black pre-commit hook with the version pinned by CI.
- Applied small semantic-preserving clarity improvements identified by Ruff.
- Synchronized the public endpoint list and indexed all current documentation.

## Security review

- `pip-audit` initially found four Starlette advisories on 1.0.1; 1.3.1 is the
  first release fixing the full set and is compatible with FastAPI 0.136.3.
- Secret scanning findings were public verification tokens, schema digests,
  local/example credentials, API parameter names, and test fixtures. No real
  credential was identified in tracked files.
- No production shell execution or subprocess interpolation path was found in
  the application packages.

## Intentionally retained

- Dated production closeouts remain as historical release evidence.
- QazStack bridge and run-recorder adapters remain because tests and runtime
  factories reference their contracts.
- Generated QazStack wheel/checksum files remain controlled artifacts and were
  not edited manually.

## Deferred maintainability work

`api/dashboard.py` remains a large server-rendered module. Splitting its CSS,
JavaScript, and rendering sections is justified, but it is not a low-risk
cleanup: it needs route snapshots, browser parity checks, and cache/header
verification in a dedicated change. No dead-code claim was made without
reference evidence.

## Final verification

Final command results and production evidence are appended after CI and release
verification.
