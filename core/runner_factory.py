"""Runner factory: assemble PipelineRunner with a deduplicating, persistent processor.

Keeps wiring out of `core/pipeline_runner.py` so existing tests that construct
`PipelineRunner` directly stay backwards-compatible.

Usage:
    queue = FetchQueue()
    runner = build_default_runner(queue)                  # uses make_repository()
    runner = build_default_runner(queue, repository=my_repo)
    runner = build_default_runner(queue, processor=my_inner)
    runner = build_default_runner(queue, run_recorder=my_recorder)

When ``GRANT_RADAR_DB_URL`` is configured, the factory also attaches a
``RunRecorder`` so pipeline executions are persisted to the ``runs`` table
and can be inspected via the ``show-runs`` CLI.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Awaitable, Callable, Optional

from .fetch_queue import FetchQueue
from .persistence import DedupProcessor, Repository
from .pipeline_runner import PipelineRunner, default_processor
from .repository_factory import make_repository
from .run_recorder_adapter import RunRecorder

logger = logging.getLogger(__name__)

Processor = Callable[[object], Awaitable[None]]


def _maybe_build_recorder(source: str = "pipeline") -> Optional[RunRecorder]:
    """Build a RunRecorder from GRANT_RADAR_DB_URL when available.

    Returns ``None`` if the env var is not set or SQLAlchemy is unavailable,
    keeping the runner fully functional in degraded environments.
    """
    db_url = os.environ.get("GRANT_RADAR_DB_URL")
    if not db_url:
        return None
    try:
        from .db import get_engine

        engine = get_engine(db_url)
    except Exception:
        logger.debug("run_recorder_engine_unavailable - skipping recorder")
        return None
    return RunRecorder(engine=engine, source=source)


def build_default_runner(
    queue: FetchQueue,
    *,
    repository: Optional[Repository] = None,
    processor: Optional[Processor] = None,
    idle_timeout: float = 1.0,
    run_recorder: Optional[Any] = None,
    source: str = "pipeline",
) -> PipelineRunner:
    """Build a PipelineRunner with dedup + persistence + run recording wired in.

    Resolution:
    * ``repository`` overrides factory; otherwise ``make_repository()`` is called
      (env-driven: GRANT_RADAR_DB_URL).
    * ``processor`` is the inner async callable; defaults to ``default_processor``
      (which applies scoring + structured logging).
    * The inner processor is wrapped with ``DedupProcessor(repo, inner=...)``
      so each record is fingerprinted, deduplicated and refreshed in storage.
    * ``run_recorder`` overrides factory; otherwise a recorder is auto-built
      from ``GRANT_RADAR_DB_URL`` when available, else left as ``None``.
    """
    repo = repository if repository is not None else make_repository()
    inner = processor if processor is not None else default_processor
    dedup = DedupProcessor(repo, inner=inner)
    recorder = (
        run_recorder if run_recorder is not None else _maybe_build_recorder(source)
    )
    return PipelineRunner(
        queue,
        processor=dedup,
        idle_timeout=idle_timeout,
        run_recorder=recorder,
    )


__all__ = ["build_default_runner"]
