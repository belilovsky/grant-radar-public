"""Tests for core.pipeline_runner.PipelineRunner."""

import asyncio

from core.fetch_queue import FetchQueue
from core.pipeline_runner import PipelineRunner
from sources.base import GrantRecord


def _record(i: int) -> GrantRecord:
    return GrantRecord(source="t", external_id=str(i), title=f"t{i}", url="https://x")


def test_drain_once_processes_all_items():
    seen: list[str] = []

    async def proc(rec: GrantRecord) -> None:
        seen.append(rec.external_id)

    async def _go():
        q = FetchQueue()
        for i in range(3):
            await q.put(_record(i))
        runner = PipelineRunner(q, processor=proc)
        return await runner.drain_once(), runner.processed, runner.errors

    n, processed, errors = asyncio.run(_go())
    assert n == 3
    assert processed == 3
    assert errors == 0
    assert seen == ["0", "1", "2"]


def test_processor_errors_counted_not_raised():
    async def bad(rec: GrantRecord) -> None:
        raise RuntimeError("boom")

    async def _go():
        q = FetchQueue()
        await q.put(_record(1))
        runner = PipelineRunner(q, processor=bad)
        n = await runner.drain_once()
        return n, runner.processed, runner.errors

    n, processed, errors = asyncio.run(_go())
    assert n == 0
    assert processed == 0
    assert errors == 1


def test_start_stop_loop_processes_late_arrivals():
    seen: list[str] = []

    async def proc(rec: GrantRecord) -> None:
        seen.append(rec.external_id)

    async def _go():
        q = FetchQueue()
        runner = PipelineRunner(q, processor=proc, idle_timeout=0.05)
        await runner.start()
        await q.put(_record(42))
        # give the loop a moment to consume
        await asyncio.sleep(0.2)
        await runner.stop()
        return runner.processed

    processed = asyncio.run(_go())
    assert processed == 1
    assert seen == ["42"]
