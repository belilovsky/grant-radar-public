"""Normalization helpers for mapping persistence rows into public opportunities."""

from __future__ import annotations

import re
from collections.abc import Iterable
from html import unescape
from typing import Any

from core.localization import normalize_content_lang
from core.models import OpportunityType
from core.nlp import clean_source_summary


def list_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        return [str(item) for item in value]
    return [str(value)]


def display_text(value: Any) -> str:
    return re.sub(r"\s+", " ", unescape(str(value or ""))).strip()


def display_summary(value: Any) -> str:
    return clean_source_summary(display_text(value))


def opportunity_type(raw: dict[str, Any]) -> OpportunityType:
    try:
        return OpportunityType(str(raw.get("type") or OpportunityType.GRANT))
    except ValueError:
        return OpportunityType.GRANT


def fallback_summary(raw: dict[str, Any], content_lang: str = "en") -> str:
    raw_payload = raw.get("raw")
    source_raw = raw_payload if isinstance(raw_payload, dict) else raw
    agency = (
        source_raw.get("agencyName")
        or source_raw.get("agency")
        or source_raw.get("agencyCode")
    )
    close_date = source_raw.get("closeDate") or source_raw.get("deadline")
    language_candidates = list_value(
        source_raw.get("language") or source_raw.get("languages")
    )
    normalized_lang = (
        normalize_content_lang(language_candidates[0])
        if language_candidates
        else normalize_content_lang(content_lang)
    )
    if not agency and not close_date:
        return ""
    parts = [
        "Opportunity notice" if normalized_lang == "en" else "Уведомление о возможности"
    ]
    if agency:
        parts.append(f"from {agency}" if normalized_lang == "en" else f"от {agency}")
    if close_date:
        parts.append(
            f"closing {close_date}"
            if normalized_lang == "en"
            else f"сроком до {close_date}"
        )
    return " ".join(parts) + "."


def public_raw(raw: dict[str, Any]) -> dict[str, Any]:
    nested_raw = raw.get("raw")
    if isinstance(nested_raw, dict) and "source_url" in raw and "discovered_at" in raw:
        return nested_raw
    if isinstance(nested_raw, dict) and {"type", "tags", "languages"}.issubset(raw):
        return nested_raw
    return raw
