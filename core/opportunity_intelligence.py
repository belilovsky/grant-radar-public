"""Shared heuristics for public opportunity lifecycle and catalog signals."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from core.models import Opportunity

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


def normalized_token(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _normalized_tags(item: Opportunity) -> set[str]:
    return {
        normalized_token(tag)
        for tag in (item.tags if isinstance(item.tags, list) else [])
        if normalized_token(tag)
    }


def _raw(item: Opportunity) -> dict[str, Any]:
    return item.raw if isinstance(item.raw, dict) else {}


def deadline_policy(item: Opportunity) -> str:
    return normalized_token(_raw(item).get("deadline_policy"))


def _status_blob(item: Opportunity) -> str:
    raw = _raw(item)
    values: list[str] = []
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
            values.append(value.strip())
    return normalized_token(" ".join(values))


def _has_term(blob: str, terms: tuple[str, ...]) -> bool:
    return any(term in blob for term in terms)


def is_awarded_item(item: Opportunity) -> bool:
    return _has_term(_status_blob(item), _AWARDED_TERMS)


def is_rolling_item(item: Opportunity) -> bool:
    policy = deadline_policy(item)
    tags = _normalized_tags(item)
    return policy == "rolling" or "rolling" in tags


def normalized_opportunity_status(item: Opportunity, today: date | None = None) -> str:
    today = today or date.today()
    status_blob = _status_blob(item)
    tags = _normalized_tags(item)
    policy = deadline_policy(item)

    if is_awarded_item(item):
        return "archived"
    if policy == "closed" or "closed" in tags or _has_term(status_blob, _CLOSED_TERMS):
        return "closed"
    if (
        "project_pipeline" in tags
        or _has_term(status_blob, _FORECAST_TERMS)
        or status_blob in {"draft", "upcoming"}
    ):
        return "upcoming"
    if item.deadline and item.deadline < today:
        return "closed"
    if is_rolling_item(item):
        return "open"
    if item.deadline and (item.deadline - today).days <= 14:
        return "closing_soon"
    if item.deadline and item.deadline >= today:
        return "open"
    if _has_term(status_blob, _OPEN_TERMS):
        return "open"
    return "open" if not item.deadline else "unknown"


def public_lifecycle(item: Opportunity, today: date | None = None) -> str:
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
