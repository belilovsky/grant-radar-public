"""Tests for PipelineRunner integration with the Run recorder.

These tests use a lightweight in-memory fake recorder so they remain
independent of the SQLAlchemy persistence layer and can run in any
environment (including the local CI fallback flow).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pytest

from core.fetch_queue import FetchQueue
from core.pipeline_runner import PipelineRunner
from sources.base import GrantRecord


@dataclass
class FakeRecorder:
    started: int = 0
    finished: List[dict] = field(default_factory=list)
    errors: int = 0
    next_id: int = 1

    def start(self) -> int:
        self.started += 1
        rid = self.next_id
        self.next_id += 1
        return rid

    def finish(self, run_id: int, processed: int, errors: int, status: str) -> None:
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


def _make_record(ext_id: str = "ext-1") -> GrantRecord:
    return GrantRecord(
        source="test",
        external_id=ext_id,
        title=f"Title {ext_id}",
        url="https://example.com",
        description="desc",
    )


@pytest.mark.asyncio
async def test_run_recorder_records_lifecycle_on_run_until_empty() -> None:
    queue = FetchQueue()
    await queue.put(_make_record("a"))
    await queue.put(_make_record("b"))

    async def proc(rec: GrantRecord) -> None:
        return None

    rec = FakeRecorder()
    runner = PipelineRunner(queue, processor=proc, idle_timeout=0.05, run_recorder=rec)

    await runner.run_until_empty()

    assert rec.started == 1
    assert len(rec.finished) == 1
    assert rec.finished[0]["processed"] == 2
    assert rec.finished[0]["errors"] == 0
    assert rec.finished[0]["status"] == "ok"


@pytest.mark.asyncio
async def test_run_recorder_reports_processor_errors() -> None:
    queue = FetchQueue()
    await queue.put(_make_record("x"))

    async def boom(rec: GrantRecord) -> None:
        raise RuntimeError("boom")

    rec = FakeRecorder()
    runner = PipelineRunner(queue, processor=boom, idle_timeout=0.05, run_recorder=rec)

    await runner.run_until_empty()

    assert rec.started == 1
    assert rec.errors == 1
    assert rec.finished[0]["processed"] == 0
    assert rec.finished[0]["errors"] == 1


@pytest.mark.asyncio
async def test_run_recorder_optional_no_recorder() -> None:
    queue = FetchQueue()
    await queue.put(_make_record("a"))

    async def proc(rec: GrantRecord) -> None:
        return None

    runner = PipelineRunner(queue, processor=proc, idle_timeout=0.05)
    await runner.run_until_empty()
    assert runner.processed == 1
    assert runner.errors == 0
