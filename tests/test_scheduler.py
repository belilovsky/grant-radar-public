"""Tests for core.scheduler.SourceScheduler."""

import asyncio

from core.scheduler import ScheduleConfig, SourceScheduler, build_default_configs


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
