# Persistence (grant-radar)

This document describes the repository / persistence layer used by the grant-radar ingestion pipeline and how to choose a backend.

## Components

- `core/persistence.py`
  - `compute_fingerprint(record)` – stable dedup key (`source:external_id`, fallback to `url:` or sha1 over `repr`).
  - `Repository` (Protocol) – `exists`, `upsert`, `all`, `size`, `clear`.
  - `InMemoryRepository` – thread-safe dict-backed implementation, used by tests / dev.
  - `DedupProcessor(repo, inner=...)` – async processor wrapping an inner callable; deduplicates and persists each record once.
- `core/db.py`
  - SQLAlchemy `Base`, `OpportunityRow` ORM model, `SqlRepository` implementation.
- `core/repository_factory.py`
  - `make_repository(url=None)` selects the backend.
- `core/runner_factory.py`
  - `build_default_runner(queue, *, repository=None, processor=None, idle_timeout=1.0)` assembles a `PipelineRunner` with dedup + persistence pre-wired.

## Backend selection

The backend is picked by `make_repository()` in this order:

1. Explicit `url` argument.
2. Environment variable `GRANT_RADAR_DB_URL`.
3. Environment variable `DATABASE_URL` as a compatibility fallback.
4. Default: `InMemoryRepository`.

Special values: empty string, `memory`, `:memory:` -> `InMemoryRepository`.

Any SQLAlchemy URL (e.g. `sqlite:///./data/grants.db`, `postgresql+psycopg://user:pass@host:5432/db`) selects the SQL backend.

## Usage

```python
from core.fetch_queue import FetchQueue
from core.runner_factory import build_default_runner

queue = FetchQueue()
runner = build_default_runner(queue)  # uses GRANT_RADAR_DB_URL or in-memory
await runner.start()
```

Override backend explicitly:

```python
from core.db import SqlRepository
from core.runner_factory import build_default_runner

repo = SqlRepository("sqlite:///./data/grants.db")
runner = build_default_runner(queue, repository=repo)
```

## Environment files

| File | Backend | Value |
| --- | --- | --- |
| `.env.example` | sqlite | `sqlite:///./data/grants.db` |
| `.env.dev` | sqlite/postgres | local sqlite in host runs; `docker-compose.dev.yml` overrides containers to postgres |
| `.env.staging` | postgres | `postgresql+psycopg://...@db:5432/grantradar` |
| `.env.prod` | postgres | `postgresql+psycopg://...@db:5432/grantradar` |

## Testing

- `tests/test_persistence.py` – fingerprints, in-memory repo, dedup processor.
- `tests/test_db_repository.py` – `SqlRepository` insert/upsert/exists/clear, `make_repository` resolution. Skipped automatically when SQLAlchemy is not installed (`pytest.importorskip("sqlalchemy")`).
- `tests/test_runner_factory.py` – end-to-end pipeline through `FetchQueue -> PipelineRunner -> DedupProcessor -> Repository` with both in-memory and `sqlite:///:memory:` backends.

## Migration plan

- M2 (current): in-memory, SQLite and Postgres-compatible SQL backends are functional.
- M3 (current): Alembic migrations live under `alembic/versions/`; `Dockerfile.prod` runs `alembic upgrade head` on container start with retry while Postgres is booting.
- M4 (current): dashboard reads persisted `opportunities` plus `/coverage` source
  metrics; future analytics can extend this with historical `runs` trends.


## Migrations (Alembic)

The schema is versioned with Alembic. Configuration lives in `alembic.ini` at
the repository root, and the runtime environment is defined in
`alembic/env.py`. The migration URL is resolved from `GRANT_RADAR_DB_URL` with
`DATABASE_URL` as a compatibility fallback.

- Baseline: `alembic/versions/0001_initial.py` creates `opportunities` and
  `dedup_keys`.
- Migration smoke tests live in `tests/test_alembic_migrations.py` and cover a
  sqlite upgrade/downgrade cycle.

### Commands

```bash
make db-upgrade                  # alembic upgrade head
make db-downgrade                # alembic downgrade -1
make db-revision m="add foo"    # авто-генерация новой ревизии
make db-migrate                  # alias на db-upgrade (для deploy-скриптов)
```

### Transition from `init_db.py` to Alembic

`scripts/init_db.py` remains useful for quick dev and CI bootstrap. For
staging or production, use `make db-upgrade` or the production entrypoint.
For a clean database, run `alembic upgrade head`. When adopting Alembic on a
database previously created by `init_db.py`, run `alembic stamp 0001_initial`
and then `alembic upgrade head`.

### Compatibility checks

`tests/test_db_repository.py::test_sql_repository_works_after_alembic_head`
applies Alembic `head` and then writes through `SqlRepository`. This smoke test
protects the main contract: ORM models and migrations must describe the same
schema.

## Indexes (revision `0003`)

Для ускорения фильтрации и дедупа на `opportunities` созданы индексы:

| Индекс | Колонка | unique |
| --- | --- | --- |
| `ix_opportunities_source` | `source` | – |
| `ix_opportunities_deadline` | `deadline` | – |
| `ix_opportunities_dedup_key` | `dedup_key` | ✅ |

The unique `dedup_key` index enforces deduplication at the database layer, so
two parallel ingests of the same record cannot both land in the table.

For PostgreSQL, future revisions should prefer
`op.create_index(..., postgresql_concurrently=True)` outside a transaction
using `with op.get_context().autocommit_block(): ...` to reduce lock pressure
on large live tables.

## Run recorder and audit log (revision `0004`)

Revision `0004_runs_table` adds a `runs` table for pipeline-run audit data and
indexes `ix_runs_source`, `ix_runs_started_at`, and `ix_runs_status`.

Columns: `id`, `source`, `started_at`, `finished_at`, `status`
(`running` / `ok` / `error`), `items_seen`, `items_new`, `items_dup`, and
`error`.

The `core/run_recorder.py` module provides a `record_run` context manager. It
opens a row with `status=running`, exposes `RunStats` for counter updates, and
finalizes the record as `ok` or `error` on exit.

```python
from sqlalchemy import create_engine
from core.run_recorder import record_run

engine = create_engine(os.environ["GRANT_RADAR_DB_URL"])
with record_run(engine, source="grants_gov") as stats:
    for item in fetch():
        stats.saw()
        if persist(item):
            stats.added()
        else:
            stats.deduped()
```

If SQLAlchemy is not installed or the `runs` table is unavailable, `record_run`
degrades to a no-op while still returning `RunStats`, so calling code stays
unchanged.

The long-running worker keeps a `status=running` row open for the lifetime of
the process and finalizes it on clean shutdown. As a result, an active worker
row in `make show-runs` is expected; the CLI displays its duration so
maintainers can distinguish a healthy daemon run from a stuck process.
