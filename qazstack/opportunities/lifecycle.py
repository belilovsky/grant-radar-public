"""Deterministic opportunity lifecycle normalization."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import date
from typing import Any

_FORECAST_TERMS = (
    "forecast",
    "forecasted",
    "pipeline",
    "planned",
    "planning",
    "preparation",
    "upcoming",
    "concept",
    "prequalification",
    "pre-qualification",
    "pre solicitation",
    "pre-solicitation",
    "general procurement notice",
)
_OPEN_TERMS = (
    "open",
    "posted",
    "active",
    "ongoing",
    "current",
    "call for proposals",
    "call open",
)
_CLOSED_TERMS = (
    "closed",
    "expired",
    "cancelled",
    "canceled",
    "withdrawn",
    "archived",
    "terminated",
)
_AWARDED_TERMS = (
    "awarded",
    "award notice",
    "winner",
    "selected",
    "contract award",
    "contract signed",
    "completed",
    "implemented",
)


def _get(item: Any, key: str) -> Any:
    return item.get(key) if isinstance(item, Mapping) else getattr(item, key, None)


def _raw(item: Any) -> Mapping[str, Any]:
    value = _get(item, "raw")
    return value if isinstance(value, Mapping) else {}


def normalized_token(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _tags(item: Any) -> set[str]:
    values = _get(item, "tags")
    return {
        normalized_token(value) for value in values or () if normalized_token(value)
    }


def deadline_policy(item: Any) -> str:
    return normalized_token(_raw(item).get("deadline_policy"))


def _status_blob(item: Any) -> str:
    values: list[str] = []
    raw = _raw(item)
    for key in (
        "opportunity_status",
        "status",
        "status_raw",
        "project_status",
        "projectstatusdisplay",
        "notice_type",
    ):
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            values.append(value)
    explicit = _get(item, "opportunity_status")
    if isinstance(explicit, str) and explicit.strip():
        values.append(explicit)
    return normalized_token(" ".join(values))


def _has_term(blob: str, terms: tuple[str, ...]) -> bool:
    return any(term in blob for term in terms)


def is_awarded_item(item: Any) -> bool:
    return _has_term(_status_blob(item), _AWARDED_TERMS)


def is_rolling_item(item: Any) -> bool:
    return deadline_policy(item) == "rolling" or "rolling" in _tags(item)


def normalized_opportunity_status(item: Any, today: date | None = None) -> str:
    today = today or date.today()
    blob = _status_blob(item)
    tags = _tags(item)
    policy = deadline_policy(item)
    deadline = _get(item, "deadline")
    if is_awarded_item(item):
        return "archived"
    if policy == "closed" or "closed" in tags or _has_term(blob, _CLOSED_TERMS):
        return "closed"
    if (
        "project_pipeline" in tags
        or _has_term(blob, _FORECAST_TERMS)
        or blob in {"draft", "upcoming"}
    ):
        return "upcoming"
    if deadline and deadline < today:
        return "closed"
    if is_rolling_item(item):
        return "open"
    if deadline and (deadline - today).days <= 14:
        return "closing_soon"
    if deadline and deadline >= today:
        return "open"
    if _has_term(blob, _OPEN_TERMS):
        return "open"
    return "open" if not deadline else "unknown"


def public_lifecycle(item: Any, today: date | None = None) -> str:
    status = normalized_opportunity_status(item, today=today)
    if is_awarded_item(item):
        return "awarded"
    if status == "upcoming":
        return "forecast"
    if status == "closing_soon":
        return "closing_soon"
    if status in {"closed", "archived"}:
        return "closed"
    if is_rolling_item(item):
        return "rolling"
    return "open"
