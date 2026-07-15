"""Scheduler for periodic source ingestion.

Iterates over registered parsers in `sources.PARSERS` and triggers fetch
cycles on configured intervals. Records produced by parsers are pushed to
an optional `FetchQueue` for downstream pipeline consumption.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import os
import signal
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Callable, Optional

from sources import PARSERS, BaseSourceParser

from .fetch_queue import FetchQueue

logger = logging.getLogger(__name__)
DEFAULT_INTERVAL_SECONDS = 6 * 60 * 60


@dataclass
class ScheduleConfig:
    """Per-source scheduling configuration."""

    source: str
    interval_seconds: int = 3600
    enabled: bool = True


class SourceScheduler:
    """Async scheduler that runs each parser on its own cadence.

    If a `FetchQueue` is provided, parsed records are enqueued for the
    pipeline consumer; otherwise they are only counted and logged.
    """

    def __init__(
        self,
        configs: Iterable[ScheduleConfig] | None = None,
        queue: Optional[FetchQueue] = None,
        parsers: Iterable[BaseSourceParser] | None = None,
        recorder_factory: Callable[[str], Any | None] | None = None,
    ):
        self.configs = list(configs or [])
        self.queue = queue
        self.parsers = list(parsers or [])
        self.recorder_factory = recorder_factory
        self._tasks: list[asyncio.Task] = []
        self._owned_parsers: list[BaseSourceParser] = []
        self._stop = asyncio.Event()

    async def _iter_records(self, parser: BaseSourceParser):
        records: Any = parser.fetch()
        if hasattr(records, "__aiter__"):
            async for record in records:  # type: ignore[union-attr]
                yield record
            return
        if inspect.isawaitable(records):
            records = await records
        for record in records or []:
            yield record

    async def _run_parser(self, parser: BaseSourceParser, interval: int) -> None:
        while not self._stop.is_set():
            try:
                count = await self._fetch_once(parser)
                logger.info("parser=%s fetched=%d", parser.name, count)
            except Exception:
                logger.exception("parser=%s failed", parser.name)
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=interval)
            except asyncio.TimeoutError:
                continue

    async def _fetch_once(self, parser: BaseSourceParser) -> int:
        source = str(getattr(parser, "slug", "") or parser.name)
        recorder = None
        run_id = None
        if self.recorder_factory is not None:
            try:
                recorder = self.recorder_factory(source)
                run_id = recorder.start() if recorder is not None else None
            except Exception:
                logger.exception("source_recorder_start_failed source=%s", source)
                recorder = None
                run_id = None

        count = 0
        errors = 0
        status = "ok"
        try:
            async for record in self._iter_records(parser):
                count += 1
                if self.queue is not None:
                    await self.queue.put(record)
        except asyncio.CancelledError:
            status = "cancelled"
            raise
        except Exception:
            errors = 1
            status = "error"
            if recorder is not None and run_id is not None:
                try:
                    recorder.record_error(run_id)
                except Exception:
                    logger.exception(
                        "source_recorder_record_error_failed source=%s", source
                    )
            raise
        finally:
            if recorder is not None and run_id is not None:
                try:
                    recorder.finish(
                        run_id,
                        processed=count,
                        errors=errors,
                        status=status,
                    )
                except Exception:
                    logger.exception("source_recorder_finish_failed source=%s", source)
        return count

    async def start(self) -> None:
        for cfg in self.configs:
            if not cfg.enabled:
                continue
            cls = PARSERS.get(cfg.source)
            if cls is None:
                logger.warning("unknown source: %s", cfg.source)
                continue
            parser = cls()  # type: ignore[abstract]
            self._owned_parsers.append(parser)
            self._tasks.append(
                asyncio.create_task(self._run_parser(parser, cfg.interval_seconds))
            )

    async def _run_once_async(self) -> None:
        parser_instances = list(self.parsers)
        owned_parsers: list[BaseSourceParser] = []
        if not parser_instances:
            for cfg in self.configs:
                if not cfg.enabled:
                    continue
                cls = PARSERS.get(cfg.source)
                if cls is not None:
                    parser = cls()  # type: ignore[abstract]
                    parser_instances.append(parser)
                    owned_parsers.append(parser)

        try:
            for parser_instance in parser_instances:
                try:
                    await self._fetch_once(parser_instance)
                except Exception:
                    logger.exception("parser=%s failed", parser_instance.name)
        finally:
            await self._close_parsers(owned_parsers)

    @staticmethod
    async def _close_parsers(parsers: Iterable[BaseSourceParser]) -> None:
        for parser in parsers:
            try:
                await parser.close()
            except Exception:
                logger.exception("parser_close_failed parser=%s", parser.name)

    def run_once(self):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._run_once_async())
        return self._run_once_async()

    async def stop(self) -> None:
        self._stop.set()
        for t in self._tasks:
            t.cancel()
        for t in self._tasks:
            try:
                await t
            except (asyncio.CancelledError, Exception):
                pass
        await self._close_parsers(self._owned_parsers)
        self._owned_parsers.clear()


def build_default_configs() -> list[ScheduleConfig]:
    """Build source configs from env for the long-running worker."""
    sources_raw = os.environ.get("GRANT_RADAR_SOURCES", ",".join(PARSERS.keys()))
    interval_raw = os.environ.get(
        "GRANT_RADAR_SOURCE_INTERVAL_SECONDS", str(DEFAULT_INTERVAL_SECONDS)
    )
    try:
        interval = max(1, int(interval_raw))
    except ValueError:
        logger.warning(
            "invalid GRANT_RADAR_SOURCE_INTERVAL_SECONDS=%r; using default",
            interval_raw,
        )
        interval = DEFAULT_INTERVAL_SECONDS

    configs = []
    for source in (s.strip() for s in sources_raw.split(",")):
        if source:
            configs.append(ScheduleConfig(source=source, interval_seconds=interval))
    return configs


async def run_worker() -> None:
    """Run scheduler and pipeline until SIGTERM/SIGINT."""
    from .runner_factory import build_default_runner, build_run_recorder_factory

    queue = FetchQueue()
    runner = build_default_runner(queue, idle_timeout=1.0, source="worker")
    scheduler = SourceScheduler(
        build_default_configs(),
        queue=queue,
        recorder_factory=build_run_recorder_factory(),
    )

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:  # pragma: no cover - Windows fallback
            pass

    runner.start()
    await scheduler.start()
    logger.info(
        "grant-radar worker started sources=%s", [c.source for c in scheduler.configs]
    )
    try:
        await stop_event.wait()
    finally:
        logger.info("grant-radar worker stopping")
        await scheduler.stop()
        await runner.stop()


def main() -> int:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(run_worker())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
