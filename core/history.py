"""Public, source-grounded version snapshots for opportunity records.

The history contract intentionally stores only normalized public fields.  It does
not retain source HTML, parser payloads, operator notes, or delivery metadata.
Snapshots are content-addressed so an unchanged parser refresh does not create a
noisy new version.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from core.typography_policy import normalize_text

HISTORY_SCHEMA_VERSION = "history.v1"
HISTORY_FIELDS = (
    "source",
    "source_url",
    "type",
    "title",
    "summary",
    "funder",
    "amount_min",
    "amount_max",
    "currency",
    "deadline",
    "eligibility",
    "tags",
    "opportunity_status",
    "lifecycle",
    "application_url",
    "deadline_policy",
)


def _value(record: Any, key: str) -> Any:
    if isinstance(record, Mapping):
        return record.get(key)
    return getattr(record, key, None)


def _raw_layers(record: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = _value(record, "raw")
    if not isinstance(raw, Mapping):
        return {}, {}
    outer = dict(raw)
    nested = outer.get("raw")
    if isinstance(nested, Mapping) and {
        "type",
        "eligibility",
        "tags",
        "languages",
    }.issubset(outer):
        return outer, dict(nested)
    return outer, outer


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = normalize_text(str(value).strip())
    return text or None


def _date_or_text(value: Any) -> str | None:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return _text(value)


def _decimal_or_text(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return format(value, "f")
    return _text(value)


def _list_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values: Sequence[Any] = [value]
    elif isinstance(value, Sequence):
        values = value
    else:
        values = [value]
    normalized = {
        normalize_text(str(item).strip()) for item in values if str(item).strip()
    }
    return sorted(normalized, key=str.casefold)


def public_snapshot(record: Any) -> dict[str, Any]:
    """Return the stable public fields used for a version hash and diff."""

    outer, nested = _raw_layers(record)
    source_url = _value(record, "source_url") or _value(record, "url")
    type_value = _value(record, "type") or outer.get("type") or nested.get("type")
    if type_value is not None and hasattr(type_value, "value"):
        type_value = getattr(type_value, "value", type_value)

    eligibility = (
        _value(record, "eligibility")
        or outer.get("eligibility")
        or nested.get("eligibility")
    )
    tags = _value(record, "tags") or outer.get("tags") or nested.get("tags")
    application_url = (
        _value(record, "application_url")
        or outer.get("application_url")
        or nested.get("application_url")
    )
    snapshot = {
        "source": _text(_value(record, "source") or nested.get("source")),
        "source_url": _text(source_url),
        "type": _text(type_value),
        "title": _text(_value(record, "title") or nested.get("title")),
        "summary": _text(
            _value(record, "summary")
            or nested.get("summary")
            or nested.get("description")
        ),
        "funder": _text(_value(record, "funder") or nested.get("funder")),
        "amount_min": _decimal_or_text(
            _value(record, "amount_min") or nested.get("amount_min")
        ),
        "amount_max": _decimal_or_text(
            _value(record, "amount_max") or nested.get("amount_max")
        ),
        "currency": _text(_value(record, "currency") or nested.get("currency")),
        "deadline": _date_or_text(_value(record, "deadline") or nested.get("deadline")),
        "eligibility": _list_value(eligibility),
        "tags": _list_value(tags),
        "opportunity_status": _text(
            _value(record, "opportunity_status")
            or outer.get("opportunity_status")
            or nested.get("opportunity_status")
            or nested.get("status")
        ),
        "lifecycle": _text(
            _value(record, "lifecycle")
            or outer.get("lifecycle")
            or nested.get("lifecycle")
        ),
        "application_url": _text(application_url),
        "deadline_policy": _text(
            outer.get("deadline_policy") or nested.get("deadline_policy")
        ),
    }
    return {key: snapshot[key] for key in HISTORY_FIELDS}


def snapshot_hash(snapshot: Mapping[str, Any]) -> str:
    """Return a stable content hash for a public snapshot."""

    encoded = json.dumps(
        {key: snapshot.get(key) for key in HISTORY_FIELDS},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def changed_fields(
    previous: Mapping[str, Any] | None,
    current: Mapping[str, Any],
) -> list[str]:
    """List fields whose public values changed, in contract order."""

    if previous is None:
        return ["initial"]
    return [
        field for field in HISTORY_FIELDS if previous.get(field) != current.get(field)
    ]


def history_entry(
    *,
    version: int,
    observed_at: Any,
    snapshot: Mapping[str, Any],
    changed: list[str],
) -> dict[str, Any]:
    """Build a JSON-safe public history entry."""

    if isinstance(observed_at, (datetime, date)):
        observed: str | None = observed_at.isoformat()
    else:
        observed = _text(observed_at)
    return {
        "version": int(version),
        "observed_at": observed,
        "content_hash": snapshot_hash(snapshot),
        "changed_fields": list(changed),
        "fields": {key: snapshot.get(key) for key in HISTORY_FIELDS},
    }


__all__ = [
    "HISTORY_FIELDS",
    "HISTORY_SCHEMA_VERSION",
    "changed_fields",
    "history_entry",
    "public_snapshot",
    "snapshot_hash",
]
