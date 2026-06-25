"""Integration tests for core.runner_factory.build_default_runner.

Verifies end-to-end wiring: FetchQueue -> PipelineRunner -> DedupProcessor
-> Repository (in-memory + sqlite-backed).
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from core.fetch_queue import FetchQueue
from core.persistence import InMemoryRepository
from core.runner_factory import build_default_runner


def _record(
    source="grants_gov",
    external_id="OPP-1",
    title="Title",
    url="https://example.org/1",
    score=8.0,
):
    return SimpleNamespace(
        source=source,
        external_id=external_id,
        title=title,
        url=url,
        score=score,
        summary="sum",
    )


@pytest.mark.asyncio
async def test_runner_factory_in_memory_dedup_persists_once():
    queue = FetchQueue()
    repo = InMemoryRepository()
    runner = build_default_runner(queue, repository=repo, idle_timeout=0.2)

    # publish the same record twice + a different one
    await queue.put(_record(external_id="OPP-1"))
    await queue.put(_record(external_id="OPP-1"))  # duplicate
    await queue.put(_record(external_id="OPP-2"))

    await runner.start()
    await asyncio.sleep(0.5)
    await runner.stop()

    assert repo.size() == 2  # OPP-1 and OPP-2 stored once each


@pytest.mark.asyncio
async def test_runner_factory_with_sqlite_backend():
    pytest.importorskip("sqlalchemy")
    from core.db import SqlRepository

    queue = FetchQueue()
    repo = SqlRepository("sqlite:///:memory:")
    runner = build_default_runner(queue, repository=repo, idle_timeout=0.2)

    await queue.put(_record(external_id="A"))
    await queue.put(_record(external_id="B"))
    await queue.put(_record(external_id="A"))  # duplicate by fingerprint

    await runner.start()
    await asyncio.sleep(0.5)
    await runner.stop()

    assert repo.size() == 2
