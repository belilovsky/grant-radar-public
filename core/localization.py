"""Content localization helpers for Grant Radar payloads."""

from __future__ import annotations

from typing import Any

from core.models import Opportunity
from core.nlp import clean_source_summary
from core.russian_summary import (
    russian_opportunity_title_fallback,
    russian_summary_fallback,
)

SUPPORTED_CONTENT_LANGS = frozenset({"en", "ru"})
_DIRECT_TRANSLATION_SUFFIXES = ("ru", "kk")
_TRANSLATABLE_KEYS = (
    "title",
    "summary",
    "eligibility",
    "detail_text",
    "detail_sections",
    "status_note",
)


def normalize_content_lang(value: str | None) -> str:
    return "en" if str(value or "").strip().lower() == "en" else "ru"


def raw_localization_target(raw: dict[str, Any]) -> dict[str, Any]:
    nested = raw.get("raw")
    if isinstance(nested, dict) and {"type", "tags", "languages"}.issubset(raw.keys()):
        return nested
    return raw


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        normalized = value.strip()
        return [normalized] if normalized else []
    if not isinstance(value, list):
        return []
    return [str(entry).strip() for entry in value if str(entry).strip()]


def _section_list(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    sections: list[dict[str, str]] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        text = _string_value(entry.get("text"))
        if not text:
            continue
        sections.append(
            {
                "heading": _string_value(entry.get("heading")),
                "text": text,
            }
        )
    return sections


def _sections_text_length(sections: list[dict[str, str]]) -> int:
    return sum(len(section.get("text") or "") for section in sections)


def _lang_bucket(raw: dict[str, Any], lang: str) -> dict[str, Any]:
    bucket = raw_localization_target(raw).get("i18n")
    if not isinstance(bucket, dict):
        return {}
    candidate = bucket.get(lang)
    return candidate if isinstance(candidate, dict) else {}


def _localized_value(raw: dict[str, Any], lang: str, key: str) -> Any:
    if lang == "en":
        return None
    target = raw_localization_target(raw)
    bucket = _lang_bucket(target, lang)
    if key in bucket:
        return bucket[key]
    direct_key = f"{key}_{lang}"
    if direct_key in target:
        return target[direct_key]
    return None


def _source_detail_language_matches(target: dict[str, Any], lang: str) -> bool:
    detail_language = normalize_content_lang(
        _string_value(target.get("detail_language"))
    )
    return detail_language == normalize_content_lang(lang)


def has_localized_content(raw: dict[str, Any], lang: str, *keys: str) -> bool:
    content_lang = normalize_content_lang(lang)
    if content_lang == "en":
        return True
    if any(_localized_value(raw, content_lang, key) is not None for key in keys):
        return True

    target = raw_localization_target(raw)
    detail_language = normalize_content_lang(
        _string_value(target.get("detail_language"))
    )
    if detail_language != content_lang:
        return False

    for key in keys:
        value = target.get(key)
        if isinstance(value, str) and value.strip():
            return True
        if key == "detail_sections" and _section_list(value):
            return True
    return False


def localized_text(
    raw: dict[str, Any],
    lang: str,
    key: str,
    *,
    fallback: str = "",
) -> str:
    content_lang = normalize_content_lang(lang)
    target = raw_localization_target(raw)
    localized = _string_value(_localized_value(raw, content_lang, key))
    if key == "detail_text" and _source_detail_language_matches(target, content_lang):
        source_detail = _string_value(target.get(key))
        if source_detail and len(source_detail) > len(localized):
            return source_detail
    if localized:
        return clean_source_summary(localized) if key == "summary" else localized
    fallback_text = _string_value(fallback)
    return clean_source_summary(fallback_text) if key == "summary" else fallback_text


def localized_string_list(
    raw: dict[str, Any],
    lang: str,
    key: str,
    *,
    fallback: list[str] | None = None,
) -> list[str]:
    content_lang = normalize_content_lang(lang)
    localized = _string_list(_localized_value(raw, content_lang, key))
    if localized:
        return localized
    return _string_list(fallback or [])


def localized_section_list(
    raw: dict[str, Any],
    lang: str,
    key: str = "detail_sections",
) -> list[dict[str, str]]:
    content_lang = normalize_content_lang(lang)
    target = raw_localization_target(raw)
    localized = _section_list(_localized_value(raw, content_lang, key))
    source_sections = _section_list(target.get(key))
    if (
        key == "detail_sections"
        and source_sections
        and _source_detail_language_matches(target, content_lang)
        and _sections_text_length(source_sections) > _sections_text_length(localized)
    ):
        return source_sections
    if localized:
        return localized
    return source_sections


def localize_opportunity(item: Opportunity, lang: str) -> Opportunity:
    content_lang = normalize_content_lang(lang)
    if content_lang == "en":
        return item
    raw = item.raw if isinstance(item.raw, dict) else {}
    summary = localized_text(
        raw,
        content_lang,
        "summary",
        fallback=item.summary,
    )
    title = russian_opportunity_title_fallback(
        item, localized_text(raw, content_lang, "title", fallback=item.title)
    )
    summary_item = item.model_copy(update={"title": title})
    return item.model_copy(
        update={
            "title": title,
            "summary": russian_summary_fallback(summary_item, summary),
            "eligibility": localized_string_list(
                raw,
                content_lang,
                "eligibility",
                fallback=item.eligibility,
            ),
        }
    )


def preserve_localized_raw(
    existing_raw: dict[str, Any] | None,
    new_raw: dict[str, Any] | None,
) -> dict[str, Any]:
    existing = existing_raw if isinstance(existing_raw, dict) else {}
    incoming = new_raw if isinstance(new_raw, dict) else {}
    merged = dict(incoming)
    existing_target = raw_localization_target(existing)
    merged_target = raw_localization_target(merged)

    existing_i18n = existing_target.get("i18n")
    incoming_i18n = merged_target.get("i18n")
    if isinstance(existing_i18n, dict):
        if not isinstance(incoming_i18n, dict):
            merged_target["i18n"] = existing_i18n
        else:
            combined_i18n = dict(existing_i18n)
            for lang, payload in incoming_i18n.items():
                if isinstance(payload, dict) and isinstance(
                    combined_i18n.get(lang), dict
                ):
                    combined_lang_payload = dict(combined_i18n[lang])
                    combined_lang_payload.update(payload)
                    combined_i18n[lang] = combined_lang_payload
                else:
                    combined_i18n[lang] = payload
            merged_target["i18n"] = combined_i18n

    for suffix in _DIRECT_TRANSLATION_SUFFIXES:
        for key in _TRANSLATABLE_KEYS:
            localized_key = f"{key}_{suffix}"
            if localized_key not in merged_target and localized_key in existing_target:
                merged_target[localized_key] = existing_target[localized_key]

    return merged
