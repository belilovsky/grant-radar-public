"""Typed, localised presentation boundary for public opportunity surfaces."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any

from api.dashboard_copy import dashboard_copy
from api.page_primitives import format_deadline
from core.models import Opportunity


class SourcePolicy(StrEnum):
    """How prominently a source-backed value may be presented."""

    OFFICIAL = "official"
    SECONDARY = "secondary"
    ARCHIVED_UNVERIFIED = "archived_unverified"


@dataclass(frozen=True, slots=True)
class OpportunityPresentation:
    """Shared display values used by HTML, embeds, and media projections."""

    title: str
    organisation: str
    source: str
    amount: str | None
    deadline: date | None
    language: str
    original_language: str | None
    source_policy: SourcePolicy


@dataclass(frozen=True, slots=True)
class ReleaseEvidence:
    """Immutable build and deploy identity exposed by the release contract."""

    source_sha: str
    source_dirty: bool
    image_digest: str | None
    artifact_digest: str | None
    built_at: str | None
    deployed_at: str | None


def release_evidence_from_env() -> ReleaseEvidence:
    """Read and validate one immutable release identity from the runtime env."""

    configured_sha = os.environ.get("APP_REVISION", "").strip().lower()
    source_sha = (
        configured_sha
        if re.fullmatch(r"[0-9a-f]{40}", configured_sha)
        else "development"
    )

    def digest(name: str) -> str | None:
        value = os.environ.get(name, "").strip().lower()
        return value if re.fullmatch(r"sha256:[0-9a-f]{64}", value) else None

    dirty_value = os.environ.get("APP_SOURCE_DIRTY", "").strip().lower()
    source_dirty = dirty_value not in {"0", "false", "no"}
    return ReleaseEvidence(
        source_sha=source_sha,
        source_dirty=source_dirty,
        image_digest=digest("APP_IMAGE_DIGEST"),
        artifact_digest=digest("APP_ARTIFACT_DIGEST"),
        built_at=os.environ.get("APP_BUILT_AT", "").strip() or None,
        deployed_at=os.environ.get("APP_DEPLOYED_AT", "").strip() or None,
    )


def opportunity_presentation(
    item: Opportunity,
    *,
    lang: str,
    amount: str | None = None,
) -> OpportunityPresentation:
    """Project one item into display-only values without duplicating business data."""

    raw = item.raw if isinstance(item.raw, dict) else {}
    original_language = str(raw.get("original_language") or "").strip() or None
    policy_value = str(raw.get("source_policy") or SourcePolicy.OFFICIAL.value)
    try:
        policy = SourcePolicy(policy_value)
    except ValueError:
        policy = SourcePolicy.SECONDARY
    source = localized_public_label(item.source, lang=lang)
    organisation = (
        localized_public_label(item.funder, lang=lang) if item.funder else source
    )
    return OpportunityPresentation(
        title=str(item.title),
        organisation=organisation,
        source=source,
        amount=amount,
        deadline=item.deadline,
        language=lang,
        original_language=original_language,
        source_policy=policy,
    )


def localized_public_label(value: Any, *, lang: str) -> str:
    """Turn machine labels into readable public text in the active language."""

    raw = str(value or "").strip()
    token = raw.lower().replace("-", "_").replace(" ", "_")
    labels = {
        "ru": {
            "central_asia": "Центральная Азия",
            "central_asia_eligible": "Доступно для Центральной Азии",
            "kazakhstan": "Казахстан",
            "global": "Международная программа",
            "rolling": "Бессрочный приём",
            "ai": "ИИ",
            "startup": "Стартап",
            "grant": "Грант",
            "accelerator": "Акселератор",
            "business_support": "Поддержка бизнеса",
            "sme": "МСБ",
        },
        "kk": {
            "central_asia": "Орталық Азия",
            "central_asia_eligible": "Орталық Азия үшін қолжетімді",
            "kazakhstan": "Қазақстан",
            "global": "Халықаралық бағдарлама",
            "rolling": "Мерзімсіз қабылдау",
            "ai": "ЖИ",
            "startup": "Стартап",
            "grant": "Грант",
            "accelerator": "Акселератор",
            "business": "Бизнес",
            "business_support": "Бизнесті қолдау",
            "sme": "ШОБ",
            "media": "Медиа",
            "forecast": "Анонс",
            "closed": "Жабық",
        },
        "en": {
            "central_asia": "Central Asia",
            "central_asia_eligible": "Eligible in Central Asia",
            "kazakhstan": "Kazakhstan",
            "global": "International programme",
            "rolling": "Rolling intake",
        },
    }
    language_labels = labels.get(lang, labels["ru"])
    if token in language_labels:
        return language_labels[token]
    label_map = dashboard_copy(lang).get("label_map")
    if isinstance(label_map, dict):
        mapped = label_map.get(token)
        if mapped:
            return str(mapped)
    if (
        "_" not in raw
        and "-" not in raw
        and any(character.isspace() for character in raw)
    ):
        return raw
    return " ".join(part for part in token.split("_") if part).capitalize()


def format_public_date(value: date | None, *, lang: str) -> str:
    """Format a known calendar date without leaking an ISO implementation value."""

    return format_deadline(value, lang, "") if value is not None else ""


def _amount_number(value: Any, *, lang: str) -> str:
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return str(value or "").strip()
    rendered = f"{decimal:,.2f}".rstrip("0").rstrip(".")
    separator = "\u202f" if lang in {"ru", "kk"} else ","
    return rendered.replace(",", separator)


def format_public_amount(
    minimum: Any,
    maximum: Any,
    currency: Any,
    *,
    lang: str,
) -> str:
    """Format structured monetary bounds consistently for public HTML surfaces."""

    lower = _amount_number(minimum, lang=lang) if minimum is not None else ""
    upper = _amount_number(maximum, lang=lang) if maximum is not None else ""
    unit = str(currency or "").strip().upper()
    if lower and upper and lower != upper:
        value = f"{lower} – {upper}"
    else:
        value = lower or upper
    return f"{value} {unit}".strip()
