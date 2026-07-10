"""Deterministic Russian summary fallbacks for public Grant Radar views."""

from __future__ import annotations

import re
from typing import Any

from core.models import Opportunity, OpportunityType
from core.nlp import clean_source_summary

_CYRILLIC_RE = re.compile(r"[А-Яа-яӘәҒғҚқҢңӨөҰұҮүҺһІіЁё]")
_LATIN_RE = re.compile(r"[A-Za-z]")

_REPLACEMENTS = (
    ("животноводство и животноводство", "животноводство"),
    (
        "строительство, ввод в эксплуатацию и эксплуатацию",
        "строительство, ввод в эксплуатацию",
    ),
    ("кухонного и кухонного оборудования", "кухонного оборудования"),
    (
        "услугами безопасности, хранения, бессерверными услугами",
        "сервисами безопасности, хранения и бессерверной разработки",
    ),
    ("услугами искусственного интеллекта Workers", "Workers AI"),
)

_STARTUP_PROGRAM_SUMMARIES = {
    "google_cloud_startup": (
        "Программа поддержки стартапов Google for Startups: облачные кредиты "
        "Google Cloud и Firebase, AI-инструменты, техническая поддержка и "
        "материалы для подходящих команд из Казахстана и Центральной Азии."
    ),
    "microsoft_founders_hub": (
        "Программа Microsoft for Startups для основателей: Azure-кредиты, "
        "AI-сервисы, инструменты разработки, наставничество и ресурсы для "
        "выхода на рынок."
    ),
    "aws_activate": (
        "Программа AWS Activate для стартапов: облачные кредиты, поддержка "
        "инфраструктуры и доступ к AI-сервисам AWS для подходящих команд."
    ),
    "nvidia_inception": (
        "Программа NVIDIA Inception для AI- и data-science-стартапов: "
        "технические ресурсы, инструменты разработчика, партнерская экосистема "
        "и поддержка подготовки к росту."
    ),
    "cloudflare_startups": (
        "Программа Cloudflare for Startups: кредиты и поддержка для команд, "
        "которые используют edge-инфраструктуру, безопасность, хранение, "
        "serverless и Workers AI."
    ),
    "mongodb_startups": (
        "Программа MongoDB for Startups: кредиты MongoDB Atlas, технические "
        "ресурсы и партнерская поддержка для стартапов, которым нужна база "
        "данных и инфраструктура роста."
    ),
}

_ASTANA_HUB_SUMMARIES = {
    "silkway": (
        "Silkway Accelerator от Astana Hub и Google for Startups помогает "
        "технологическим стартапам из Центральной Азии пройти акселерацию, "
        "проверить продукт, подготовиться к инвесторам и усилить выход на рынок."
    ),
    "regional it hub": (
        "Regional IT Hub от Astana Hub поддерживает IT-команды и стартапы в "
        "регионах Казахстана через локальные сообщества, акселерационные "
        "маршруты, партнерские программы и практическую поддержку роста."
    ),
}

_KAZAKHSTAN_WATCH_SUMMARIES = {
    "ебрр казахстан консультирование мсп": (
        "ЕБРР в Казахстане поддерживает стартапы и МСП через консультационные "
        "программы, доступ к финансированию и помощь в развитии управленческих "
        "процессов, продаж и устойчивости бизнеса."
    ),
}


def _raw(item: Opportunity) -> dict[str, Any]:
    return item.raw if isinstance(item.raw, dict) else {}


def _string(value: Any) -> str:
    return str(value or "").strip()


def _has_cyrillic(text: str) -> bool:
    return bool(_CYRILLIC_RE.search(text))


def _latin_heavy_ru(text: str) -> bool:
    if not text:
        return False
    latin = len(_LATIN_RE.findall(text))
    cyrillic = len(_CYRILLIC_RE.findall(text))
    return latin > 24 and latin > cyrillic


def _clean_ru_machine_text(text: str) -> str:
    cleaned = clean_source_summary(text)
    for before, after in _REPLACEMENTS:
        cleaned = cleaned.replace(before, after)
    return cleaned


def russian_title_fallback(title: str) -> str:
    """Clean obvious machine-translation artifacts in Russian titles."""

    return _clean_ru_machine_text(title)


def russian_opportunity_title_fallback(item: Opportunity, title: str) -> str:
    """Return a Russian title for source titles that are still English."""

    cleaned = russian_title_fallback(title)
    if cleaned and _has_cyrillic(cleaned) and not _latin_heavy_ru(cleaned):
        return cleaned

    source = item.source
    if source == "adb_kazakhstan":
        return "Проект Азиатского банка развития для Казахстана"
    if source == "world_bank_kazakhstan":
        return "Проект Всемирного банка для Казахстана"
    if source in {
        "undp_procurement",
        "isdb_project_procurement",
        "ebrd_ecepp_procurement",
    }:
        country = _country_label(" ".join([item.title, item.summary]))
        return (
            f"Закупка в {country}: {_procurement_focus(item)}"
            f"{_reference_suffix(item)}"
        )
    if source == "unicef_kazakhstan" or item.type == OpportunityType.TENDER:
        country = _country_label(" ".join([item.title, item.summary]))
        return (
            f"Закупочная возможность в {country}: {_procurement_focus(item)}"
            f"{_reference_suffix(item)}"
        )
    return cleaned


def _country_label(text: str) -> str:
    lowered = text.lower()
    if "kyrgyz" in lowered or "кыргыз" in lowered or "киргиз" in lowered:
        return "Кыргызстане"
    if "uzbek" in lowered or "узбе" in lowered:
        return "Узбекистане"
    if "tajik" in lowered or "таджик" in lowered:
        return "Таджикистане"
    return "Казахстане"


def _readable_title(title: str) -> str:
    cleaned = _clean_ru_machine_text(title)
    if cleaned and _has_cyrillic(cleaned) and not _latin_heavy_ru(cleaned):
        return cleaned
    return ""


def _reference_suffix(item: Opportunity) -> str:
    raw = _raw(item)
    reference = _string(raw.get("reference") or raw.get("external_id"))
    if (
        reference
        and len(reference) <= 48
        and re.fullmatch(r"[A-Za-zА-Яа-я0-9][A-Za-zА-Яа-я0-9._/-]*", reference)
        and reference.casefold() not in item.title.casefold()
    ):
        return f" — {reference}"
    compact_id = str(item.id).split("-", maxsplit=1)[0].upper()
    return f" — № {compact_id}" if compact_id else ""


def _procurement_focus(item: Opportunity) -> str:
    text = " ".join([item.title, item.summary, " ".join(item.tags)]).lower()
    if any(term in text for term in ("consultant", "consulting", "консульт")):
        return "консультационные услуги"
    if any(term in text for term in ("laboratory", "equipment", "оборудован")):
        return "поставка оборудования"
    if any(
        term in text
        for term in ("water", "irrigation", "groundwater", "climate", "green")
    ):
        return "экологические, водные или климатические задачи"
    if any(
        term in text
        for term in ("construction", "reconstruction", "road", "dam", "строитель")
    ):
        return "строительные или инфраструктурные работы"
    if any(
        term in text
        for term in (
            "digital",
            "platform",
            "system",
            "information",
            "цифров",
            "информацион",
        )
    ):
        return "цифровые системы и аналитическая поддержка"
    return "проектные услуги, поставка или консультационная поддержка"


def _procurement_summary(item: Opportunity) -> str:
    raw = _raw(item)
    reference = _string(raw.get("reference") or raw.get("external_id"))
    office = _string(raw.get("office"))
    country = _country_label(" ".join([item.title, office, reference]))
    title = _readable_title(item.title)
    subject = f": {title}" if title else f" по направлению «{_procurement_focus(item)}»"
    detail_hint = (
        " Проверьте техническое задание, требования к участникам и срок подачи "
        "на странице источника."
    )
    if item.source == "undp_procurement":
        suffix = f" Номер закупки: {reference}." if reference else ""
        return f"Закупка ПРООН в {country}{subject}.{suffix}{detail_hint}"
    if item.source == "isdb_project_procurement":
        suffix = f" Формат: {raw.get('notice_type')}." if raw.get("notice_type") else ""
        return (
            f"Закупка или консультационный конкурс IsDB в {country}"
            f"{subject}.{suffix}{detail_hint}"
        )
    if item.source == "ebrd_ecepp_procurement":
        suffix = f" Формат: {raw.get('notice_type')}." if raw.get("notice_type") else ""
        return f"Открытая закупка ЕБРР ECEPP в {country}{subject}.{suffix}{detail_hint}"
    return f"Закупочная возможность в {country}{subject}.{detail_hint}"


def _project_summary(item: Opportunity) -> str:
    title = _string(item.title)
    if item.source == "adb_kazakhstan":
        prefix = "Проект Азиатского банка развития для Казахстана"
        subject = "" if title.casefold() == prefix.casefold() else f": {title}"
        return (
            f"{prefix}{subject}. Карточка полезна для отслеживания проектного "
            "финансирования, инфраструктуры, зеленого перехода и связанных "
            "закупок."
        )
    if item.source == "world_bank_kazakhstan":
        prefix = "Проект Всемирного банка для Казахстана"
        subject = "" if title.casefold() == prefix.casefold() else f": {title}"
        return (
            f"{prefix}{subject}. Карточка показывает направление поддержки, заемщика, "
            "финансирование и сроки проектного цикла."
        )
    return f"Проектная возможность для Казахстана: {title}."


def _eeas_summary(item: Opportunity) -> str:
    raw = _raw(item)
    reference = _string(raw.get("reference") or raw.get("external_id"))
    suffix = f" Код конкурса: {reference}." if reference else ""
    return (
        "Конкурс предложений ЕС для Казахстана: поддержка гражданского "
        "общества, прав человека или смежных программных направлений. "
        "Проверьте условия, бюджет и дедлайн на странице источника."
        f"{suffix}"
    )


def _needs_fallback(text: str) -> bool:
    cleaned = clean_source_summary(text)
    if not cleaned:
        return True
    if _latin_heavy_ru(cleaned):
        return True
    return False


def russian_summary_fallback(item: Opportunity, summary: str) -> str:
    """Return a Russian public summary when source text is missing or English."""

    cleaned = _clean_ru_machine_text(summary)
    source = item.source
    title_lower = item.title.lower()

    if source in {
        "undp_procurement",
        "isdb_project_procurement",
        "ebrd_ecepp_procurement",
    } and (len(cleaned) < 120 or "Номер ссылки:" in cleaned):
        return _procurement_summary(item)

    if source == "kazakhstan_watch" and len(cleaned) < 100:
        for key, value in _KAZAKHSTAN_WATCH_SUMMARIES.items():
            if key in title_lower:
                return value

    if cleaned and _has_cyrillic(cleaned) and not _latin_heavy_ru(cleaned):
        return cleaned

    if source in _STARTUP_PROGRAM_SUMMARIES:
        return _STARTUP_PROGRAM_SUMMARIES[source]

    if source == "astana_hub":
        for key, value in _ASTANA_HUB_SUMMARIES.items():
            if key in title_lower:
                return value

    if source == "kazakhstan_watch":
        for key, value in _KAZAKHSTAN_WATCH_SUMMARIES.items():
            if key in title_lower:
                return value

    if source in {"adb_kazakhstan", "world_bank_kazakhstan"}:
        return _project_summary(item)

    if source in {
        "undp_procurement",
        "isdb_project_procurement",
        "ebrd_ecepp_procurement",
    }:
        return _procurement_summary(item)

    if source == "eeas_kazakhstan":
        return _eeas_summary(item)

    if item.type == OpportunityType.TENDER:
        return _procurement_summary(item)

    if _needs_fallback(cleaned):
        return (
            "Возможность поддержки для команд и организаций, связанных с "
            "Казахстаном или Центральной Азией. Проверьте требования, сроки и "
            "порядок подачи на странице источника."
        )
    return cleaned
