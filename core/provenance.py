"""Public provenance profile for QAZ.FUND opportunity records.

The profile deliberately separates an observed record from independently
verified evidence.  It is a small, JSON-safe contract that can be embedded in
the public opportunity payload and consumed by QazPipe or AI clients without
exposing source HTML or operator data.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from qazstack.evidence import resolve_public_evidence_state

from core.models import Opportunity

PROVENANCE_SCHEMA_VERSION = "provenance.v1"
_CONFIDENCE_VALUES = {"supported", "reported", "unknown"}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    value_text = _text(value)
    return value_text or None


def _explicit_timestamp(raw: dict[str, Any]) -> str | None:
    for key in ("last_verified_at", "verified_at", "checked_at"):
        timestamp = _iso(raw.get(key))
        if timestamp:
            return timestamp
    return None


def _source_language(
    item: Opportunity, raw: dict[str, Any]
) -> tuple[str | None, str | None]:
    for key, basis in (("source_language", "explicit"), ("detail_language", "detail")):
        value = _text(raw.get(key))
        if value:
            return value, basis
    languages = [_text(value) for value in item.languages if _text(value)]
    if len(languages) == 1:
        return languages[0], "record_languages"
    return None, None


def _confidence(
    raw: dict[str, Any],
    *,
    field: str,
    value_present: bool,
) -> str:
    explicit = _text(raw.get(f"{field}_confidence")).casefold()
    if explicit in _CONFIDENCE_VALUES:
        return explicit
    if (
        raw.get(f"{field}_raw")
        or raw.get(f"{field}_source")
        or raw.get(f"{field}_policy")
    ):
        return "supported"
    if value_present:
        return "reported"
    return "unknown"


def _status(item: Opportunity, raw: dict[str, Any]) -> str:
    value = (
        item.opportunity_status
        or item.lifecycle
        or raw.get("opportunity_status")
        or raw.get("status")
        or raw.get("status_raw")
    )
    return _text(value).casefold() or "unknown"


def provenance_profile(item: Opportunity) -> dict[str, Any]:
    """Build the versioned, public-safe provenance profile for ``item``.

    ``discovered_at`` is an observation timestamp, not a verification claim.
    ``last_verified_at`` is emitted only when the source adapter supplied an
    explicit check timestamp.  This prevents a fresh parser run from being
    presented as editorial or independent verification.
    """

    raw = item.raw if isinstance(item.raw, dict) else {}
    source_language, source_language_basis = _source_language(item, raw)
    deadline_confidence = _confidence(
        raw,
        field="deadline",
        value_present=bool(item.deadline or raw.get("deadline_policy") == "rolling"),
    )
    amount_confidence = _confidence(
        raw,
        field="amount",
        value_present=bool(
            item.amount_min is not None
            or item.amount_max is not None
            or raw.get("amount_raw")
        ),
    )
    evidence_state = resolve_public_evidence_state(
        direct_source_url=item.source_url,
        reviewed_source_urls=raw.get("reviewed_source_urls") or (),
        declared_state=raw.get("evidence_state"),
    ).value
    evidence_basis: list[str] = []
    if _text(item.source_url):
        evidence_basis.append("direct_source_url")
    if raw.get("reviewed_source_urls"):
        evidence_basis.append("reviewed_source_urls")
    if raw.get("evidence_state"):
        evidence_basis.append("declared_state")

    missing_metadata: list[str] = []
    if not source_language:
        missing_metadata.append("source_language")
    if not _explicit_timestamp(raw):
        missing_metadata.append("last_verified_at")
    if _status(item, raw) == "unknown":
        missing_metadata.append("status")
    if deadline_confidence == "unknown":
        missing_metadata.append("deadline_basis")
    if amount_confidence == "unknown":
        missing_metadata.append("amount_basis")

    return {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "source": _text(item.source) or "unknown",
        "source_url": _text(item.source_url) or None,
        "evidence_state": evidence_state,
        "evidence_basis": evidence_basis,
        "observed_at": _iso(item.discovered_at),
        "last_verified_at": _explicit_timestamp(raw),
        "source_language": source_language,
        "source_language_basis": source_language_basis,
        "status": _status(item, raw),
        "deadline_confidence": deadline_confidence,
        "amount_confidence": amount_confidence,
        "missing_metadata": missing_metadata,
    }
