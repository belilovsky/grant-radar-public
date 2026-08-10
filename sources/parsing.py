"""Shared, side-effect-free parsing primitives for source adapters."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from datetime import date
from typing import Callable

from lxml import etree as ET


def unique_normalized(values: Iterable[str]) -> list[str]:
    """Return non-empty normalized values while preserving source order."""

    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def contains_term(text: str, keyword: str) -> bool:
    """Match a keyword on token boundaries, accepting spaces, dashes or underscores."""

    normalized_keyword = re.escape(keyword.lower()).replace(r"\ ", r"[\s_-]+")
    pattern = rf"(?<![a-z0-9]){normalized_keyword}(?![a-z0-9])"
    return re.search(pattern, text.lower()) is not None


def infer_tags(text: str, themes: Mapping[str, Iterable[str]]) -> list[str]:
    """Infer ordered theme tags with the shared token-boundary policy."""

    return [
        tag
        for tag, keywords in themes.items()
        if any(contains_term(text, keyword) for keyword in keywords)
    ]


def infer_substring_tags(text: str, themes: Mapping[str, Iterable[str]]) -> list[str]:
    """Infer themes whose upstream vocabulary intentionally permits substrings."""

    lowered = text.lower()
    return [
        tag
        for tag, keywords in themes.items()
        if any(keyword in lowered for keyword in keywords)
    ]


def parse_text_date(
    day: str,
    month: str,
    year: str,
    months: Mapping[str, int],
) -> date | None:
    month_number = months.get(month.strip().lower())
    if month_number is None:
        return None
    try:
        return date(int(year), month_number, int(day))
    except ValueError:
        return None


def html_title(
    html: str,
    cleaner: Callable[[str], str],
    *,
    strip_tags: bool = False,
) -> str | None:
    match = re.search(
        r"<title[^>]*>(?P<title>.*?)</title>", html, re.IGNORECASE | re.DOTALL
    )
    if match is None:
        return None
    value = match.group("title")
    if strip_tags:
        value = re.sub(r"<[^>]+>", " ", value)
    return cleaner(value) or None


def is_unavailable_page(html: str, cleaner: Callable[[str], str]) -> bool:
    title = (html_title(html, cleaner, strip_tags=True) or "").lower()
    text = cleaner(re.sub(r"<[^>]+>", " ", html)).lower()
    return "technical difficulties" in title or (
        "experiencing technical difficulties" in text and "please try again" in text
    )


def is_blocked_fetch(status_code: int, page_title: str | None) -> bool:
    title = (page_title or "").strip().lower()
    return status_code in {401, 403, 429} or title in {
        "access denied",
        "403 forbidden",
        "too many requests",
    }


def secure_xml_parser() -> ET.XMLParser:
    """Build the hardened XML parser used by feed and IATI adapters."""

    return ET.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)
