"""UNDP procurement parser for Central Asia opportunities."""

from __future__ import annotations

import re
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from datetime import date, datetime
from urllib.parse import parse_qs, urljoin, urlparse

import structlog

from core.models import Opportunity, OpportunityType
from core.source_text import clean_source_text as _clean_text
from sources.base import BaseSource

log = structlog.get_logger()

LISTING_URL = "https://procurement-notices.undp.org/"

ROW_RE = re.compile(
    r'<a\s+href="(?P<href>view_negotiation\.cfm\?nego_id=\d+)"[^>]*>'
    r"(?P<body>.*?)</a>",
    re.IGNORECASE | re.DOTALL,
)
CELL_RE = re.compile(
    r"<div class=\"vacanciesTable__cell\">\s*"
    r"<div class=\"vacanciesTable__cell__label\">\s*(?P<label>.*?)</div>\s*"
    r"<span>(?P<value>.*?)</span>\s*</div>",
    re.IGNORECASE | re.DOTALL,
)

DATE_RE = re.compile(
    r"(?P<day>\d{1,2})-(?P<month>[A-Za-z]{3})-(?P<year>\d{2,4})",
    re.IGNORECASE,
)

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

CENTRAL_ASIA_TERMS = (
    "kazakhstan",
    "kazakh",
    "uzbek",
    "uzbekistan",
    "kyrgyz",
    "kyrgyzstan",
    "tajik",
    "tajikistan",
    "turkmen",
    "turkmenistan",
)

THEME_KEYWORDS = {
    "education": ("education", "school", "university", "learning", "teacher"),
    "digital": ("digital", "information", "information system", "it", "technology"),
    "procurement": ("procurement", "tender", "rfp", "rfq", "quotation"),
    "infrastructure": ("infrastructure", "construction", "road", "water", "energy"),
    "consulting": ("consultant", "consulting", "individual contractor"),
}

OPERATIONAL_SERVICE_TERMS = (
    "accommodation",
    "catering",
    "conference hall",
    "conference package",
    "event management",
    "conference services",
    "hotel",
    "hotel services",
    "meeting room",
    "lodging",
    "проживан",
    "гостини",
    "отел",
    "конференц",
    "зал",
    "пакет услуг",
    "размещени",
    "кейтеринг",
    "venue",
)


@dataclass(frozen=True)
class UndpNotice:
    external_id: str
    title: str
    reference: str
    office: str
    process: str
    deadline: date | None
    url: str


def _normalize_label(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


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
        year = int(match.group("year"))
        if year < 100:
            year += 2000
        return datetime(
            year,
            MONTHS[match.group("month").lower()],
            int(match.group("day")),
        ).date()
    except (KeyError, ValueError):
        return None


def _contains_central_asia(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in CENTRAL_ASIA_TERMS)


def _infer_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags: list[str] = []
    for tag, keywords in THEME_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            tags.append(tag)
    return tags


def _is_operational_service_notice(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in OPERATIONAL_SERVICE_TERMS)


def _extract_notices(
    html: str,
    *,
    today: date | None = None,
) -> list[UndpNotice]:
    today = today or date.today()
    notices: list[UndpNotice] = []
    seen: set[str] = set()
    seen_urls: set[str] = set()

    for row in ROW_RE.finditer(html):
        row_body = row.group("body")
        fields: dict[str, str] = {}
        for match in CELL_RE.finditer(row_body):
            label = _normalize_label(_clean_text(match.group("label")))
            value = _clean_text(match.group("value"))
            if not value:
                continue
            fields[label] = value

        title = fields.get("title")
        office = fields.get("undp office/country")
        process = fields.get("process") or fields.get("procurement process")
        reference = fields.get("ref no") or fields.get("reference") or ""
        deadline_text = fields.get("deadline") or ""
        if not title or not office:
            continue

        if _is_operational_service_notice(f"{title} {process or ''} {reference}"):
            continue

        office_scope = f"{office} {title}"
        if not _contains_central_asia(office_scope):
            continue

        deadline = _parse_date(deadline_text)
        if deadline is not None and deadline < today:
            continue

        url = urljoin(LISTING_URL, row.group("href"))
        normalized_url = url.rstrip("/").lower()
        if normalized_url in seen_urls:
            continue
        query = parse_qs(urlparse(url).query)
        nego_id = (query.get("nego_id") or [""])[0]
        external_id = reference or nego_id
        if not external_id or external_id in seen:
            continue
        seen.add(external_id)
        seen_urls.add(normalized_url)

        notices.append(
            UndpNotice(
                external_id=external_id,
                title=title,
                reference=reference,
                office=office,
                process=process or "procurement",
                deadline=deadline,
                url=url,
            )
        )

    return notices


class UndpProcurementSource(BaseSource):
    slug = "undp_procurement"
    name = "UNDP Procurement"
    base_url = LISTING_URL
    default_tags = [
        "central_asia",
        "undp",
        "procurement",
        "tender",
    ]

    async def fetch(self) -> AsyncIterator[Opportunity]:
        try:
            response = await self.client.get(LISTING_URL)
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            log.warning("undp_procurement.fetch_failed", error=str(exc))
            return

        count = 0
        for notice in _extract_notices(response.text):
            text = f"{notice.title} {notice.office} {notice.process} {notice.reference}"
            tags = _unique([*self.default_tags, *_infer_tags(text)])
            count += 1
            yield Opportunity(
                source=self.slug,
                source_url=notice.url,  # type: ignore[arg-type]
                type=OpportunityType.TENDER,
                title=notice.title,
                summary=(
                    f"UNDP procurement opportunity in {notice.office}. "
                    f"Reference number: {notice.reference}."
                ),
                funder="United Nations Development Programme",
                deadline=notice.deadline,
                tags=tags,
                raw={
                    "external_id": notice.external_id,
                    "reference": notice.reference,
                    "office": notice.office,
                    "process": notice.process,
                    "listing_url": LISTING_URL,
                },
            )

        log.info("undp_procurement.batch", count=count)


UndpProcurementParser = UndpProcurementSource
