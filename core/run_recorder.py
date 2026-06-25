"""Pipeline run recorder.

Writes a row to the `runs` table at the start of a pipeline execution and
updates it on completion (status, counters, optional error). Designed to be
used as a context manager from PipelineRunner.

The recorder is intentionally tolerant: if SQLAlchemy is not installed, or
if the runs table does not exist (e.g. tests running on an older revision),
it silently degrades into a no-op so that the pipeline keeps working.
"""

from __future__ import annotations

import datetime as _dt
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator, Optional


@dataclass
class RunStats:
    items_seen: int = 0
    items_new: int = 0
    items_dup: int = 0
    error: Optional[str] = None

    def saw(self, n: int = 1) -> None:
        self.items_seen += n

    def added(self, n: int = 1) -> None:
        self.items_new += n

    def deduped(self, n: int = 1) -> None:
        self.items_dup += n


@dataclass
class _RecorderState:
    run_id: Optional[int] = None
    stats: RunStats = field(default_factory=RunStats)


def _utcnow() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


@contextmanager
def record_run(engine, source: str) -> Iterator[RunStats]:
    """Context manager that records a pipeline run for ``source``.

    Yields a :class:`RunStats` instance the caller mutates while ingesting.
    On exit the row is finalised with status=ok|error and the collected
    counters. Any exception is re-raised after the row is updated.
    """
    state = _RecorderState()
    try:
        from sqlalchemy import MetaData, Table, insert, update
    except Exception:
        # SQLAlchemy missing -> degrade to a pure stats container.
        yield state.stats
        return

    md = MetaData()
    try:
        runs = Table("runs", md, autoload_with=engine)
    except Exception:
        # runs table absent (older revision) -> no-op recorder.
        yield state.stats
        return

    started_at = _utcnow()
    with engine.begin() as conn:
        result = conn.execute(
            insert(runs).values(
                source=source,
                started_at=started_at,
                status="running",
                items_seen=0,
                items_new=0,
                items_dup=0,
            )
        )
        state.run_id = int(result.inserted_primary_key[0])

    try:
        yield state.stats
    except BaseException as exc:  # noqa: BLE001
        state.stats.error = f"{type(exc).__name__}: {exc}"
        with engine.begin() as conn:
            conn.execute(
                update(runs)
                .where(runs.c.id == state.run_id)
                .values(
                    finished_at=_utcnow(),
                    status="error",
                    items_seen=state.stats.items_seen,
                    items_new=state.stats.items_new,
                    items_dup=state.stats.items_dup,
                    error=state.stats.error,
                )
            )
        raise
    else:
        with engine.begin() as conn:
            conn.execute(
                update(runs)
                .where(runs.c.id == state.run_id)
                .values(
                    finished_at=_utcnow(),
                    status="ok",
                    items_seen=state.stats.items_seen,
                    items_new=state.stats.items_new,
                    items_dup=state.stats.items_dup,
                )
            )
