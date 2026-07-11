"""Geo-fit helpers for Kazakhstan/Central Asia opportunity radars."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from .models import OpportunityRecord

CENTRAL_ASIA_GEO_PATTERNS: tuple[str, ...] = (
    r"\bkazakhstan\b",
    r"\bcentral[\s_-]+asia\b",
    r"\bcentral[\s_-]+asian\b",
    r"\beurasia\b",
    r"\bcis\b",
    r"\buzbekistan\b",
    r"\bkyrgyzstan\b",
    r"\btajikistan\b",
    r"\bturkmenistan\b",
)

GLOBAL_GEO_PATTERNS: tuple[str, ...] = (
    r"\bglobal\b",
    r"\bworldwide\b",
    r"\binternational\b",
    r"\bany[\s_-]+country\b",
    r"\ball[\s_-]+countries\b",
)

POSITIVE_GEO_PATTERNS: tuple[str, ...] = CENTRAL_ASIA_GEO_PATTERNS + GLOBAL_GEO_PATTERNS

HARD_EXCLUSION_PATTERNS: tuple[str, ...] = (
    r"\((?:u\.?s\.?|usa|united[\s_-]+states|hungary|iraq|india)\)",
    r"\bamerican[\s_-]+indians?\b",
    r"\bnative[\s_-]+americans?\b",
    r"\balaska[\s_-]+natives?\b",
    r"\bnative[\s_-]+hawaiians?\b",
    r"\bfederally[\s_-]+recognized[\s_-]+tribes?\b",
    r"\bindian[\s_-]+tribes?\b",
    r"\btribal[\s_-]+governments?\b",
    r"\btribal[\s_-]+organizations?\b",
    r"\bu\.?s\.?[\s_-]+only\b",
    r"\bunited[\s_-]+states[\s_-]+only\b",
    r"\bu\.?s\.?[\s_-]+citizens?\b",
    r"\bu\.?s\.?[\s_-]+permanent[\s_-]+residents?\b",
    r"\bhungary\b",
    r"\biraq\b",
    r"\bindia\b",
)

LOW_CONFIDENCE_SOURCE_SLUGS: frozenset[str] = frozenset(
    {"grants_gov", "opportunity_desk", "fundsforngos"}
)

HARD_EXCLUSION_RAW_VALUES: tuple[str, ...] = (
    "HHS-ACF-ANA",
    "Administration for Native Americans",
    "AI3 Action Institute",
    "Technical Difficulties",
    "experiencing technical difficulties",
)


@dataclass(frozen=True)
class GeoFitResult:
    """Result of Kazakhstan/Central Asia opportunity geo-fit evaluation."""

    has_positive_signal: bool
    has_central_asia_signal: bool
    exclusion_reason: str | None = None
    low_confidence: bool = False

    @property
    def is_relevant(self) -> bool:
        """Whether the opportunity is suitable for a Kazakhstan-focused feed."""

        return self.exclusion_reason is None and not self.low_confidence


def _get(item: Any, key: str) -> Any:
    if isinstance(item, Mapping):
        return item.get(key)
    return getattr(item, key, None)


def _flatten(value: Any) -> Iterable[str]:
    if value is None:
        return
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, Mapping):
        for key, nested in value.items():
            yield str(key)
            yield from _flatten(nested)
        return
    if isinstance(value, Iterable):
        for nested in value:
            yield from _flatten(nested)
        return
    yield str(value)


def _text(item: Any, *, include_raw: bool, include_tags: bool) -> str:
    parts: list[str] = []
    for key in ("title", "summary", "description", "funder"):
        value = _get(item, key)
        if value:
            parts.extend(_flatten(value))
    parts.extend(_flatten(_get(item, "eligibility")))
    parts.extend(_flatten(_get(item, "languages")))
    if include_tags:
        parts.extend(_flatten(_get(item, "tags")))
    raw = _get(item, "raw") if include_raw else None
    if raw is not None:
        parts.extend(_flatten(raw))
    return " ".join(parts).lower()


def _raw_json(item: Any) -> str:
    raw = _get(item, "raw")
    try:
        return json.dumps(raw or {}, ensure_ascii=False, default=str)
    except TypeError:
        return str(raw or "")


def _matches_any(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _has_signal(item: Any, patterns: Iterable[str]) -> bool:
    text = _text(item, include_raw=False, include_tags=False)
    return _matches_any(text, patterns)


def as_opportunity_record(item: Any) -> OpportunityRecord:
    """Convert a product-local object or mapping into ``OpportunityRecord``."""

    return OpportunityRecord(
        source=str(_get(item, "source") or ""),
        title=str(_get(item, "title") or ""),
        summary=str(_get(item, "summary") or ""),
        description=str(_get(item, "description") or ""),
        funder=_get(item, "funder"),
        eligibility=tuple(_flatten(_get(item, "eligibility"))),
        languages=tuple(_flatten(_get(item, "languages"))),
        tags=tuple(_flatten(_get(item, "tags"))),
        deadline=_get(item, "deadline"),
        raw=_get(item, "raw") or {},
    )


def evaluate_geo_fit(item: Any) -> GeoFitResult:
    """Evaluate geo relevance for a Kazakhstan/Central Asia opportunity feed."""

    record = as_opportunity_record(item)
    source = record.source.lower()
    has_central_asia = _has_signal(record, CENTRAL_ASIA_GEO_PATTERNS)
    has_positive = _has_signal(record, POSITIVE_GEO_PATTERNS)
    text = _text(record, include_raw=True, include_tags=True)

    exclusion_reason: str | None = None
    if _matches_any(text, HARD_EXCLUSION_PATTERNS):
        exclusion_reason = "hard geo exclusion"
    else:
        raw_text = _raw_json(record).lower()
        for value in HARD_EXCLUSION_RAW_VALUES:
            if value.lower() in raw_text:
                exclusion_reason = value
                break

    low_confidence = source in LOW_CONFIDENCE_SOURCE_SLUGS and not has_central_asia
    return GeoFitResult(
        has_positive_signal=has_positive,
        has_central_asia_signal=has_central_asia,
        exclusion_reason=exclusion_reason,
        low_confidence=low_confidence,
    )
