# Legacy candidates and retained compatibility

Date: 2026-07-16.

## Removed

| Area | Evidence | Decision |
| --- | --- | --- |
| Redis runtime | Zero keys, no app clients, no code imports | Remove service and dependency |
| Celery, APScheduler, Telegram, Google API, Tenacity | No imports or runtime entry points | Remove dependencies and stale env keys |
| Dated release notes in active docs index | Superseded by current deploy/checklist docs | Move to historical archive |
| Unreachable async scaffolding | Vulture 100% confidence, tests cover contracts | Simplify |

## Retained because referenced

| Path or symbol | Why it stays |
| --- | --- |
| `vendor/qazstack-1.37.2-py3-none-any.whl` | Checksum-pinned production dependency and ecosystem contract |
| `LEGACY_FUNDER_REDIRECTS` | Preserves existing public funder URLs |
| Alembic migrations `0001`-`0004` | Required to build and verify the database schema from scratch |
| `core.pipeline`, queue runner and recorder adapters | Used by refresh, worker and persistence paths |
| Source-specific parsing helpers | Similar names encode different upstream schemas and policies |
| `scripts/qaz_fund_cutover.sh` | Explicitly referenced one-off domain/TLS recovery tool |

## Deferred, not dead

| Candidate | Evidence | Safe next step |
| --- | --- | --- |
| `api/main.py` high-complexity storage and coverage functions | Radon reports D/F complexity, but 421 tests cover many branches | Extract only behind characterization tests in a separate refactor PR |
| `scripts/content_audit.py` and `scripts/production_smoke.py` orchestration functions | High complexity but operationally critical and deterministic | Split result collection from validation without changing output schema |
| Large server-rendered dashboard modules | Live AV DS UI and interaction contract | Extract static assets only with browser snapshots and production parity checks |
| Repeated `_unique`, `_infer_tags`, date and title helpers | Mostly source-policy-specific, not byte-for-byte shared behavior | Consolidate only pairs proven equivalent by property tests |
| Dangling Git objects in the shared worktree store | `git fsck` reports recoverable historical objects and one 64-byte worktree ref residue | Let Git expiry prune them after all active worktrees are reviewed |

No compatibility route, source adapter, schema object or production data was
deleted during this pass.
