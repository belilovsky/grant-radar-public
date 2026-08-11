"""Public, source-grounded comparison read model.

The comparison surface deliberately keeps missing values explicit. It is a
small API primitive for a future visual compare view, not an eligibility
verdict or a synthetic recommendation.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Iterable
from uuid import UUID

from qazstack.opportunities import public_lifecycle

from core.models import Opportunity
from sources import PARSERS

COMPARISON_SCHEMA_VERSION = "comparison.v1"
MAX_COMPARISON_ITEMS = 4

_FIELD_LABELS: dict[str, dict[str, str]] = {
    "funder": {"ru": "Организатор", "kk": "Ұйымдастырушы", "en": "Organizer"},
    "source": {"ru": "Источник", "kk": "Дереккөз", "en": "Source"},
    "type": {"ru": "Формат", "kk": "Формат", "en": "Format"},
    "lifecycle": {"ru": "Статус", "kk": "Мәртебе", "en": "Status"},
    "deadline": {"ru": "Срок", "kk": "Мерзім", "en": "Deadline"},
    "amount": {"ru": "Сумма", "kk": "Сома", "en": "Amount"},
    "eligibility": {"ru": "Для кого", "kk": "Кім үшін", "en": "Eligibility"},
    "tags": {"ru": "Темы", "kk": "Тақырыптар", "en": "Topics"},
    "source_url": {
        "ru": "Официальный источник",
        "kk": "Ресми дереккөз",
        "en": "Official source",
    },
}

_COPY: dict[str, dict[str, str]] = {
    "ru": {
        "title": "Сравнение программ – QAZ.FUND",
        "heading": "Сравнить программы",
        "table_heading": "Сводная таблица",
        "intro": (
            "Сопоставьте условия по опубликованным данным и проверьте каждую "
            "карточку у организатора."
        ),
        "unknown": "Не указано",
        "not_enough": "Выберите как минимум две карточки для сравнения.",
        "too_many": "В одном сравнении можно сопоставить не более четырёх карточек.",
        "missing": "Карточка не найдена в текущем каталоге.",
        "warning": "Пустое значение означает, что поле не опубликовано в текущей карточке.",
        "back": "Вернуться в каталог",
        "cards": "Карточки",
        "status": "Статус",
        "footer": "QAZ.FUND не выдаёт средства и не принимает заявки.",
        "source_link": "Открыть источник",
        "scroll_hint": "Прокрутите таблицу по горизонтали, чтобы увидеть все карточки.",
    },
    "kk": {
        "title": "Бағдарламаларды салыстыру – QAZ.FUND",
        "heading": "Бағдарламаларды салыстыру",
        "table_heading": "Салыстыру кестесі",
        "intro": (
            "Жарияланған деректер бойынша шарттарды салыстырып, әр карточканы "
            "ұйымдастырушыдан тексеріңіз."
        ),
        "unknown": "Көрсетілмеген",
        "not_enough": "Салыстыру үшін кемінде екі карточканы таңдаңыз.",
        "too_many": "Бір салыстыруда төрт карточкадан артық болмауы керек.",
        "missing": "Карточка ағымдағы каталогтан табылмады.",
        "warning": "Бос мән бұл өрістің ағымдағы карточкада жарияланбағанын білдіреді.",
        "back": "Каталогқа оралу",
        "cards": "Карточкалар",
        "status": "Мәртебе",
        "footer": "QAZ.FUND қаражат бөлмейді және өтінім қабылдамайды.",
        "source_link": "Дереккөзді ашу",
        "scroll_hint": "Кестені көлденең жылжытып, барлық карточканы көріңіз.",
    },
    "en": {
        "title": "Compare programs – QAZ.FUND",
        "heading": "Compare programs",
        "table_heading": "Comparison table",
        "intro": "Compare published fields and verify every card with the organizer.",
        "unknown": "Not published",
        "not_enough": "Choose at least two cards to compare.",
        "too_many": "A comparison can contain no more than four cards.",
        "missing": "The card is not present in the current catalog.",
        "warning": "An empty value means that the field is not published in the current card.",
        "back": "Back to catalog",
        "cards": "Cards",
        "status": "Status",
        "footer": "QAZ.FUND does not award funds or process applications.",
        "source_link": "Open source",
        "scroll_hint": "Scroll the table horizontally to view every card.",
    },
}


def parse_comparison_ids(raw: str | None) -> list[str]:
    """Parse a comma-separated, de-duplicated list of opportunity UUIDs."""

    if not raw:
        return []
    result: list[str] = []
    seen: set[str] = set()
    for token in raw.split(","):
        value = token.strip()
        if not value:
            continue
        try:
            normalized = str(UUID(value))
        except ValueError as exc:
            raise ValueError(f"invalid opportunity id: {value}") from exc
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def _text(value: Any) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def _source_label(item: Opportunity) -> str:
    source_cls = PARSERS.get(item.source)
    if source_cls is not None:
        return str(source_cls.name)
    return str(item.source).replace("_", " ").strip().title() or "Source"


def _amount(item: Opportunity, unknown: str) -> dict[str, Any]:
    minimum = item.amount_min
    maximum = item.amount_max
    if minimum is None and maximum is None:
        return {"min": None, "max": None, "currency": None, "display": unknown}
    currency = _text(item.currency) or unknown
    display = f"{minimum or maximum}–{maximum or minimum} {currency}"
    if minimum == maximum or minimum is None or maximum is None:
        display = f"{minimum or maximum} {currency}"
    return {
        "min": str(minimum) if minimum is not None else None,
        "max": str(maximum) if maximum is not None else None,
        "currency": currency,
        "display": display,
    }


def _field_value(item: Opportunity, field: str, *, unknown: str) -> Any:
    if field == "funder":
        return _text(item.funder) or unknown
    if field == "source":
        return _text(item.source) or unknown
    if field == "type":
        return item.type.value
    if field == "lifecycle":
        return public_lifecycle(item)
    if field == "deadline":
        return item.deadline.isoformat() if item.deadline else unknown
    if field == "amount":
        return _amount(item, unknown)
    if field == "eligibility":
        return list(item.eligibility) or [unknown]
    if field == "tags":
        return list(item.tags) or [unknown]
    if field == "source_url":
        return str(item.source_url)
    raise KeyError(field)


def _field_present(item: Opportunity, field: str) -> bool:
    if field == "funder":
        return bool(_text(item.funder))
    if field == "source":
        return bool(_text(item.source))
    if field == "type":
        return bool(item.type)
    if field == "lifecycle":
        return bool(public_lifecycle(item))
    if field == "deadline":
        return item.deadline is not None
    if field == "amount":
        return item.amount_min is not None or item.amount_max is not None
    if field == "eligibility":
        return bool(item.eligibility)
    if field == "tags":
        return bool(item.tags)
    if field == "source_url":
        return bool(str(item.source_url).strip())
    return False


def build_comparison_snapshot(
    items: Iterable[Opportunity],
    requested_ids: list[str],
    *,
    lang: str = "ru",
    as_of: date | None = None,
    links: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a deterministic comparison payload with explicit unknowns."""

    active_lang = lang if lang in _COPY else "ru"
    copy = _COPY[active_lang]
    by_id = {str(item.id): item for item in items}
    selected = [by_id[item_id] for item_id in requested_ids if item_id in by_id]
    missing = [item_id for item_id in requested_ids if item_id not in by_id]
    fields = tuple(_FIELD_LABELS)
    field_coverage: dict[str, dict[str, Any]] = {}
    for field in fields:
        present = sum(1 for item in selected if _field_present(item, field))
        total = len(selected)
        field_coverage[field] = {
            "label": _FIELD_LABELS[field][active_lang],
            "present": present,
            "total": total,
            "ratio": round(present / total, 4) if total else 0.0,
        }

    cards: list[dict[str, Any]] = []
    for item in selected:
        cards.append(
            {
                "id": str(item.id),
                "title": item.title,
                "summary": item.summary,
                "source_label": _source_label(item),
                "fields": {
                    field: _field_value(item, field, unknown=copy["unknown"])
                    for field in fields
                },
                "unknown_fields": [
                    field for field in fields if not _field_present(item, field)
                ],
            }
        )

    status = "ready" if len(selected) >= 2 else "insufficient"
    if missing and selected:
        status = "partial"
    warnings = [copy["warning"]]
    if missing:
        warnings.append(f"{copy['missing']} ({len(missing)})")
    if len(selected) < 2:
        warnings.insert(0, copy["not_enough"])
    return {
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "as_of": (as_of or date.today()).isoformat(),
        "status": status,
        "selection": {
            "requested_ids": requested_ids,
            "found_ids": [str(item.id) for item in selected],
            "missing_ids": missing,
            "max_items": MAX_COMPARISON_ITEMS,
        },
        "field_coverage": field_coverage,
        "cards": cards,
        "warnings": warnings,
        "links": links or {},
    }


def comparison_copy(lang: str) -> dict[str, str]:
    """Return the small public copy set for a future server-rendered view."""

    return dict(_COPY.get(lang, _COPY["ru"]))


def comparison_field_labels(lang: str) -> dict[str, str]:
    """Return localized labels without exposing the internal label table."""

    active_lang = lang if lang in _COPY else "ru"
    return {field: values[active_lang] for field, values in _FIELD_LABELS.items()}
