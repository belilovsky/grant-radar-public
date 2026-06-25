"""Tests for core.fetch_queue.FetchQueue."""

import asyncio

from core.fetch_queue import FetchQueue
from sources.base import GrantRecord


def _record(i: int) -> GrantRecord:
    return GrantRecord(source="t", external_id=str(i), title=f"t{i}", url="https://x")


def test_put_get_roundtrip():
    async def _go():
        q = FetchQueue(maxsize=10)
        await q.put(_record(1))
        await q.put(_record(2))
        a = await q.get()
        b = await q.get()
        return a, b, q.stats

    a, b, stats = asyncio.run(_go())
    assert a.external_id == "1"
    assert b.external_id == "2"
    assert stats == {"enqueued": 2, "dequeued": 2, "pending": 0}


def test_get_timeout_returns_none():
    async def _go():
        q = FetchQueue()
        return await q.get(timeout=0.01)

    assert asyncio.run(_go()) is None


def test_join_completes_after_task_done():
    async def _go():
        q = FetchQueue()
        await q.put(_record(1))
        await q.get()
        q.task_done()
        await asyncio.wait_for(q.join(), timeout=0.5)
        return True

    assert asyncio.run(_go()) is True
