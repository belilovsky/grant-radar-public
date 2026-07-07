"""Lightweight text-quality and entity helpers for Grant Radar.

The production enrichment path can use an LLM, but these deterministic helpers
keep audits and tests useful even when provider credentials are unavailable.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

_CYRILLIC_RE = re.compile(r"[А-Яа-яӘәҒғҚқҢңӨөҰұҮүҺһІіЁё]")
_LATIN_RE = re.compile(r"[A-Za-z]")
_WORD_RE = re.compile(r"[A-Za-zА-Яа-яӘәҒғҚқҢңӨөҰұҮүҺһІіЁё0-9]+")
_REPEATED_BRIDGE_RE = re.compile(
    r"\b(?P<phrase>[А-Яа-яӘәҒғҚқҢңӨөҰұҮүҺһІіЁёA-Za-z][\w\-]{3,})\s+"
    r"(?:и|или|and|or)\s+(?P=phrase)\b",
    re.IGNORECASE,
)

_SUPPORT_TYPE_PATTERNS = {
    "grant": (
        "grant",
        "грант",
        "конкурс заявок",
        "call for proposals",
        "call for applications",
    ),
    "subsidy": ("subsid", "субсид", "возмещение", "reimbursement"),
    "preferential_financing": (
        "льготн",
        "preferential",
        "кредит",
        "credit",
        "credits",
        "loan",
        "заем",
        "заём",
        "leasing",
        "лизинг",
    ),
    "project_finance": (
        "project pipeline",
        "project will",
        "проект",
        "проектное финанс",
        "finance",
        "financing",
        "infrastructure",
        "инфраструктур",
    ),
    "accelerator": ("accelerator", "акселератор", "mentoring", "ментор"),
    "startup_support": ("startup support", "support program", "программа", "поддержк"),
    "training": ("training", "education", "обучени", "образован", "курс"),
    "award": ("award", "prize", "преми", "награда"),
    "tender": (
        "tender",
        "procurement",
        "expression of interest",
        "consulting services",
        "закуп",
        "тендер",
        "консультант",
        "rfp",
    ),
    "tax_benefit": ("tax", "налог", "льгот"),
    "investment": ("investment", "инвест", "venture", "венчур"),
}

_SECTOR_PATTERNS = {
    "ai": ("artificial intelligence", "ai", "ии", "искусственн"),
    "agrotech": ("agro", "agri", "агро", "сельхоз", "фермер", "животновод"),
    "vettech": ("veterinary", "ветеринар", "животновод", "animal"),
    "ecotech": ("eco", "green", "climate", "эколог", "климат", "устойчив"),
    "education": ("education", "school", "university", "образован", "университет"),
    "sme": ("sme", "small business", "мсп", "малый бизнес", "предпринимател"),
    "civil_society": ("civil society", "ngo", "нпо", "гражданск"),
    "startup": ("startup", "стартап", "founder", "основател"),
    "digitalization": ("digital", "цифров", "technology", "технолог"),
}

_REGION_PATTERNS = {
    "kazakhstan": ("kazakhstan", "казахстан", "қазақстан"),
    "central_asia": ("central asia", "центральн", "central asian"),
    "uzbekistan": ("uzbekistan", "узбекистан", "uzb"),
    "tajikistan": ("tajikistan", "таджикистан", "tjk"),
    "kyrgyzstan": ("kyrgyzstan", "kyrgyz republic", "кыргыз", "киргиз"),
    "global": ("global", "worldwide", "глобальн", "международ"),
}

_AUDIENCE_PATTERNS = {
    "business": ("business", "entrepreneur", "предпринимател", "бизнес", "мсп"),
    "ngo": ("ngo", "civil society", "нпо", "обществен"),
    "research": ("research", "university", "science", "исслед", "наук", "университет"),
    "startup": ("startup", "founder", "стартап"),
    "government": ("government", "ministry", "государств", "министерств"),
    "farmers": ("farmer", "agricultural producer", "аграр", "фермер", "сельхоз"),
}

_FUNDER_HINTS = (
    "Astana Hub",
    "QazInnovations",
    "Damu",
    "QIC",
    "QazTrade",
    "KazakhExport",
    "KazAgroFinance",
    "Аграрная кредитная корпорация",
    "UNDP",
    "UNICEF",
    "UNESCO",
    "World Bank",
    "ADB",
    "EBRD",
    "EEAS",
    "Erasmus",
    "Google",
)


def _tokens(values: Iterable[Any]) -> str:
    return " ".join(str(value or "") for value in values).lower()


def _matches_any(text: str, patterns: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(pattern.lower() in lowered for pattern in patterns)


def _strip_title_prefix(text: str, title: str) -> str:
    title_tokens = " ".join(str(title or "").split()).strip(" -:;,.")
    if not title_tokens:
        return text
    candidates = [title_tokens]
    if ":" in title_tokens:
        leading_clause = title_tokens.split(":", 1)[0].strip(" -:;,.")
        if len(leading_clause) >= 12:
            candidates.append(leading_clause)
    patterns = []
    for candidate in sorted(set(candidates), key=len, reverse=True):
        prefix = r"\s+".join(re.escape(token) for token in candidate.split())
        patterns.append(re.compile(rf"^\s*{prefix}\s*[:\-–—.]?\s*", re.IGNORECASE))
    cleaned = text
    for _ in range(3):
        match = next(
            (pattern.match(cleaned) for pattern in patterns if pattern.match(cleaned)),
            None,
        )
        if match is None:
            break
        remainder = cleaned[match.end() :].lstrip(" -:;,.")
        if len(remainder) < 20:
            break
        cleaned = remainder
    return cleaned


def clean_source_summary(text: str, *, title: str = "") -> str:
    """Remove source UI fragments that should not leak into public summaries."""

    normalized = re.sub(r"\s+", " ", str(text or "")).strip()
    if not normalized:
        return ""
    cleaned = re.split(r"\b(?:Читать далее|Read more)\b", normalized, maxsplit=1)[
        0
    ].strip(" -:;,")
    return _strip_title_prefix(cleaned, title).strip(" -:;,")


def extract_rule_based_entities(
    *,
    title: str,
    summary: str,
    tags: Iterable[str] = (),
    detail_text: str = "",
) -> dict[str, list[str]]:
    """Extract coarse entities used by product filters and QA.

    This intentionally stays conservative: it records obvious classes only and
    leaves nuanced extraction to the DeepSeek enrichment script.
    """

    text = _tokens([title, summary, detail_text, *tags])
    entities = {
        "support_types": sorted(
            key
            for key, patterns in _SUPPORT_TYPE_PATTERNS.items()
            if _matches_any(text, patterns)
        ),
        "sectors": sorted(
            key
            for key, patterns in _SECTOR_PATTERNS.items()
            if _matches_any(text, patterns)
        ),
        "regions": sorted(
            key
            for key, patterns in _REGION_PATTERNS.items()
            if _matches_any(text, patterns)
        ),
        "audiences": sorted(
            key
            for key, patterns in _AUDIENCE_PATTERNS.items()
            if _matches_any(text, patterns)
        ),
        "funders": sorted(hint for hint in _FUNDER_HINTS if hint.lower() in text),
    }
    return {key: values for key, values in entities.items() if values}


def text_quality_flags(
    *,
    title: str,
    summary: str,
    lang: str = "ru",
) -> list[str]:
    text = f"{title} {summary}".strip()
    flags: list[str] = []
    summary_text = clean_source_summary(summary)
    if not summary_text:
        flags.append("missing_summary")
    elif len(summary_text) < 80:
        flags.append("short_summary")

    if _REPEATED_BRIDGE_RE.search(text):
        flags.append("repeated_phrase")

    words = _WORD_RE.findall(summary_text)
    if lang == "ru" and summary_text:
        latin_chars = len(_LATIN_RE.findall(summary_text))
        cyrillic_chars = len(_CYRILLIC_RE.findall(summary_text))
        if latin_chars > 24 and latin_chars > cyrillic_chars:
            flags.append("latin_heavy_ru_text")
        if words and not cyrillic_chars and len(summary_text) > 40:
            flags.append("missing_cyrillic_ru_text")

    if any(
        marker in summary_text.lower()
        for marker in ("click here", "read more", "читать далее")
    ):
        flags.append("source_ui_noise")
    return flags
