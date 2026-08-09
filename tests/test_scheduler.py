"""Tests for core.scheduler.SourceScheduler."""

import asyncio
from dataclasses import dataclass, field

from core.scheduler import (
    ScheduleConfig,
    SourceScheduler,
    _heartbeat_worker,
    build_default_configs,
)
from sources.base import GrantRecord


@dataclass
class _Recorder:
    started: int = 0
    finished: list[dict[str, object]] = field(default_factory=list)
    errors: int = 0

    def start(self) -> int:
        self.started += 1
        return self.started

    def finish(
        self,
        run_id: int,
        processed: int = 0,
        errors: int = 0,
        status: str = "ok",
    ) -> None:
        self.finished.append(
            {
                "run_id": run_id,
                "processed": processed,
                "errors": errors,
                "status": status,
            }
        )

    def record_error(self, run_id: int) -> None:
        self.errors += 1


class _Parser:
    name = "empty_source"
    slug = "empty_source"
    closed = False

    async def fetch(self):
        if self.closed:
            yield GrantRecord(
                source=self.slug,
                external_id="unused",
                title="Unused",
                url="https://example.org/unused",
            )

    async def close(self) -> None:
        self.closed = True


class _FailingParser(_Parser):
    name = "failing_source"
    slug = "failing_source"

    async def fetch(self):
        if self.closed:
            yield GrantRecord(
                source=self.slug,
                external_id="unused",
                title="Unused",
                url="https://example.org/unused",
            )
        raise RuntimeError("source failed")


class _SoftFailingParser(_Parser):
    name = "soft_failing_source"
    slug = "soft_failing_source"

    async def fetch(self):
        self.last_fetch_error = "ConnectError: upstream unavailable"
        if self.last_fetch_error:
            return
        yield GrantRecord(
            source=self.slug,
            external_id="unused",
            title="Unused",
            url="https://example.org/unused",
        )


class _StaleErrorParser(_Parser):
    name = "stale_error_source"
    slug = "stale_error_source"
    last_fetch_error = "old failure"


class _CloseFailingParser(_Parser):
    name = "close_failing_source"
    slug = "close_failing_source"

    async def close(self) -> None:
        raise RuntimeError("close failed")


def test_unknown_source_does_not_crash():
    async def _go():
        sched = SourceScheduler(
            [ScheduleConfig(source="does_not_exist", interval_seconds=1)]
        )
        await sched.start()
        # No tasks should be scheduled for unknown source
        assert sched._tasks == []
        await sched.stop()

    asyncio.run(_go())


def test_disabled_source_skipped():
    async def _go():
        sched = SourceScheduler(
            [
                ScheduleConfig(source="grants_gov", interval_seconds=1, enabled=False),
            ]
        )
        await sched.start()
        assert sched._tasks == []
        await sched.stop()

    asyncio.run(_go())


def test_known_source_starts_task():
    async def _go():
        sched = SourceScheduler(
            [
                ScheduleConfig(source="grants_gov", interval_seconds=3600),
            ]
        )
        await sched.start()
        assert len(sched._tasks) == 1
        await sched.stop()
        assert all(t.done() or t.cancelled() for t in sched._tasks)

    asyncio.run(_go())


def test_build_default_configs_from_env(monkeypatch):
    monkeypatch.setenv("GRANT_RADAR_SOURCES", "grants_gov, internews")
    monkeypatch.setenv("GRANT_RADAR_SOURCE_INTERVAL_SECONDS", "42")

    configs = build_default_configs()

    assert [c.source for c in configs] == ["grants_gov", "internews"]
    assert {c.interval_seconds for c in configs} == {42}


def test_run_once_records_success_for_empty_source() -> None:
    async def _go() -> None:
        recorder = _Recorder()
        scheduler = SourceScheduler(
            parsers=[_Parser()],
            recorder_factory=lambda _source: recorder,
        )

        await scheduler.run_once()

        assert recorder.started == 1
        assert recorder.finished == [
            {"run_id": 1, "processed": 0, "errors": 0, "status": "ok"}
        ]

    asyncio.run(_go())


def test_run_once_records_source_failure() -> None:
    async def _go() -> None:
        recorder = _Recorder()
        scheduler = SourceScheduler(
            parsers=[_FailingParser()],
            recorder_factory=lambda _source: recorder,
        )

        await scheduler.run_once()

        assert recorder.errors == 1
        assert recorder.finished == [
            {"run_id": 1, "processed": 0, "errors": 1, "status": "error"}
        ]

    asyncio.run(_go())


def test_run_once_records_parser_reported_failure() -> None:
    async def _go() -> None:
        recorder = _Recorder()
        scheduler = SourceScheduler(
            parsers=[_SoftFailingParser()],
            recorder_factory=lambda _source: recorder,
        )

        await scheduler.run_once()

        assert recorder.errors == 1
        assert recorder.finished == [
            {"run_id": 1, "processed": 0, "errors": 1, "status": "error"}
        ]

    asyncio.run(_go())


def test_run_once_clears_stale_parser_error_before_fetch() -> None:
    async def _go() -> None:
        recorder = _Recorder()
        parser = _StaleErrorParser()
        scheduler = SourceScheduler(
            parsers=[parser],
            recorder_factory=lambda _source: recorder,
        )

        await scheduler.run_once()

        assert parser.last_fetch_error is None
        assert recorder.finished == [
            {"run_id": 1, "processed": 0, "errors": 0, "status": "ok"}
        ]

    asyncio.run(_go())


def test_scheduler_closes_parsers_it_creates(monkeypatch) -> None:
    async def _go() -> None:
        parser = _Parser()
        monkeypatch.setitem(
            __import__("core.scheduler", fromlist=["PARSERS"]).PARSERS,
            parser.slug,
            lambda: parser,
        )
        scheduler = SourceScheduler(
            [ScheduleConfig(source=parser.slug, interval_seconds=3600)]
        )

        await scheduler.start()
        await scheduler.stop()

        assert parser.closed is True

    asyncio.run(_go())


def test_scheduler_closes_remaining_parsers_after_close_failure() -> None:
    async def _go() -> None:
        remaining = _Parser()

        await SourceScheduler._close_parsers([_CloseFailingParser(), remaining])

        assert remaining.closed is True

    asyncio.run(_go())


def test_scheduler_bounds_parallel_source_fetches() -> None:
    async def _go() -> None:
        state = {"active": 0, "peak": 0}

        class _ConcurrentParser(_Parser):
            async def fetch(self):
                state["active"] += 1
                state["peak"] = max(state["peak"], state["active"])
                try:
                    await asyncio.sleep(0.02)
                finally:
                    state["active"] -= 1
                yield GrantRecord(
                    source=self.slug,
                    external_id="bounded",
                    title="Bounded fetch",
                    url="https://example.org/bounded",
                )

        scheduler = SourceScheduler(max_concurrency=2)
        await asyncio.gather(
            *(scheduler._fetch_once(_ConcurrentParser()) for _ in range(6))
        )

        assert state["peak"] == 2

    asyncio.run(_go())


def test_worker_heartbeat_tracks_event_loop_liveness(tmp_path) -> None:
    async def _go() -> None:
        heartbeat = tmp_path / "worker-heartbeat"
        stop_event = asyncio.Event()
        task = asyncio.create_task(
            _heartbeat_worker(
                stop_event,
                path=str(heartbeat),
                interval_seconds=1,
            )
        )
        for _ in range(20):
            if heartbeat.exists():
                break
            await asyncio.sleep(0.01)
        stop_event.set()
        await task

        assert heartbeat.is_file()

    asyncio.run(_go())
