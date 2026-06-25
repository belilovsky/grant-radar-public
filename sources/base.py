"""Base classes and record contract for grant source parsers.

The codebase has two ingestion paths:

* API-oriented ``BaseSource`` implementations that can yield rich
  ``core.models.Opportunity`` objects.
* Queue-oriented parser/scheduler code that works with lightweight
  ``GrantRecord`` objects.

Both paths share the same HTTP client and lifecycle helpers here so new
sources can be wired into either layer without duplicating plumbing.
"""

from __future__ import annotations

import abc
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import httpx
import structlog

from core.models import Opportunity

log = structlog.get_logger()


@dataclass
class GrantRecord:
    """Normalized lightweight opportunity record for the M2 queue."""

    source: str
    external_id: str
    title: str
    url: str
    description: str = ""
    deadline: date | None = None
    tags: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
    score: float | None = None

    @property
    def id(self) -> str:
        return self.external_id

    @property
    def summary(self) -> str:
        return self.description

    @property
    def source_url(self) -> str:
        return self.url

    def fingerprint(self) -> str:
        if self.external_id:
            return f"{self.source}:{self.external_id}"
        return f"{self.source}:{self.url}"


class BaseSourceParser(abc.ABC):
    """Common async parser contract used by the scheduler."""

    name: str
    base_url: str
    request_delay: float = 1.0

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client or httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "grant-radar/0.1 (+https://github.com/belilovsky/grant-radar)"
            },
            follow_redirects=True,
        )
        self._log = log.bind(source=self.name)

    @abc.abstractmethod
    async def fetch(self) -> AsyncIterator[GrantRecord | Opportunity]:
        """Yield normalized records from the source."""
        raise NotImplementedError
        yield  # type: ignore[unreachable]

    async def healthcheck(self) -> bool:
        try:
            resp = await self.client.get(self.base_url)
            return resp.status_code < 500
        except Exception:  # noqa: BLE001
            return False

    async def close(self) -> None:
        await self.client.aclose()

    async def __aenter__(self) -> "BaseSourceParser":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()


class BaseSource(BaseSourceParser):
    slug: str
    name: str
    base_url: str
    default_tags: list[str] = []

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client or httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "grant-radar/0.1 (+https://github.com/belilovsky/grant-radar)"
            },
            follow_redirects=True,
        )

    @abc.abstractmethod
    async def fetch(self) -> AsyncIterator[Opportunity]:
        """Выдаёт новые Opportunity из источника."""
        raise NotImplementedError
        yield  # type: ignore[unreachable]
