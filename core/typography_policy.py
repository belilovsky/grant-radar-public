"""QAZ.FUND consumer snapshot of the portfolio Typography Policy v1.

The shared portfolio package owns the contract.  This dependency-free copy is
kept in the service so the public projection remains safe when the package is
not installed in the runtime image.  Keep the version and behavior aligned
with ``portfolio-typography-policy``; product code must not add a competing
dash rule.
"""

from __future__ import annotations

import re
from typing import Any

POLICY_VERSION = "1.0.0"

_VIOLATION_RE = re.compile(
    r"(?P<unicode>\u2014)"
    r"|(?P<named>&mdash;)"
    r"|(?P<decimal>&#8212;)"
    r"|(?P<hex>&#x2014;)",
    re.IGNORECASE,
)
_PROTECTED_RE = re.compile(
    r"(?ix)"
    r"(?:\b(?:https?|ftp)://[^\s<>\"']+)"
    r"|(?:\b(?:href|src|action|cite|poster)\s*=\s*[\"'][^\"']*[\"'])"
)


def _protected_ranges(text: str) -> list[tuple[int, int]]:
    return [match.span() for match in _PROTECTED_RE.finditer(text)]


def _is_protected(position: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= position < end for start, end in ranges)


def _kind(match: re.Match[str]) -> str:
    for name in ("unicode", "named", "decimal", "hex"):
        if match.group(name) is not None:
            return name
    return "unknown"


def _replacement(match: re.Match[str]) -> str:
    kind = _kind(match)
    if kind == "unicode":
        return "–"
    if kind == "named":
        return "&ndash;"
    if kind == "decimal":
        return "&#8211;"
    if kind == "hex":
        return "&#x2013;"
    return match.group(0)


def normalize_text(value: str) -> str:
    """Normalize editorial em dashes while preserving technical values."""

    protected = _protected_ranges(value)
    pieces: list[str] = []
    cursor = 0
    for match in _VIOLATION_RE.finditer(value):
        if _is_protected(match.start(), protected):
            continue
        pieces.extend((value[cursor : match.start()], _replacement(match)))
        cursor = match.end()
    pieces.append(value[cursor:])
    return "".join(pieces)


def scan_text(value: str) -> list[dict[str, object]]:
    """Return violations outside protected technical contexts."""

    protected = _protected_ranges(value)
    findings: list[dict[str, object]] = []
    for match in _VIOLATION_RE.finditer(value):
        if _is_protected(match.start(), protected):
            continue
        previous_newline = value.rfind("\n", 0, match.start())
        findings.append(
            {
                "line": value.count("\n", 0, match.start()) + 1,
                "column": match.start() - previous_newline,
                "kind": _kind(match),
                "snippet": value[
                    max(0, match.start() - 36) : min(len(value), match.end() + 36)
                ].replace("\n", "\\n"),
            }
        )
    return findings


def normalize_public_value(value: Any) -> Any:
    """Recursively normalize public strings without changing object shape."""

    if isinstance(value, str):
        return normalize_text(value)
    if isinstance(value, list):
        return [normalize_public_value(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_public_value(item) for key, item in value.items()}
    return value


def normalize_public_opportunity(item: Any) -> Any:
    """Normalize public Opportunity fields while preserving raw provenance."""

    public_fields = (
        "source",
        "title",
        "summary",
        "funder",
        "funder_slug",
        "currency",
        "opportunity_status",
        "lifecycle",
        "eligibility",
        "tags",
        "languages",
    )
    updates = {
        field: normalize_public_value(getattr(item, field))
        for field in public_fields
        if hasattr(item, field)
    }
    model_copy = getattr(item, "model_copy", None)
    return model_copy(update=updates) if callable(model_copy) else item


def normalize_public_detail(item: Any) -> Any:
    """Normalize a public detail model without touching its raw payload."""

    normalized = normalize_public_opportunity(item)
    sections = []
    for section in getattr(normalized, "detail_sections", []):
        data = normalize_public_value(section.model_dump())
        sections.append(section.model_copy(update=data))
    metadata = []
    for field in getattr(normalized, "metadata", []):
        data = normalize_public_value(field.model_dump())
        metadata.append(field.model_copy(update=data))
    updates = {
        "detail_text": normalize_public_value(getattr(normalized, "detail_text")),
        "detail_sections": sections,
        "metadata": metadata,
    }
    model_copy = getattr(normalized, "model_copy", None)
    return model_copy(update=updates) if callable(model_copy) else normalized


__all__ = [
    "POLICY_VERSION",
    "normalize_public_detail",
    "normalize_public_opportunity",
    "normalize_public_value",
    "normalize_text",
    "scan_text",
]
