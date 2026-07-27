"""Derived public analytics for the QAZ.FUND data centre."""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from typing import Any, Iterable

from core.public_contract import OpportunityV1, dataset_revision

ACTIVE_STATUSES = frozenset(
    {
        "open",
        "closing_soon",
        "rolling",
        "forecast",
        "upcoming",
    }
)

FORMAT_LABELS = {
    "ru": {
        "grant": "Гранты",
        "subsidy": "Субсидии",
        "procurement": "Закупки и конкурсы",
        "preferential_finance": "Льготное финансирование",
        "loan_guarantee": "Гарантии",
        "reimbursement": "Возмещение затрат",
        "tax_benefit": "Налоговые льготы",
        "accelerator": "Акселераторы",
        "cloud_credit": "Облачные программы",
        "contest": "Конкурсы",
        "fellowship": "Стипендии",
        "unknown": "Не определено",
    },
    "en": {
        "grant": "Grants",
        "subsidy": "Subsidies",
        "procurement": "Procurement and calls",
        "preferential_finance": "Preferential finance",
        "loan_guarantee": "Guarantees",
        "reimbursement": "Cost reimbursement",
        "tax_benefit": "Tax incentives",
        "accelerator": "Accelerators",
        "cloud_credit": "Cloud programmes",
        "contest": "Competitions",
        "fellowship": "Fellowships",
        "unknown": "Not classified",
    },
}

AUDIENCE_LABELS = {
    "ru": {
        "startups": "Стартапы",
        "business": "Бизнес",
        "farmers": "Фермеры",
        "nonprofits": "НКО",
        "researchers": "Исследователи",
        "public_sector": "Госсектор",
        "media": "СМИ",
        "unknown": "Аудитория не указана",
    },
    "en": {
        "startups": "Startups",
        "business": "Businesses",
        "farmers": "Farmers",
        "nonprofits": "Nonprofits",
        "researchers": "Researchers",
        "public_sector": "Public sector",
        "media": "Media",
        "unknown": "Audience not specified",
    },
}

THEME_LABELS = {
    "ru": {
        "ai": "ИИ",
        "education": "Образование",
        "science": "Наука",
        "digital": "Цифровые решения",
        "agriculture": "Сельское хозяйство",
        "climate": "Климат и экология",
        "media": "СМИ",
        "civil_society": "Гражданское общество",
        "health": "Здравоохранение",
        "infrastructure": "Инфраструктура",
    },
    "en": {
        "ai": "AI",
        "education": "Education",
        "science": "Science",
        "digital": "Digital",
        "agriculture": "Agriculture",
        "climate": "Climate and environment",
        "media": "Media",
        "civil_society": "Civil society",
        "health": "Health",
        "infrastructure": "Infrastructure",
    },
}


def _normalized(value: object) -> str:
    return " ".join(str(value or "").replace("_", " ").split()).strip()


def _status(item: OpportunityV1) -> str:
    return _normalized(item.status).lower().replace(" ", "_") or "unknown"


def _is_active(item: OpportunityV1) -> bool:
    return _status(item) in ACTIVE_STATUSES


def _is_current(item: OpportunityV1, *, today: date) -> bool:
    if not _is_active(item):
        return False
    return item.deadline is None or item.deadline >= today


def _is_amount_known(item: OpportunityV1) -> bool:
    amount = item.funding_amount
    return bool(
        amount.minimum is not None
        or amount.maximum is not None
        or str(amount.display or "").strip()
    )


def _is_eligibility_known(item: OpportunityV1) -> bool:
    return bool(item.eligibility or str(item.eligibility_summary or "").strip())


def _is_deadline_known(item: OpportunityV1) -> bool:
    return item.deadline is not None or item.deadline_type == "rolling"


def _is_application_known(item: OpportunityV1) -> bool:
    return bool(item.links.application)


def _share(count: int, total: int) -> float:
    return round((count / total) * 100, 1) if total else 0.0


def _rows(
    counter: Counter[str],
    *,
    labels: dict[str, str] | None = None,
    total: int,
    limit: int = 10,
) -> list[dict[str, int | float | str]]:
    return [
        {
            "key": key,
            "label": (labels or {}).get(key, _normalized(key).capitalize()),
            "count": count,
            "share": _share(count, total),
        }
        for key, count in counter.most_common(limit)
    ]


def _theme_key(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "artificial_intelligence": "ai",
        "edtech": "education",
        "higher_education": "education",
        "research": "science",
        "technology": "digital",
        "digital_transformation": "digital",
        "govtech": "digital",
        "agrotech": "agriculture",
        "environment": "climate",
        "ecotech": "climate",
        "journalism": "media",
        "ngo": "civil_society",
    }
    return aliases.get(normalized, normalized)


def _deadline_windows(
    items: Iterable[OpportunityV1],
    *,
    today: date,
    lang: str,
) -> list[dict[str, int | float | str]]:
    labels = (
        [
            ("0_30", "До 30 дней"),
            ("31_60", "31–60 дней"),
            ("61_90", "61–90 дней"),
            ("later", "Позже"),
            ("rolling", "Без фиксированного срока"),
            ("unknown", "Срок не указан"),
        ]
        if lang == "ru"
        else [
            ("0_30", "Within 30 days"),
            ("31_60", "31–60 days"),
            ("61_90", "61–90 days"),
            ("later", "Later"),
            ("rolling", "Rolling"),
            ("unknown", "No deadline"),
        ]
    )
    counts: Counter[str] = Counter()
    for item in items:
        if item.deadline_type == "rolling":
            counts["rolling"] += 1
            continue
        if item.deadline is None:
            counts["unknown"] += 1
            continue
        days = (item.deadline - today).days
        if days <= 30:
            counts["0_30"] += 1
        elif days <= 60:
            counts["31_60"] += 1
        elif days <= 90:
            counts["61_90"] += 1
        else:
            counts["later"] += 1
    total = sum(counts.values())
    return [
        {
            "key": key,
            "label": label,
            "count": counts[key],
            "share": _share(counts[key], total),
        }
        for key, label in labels
        if counts[key]
    ]


def build_insights_payload(
    items: list[OpportunityV1],
    *,
    lang: str = "ru",
    today: date | None = None,
    history: dict[str, Any] | None = None,
    catalog_items: list[OpportunityV1] | None = None,
) -> dict[str, Any]:
    """Build deterministic current-state analytics without inventing missing facts."""

    active_lang = "en" if lang == "en" else "ru"
    current_day = today or date.today()
    candidate_catalog = items if catalog_items is None else catalog_items
    active = [
        item for item in candidate_catalog if _is_current(item, today=current_day)
    ]
    archival = [item for item in items if not _is_current(item, today=current_day)]
    outside_current_catalog = max(0, len(items) - len(active))
    review_queue = max(0, outside_current_catalog - len(archival))
    sources = Counter(item.source.name for item in active)
    indexed_sources = {item.source.name for item in items}
    formats: Counter[str] = Counter(
        (item.formats[0] if item.formats else "unknown") for item in active
    )
    audiences: Counter[str] = Counter()
    for item in active:
        values = item.target_audience or ["unknown"]
        audiences.update(values)
    themes: Counter[str] = Counter()
    for item in active:
        themes.update(_theme_key(value) for value in item.themes if value)

    closing_30 = sum(
        1
        for item in active
        if item.deadline is not None
        and current_day <= item.deadline <= current_day + timedelta(days=30)
    )
    complete_deadline = sum(_is_deadline_known(item) for item in active)
    complete_amount = sum(_is_amount_known(item) for item in active)
    complete_eligibility = sum(_is_eligibility_known(item) for item in active)
    complete_application = sum(_is_application_known(item) for item in active)
    complete_core = sum(
        _is_deadline_known(item)
        and _is_amount_known(item)
        and _is_eligibility_known(item)
        and _is_application_known(item)
        for item in active
    )
    procurement_count = sum(1 for item in active if "procurement" in set(item.formats))
    kazakhstan_count = sum(1 for item in active if "kazakhstan" in set(item.regions))
    sourced_count = sum(
        1 for item in active if item.provenance.evidence_state == "sourced"
    )
    verified_count = sum(
        1 for item in active if item.provenance.evidence_state == "verified"
    )

    completeness = [
        {
            "key": "deadline",
            "label": "Срок" if active_lang == "ru" else "Deadline",
            "count": complete_deadline,
            "share": _share(complete_deadline, len(active)),
        },
        {
            "key": "eligibility",
            "label": "Требования" if active_lang == "ru" else "Eligibility",
            "count": complete_eligibility,
            "share": _share(complete_eligibility, len(active)),
        },
        {
            "key": "amount",
            "label": "Сумма" if active_lang == "ru" else "Funding amount",
            "count": complete_amount,
            "share": _share(complete_amount, len(active)),
        },
        {
            "key": "application",
            "label": "Прямая подача" if active_lang == "ru" else "Application route",
            "count": complete_application,
            "share": _share(complete_application, len(active)),
        },
    ]

    return {
        "schema_version": "qazfund-insights.v1",
        "as_of": current_day.isoformat(),
        "language": active_lang,
        "dataset_revision": dataset_revision(items),
        "scope": {
            "indexed_relevant": len(items),
            "current_catalog": len(active),
            "active": len(active),
            "outside_current_catalog": outside_current_catalog,
            "closed_or_archival": len(archival),
            "review_queue": review_queue,
            "sources": len(sources),
            "indexed_sources": len(indexed_sources),
            "closing_within_30_days": closing_30,
            "kazakhstan_explicit": kazakhstan_count,
        },
        "quality": {
            "completeness": completeness,
            "complete_core_fields": complete_core,
            "complete_core_share": _share(complete_core, len(active)),
            "evidence": {
                "sourced": sourced_count,
                "verified": verified_count,
                "other": max(0, len(active) - sourced_count - verified_count),
            },
            "definitions": {
                "sourced": (
                    "Карточка связана с первоисточником, но не подтверждена "
                    "независимой проверкой."
                    if active_lang == "ru"
                    else (
                        "The record is linked to its primary source but has not "
                        "been independently verified."
                    )
                ),
                "complete_core_fields": (
                    "Одновременно известны срок, сумма, требования и путь подачи."
                    if active_lang == "ru"
                    else (
                        "Deadline, amount, eligibility and application route are "
                        "all known."
                    )
                ),
            },
        },
        "distribution": {
            "formats": _rows(
                formats,
                labels=FORMAT_LABELS[active_lang],
                total=len(active),
                limit=12,
            ),
            "audiences": _rows(
                audiences,
                labels=AUDIENCE_LABELS[active_lang],
                total=sum(audiences.values()),
                limit=10,
            ),
            "themes": _rows(
                themes,
                labels=THEME_LABELS[active_lang],
                total=sum(themes.values()),
                limit=10,
            ),
            "sources": _rows(sources, total=len(active), limit=12),
            "deadlines": _deadline_windows(
                active,
                today=current_day,
                lang=active_lang,
            ),
        },
        "signals": {
            "procurement_count": procurement_count,
            "procurement_share": _share(procurement_count, len(active)),
            "largest_source": (
                {
                    "name": sources.most_common(1)[0][0],
                    "count": sources.most_common(1)[0][1],
                    "share": _share(sources.most_common(1)[0][1], len(active)),
                }
                if sources
                else None
            ),
            "closing_within_30_days": closing_30,
        },
        "history": history
        or {
            "available": False,
            "state": "collecting",
            "period_hours": 24,
            "created": 0,
            "changed": 0,
            "items": [],
        },
    }


__all__ = ["ACTIVE_STATUSES", "build_insights_payload"]
