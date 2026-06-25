"""UNESCO IITE announcements parser for AI and education opportunities."""

from __future__ import annotations

import re
from collections.abc import AsyncIterator, Iterable
from datetime import date
from html import unescape
from urllib.parse import urljoin

import structlog

from core.models import Opportunity, OpportunityType
from sources.base import BaseSource

log = structlog.get_logger()

UNESCO_IITE_ANNOUNCEMENTS_URL = "https://iite.unesco.org/announcements/"

MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

TITLE_TERMS = (
    "call for entries",
    "call for proposals",
    "consultant",
    "competition",
    "challenge",
    "award",
    "awards",
)
THEMATIC_TERMS = (
    "ai",
    "artificial intelligence",
    "education",
    "teacher",
    "learning",
    "ict",
    "open badges",
    "e-assessment",
    "digital",
)


def _clean_text(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", unescape(without_tags)).strip()


def _plain_text(html: str) -> str:
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    return _clean_text(html)


def _html_title(html: str) -> str | None:
    match = re.search(
        r"<title[^>]*>(?P<title>.*?)</title>", html, re.IGNORECASE | re.DOTALL
    )
    if match is None:
        return None
    title = _clean_text(match.group("title"))
    return title or None


def _meta_description(html: str) -> str | None:
    pattern = (
        r"<meta[^>]+(?:name|property)=[\"'](?:description|og:description)[\"']"
        r"[^>]+content=[\"'](?P<content>[^\"']+)[\"']"
    )
    match = re.search(
        pattern,
        html,
        re.IGNORECASE,
    )
    if match is None:
        return None
    return _clean_text(match.group("content")) or None


def _article_text(html: str) -> str:
    match = re.search(
        r"<article\b[^>]*>(?P<article>.*?)</article>",
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if match is None:
        return _plain_text(html)
    return _plain_text(match.group("article"))


def _extract_links(html: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for match in re.finditer(
        r'<a\s+[^>]*href=["\'](?P<href>[^"\']+)["\'][^>]*>(?P<label>.*?)</a>',
        html,
        re.IGNORECASE | re.DOTALL,
    ):
        url = urljoin(UNESCO_IITE_ANNOUNCEMENTS_URL, unescape(match.group("href")))
        title = _clean_text(match.group("label"))
        if (
            not title
            or "/announcements/" not in url
            or url.rstrip("/") == UNESCO_IITE_ANNOUNCEMENTS_URL.rstrip("/")
        ):
            continue
        key = url.rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        out.append((url, title))
    return out


def _parse_text_date(day: str, month: str, year: str) -> date | None:
    month_number = MONTHS.get(month.strip().lower())
    if month_number is None:
        return None
    try:
        return date(int(year), month_number, int(day))
    except ValueError:
        return None


def _deadline(text: str) -> tuple[date | None, str | None]:
    patterns = (
        r"(?:application|submission)\s+deadline[^.\n:]*[:\s]+(?P<day>\d{1,2})\s+"
        r"(?P<month>[A-Za-z]+)\s+(?P<year>20\d{2})",
        r"(?:application|submission)\s+deadline[^.\n:]*[:\s]+(?P<month>[A-Za-z]+)\s+"
        r"(?P<day>\d{1,2})(?:st|nd|rd|th)?[,]?\s+(?P<year>20\d{2})",
        r"deadline[^.\n]{0,80}?(?:until|till|to|:)?\s*(?P<day>\d{1,2})\s+"
        r"(?P<month>[A-Za-z]+)\s+(?P<year>20\d{2})",
        r"deadline[^.\n]{0,80}?(?:until|till|to|:|is)?\s*(?P<month>[A-Za-z]+)\s+"
        r"(?P<day>\d{1,2})(?:st|nd|rd|th)?[,]?\s+(?P<year>20\d{2})",
        r"(?:submission|applications?)[^.\n]{0,120}?(?P<day>\d{1,2})\s+"
        r"(?P<month>[A-Za-z]+)\s+(?P<year>20\d{2})",
        r"(?:submission|applications?)[^.\n]{0,120}?(?P<month>[A-Za-z]+)\s+"
        r"(?P<day>\d{1,2})(?:st|nd|rd|th)?[,]?\s+(?P<year>20\d{2})",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match is None:
            continue
        parsed = _parse_text_date(
            match.group("day"), match.group("month"), match.group("year")
        )
        if parsed is not None:
            return parsed, match.group(0)
    return None, None


def _type_for(title: str) -> OpportunityType:
    lowered = title.lower()
    if "award" in lowered or "competition" in lowered or "entries" in lowered:
        return OpportunityType.CONTEST
    if "consultant" in lowered or "proposals" in lowered:
        return OpportunityType.TENDER
    return OpportunityType.GRANT


def _tags(title: str, text: str) -> list[str]:
    lowered = f"{title} {text}".lower()
    title_lowered = title.lower()
    tags = ["global", "central_asia_eligible", "unesco", "education"]
    if re.search(r"(?<![a-z0-9])ai(?![a-z0-9])|artificial intelligence", lowered):
        tags.append("ai")
    if "teacher" in lowered:
        tags.append("teacher_training")
    if "open badges" in lowered or "e-assessment" in lowered:
        tags.extend(["digital_skills", "assessment"])
    if "proposal" in title_lowered or "consultant" in title_lowered:
        tags.append("procurement")
    return _unique(tags)


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        normalized = value.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def _is_candidate(title: str, detail_text: str = "") -> bool:
    lowered = f"{title} {detail_text}".lower()
    return any(term in lowered for term in TITLE_TERMS) and any(
        term in lowered for term in THEMATIC_TERMS
    )


def _has_opportunity_term(title: str) -> bool:
    lowered = title.lower()
    return any(term in lowered for term in TITLE_TERMS)


class UnescoIiteSource(BaseSource):
    slug = "unesco_iite"
    name = "UNESCO IITE announcements"
    base_url = UNESCO_IITE_ANNOUNCEMENTS_URL
    default_tags = ["global", "central_asia_eligible", "unesco", "education"]

    async def fetch(self) -> AsyncIterator[Opportunity]:
        try:
            response = await self.client.get(UNESCO_IITE_ANNOUNCEMENTS_URL)
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "unesco_iite.listing_failed",
                url=UNESCO_IITE_ANNOUNCEMENTS_URL,
                error=str(exc),
            )
            return

        today = date.today()
        for url, listing_title in _extract_links(response.text)[:12]:
            try:
                detail = await self.client.get(url)
                detail.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                log.warning("unesco_iite.detail_failed", url=url, error=str(exc))
                continue

            page_title = _html_title(detail.text)
            article_text = _article_text(detail.text)
            meta_description = _meta_description(detail.text)
            candidate_text = " ".join(
                value for value in (page_title, meta_description, article_text) if value
            )
            if not _is_candidate(listing_title, candidate_text):
                continue
            deadline, deadline_raw = _deadline(article_text or candidate_text)
            if deadline is not None and deadline < today:
                continue

            title = page_title.split(" – ")[0].strip() if page_title else listing_title
            summary = meta_description
            if not summary:
                marker = article_text.lower().find(title.lower())
                summary_source = (
                    article_text[marker + len(title) :] if marker >= 0 else article_text
                )
                summary = summary_source[:420].strip()

            yield Opportunity(
                source=self.slug,
                source_url=url,  # type: ignore[arg-type]
                type=_type_for(title),
                title=title,
                summary=summary,
                funder="UNESCO IITE",
                deadline=deadline,
                eligibility=["global", "education_organisation"],
                tags=_tags(title, candidate_text),
                raw={
                    "external_id": url.rstrip("/").rsplit("/", 1)[-1],
                    "listing_title": listing_title,
                    "page_title": page_title,
                    "deadline_raw": deadline_raw,
                    "status_code": detail.status_code,
                },
            )


UnescoIiteParser = UnescoIiteSource
