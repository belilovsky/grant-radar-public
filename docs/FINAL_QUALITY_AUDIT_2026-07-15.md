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

- Local quality gate: Black, isort, Flake8, and mypy passed; mypy checked 63
  source files.
- Test suite: 410 passed. The single warning is an upstream FastAPI TestClient
  deprecation notice about a future `httpx2` migration.
- `compileall`, `pip check`, all pre-commit hooks, shell syntax, documentation
  links, and `git diff --check`: passed.
- `pip-audit`: no known vulnerabilities after the Starlette update. The
  vendored QazStack wheel is not published on PyPI and is checksum-verified by
  the repository contract instead.
- GitHub Actions `Quality and tests`: passed for pull request #14.
- Pull request #14 merged into `main` as revision
  `e954b9e7ab3a45920b3b72f94b03a59c5357a3df`.
- The documented conservative deploy completed without `rsync --delete` at
  `2026-07-15T16:10:50Z`.
- Production API, PostgreSQL, and Redis reported healthy; the worker reported
  running. The API image reports Starlette 1.3.1.
- Post-release smoke: database readiness, 26 sources, 155 relevant open items,
  zero stale sources, JSON/NDJSON/digest surfaces, both public languages, and
  machine-discovery contracts passed.
- Content audit: zero issues across 155 public opportunities.
- NLP quality audit: zero issues across 150 Russian and 150 English records.

The only deliberately deferred item is the staged decomposition of
`api/dashboard.py`; it is maintainability work, not a known runtime defect.
