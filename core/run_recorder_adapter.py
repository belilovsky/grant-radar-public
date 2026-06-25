"""Adapter exposing a ``start()/finish()/record_error()`` recorder API.

``PipelineRunner`` expects a recorder object with three simple methods.
The primary persistence module ``core.run_recorder`` ships a context-manager
oriented helper (``record_run``); this adapter wraps the same ``runs`` table
but presents the imperative interface used by the runner. When SQLAlchemy or
the ``runs`` table is unavailable it silently degrades into a no-op so that
pipelines keep working in degraded environments (older migrations, sqlite
in-memory tests, etc.).
"""

from __future__ import annotations

import datetime as _dt
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _utcnow() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


class RunRecorder:
    """Imperative recorder backed by the ``runs`` table.

    Parameters
    ----------
    engine:
        Optional SQLAlchemy ``Engine``. When ``None`` the recorder operates
        in no-op mode (useful for tests and for environments without
        ``GRANT_RADAR_DB_URL``).
    source:
        Logical pipeline name written to the ``source`` column of ``runs``.
    """

    def __init__(self, engine: Optional[Any] = None, source: str = "pipeline") -> None:
        self._engine = engine
        self._source = source
        self._table = None
        if engine is not None:
            self._table = self._reflect_runs_table()

    # ------------------------------------------------------------------
    # Table reflection
    # ------------------------------------------------------------------
    def _reflect_runs_table(self):
        try:
            from sqlalchemy import MetaData, Table
        except Exception:  # pragma: no cover - SQLAlchemy missing
            return None
        try:
            md = MetaData()
            return Table("runs", md, autoload_with=self._engine)
        except Exception:
            logger.debug("runs_table_unavailable - recorder degrades to no-op")
            return None

    # ------------------------------------------------------------------
    # PipelineRunner-facing API
    # ------------------------------------------------------------------
    def start(self) -> Optional[int]:
        if self._engine is None or self._table is None:
            return None
        try:
            from sqlalchemy import insert

            stmt = insert(self._table).values(
                source=self._source,
                started_at=_utcnow(),
                status="running",
                items_seen=0,
                items_new=0,
                items_dup=0,
            )
            with self._engine.begin() as conn:
                result = conn.execute(stmt)
                pk = result.inserted_primary_key
                return int(pk[0]) if pk else None
        except Exception:
            logger.exception("run_recorder_start_failed")
            return None

    def finish(
        self,
        run_id: int,
        processed: int = 0,
        errors: int = 0,
        status: str = "ok",
    ) -> None:
        if self._engine is None or self._table is None or run_id is None:
            return
        try:
            from sqlalchemy import update

            final_status = status if errors == 0 else "error"
            stmt = (
                update(self._table)
                .where(self._table.c.id == run_id)
                .values(
                    finished_at=_utcnow(),
                    status=final_status,
                    items_seen=processed,
                    items_new=max(processed - errors, 0),
                )
            )
            with self._engine.begin() as conn:
                conn.execute(stmt)
        except Exception:
            logger.exception("run_recorder_finish_failed run_id=%s", run_id)

    def record_error(self, run_id: int) -> None:  # pragma: no cover - thin
        # Errors are aggregated at finish() time; method exists to satisfy the
        # PipelineRunner contract and to allow future per-error bookkeeping.
        return None


__all__ = ["RunRecorder"]
