# QAZ.FUND repository cleanup audit

Date: 2026-07-16.

## Baseline

- Branch base: `origin/main` at `1d0dc24840e2922ab4494bfe90622d862c8a842c`.
- Working tree: clean before the audit.
- `make lint`: passed.
- `make ci-fast`: 421 tests passed with one Starlette/httpx deprecation warning.
- No tracked caches, temporary copies, logs, broken symlinks or backup files.
- The checksum-pinned QazStack 1.37.2 wheel is the largest tracked binary and is
  required by the production image.

## Static findings

- Vulture found two unreachable statements used to make abstract methods look
  like async generators and an artificial unsatisfiable branch in the
  await-compatible runner start result. The abstract source contract was typed
  as a coroutine even though every implementation returns an async iterator.
- Runtime dependency inspection found Redis, Celery, APScheduler, Telegram,
  Google API clients and Tenacity installed but not imported by the API,
  worker, scripts or migrations.
- Production Redis inspection found zero keys and no application clients. The
  only client was the read-only audit command itself.
- `certifi` was imported directly by the Kazakhstan domestic adapter but was
  available only transitively.
- Starlette's test client emitted a deprecation warning because its dedicated
  `httpx2` backend was absent.
- The public snapshot exporter accepted dangerous overwrite destinations when
  `FORCE_OVERWRITE=1`.
- Eight dated closeout documents were mixed with current operating guidance.
- Ruff found mutable class-level source tag lists and a CA bundle file handle
  created outside its context manager.
- Exact-content and empty-file scans found no tracked duplicates or empty files.
- `detect-secrets` candidates were reviewed; all were examples, test fixtures,
  static asset hashes or keyword false positives. No committed secret was found.

## Actions

- Removed the unused Redis service, environment wiring and related Make target.
- Removed unused runtime integration packages and stale environment placeholders.
- Declared `certifi` directly, added `httpx2`, updated Playwright and removed the
  unused Ruff dependency.
- Added Vulture to the standard lint gate and removed its production/test noise.
- Corrected the abstract source contract, marked shared source tags as
  intentional `ClassVar` data and guaranteed closure of the generated CA bundle.
- Hardened public snapshot export against `/`, the repository root and paths
  nested inside the repository. The exporter now also honors `DEST_DIR` from
  the environment and keeps cleanup evidence in the public snapshot.
- Moved historical release evidence under `docs/archive/releases/` and reduced
  the main documentation index to durable entry points.

## Validation

- `make lint`: passed, including Black, isort, Flake8, mypy and Vulture.
- `make ci-fast`: 427 passed, zero warnings (baseline: 421 passed, one warning).
- Clean runtime virtualenv: installed from `requirements-prod.txt`; `pip check`
  and `api.main` import passed; removed integration packages were absent.
- `pip-audit -r requirements-prod.txt`: no known vulnerabilities. The vendored
  QazStack wheel is not on PyPI, so pip-audit cannot inspect it; its checked-in
  SHA-256 manifest passed independently.
- Public export destructive-path guards, environment destination, clean Git
  initialization and cleanup-document inclusion: passed.
- Shell syntax, local Markdown links, tracked duplicate/empty-file checks and
  `git diff --check`: passed.
- Docker Compose config and image build could not run locally because Docker CLI
  is not installed on this Mac. They remain mandatory CI/deploy gates.
- Production smoke and content/NLP audit results are added after deployment.

## Known risks and next cleanup batch

- High-complexity storage, dashboard and operational audit functions remain
  intentionally unchanged. Their extraction needs characterization tests and a
  separate behavior-preserving refactor PR.
- Shared helpers with similar names remain local until property tests prove
  identical policy; similarity alone is not deletion evidence.
- Historical dangling Git objects remain in the shared worktree store. They are
  recoverable and should be expired only after all active worktrees are reviewed.
- The former Redis container may remain as an orphan after Compose rollout. It
  can be removed only after the new API and worker are healthy and Redis is
  re-confirmed empty with no application clients.

## Workspace-only cleanup

Ignored Python, mypy, pytest and Playwright caches are removed after the final
validation pass. They are not repository changes.
