"""Fail-closed publication rules for known unsafe opportunity records.

This boundary is intentionally small and evidence-backed. It is not a general
reputation engine: entries are added only when a publication or destination has
been independently confirmed as unsafe or falsely impersonating an organiser.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse

BLOCKED_DESTINATION_HOSTS = frozenset({"ifcgrants.org"})
BLOCKED_PUBLICATION_MARKERS = frozenset({"ifc-women-led-business-grant-2026"})


def _value(item: Any, key: str) -> Any:
    if isinstance(item, Mapping):
        return item.get(key)
    return getattr(item, key, None)


def _normalized_marker(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")


def _candidate_values(item: Any) -> list[str]:
    values = [
        str(_value(item, "title") or ""),
        str(_value(item, "summary") or ""),
        str(_value(item, "source_url") or ""),
        str(_value(item, "application_url") or ""),
    ]
    raw = _value(item, "raw")
    if isinstance(raw, Mapping):
        for key in (
            "external_id",
            "application_url",
            "official_source",
            "source_url",
            "url",
        ):
            values.append(str(raw.get(key) or ""))
        reviewed = raw.get("reviewed_source_urls")
        if isinstance(reviewed, (list, tuple, set)):
            values.extend(str(value or "") for value in reviewed)
    return [value.strip() for value in values if value and value.strip()]


def blocked_publication_reason(item: Any) -> str | None:
    """Return a stable reason code when an item must not be published."""

    values = _candidate_values(item)
    for value in values:
        parsed = urlparse(value)
        host = (parsed.hostname or "").lower().rstrip(".")
        if host.startswith("www."):
            host = host[4:]
        if host in BLOCKED_DESTINATION_HOSTS:
            return f"blocked_destination_host:{host}"

    normalized = " ".join(_normalized_marker(value) for value in values)
    for marker in BLOCKED_PUBLICATION_MARKERS:
        if marker in normalized:
            return f"blocked_publication_marker:{marker}"
    return None


def is_publication_blocked(item: Any) -> bool:
    return blocked_publication_reason(item) is not None
