"""Integration test for M2 end-to-end flow.

Exercises: Parsers -> SourceScheduler -> FetchQueue -> PipelineRunner -> Processor.
"""

from __future__ import annotations

import pytest

from core.fetch_queue import FetchQueue
from core.pipeline_runner import PipelineRunner
from core.scheduler import SourceScheduler
from sources import PARSERS


class _StubParser:
    name = "stub"

    def fetch(self):
        return [
            {"id": "g1", "title": "Grant One", "source": self.name},
            {"id": "g2", "title": "Grant Two", "source": self.name},
        ]


def test_m2_end_to_end_flow():
    queue = FetchQueue()
    scheduler = SourceScheduler(parsers=[_StubParser()], queue=queue)
    scheduler.run_once()

    assert queue.size() == 2

    processed = []

    def processor(record):
        processed.append(record)

    runner = PipelineRunner(queue=queue, processor=processor)
    runner.run_until_empty()

    assert len(processed) == 2
    assert {r["id"] for r in processed} == {"g1", "g2"}
    assert queue.size() == 0


def test_parsers_registry_contains_m2_sources():
    # M2 sources should be registered
    expected = {"grants_gov", "astana_hub", "internews"}
    assert expected.issubset(set(PARSERS.keys()))


class _EmptyParser:
    name = "empty"

    def fetch(self):
        return []


class _RaisingParser:
    name = "raising"

    def fetch(self):
        raise RuntimeError("boom")


def test_m2_empty_parser_results_in_empty_queue():
    queue = FetchQueue()
    scheduler = SourceScheduler(parsers=[_EmptyParser()], queue=queue)
    scheduler.run_once()
    assert queue.size() == 0


def test_m2_processor_exception_increments_errors_and_drains_queue():
    queue = FetchQueue()
    scheduler = SourceScheduler(parsers=[_StubParser()], queue=queue)
    scheduler.run_once()
    assert queue.size() == 2

    def bad_processor(record):
        raise ValueError("processor error: " + str(record.get("id")))

    runner = PipelineRunner(queue=queue, processor=bad_processor)
    runner.run_until_empty()

    # Both records were attempted; both raised; queue is drained
    assert queue.size() == 0
    assert getattr(runner, "errors", 0) == 2
    assert getattr(runner, "processed", 0) == 0


def test_m2_scheduler_isolates_failing_parser():
    queue = FetchQueue()
    scheduler = SourceScheduler(
        parsers=[_RaisingParser(), _StubParser()],
        queue=queue,
    )
    # Failing parser should not prevent the good one from enqueuing items
    try:
        scheduler.run_once()
    except Exception:
        pytest.fail("SourceScheduler must isolate failing parsers")

    assert queue.size() == 2
