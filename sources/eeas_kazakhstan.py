"""EEAS Kazakhstan grant parser.

The EEAS grants listing is server-rendered and exposes grant cards with
Kazakhstan-specific delegation links. This adapter keeps the extraction narrow:
it only follows Kazakhstan delegation grant/call pages and records the page
metadata plus deadline.
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from datetime import date, datetime
from html import unescape
from urllib.parse import urljoin

import structlog

from core.models import Opportunity, OpportunityType
from sources.base import BaseSource

log = structlog.get_logger()

LISTING_URL = (
    "https://www.eeas.europa.eu/eeas/grants_en?f%5B0%5D=grant_site%3AKazakhstan&s=222"
)
DETAIL_PREFIX = "https://www.eeas.europa.eu"
FALLBACK_DETAIL_URLS = (
    "https://www.eeas.europa.eu/delegations/kazakhstan/"
    "call-proposals-%E2%80%9Csupport-civil-society-kazakhstan%E2%80%9D-2_en?s=222",
    "https://www.eeas.europa.eu/delegations/kazakhstan/"
    "call-proposals-facilitating-region-specific-approaches-addressing-climate-"
    "and-environment-related_en?s=222",
    "https://www.eeas.europa.eu/delegations/kazakhstan/"
    "call-proposals-under-peace-stability-and-conflict-prevention-thematic-programme_en?s=222",
)

LINK_RE = re.compile(
    r"<a\b[^>]*href\s*=\s*(?:"
    r"\"(?P<href_d>/delegations/kazakhstan/[^\"]+)\"|"
    r"'(?P<href_s>/delegations/kazakhstan/[^']+)'|"
    r"(?P<href_u>/delegations/kazakhstan/[^\s>]+)"
    r")[^>]*>(?P<title>.*?)</a>",
    re.IGNORECASE | re.DOTALL,
)
TIME_RE = re.compile(
    r"<time[^>]+datetime=[\"'](?P<iso>\d{4}-\d{2}-\d{2})T[^\"']+[\"'][^>]*>"
    r"(?P<label>.*?)</time>",
    re.IGNORECASE | re.DOTALL,
)
TITLE_RE = re.compile(r"<h1[^>]*>(?P<title>.*?)</h1>", re.IGNORECASE | re.DOTALL)
META_RE = re.compile(r"<meta\s+(?P<attrs>[^>]*?)>", re.IGNORECASE | re.DOTALL)
DEADLINE_TEXT_RE = re.compile(
    r"deadline[^.]{0,100}?(?:is|:)?\s*"
    r"(?P<day>\d{1,2})\s+"
    r"(?P<month>jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+"
    r"(?P<year>\d{4})",
    re.IGNORECASE,
)
DATE_DOTTED_RE = re.compile(r"(?P<day>\d{1,2})[.](?P<month>\d{1,2})[.](?P<year>\d{4})")
REFERENCE_RE = re.compile(r"EuropeAid/[A-Z0-9./-]+", re.IGNORECASE)

MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}
OPPORTUNITY_KEYWORDS = (
    "call",
    "proposal",
    "grant",
    "application",
    "expression of interest",
)
NON_OPPORTUNITY_KEYWORDS = (
    "contracts were concluded",
    "list of contracts",
    "contracts concluded",
    "signed contracts",
    "award notice",
)
THEME_KEYWORDS = {
    "governance": ("governance", "accountable", "transparent", "democracy"),
    "civil_society": ("civil society", "cso", "ngo"),
    "digital": ("digital", "technology", "online", "data"),
    "green_transition": ("green", "climate", "environment"),
    "human_rights": ("human rights", "rights"),
}
GENERIC_TITLE_PREFIXES = (
    "call for proposals “support to civil society in kazakhstan”",
    'call for proposals "support to civil society in kazakhstan"',
    "конкурс заявок «поддержка гражданского общества в казахстане»",
)


@dataclass(frozen=True)
class ListingEntry:
    url: str
    title: str
    deadline: date | None


def _clean_text(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", unescape(without_tags)).strip()


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


def _meta_content(html: str, *names: str) -> str | None:
    wanted = {name.lower() for name in names}
    for match in META_RE.finditer(html):
        attrs = match.group("attrs")
        name_match = re.search(
            r"(?:name|property)=[\"'](?P<name>[^\"']+)[\"']",
            attrs,
            re.IGNORECASE,
        )
        content_match = re.search(
            r"content=[\"'](?P<content>[^\"']*)[\"']",
            attrs,
            re.IGNORECASE | re.DOTALL,
        )
        if (
            name_match is not None
            and content_match is not None
            and name_match.group("name").lower() in wanted
        ):
            content = _clean_text(content_match.group("content"))
            if content:
                return content
    return None


def _parse_date_from_text(text: str) -> date | None:
    iso_match = re.search(r"\b(?P<iso>\d{4}-\d{2}-\d{2})\b", text)
    if iso_match is not None:
        try:
            return date.fromisoformat(iso_match.group("iso"))
        except ValueError:
            pass

    text_match = DEADLINE_TEXT_RE.search(text)
    if text_match is not None:
        try:
            return datetime(
                int(text_match.group("year")),
                MONTHS[text_match.group("month").lower()[:3]],
                int(text_match.group("day")),
            ).date()
        except (KeyError, ValueError):
            pass

    dotted_match = DATE_DOTTED_RE.search(text)
    if dotted_match is not None:
        try:
            return datetime(
                int(dotted_match.group("year")),
                int(dotted_match.group("month")),
                int(dotted_match.group("day")),
            ).date()
        except ValueError:
            pass

    return None


def _extract_listing_entries(html: str) -> list[ListingEntry]:
    entries: list[ListingEntry] = []
    seen: set[str] = set()
    for match in LINK_RE.finditer(html):
        href = match.group("href_d") or match.group("href_s") or match.group("href_u")
        title = _clean_text(match.group("title"))
        if not href or not title:
            continue
        if not any(keyword in title.lower() for keyword in OPPORTUNITY_KEYWORDS):
            continue
        if any(keyword in title.lower() for keyword in NON_OPPORTUNITY_KEYWORDS):
            continue
        url = urljoin(DETAIL_PREFIX, href)
        if url in seen:
            continue
        seen.add(url)
        context = html[match.start() : match.end() + 1000]
        time_match = TIME_RE.search(context)
        deadline = (
            _parse_date_from_text(time_match.group("iso")) if time_match else None
        )
        deadline = deadline or _parse_date_from_text(context)
        entries.append(ListingEntry(url=url, title=title, deadline=deadline))
    return entries


def _fallback_entries() -> list[ListingEntry]:
    return [
        ListingEntry(url=url, title="EEAS Kazakhstan call", deadline=None)
        for url in FALLBACK_DETAIL_URLS
    ]


def _title_from_detail(html: str) -> str | None:
    title = _meta_content(html, "og:title", "twitter:title")
    if title:
        return title
    match = TITLE_RE.search(html)
    if match is None:
        return None
    return _clean_text(match.group("title")) or None


def _reference_from_detail(html: str) -> str | None:
    match = REFERENCE_RE.search(html)
    return match.group(0) if match is not None else None


def _display_title(title: str, reference: str | None) -> str:
    cleaned = title.strip()
    lowered = cleaned.lower()
    if not reference:
        return cleaned
    if any(lowered.startswith(prefix) for prefix in GENERIC_TITLE_PREFIXES):
        return f"{cleaned} ({reference})"
    return cleaned


def _fallback_summary(title: str) -> str:
    subject = title.strip().rstrip(".") or "funding opportunity"
    return (
        f"Official EEAS Kazakhstan call: {subject}. Review the source page for "
        "eligibility, available funding, submission documents and the current deadline."
    )


def _infer_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags: list[str] = []
    for tag, keywords in THEME_KEYWORDS.items():
        if any(_contains_term(lowered, keyword) for keyword in keywords):
            tags.append(tag)
    return tags


def _contains_term(text: str, keyword: str) -> bool:
    normalized_keyword = re.escape(keyword.lower()).replace(r"\ ", r"[\s_-]+")
    pattern = rf"(?<![a-z0-9]){normalized_keyword}(?![a-z0-9])"
    return re.search(pattern, text) is not None


class EeasKazakhstanSource(BaseSource):
    slug = "eeas_kazakhstan"
    name = "EEAS Kazakhstan grants"
    base_url = "https://www.eeas.europa.eu/eeas/grants_en"
    default_tags = ["kazakhstan", "central_asia", "eu", "eeas", "grant"]

    async def fetch(self) -> AsyncIterator[Opportunity]:
        try:
            response = await self.client.get(LISTING_URL)
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            log.warning("eeas_kazakhstan.listing_failed", error=str(exc))
            return

        count = 0
        entries = _extract_listing_entries(response.text)[:20]
        if not entries:
            log.info("eeas_kazakhstan.listing_fallback_used", url=LISTING_URL)
            entries = _fallback_entries()

        for entry in entries:
            detail_html = ""
            try:
                detail_response = await self.client.get(entry.url)
                detail_response.raise_for_status()
                detail_html = detail_response.text
            except Exception as exc:  # noqa: BLE001
                log.warning(
                    "eeas_kazakhstan.detail_failed",
                    url=entry.url,
                    error=str(exc),
                )

            title = _title_from_detail(detail_html) or entry.title
            summary = _meta_content(detail_html, "description", "og:description")
            summary = summary or _fallback_summary(title)
            deadline = _parse_date_from_text(detail_html) or entry.deadline
            reference = _reference_from_detail(detail_html)
            title = _display_title(title, reference)
            tags = _unique([*self.default_tags, *_infer_tags(f"{title} {summary}")])
            count += 1
            yield Opportunity(
                source=self.slug,
                source_url=entry.url,  # type: ignore[arg-type]
                type=OpportunityType.GRANT,
                title=title,
                summary=summary,
                funder="European External Action Service",
                deadline=deadline,
                tags=tags,
                raw={
                    "external_id": reference or entry.url,
                    "reference": reference,
                    "listing_url": LISTING_URL,
                    "listing_deadline": (
                        entry.deadline.isoformat() if entry.deadline else None
                    ),
                },
            )

        log.info("eeas_kazakhstan.batch", count=count)


EeasKazakhstanParser = EeasKazakhstanSource
