"""Public opportunity history read model."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from core.history import HISTORY_FIELDS, HISTORY_SCHEMA_VERSION
from core.models import Opportunity

_REASONS = {
    "ru": {
        "backend": "История изменений пока недоступна для этого режима хранения.",
        "empty": "Для карточки ещё не зафиксировано изменение публичных полей.",
    },
    "kk": {
        "backend": "Бұл сақтау режимінде өзгерістер тарихы әзірге қолжетімсіз.",
        "empty": "Карточканың жария өрістеріндегі өзгеріс әлі тіркелмеген.",
    },
    "en": {
        "backend": "Change history is not available for this storage mode yet.",
        "empty": "No change to the public fields has been recorded for this card yet.",
    },
}


def _iso(value: Any) -> str | None:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    text = str(value or "").strip()
    return text or None


def build_history_snapshot(
    *,
    item: Opportunity,
    entries: list[dict[str, Any]],
    lang: str,
    links: dict[str, str],
    backend_available: bool,
) -> dict[str, Any]:
    """Build the versioned public history payload.

    History is deliberately descriptive.  It does not decide whether a change
    makes a programme eligible or advisable.
    """

    normalized_lang = lang if lang in _REASONS else "en"
    if not backend_available:
        state = "not_available"
        reason = _REASONS[normalized_lang]["backend"]
    elif not entries:
        state = "not_available"
        reason = _REASONS[normalized_lang]["empty"]
    else:
        state = "ready"
        reason = None

    latest_fields = entries[-1].get("fields") if entries else {}
    if not isinstance(latest_fields, dict):
        latest_fields = {}
    field_coverage = {
        field: bool(latest_fields.get(field) not in (None, "", []))
        for field in HISTORY_FIELDS
    }
    payload: dict[str, Any] = {
        "schema_version": HISTORY_SCHEMA_VERSION,
        "status": state,
        "language": normalized_lang,
        "history_scope": "public-normalized-fields",
        "opportunity_id": str(item.id),
        "source": str(item.source),
        "source_url": str(item.source_url),
        "as_of": _iso(item.discovered_at),
        "current_version": entries[-1].get("version") if entries else None,
        "version_count": len(entries),
        "field_coverage": field_coverage,
        "items": entries,
        "links": links,
    }
    if reason:
        payload["reason"] = reason
    return payload


__all__ = ["build_history_snapshot"]
