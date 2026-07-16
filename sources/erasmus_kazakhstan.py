"""Erasmus+ Kazakhstan call parser for HEI opportunities."""

from __future__ import annotations

import re
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from datetime import date
from typing import ClassVar
from urllib.parse import urljoin

import structlog

from core.models import Opportunity, OpportunityType
from core.source_text import clean_source_text as _clean_text
from sources.base import BaseSource

log = structlog.get_logger()

ERASMUS_NEWS_URL = "https://erasmus.kz/en/novosti"
ERASMUS_ARCHIVE_URL = "https://erasmus.kz/en/novosti/novosti-{year}-g"

ITEM_RE = re.compile(
    r'<a\b[^>]*href=["\'](?P<href>[^"\']+)["\'][^>]*class=["\'][^"\']*\bitem-news\b'
    r'[^"\']*["\'][^>]*>(?P<body>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
DATE_LABEL_RE = re.compile(
    r'<div[^>]*class=["\'][^"\']*\bitem-news__date\b[^"\']*["\'][^>]*>(?P<value>.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)
TITLE_RE = re.compile(
    r'<div[^>]*class=["\'][^"\']*\bitem-news__title\b[^"\']*["\'][^>]*>(?P<value>.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)
TEXT_RE = re.compile(
    r'<div[^>]*class=["\'][^"\']*\bitem-news__text\b[^"\']*["\'][^>]*>(?P<value>.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)
ARTICLE_BLOCK_RE = re.compile(
    r'<div[^>]*class=["\'][^"\']*\bnews-single__text\b[^"\']*["\'][^>]*>(?P<body>.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)
ARTICLE_TITLE_RE = re.compile(
    r"<h1[^>]*class=[\"'][^\"']*news-single__title[^\"']*[\"'][^>]*>(?P<title>.*?)</h1>",
    re.IGNORECASE | re.DOTALL,
)
PARAGRAPH_RE = re.compile(r"<p\b[^>]*>(?P<body>.*?)</p>", re.IGNORECASE | re.DOTALL)
LINK_RE = re.compile(
    r'<a\b[^>]*href=["\'](?P<href>[^"\']+)["\'][^>]*>(?P<label>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
DATE_RE = re.compile(
    r"(?P<day>\d{1,2})\s+(?P<month>[A-Za-z]+)\s+(?P<year>20\d{2})",
    re.IGNORECASE,
)
LISTING_DATE_RE = re.compile(r"(?P<day>\d{2})[.](?P<month>\d{2})[.](?P<year>\d{4})")

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

CALL_MARKERS = (
    "call is now open",
    "call now open",
    "officially open",
    "programme actions and deadlines",
    "submit project proposals",
)
SKIP_MARKERS = ("call results", "results featuring", "information day")
ACTION_TAGS = {
    "jean monnet": ["jean_monnet", "eu_studies", "policy"],
    "capacity building": ["capacity_building", "higher_education"],
    "cbhe": ["capacity_building", "higher_education"],
    "erasmus mundus": ["erasmus_mundus", "joint_degrees", "higher_education"],
    "design measure": ["erasmus_mundus", "joint_degrees", "higher_education"],
    "international credit mobility": ["mobility", "student_exchange"],
    "icm": ["mobility", "student_exchange"],
}


@dataclass(frozen=True)
class ListingEntry:
    url: str
    title: str
    teaser: str
    published: date | None


@dataclass(frozen=True)
class ActionEntry:
    url: str
    title: str
    summary: str
    deadline: date | None
    rolling: bool = False


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


def _parse_listing_date(value: str) -> date | None:
    match = LISTING_DATE_RE.search(value)
    if match is None:
        return None
    try:
        return date(
            int(match.group("year")),
            int(match.group("month")),
            int(match.group("day")),
        )
    except ValueError:
        return None


def _parse_text_date(day: str, month: str, year: str) -> date | None:
    month_number = MONTHS.get(month.strip().lower())
    if month_number is None:
        return None
    try:
        return date(int(year), month_number, int(day))
    except ValueError:
        return None


def _listing_urls(today: date | None = None) -> list[str]:
    today = today or date.today()
    previous_year = today.year - 1
    return [ERASMUS_NEWS_URL, ERASMUS_ARCHIVE_URL.format(year=previous_year)]


def _extract_listing_entries(html: str) -> list[ListingEntry]:
    entries: list[ListingEntry] = []
    seen: set[str] = set()
    for match in ITEM_RE.finditer(html):
        body = match.group("body")
        url = match.group("href")
        if not url or url in seen:
            continue
        seen.add(url)
        title_match = TITLE_RE.search(body)
        teaser_match = TEXT_RE.search(body)
        if title_match is None:
            continue
        title = _clean_text(title_match.group("value"))
        teaser = _clean_text(teaser_match.group("value")) if teaser_match else ""
        date_match = DATE_LABEL_RE.search(body)
        published = (
            _parse_listing_date(_clean_text(date_match.group("value")))
            if date_match
            else None
        )
        entries.append(
            ListingEntry(
                url=url,
                title=title,
                teaser=teaser,
                published=published,
            )
        )
    return entries


def _is_call_candidate(entry: ListingEntry) -> bool:
    lowered = f"{entry.title} {entry.teaser}".lower()
    if any(marker in lowered for marker in SKIP_MARKERS):
        return False
    if any(marker in lowered for marker in CALL_MARKERS):
        return True
    if "call" not in lowered:
        return False
    return "opportunit" in lowered


def _article_block(html: str) -> str:
    match = ARTICLE_BLOCK_RE.search(html)
    return match.group("body") if match is not None else html


def _article_title(html: str) -> str | None:
    match = ARTICLE_TITLE_RE.search(html)
    if match is None:
        return None
    return _clean_text(match.group("title")) or None


def _slugify(value: str) -> str:
    lowered = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return lowered.strip("-") or "action"


def _extract_actions(
    html: str, *, article_url: str, today: date | None = None
) -> list[ActionEntry]:
    today = today or date.today()
    actions: list[ActionEntry] = []
    seen: set[str] = set()
    article_block = _article_block(html)
    paragraphs: list[tuple[str, str]] = []
    for match in PARAGRAPH_RE.finditer(article_block):
        paragraph_html = match.group("body")
        paragraph_text = _clean_text(paragraph_html)
        paragraphs.append((paragraph_html, paragraph_text))

    for index, (paragraph_html, paragraph_text) in enumerate(paragraphs):
        link_matches = list(LINK_RE.finditer(paragraph_html))
        if not link_matches:
            continue

        date_match = DATE_RE.search(paragraph_text)
        if date_match is None:
            for offset in (1, -1):
                neighbor = index + offset
                if 0 <= neighbor < len(paragraphs):
                    date_match = DATE_RE.search(
                        f"{paragraph_text} {paragraphs[neighbor][1]}"
                    )
                    if date_match is not None:
                        break

        deadline: date | None = None
        rolling = False
        if date_match is not None:
            deadline = _parse_text_date(
                date_match.group("day"),
                date_match.group("month"),
                date_match.group("year"),
            )
            if deadline is None:
                rolling = True
        elif "call" in paragraph_text.lower():
            rolling = True
        else:
            continue

        summary_source = (
            paragraph_text[: date_match.start()]
            if date_match is not None
            else paragraph_text
        )
        for link_match in link_matches:
            raw_title = _clean_text(link_match.group("label"))
            action_url = urljoin(article_url, link_match.group("href"))
            if not raw_title:
                continue
            title = raw_title
            summary = summary_source.replace(raw_title, "", 1).strip(" -–\u2014:")
            if not title or not action_url:
                continue
            if action_url in seen:
                continue
            seen.add(action_url)
            if not summary and not paragraph_text:
                continue

            actions.append(
                ActionEntry(
                    url=action_url,
                    title=title,
                    summary=summary,
                    deadline=deadline,
                    rolling=rolling,
                )
            )
    return actions


def _infer_tags(action: ActionEntry) -> list[str]:
    lowered = f"{action.title} {action.summary}".lower()
    tags = [
        "kazakhstan",
        "central_asia",
        "eu",
        "erasmus",
        "higher_education",
    ]
    if "organization" in lowered:
        tags.append("organizations")
    for marker, marker_tags in ACTION_TAGS.items():
        if marker in lowered:
            tags.extend(marker_tags)
    if action.rolling:
        tags.append("rolling")
    return _unique(tags)


class ErasmusKazakhstanSource(BaseSource):
    slug = "erasmus_kazakhstan"
    name = "Erasmus+ Kazakhstan calls"
    base_url = ERASMUS_NEWS_URL
    default_tags: ClassVar[list[str]] = [
        "kazakhstan",
        "central_asia",
        "eu",
        "erasmus",
        "higher_education",
    ]

    async def fetch(self) -> AsyncIterator[Opportunity]:
        today = date.today()
        listing_entries: list[ListingEntry] = []
        seen_urls: set[str] = set()

        for listing_url in _listing_urls(today):
            try:
                response = await self.client.get(listing_url)
                response.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                log.warning(
                    "erasmus_kazakhstan.listing_failed",
                    url=listing_url,
                    error=str(exc),
                )
                continue

            for entry in _extract_listing_entries(response.text):
                if entry.url in seen_urls or not _is_call_candidate(entry):
                    continue
                seen_urls.add(entry.url)
                listing_entries.append(entry)

        count = 0
        for entry in listing_entries[:4]:
            try:
                detail_response = await self.client.get(entry.url)
                detail_response.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                log.warning(
                    "erasmus_kazakhstan.detail_failed",
                    url=entry.url,
                    error=str(exc),
                )
                continue

            detail_html = detail_response.text
            article_title = _article_title(detail_html) or entry.title
            for action in _extract_actions(
                detail_html, article_url=entry.url, today=today
            ):
                action_summary = action.summary or "Programme details"
                count += 1
                yield Opportunity(
                    source=self.slug,
                    source_url=action.url,  # type: ignore[arg-type]
                    type=OpportunityType.GRANT,
                    title=f"{action.title} – Erasmus+ Kazakhstan",
                    summary=(
                        f"{action_summary}. Open Erasmus+ call for Kazakhstani higher "
                        f"education institutions and organizations."
                    ),
                    funder="European Union / Erasmus+",
                    deadline=action.deadline,
                    eligibility=[
                        "Kazakhstani higher education institutions",
                        "Eligible organizations in Kazakhstan",
                    ],
                    tags=_unique([*self.default_tags, *_infer_tags(action)]),
                    languages=["en"],
                    raw={
                        "article_url": entry.url,
                        "article_title": article_title,
                        "listing_published": (
                            entry.published.isoformat() if entry.published else None
                        ),
                        "action_title": action.title,
                        **({"deadline_policy": "rolling"} if action.rolling else {}),
                    },
                )

        log.info("erasmus_kazakhstan.batch", count=count)


ErasmusKazakhstanParser = ErasmusKazakhstanSource
