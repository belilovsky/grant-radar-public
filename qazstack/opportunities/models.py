"""Shared opportunity records and source contracts.

This is a vendored dependency-free snapshot from QazStack. Keep it small and
update only through explicit QazStack primitive sync passes.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class OpportunityRecord:
    """Minimal opportunity shape used by geo-fit and parser parity checks."""

    source: str
    title: str
    summary: str = ""
    description: str = ""
    funder: str | None = None
    eligibility: Sequence[str] = field(default_factory=tuple)
    languages: Sequence[str] = field(default_factory=tuple)
    tags: Sequence[str] = field(default_factory=tuple)
    deadline: date | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SourceContract:
    """Public source parser contract shared by opportunity-radar products."""

    slug: str
    name: str
    base_url: str
    request_delay: float = 1.0
    default_tags: Sequence[str] = field(default_factory=tuple)

    def validate(self) -> None:
        """Raise ``ValueError`` when the source contract is not usable."""

        if not self.slug.strip():
            raise ValueError("source contract slug is required")
        if not self.name.strip():
            raise ValueError("source contract name is required")
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError("source contract base_url must be absolute http(s)")
        if self.request_delay < 0:
            raise ValueError("source contract request_delay must be non-negative")
