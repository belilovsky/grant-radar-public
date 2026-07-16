"""Pipeline runner: drains FetchQueue and processes GrantRecord items.

This is the consumer side of the M2 ingestion pipeline. It pulls records
produced by `SourceScheduler` and applies normalization/scoring/persistence.
The processor wires through `core.scoring` when available; otherwise it falls
back to a logging-only placeholder so unit tests can run in isolation.

When a Run recorder is supplied, the runner records start/finish timestamps
and processed/error counters into the persistence layer for observability.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any, Awaitable, Callable, Optional

from sources.base import GrantRecord

from .fetch_queue import FetchQueue

try:  # Optional dependency on scoring module
    from .scoring import score as _score_opportunity  # type: ignore
except Exception:  # pragma: no cover - scoring is optional in unit tests
    _score_opportunity = None  # type: ignore

logger = logging.getLogger(__name__)

Processor = Callable[[GrantRecord], Awaitable[None]]


class _AwaitableNoop:
    def __await__(self):
        return iter(())


def _record_external_id(record: Any) -> str:
    if isinstance(record, dict):
        return str(record.get("external_id") or record.get("id") or "-")
    return str(getattr(record, "external_id", "-"))


async def default_processor(record: GrantRecord) -> None:
    """Default processor: score the record (if scoring available) and log it."""
    score: Optional[float] = getattr(record, "score", None)
    if _score_opportunity is not None:
        if score in (None, 0, 0.0):
            try:
                score = float(_score_opportunity(record))  # type: ignore[arg-type]
                setattr(record, "score", score)
            except Exception:  # pragma: no cover - scoring resilience
                logger.exception(
                    "scoring_failed source=%s id=%s",
                    record.source,
                    record.external_id,
                )
                score = None
    logger.info(
        "processed source=%s external_id=%s title=%s score=%s",
        record.source,
        record.external_id,
        record.title,
        score,
    )


class PipelineRunner:
    """Consumes records from a FetchQueue and runs them through a processor.

    Optionally accepts a ``run_recorder`` exposing ``start()``, ``finish(...)``
    and ``record_error()`` hooks. When provided, the runner reports lifecycle
    events into the persistence layer so operators can inspect runs via the
    ``show-runs`` CLI.
    """

    def __init__(
        self,
        queue: FetchQueue,
        processor: Optional[Processor] = None,
        idle_timeout: float = 1.0,
        run_recorder: Optional[Any] = None,
    ):
        self.queue = queue
        self.processor = processor or default_processor
        self.idle_timeout = idle_timeout
        self.run_recorder = run_recorder
        self._stop = asyncio.Event()
        self._task: Optional[asyncio.Task] = None
        self.processed = 0
        self.errors = 0
        self._run_id: Optional[int] = None

    def _start_run(self) -> None:
        if self.run_recorder is None:
            return
        try:
            self._run_id = self.run_recorder.start()
        except Exception:  # pragma: no cover - persistence resilience
            logger.exception("run_recorder_start_failed")
            self._run_id = None

    def _finish_run(self, status: str = "ok") -> None:
        if self.run_recorder is None or self._run_id is None:
            return
        try:
            self.run_recorder.finish(
                self._run_id,
                processed=self.processed,
                errors=self.errors,
                status=status,
            )
        except Exception:  # pragma: no cover - persistence resilience
            logger.exception("run_recorder_finish_failed run_id=%s", self._run_id)
        finally:
            self._run_id = None

    async def _process_one(self, record: GrantRecord) -> None:
        try:
            result = self.processor(record)
            if inspect.isawaitable(result):
                await result
            self.processed += 1
        except Exception:
            self.errors += 1
            logger.exception("processor_failed for %s", _record_external_id(record))
            if self.run_recorder is not None and self._run_id is not None:
                try:
                    self.run_recorder.record_error(self._run_id)
                except Exception:  # pragma: no cover
                    logger.exception("run_recorder_record_error_failed")

    async def _loop(self) -> None:
        while not self._stop.is_set():
            record = await self.queue.get(timeout=self.idle_timeout)
            if record is None:
                continue
            try:
                await self._process_one(record)
            finally:
                self.queue.task_done()

    async def _run_until_empty_async(self) -> None:
        self._start_run()
        try:
            while self.queue.size() > 0:
                record = await self.queue.get(timeout=self.idle_timeout)
                if record is None:
                    break
                try:
                    await self._process_one(record)
                finally:
                    self.queue.task_done()
        finally:
            self._finish_run()

    def run_until_empty(self):
        """Drain the queue until empty.

        Returns a coroutine inside an existing event loop and runs immediately
        when called from synchronous code. This keeps older M2 smoke tests and
        newer async tests compatible.
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._run_until_empty_async())
        return self._run_until_empty_async()

    async def drain_once(self) -> int:
        before = self.processed
        await self._run_until_empty_async()
        return self.processed - before

    def start(self):
        if self._task is None or self._task.done():
            self._stop.clear()
            self._start_run()
            self._task = asyncio.create_task(self._loop())
        return _AwaitableNoop()

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            try:
                await asyncio.wait_for(self._task, timeout=self.idle_timeout * 2)
            except asyncio.TimeoutError:
                self._task.cancel()
            self._task = None
        self._finish_run()
