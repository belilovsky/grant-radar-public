# Persistence (grant-radar)

This document describes the repository / persistence layer used by the grant-radar ingestion pipeline and how to choose a backend.

## Components

- `core/persistence.py`
  - `compute_fingerprint(record)` — stable dedup key (`source:external_id`, fallback to `url:` or sha1 over `repr`).
  - `Repository` (Protocol) — `exists`, `upsert`, `all`, `size`, `clear`.
  - `InMemoryRepository` — thread-safe dict-backed implementation, used by tests / dev.
  - `DedupProcessor(repo, inner=...)` — async processor wrapping an inner callable; deduplicates and persists each record once.
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

- `tests/test_persistence.py` — fingerprints, in-memory repo, dedup processor.
- `tests/test_db_repository.py` — `SqlRepository` insert/upsert/exists/clear, `make_repository` resolution. Skipped automatically when SQLAlchemy is not installed (`pytest.importorskip("sqlalchemy")`).
- `tests/test_runner_factory.py` — end-to-end pipeline through `FetchQueue -> PipelineRunner -> DedupProcessor -> Repository` with both in-memory and `sqlite:///:memory:` backends.

## Migration plan

- M2 (current): in-memory, SQLite and Postgres-compatible SQL backends are functional.
- M3 (current): Alembic migrations live under `alembic/versions/`; `Dockerfile.prod` runs `alembic upgrade head` on container start with retry while Postgres is booting.
- M4 (current): dashboard reads persisted `opportunities` plus `/coverage` source
  metrics; future analytics can extend this with historical `runs` trends.


## Migrations (Alembic)

Схема версионируется через Alembic. Конфиг: `alembic.ini` (корень репо), окружение: `alembic/env.py` (URL берётся из `GRANT_RADAR_DB_URL`, затем fallback `DATABASE_URL`).

- Baseline: `alembic/versions/0001_initial.py` — создаёт `opportunities` и `dedup_keys`.
- Smoke-тесты миграций: `tests/test_alembic_migrations.py` (sqlite, upgrade/downgrade cycle).

### Команды

```bash
make db-upgrade                  # alembic upgrade head
make db-downgrade                # alembic downgrade -1
make db-revision m="add foo"    # авто-генерация новой ревизии
make db-migrate                  # alias на db-upgrade (для deploy-скриптов)
```

### Переход с `init_db.py` на Alembic

`scripts/init_db.py` остаётся для быстрого bootstrap в dev/CI. Для staging/prod используйте `make db-upgrade` или production entrypoint. При развёртывании на чистую базу: `alembic upgrade head`. При первоначальном внедрении на базу, уже созданную `init_db.py`: `alembic stamp 0001_initial`, затем `alembic upgrade head`.

### Проверки совместимости

`tests/test_db_repository.py::test_sql_repository_works_after_alembic_head` применяет Alembic `head`, затем пишет через `SqlRepository`. Этот smoke защищает главный контракт: ORM и миграции должны описывать одну и ту же схему.


## Indexes (ревизия 0003)

Для ускорения фильтрации и дедупа на `opportunities` созданы индексы:

| Индекс | Колонка | unique |
| --- | --- | --- |
| `ix_opportunities_source` | `source` | — |
| `ix_opportunities_deadline` | `deadline` | — |
| `ix_opportunities_dedup_key` | `dedup_key` | ✅ |

Уникальный индекс по `dedup_key` выносит инвариант дедупикации на уровень БД —
две параллельных выгрузки одного и того же объявления не могут обе попасть в таблицу.

Для PostgreSQL в будущих ревизиях имеет смысл добавлять индексы через
`op.create_index(..., postgresql_concurrently=True)` вне транзакции
(`with op.get_context().autocommit_block(): ...`) — это избавляет от блокировок
боевых записей на больших таблицах.

## Run recorder & audit log (ревизия 0004)

Ревизия `0004_runs_table` добавляет таблицу `runs` (аудит запусков пайплайна)
и индексы `ix_runs_source`, `ix_runs_started_at`, `ix_runs_status`.

Колонки: `id`, `source`, `started_at`, `finished_at`, `status` (`running`/`ok`/`error`),
`items_seen`, `items_new`, `items_dup`, `error`.

Модуль `core/run_recorder.py` предоставляет контекст-менеджер `record_run`,
который открывает строку с `status=running`, отдаёт `RunStats` для мутации
счётчиков и финализирует запись как `ok` или `error` (с сообщением
исключения) при выходе из блока.

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

Если SQLAlchemy не установлен или таблица `runs` отсутствует (например, старая
ревизия), `record_run` деградирует в no-op, но всё равно отдаёт `RunStats` —
вызывающий код работает без изменений.

Долгоживущий worker открывает строку `status=running` на время работы процесса
и финализирует её при штатной остановке контейнера. Поэтому активная строка
worker в `make show-runs` является нормальным состоянием; CLI показывает её
текущую длительность, чтобы оператор видел, что это живой daemon-run.
