"""IsDB project procurement parser for Kazakhstan and Central Asia."""

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

BASE_URL = "https://www.isdb.org"
TENDER_URLS = (
    "https://www.isdb.org/project-procurement/tenders?tender_type=GPN",
    "https://www.isdb.org/project-procurement/tenders?tender_type=EOI",
    "https://www.isdb.org/project-procurement/tenders?tender_type=PQN",
    "https://www.isdb.org/project-procurement/tenders?tender_type=SPN",
)

CENTRAL_ASIA_COUNTRIES = {
    "kazakhstan",
    "kyrgyz",
    "kyrgyz republic",
    "kyrgyzstan",
    "tajikistan",
    "turkmenistan",
    "uzbekistan",
}
ACTIVE_STATUSES = {"active", "actif"}

ARTICLE_RE = re.compile(
    r"<article\b(?P<attrs>[^>]*)>(?P<body>.*?)</article>", re.I | re.S
)
TITLE_LINK_RE = re.compile(
    r"<h2>\s*<a\b[^>]*href=[\"'](?P<href>[^\"']+)[\"'][^>]*>"
    r"(?P<title>.*?)</a>\s*</h2>",
    re.I | re.S,
)
STATUS_RE = re.compile(
    r"field--name-field-tender-status.*?<div[^>]*>(?P<value>.*?)</div>",
    re.I | re.S,
)
TYPE_RE = re.compile(
    r"field--name-field-tender-type.*?<div[^>]*>(?P<value>.*?)</div>",
    re.I | re.S,
)
COUNTRY_RE = re.compile(
    r"field--name-field-world-country[^>]*>\s*(?P<value>[^<]+?)\s*</div>",
    re.I | re.S,
)
DATE_RE = re.compile(r"<time\b[^>]*>(?P<value>[^<]+)</time>", re.I | re.S)

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}
THEME_KEYWORDS = {
    "education": ("education", "school", "learning", "teacher", "training"),
    "digital": ("digital", "e-government", "information system", "platform", "ict"),
    "finance": ("finance", "banking", "sukuk", "credit", "financial"),
    "infrastructure": (
        "infrastructure",
        "road",
        "water",
        "electricity",
        "transmission",
    ),
    "green_transition": ("climate", "renewable", "solar", "resilient", "green"),
}


@dataclass(frozen=True)
class IsdbTender:
    url: str
    title: str
    status: str
    tender_type: str
    country: str
    deadline: date | None
    deadline_raw: str | None


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


def _field(pattern: re.Pattern[str], html: str) -> str | None:
    match = pattern.search(html)
    if match is None:
        return None
    value = _clean_text(match.group("value"))
    return value or None


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    match = re.search(
        r"(?P<day>\d{1,2})\s+(?P<month>[A-Za-z]+)\s+(?P<year>\d{4})",
        value,
    )
    if match is None:
        return None
    try:
        return datetime(
            int(match.group("year")),
            MONTHS[match.group("month").lower()],
            int(match.group("day")),
        ).date()
    except (KeyError, ValueError):
        return None


def _is_central_asia_country(country: str) -> bool:
    return country.strip().lower() in CENTRAL_ASIA_COUNTRIES


def _infer_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags: list[str] = []
    for tag, keywords in THEME_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            tags.append(tag)
    return tags


def _extract_tenders(html: str) -> list[IsdbTender]:
    tenders: list[IsdbTender] = []
    seen: set[str] = set()
    for article in ARTICLE_RE.finditer(html):
        body = article.group("body")
        title_match = TITLE_LINK_RE.search(body)
        if title_match is None:
            continue

        url = urljoin(BASE_URL, title_match.group("href"))
        if url in seen:
            continue
        seen.add(url)

        title = _clean_text(title_match.group("title"))
        status = _field(STATUS_RE, body) or ""
        tender_type = _field(TYPE_RE, body) or "Project procurement"
        country = _field(COUNTRY_RE, body) or ""
        deadline_raw = _field(DATE_RE, body)
        if status.strip().lower() not in ACTIVE_STATUSES:
            continue
        if not _is_central_asia_country(country):
            continue
        tenders.append(
            IsdbTender(
                url=url,
                title=title,
                status=status,
                tender_type=tender_type,
                country=country,
                deadline=_parse_date(deadline_raw),
                deadline_raw=deadline_raw,
            )
        )
    return tenders


class IsdbProjectProcurementSource(BaseSource):
    slug = "isdb_project_procurement"
    name = "IsDB Procurement"
    base_url = "https://www.isdb.org/project-procurement/pproc-front"
    default_tags = ["central_asia", "isdb", "tender", "procurement"]

    async def fetch(self) -> AsyncIterator[Opportunity]:
        seen: set[str] = set()
        count = 0
        for listing_url in TENDER_URLS:
            try:
                response = await self.client.get(listing_url)
                response.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                log.warning(
                    "isdb_project_procurement.fetch_failed",
                    url=listing_url,
                    error=str(exc),
                )
                continue

            for tender in _extract_tenders(response.text):
                if tender.url in seen:
                    continue
                seen.add(tender.url)
                count += 1
                text = f"{tender.title} {tender.country} {tender.tender_type}"
                tags = _unique(
                    [
                        *self.default_tags,
                        tender.country.replace(" ", "_"),
                        *_infer_tags(text),
                    ]
                )
                yield Opportunity(
                    source=self.slug,
                    source_url=tender.url,  # type: ignore[arg-type]
                    type=OpportunityType.TENDER,
                    title=tender.title,
                    summary=(
                        f"Active IsDB project procurement notice for {tender.country}: "
                        f"{tender.tender_type}. Review the official procurement "
                        "documents, eligibility requirements and submission conditions."
                    ),
                    funder="Islamic Development Bank",
                    deadline=tender.deadline,
                    tags=tags,
                    raw={
                        "external_id": tender.url.rsplit("/", 1)[-1],
                        "status": tender.status,
                        "tender_type": tender.tender_type,
                        "country": tender.country,
                        "deadline_raw": tender.deadline_raw,
                    },
                )

        log.info("isdb_project_procurement.batch", count=count)


IsdbProjectProcurementParser = IsdbProjectProcurementSource
