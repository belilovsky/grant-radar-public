"""In-memory async fetch queue between scheduler and pipeline (skeleton).

The scheduler enqueues GrantRecord objects produced by source parsers; the
pipeline consumer dequeues them for normalization, scoring, and persistence.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from sources.base import GrantRecord

logger = logging.getLogger(__name__)


class FetchQueue:
    """Thin wrapper around asyncio.Queue with metrics."""

    def __init__(self, maxsize: int = 1000):
        self._queue: asyncio.Queue[GrantRecord] = asyncio.Queue(maxsize=maxsize)
        self._enqueued = 0
        self._dequeued = 0

    async def put(self, record: GrantRecord) -> None:
        await self._queue.put(record)
        self._enqueued += 1

    async def get(self, timeout: Optional[float] = None) -> Optional[GrantRecord]:
        try:
            if timeout is None:
                record = await self._queue.get()
            else:
                record = await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
        self._dequeued += 1
        return record

    def task_done(self) -> None:
        self._queue.task_done()

    async def join(self) -> None:
        await self._queue.join()

    @property
    def stats(self) -> dict:
        return {
            "enqueued": self._enqueued,
            "dequeued": self._dequeued,
            "pending": self._queue.qsize(),
        }

    def size(self) -> int:
        return self._queue.qsize()
