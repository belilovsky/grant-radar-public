"""EBRD ECEPP procurement parser for Kazakhstan and Central Asia."""

from __future__ import annotations

import re
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from datetime import date, datetime
from typing import ClassVar
from urllib.parse import urljoin

import structlog

from core.models import Opportunity, OpportunityType
from core.source_text import clean_source_text as _clean_text
from sources.base import BaseSource

log = structlog.get_logger()

ECEPP_SEARCH_URL = "https://ecepp.ebrd.com/delta/noticeSearchResults.html"
ECEPP_BASE_URL = "https://ecepp.ebrd.com/delta/"

COUNTRY_ALIASES = {
    "kazakhstan": "kazakhstan",
    "kyrgyz republic": "kyrgyzstan",
    "kyrgyzstan": "kyrgyzstan",
    "tajikistan": "tajikistan",
    "turkmenistan": "turkmenistan",
    "uzbekistan": "uzbekistan",
}

ROW_RE = re.compile(r"<tr\b[^>]*>(?P<body>.*?)</tr>", re.IGNORECASE | re.DOTALL)
TD_RE = re.compile(r"<td\b[^>]*>(?P<body>.*?)</td>", re.IGNORECASE | re.DOTALL)
LINK_RE = re.compile(
    r"<a\b[^>]*href=[\"'](?P<href>[^\"']+)[\"'][^>]*>(?P<title>.*?)</a>",
    re.IGNORECASE | re.DOTALL,
)
DATE_RE = re.compile(
    r"(?P<day>\d{2})/(?P<month>\d{2})/(?P<year>\d{4})"
    r"(?:\s+(?P<hour>\d{2}):(?P<minute>\d{2}))?"
)

THEME_KEYWORDS = {
    "education": ("education", "school", "learning", "training"),
    "digital": ("digital", "information system", "ict", "e-government"),
    "transport": ("road", "transport", "bus", "e-bus", "rail"),
    "water": ("water", "wastewater", "irrigation"),
    "energy": ("energy", "electric", "power", "substation"),
    "infrastructure": ("construction", "rehabilitation", "reconstruction"),
    "consultancy": ("consultant", "consultancy", "supervision", "technical"),
    "green_transition": ("climate", "green", "renewable", "resilience"),
}


@dataclass(frozen=True)
class EceppNotice:
    url: str
    title: str
    notice_type: str
    exercise_title: str
    published_raw: str
    closing_raw: str
    deadline: date | None
    current_state: str
    country: str
    metadata: str


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


def _parse_date(value: str) -> date | None:
    match = DATE_RE.search(value)
    if match is None:
        return None
    try:
        return datetime(
            int(match.group("year")),
            int(match.group("month")),
            int(match.group("day")),
        ).date()
    except ValueError:
        return None


def _country_from_text(value: str) -> tuple[str, str] | None:
    lowered = value.lower()
    for label, slug in COUNTRY_ALIASES.items():
        if re.search(rf"(?<![a-z]){re.escape(label)}(?![a-z])", lowered):
            return label.title(), slug
    return None


def _infer_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags: list[str] = []
    for tag, keywords in THEME_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            tags.append(tag)
    return tags


def _extract_notices(html: str, *, today: date | None = None) -> list[EceppNotice]:
    today = today or date.today()
    notices: list[EceppNotice] = []
    seen: set[str] = set()
    for row_match in ROW_RE.finditer(html):
        cells = [
            match.group("body") for match in TD_RE.finditer(row_match.group("body"))
        ]
        if len(cells) < 10:
            continue

        link_match = LINK_RE.search(cells[0])
        if link_match is None:
            continue
        url = urljoin(ECEPP_BASE_URL, link_match.group("href"))
        if url in seen:
            continue
        seen.add(url)

        title = _clean_text(link_match.group("title"))
        notice_type = _clean_text(cells[1])
        exercise_title = _clean_text(cells[2])
        published_raw = _clean_text(cells[3])
        closing_raw = _clean_text(cells[4])
        current_state = _clean_text(cells[5])
        metadata = _clean_text(cells[9])

        if current_state.lower() != "open":
            continue
        country_pair = _country_from_text(f"{title} {metadata}")
        if country_pair is None:
            continue
        deadline = _parse_date(closing_raw)
        if deadline is not None and deadline < today:
            continue

        notices.append(
            EceppNotice(
                url=url,
                title=title,
                notice_type=notice_type,
                exercise_title=exercise_title,
                published_raw=published_raw,
                closing_raw=closing_raw,
                deadline=deadline,
                current_state=current_state,
                country=country_pair[0],
                metadata=metadata,
            )
        )
    return notices


class EbrdEceppProcurementSource(BaseSource):
    slug = "ebrd_ecepp_procurement"
    name = "EBRD ECEPP Procurement"
    base_url = ECEPP_SEARCH_URL
    default_tags: ClassVar[list[str]] = [
        "central_asia",
        "ebrd",
        "ecepp",
        "tender",
        "procurement",
    ]

    async def fetch(self) -> AsyncIterator[Opportunity]:
        try:
            response = await self.client.get(ECEPP_SEARCH_URL)
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            log.warning("ebrd_ecepp_procurement.fetch_failed", error=str(exc))
            return

        count = 0
        for notice in _extract_notices(response.text):
            country_slug = COUNTRY_ALIASES.get(
                notice.country.lower(), notice.country.lower()
            )
            text = f"{notice.title} {notice.exercise_title} {notice.metadata}"
            tags = _unique(
                [
                    *self.default_tags,
                    country_slug.replace(" ", "_"),
                    *_infer_tags(text),
                ]
            )
            count += 1
            yield Opportunity(
                source=self.slug,
                source_url=notice.url,  # type: ignore[arg-type]
                type=OpportunityType.TENDER,
                title=notice.title,
                summary=(
                    f"Open EBRD ECEPP procurement notice for {notice.country}: "
                    f"{notice.notice_type}. {notice.exercise_title}"
                ),
                funder="European Bank for Reconstruction and Development",
                deadline=notice.deadline,
                tags=tags,
                raw={
                    "external_id": notice.url.rsplit("=", 1)[-1],
                    "notice_type": notice.notice_type,
                    "exercise_title": notice.exercise_title,
                    "published_raw": notice.published_raw,
                    "closing_raw": notice.closing_raw,
                    "current_state": notice.current_state,
                    "country": notice.country,
                    "metadata": notice.metadata,
                },
            )

        log.info("ebrd_ecepp_procurement.batch", count=count)


EbrdEceppProcurementParser = EbrdEceppProcurementSource
