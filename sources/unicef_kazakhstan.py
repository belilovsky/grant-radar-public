"""UNICEF Kazakhstan tender parser."""

from __future__ import annotations

import re
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, ClassVar, cast
from urllib.parse import urljoin

import structlog

from core.models import Opportunity, OpportunityType
from core.source_text import clean_source_text as _clean_text
from sources.base import BaseSource

log = structlog.get_logger()

UNICEF_KAZAKHSTAN_TENDERS_URL = "https://www.unicef.org/kazakhstan/en/tenders"
UNICEF_KAZAKHSTAN_TENDERS_READER_URL = (
    "https://r.jina.ai/http://r.jina.ai/http://" f"{UNICEF_KAZAKHSTAN_TENDERS_URL}"
)
UNICEF_FETCH_HEADERS: list[dict[str, str]] = [
    {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 "
            "Mobile/7.0 Safari/604.1"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    },
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    },
]
REFERENCE_RE = re.compile(
    r"\b(?P<ref>(?:RFP|LRFP|LRPS|RFQ|ITB|EOI)/KAZA/\d{4}/\d{3,})\b",
    re.IGNORECASE,
)
REFERENCE_TITLE_RE = re.compile(
    r"(?P<ref>(?:RFP|LRFP|LRPS|RFQ|ITB|EOI)/KAZA/\d{4}/\d{3,})\s*[-:]\s*"
    r"(?P<title>[^<.]{20,600})",
    re.IGNORECASE | re.DOTALL,
)
RECEIVED_BY_RE = re.compile(
    r"(?:received|submitted).{0,220}?\bon\s+"
    r"(?P<day>\d{1,2})\s+"
    r"(?P<month>january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\s+"
    r"(?P<year>\d{4})",
    re.IGNORECASE | re.DOTALL,
)
ISO_DATE_RE = re.compile(r"\b(?P<iso>\d{4}-\d{2}-\d{2})\b")
LINK_RE = re.compile(
    r"<a\b[^>]*href=[\"'](?P<href>[^\"']+)[\"'][^>]*>(?P<label>.*?)</a>",
    re.IGNORECASE | re.DOTALL,
)
MARKDOWN_LINK_RE = re.compile(
    r"\[(?P<label>[^\]]{0,120})\]\((?P<href>https?://[^)\s]+)\)",
    re.IGNORECASE,
)
DRIVE_URL_RE = re.compile(r"https://drive\.google\.com/[^\s)\"']+", re.IGNORECASE)

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
    "education": ("education", "learning", "school", "teacher", "skills"),
    "health": ("health", "mental health", "wellbeing"),
    "digital": ("digital", "online", "data", "technology", "platform"),
    "children": ("children", "child", "youth", "adolescent"),
    "evaluation": ("evaluation", "monitoring", "assessment"),
}

OPERATIONAL_SERVICE_TERMS = (
    "accommodation",
    "catering",
    "conference hall",
    "conference package",
    "event management",
    "hotel",
    "meeting room",
    "venue",
)


@dataclass(frozen=True)
class UnicefTender:
    reference: str
    title: str
    summary: str
    deadline: date | None
    source_url: str | None
    application_url: str | None


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


def _parse_deadline(text: str) -> date | None:
    match = RECEIVED_BY_RE.search(text)
    if match is not None:
        try:
            return datetime(
                int(match.group("year")),
                MONTHS[match.group("month").lower()],
                int(match.group("day")),
            ).date()
        except (KeyError, ValueError):
            pass

    iso_match = ISO_DATE_RE.search(text)
    if iso_match is not None:
        try:
            return date.fromisoformat(iso_match.group("iso"))
        except ValueError:
            pass
    return None


def _is_blocked_page(text: str, status_code: int) -> bool:
    if status_code >= 500:
        return True
    lowered = text.lower()
    return status_code != 200 or "just a moment" in lowered or "_cf_chl_opt" in lowered


def _is_recently_closed(deadline: date, today: date | None = None) -> bool:
    today = today or date.today()
    return (today - deadline).days <= 365


def _policy_for_closed_deadline(
    deadline: date | None, today: date | None = None
) -> str | None:
    if deadline is None or not _is_recently_closed(deadline, today):
        return None
    return "closed"


def _infer_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags: list[str] = []
    for tag, keywords in THEME_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            tags.append(tag)
    return tags


def _is_operational_service_tender(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in OPERATIONAL_SERVICE_TERMS)


def _application_url(html_fragment: str) -> str | None:
    for match in LINK_RE.finditer(html_fragment):
        label = _clean_text(match.group("label")).lower()
        href = match.group("href").strip()
        if (
            "proposal" in label or "bid" in label or "drive.google.com" in href
        ) and href.startswith("http"):
            return href
    for match in MARKDOWN_LINK_RE.finditer(html_fragment):
        label = _clean_text(match.group("label")).lower()
        href = match.group("href").strip()
        if "proposal" in label or "bid" in label or "drive.google.com" in href:
            return href
    drive_match = DRIVE_URL_RE.search(html_fragment)
    if drive_match is not None:
        return drive_match.group(0).rstrip(".,")
    return None


def _source_url(html_fragment: str) -> str | None:
    for match in LINK_RE.finditer(html_fragment):
        href = match.group("href").strip()
        if not href or href.startswith("#"):
            continue
        if "drive.google.com" in href:
            continue
        return urljoin(UNICEF_KAZAKHSTAN_TENDERS_URL, href)
    for match in MARKDOWN_LINK_RE.finditer(html_fragment):
        href = match.group("href").strip()
        if not href or "drive.google.com" in href:
            continue
        return href
    return None


def _reference_fragment(html: str, start_index: int, end_index: int) -> str:
    previous_hr = html.rfind("<hr", 0, start_index)
    if previous_hr == -1:
        start = max(0, start_index - 500)
    else:
        previous_hr_end = html.find(">", previous_hr)
        start = previous_hr_end + 1 if previous_hr_end != -1 else previous_hr

    next_hr = html.find("<hr", end_index)
    end = next_hr if next_hr != -1 else min(len(html), end_index + 3500)
    return html[start:end]


def _extract_tenders(html: str, *, today: date | None = None) -> list[UnicefTender]:
    today = today or date.today()
    tenders: list[UnicefTender] = []
    closed_tenders: list[UnicefTender] = []
    seen: set[str] = set()
    for ref_match in REFERENCE_RE.finditer(html):
        reference = ref_match.group("ref").upper()
        if reference in seen:
            continue
        seen.add(reference)

        fragment = _reference_fragment(html, ref_match.start(), ref_match.end())
        text = _clean_text(fragment)
        title_match = REFERENCE_TITLE_RE.search(fragment)
        title = _clean_text(title_match.group("title")) if title_match else reference
        if len(title) > 260:
            title = f"{title[:257].rstrip()}..."
        deadline = _parse_deadline(text)
        summary = text
        if len(summary) > 700:
            summary = f"{summary[:697].rstrip()}..."
        if _is_operational_service_tender(f"{title} {summary}"):
            continue
        if deadline is not None and deadline < today:
            if _policy_for_closed_deadline(deadline, today):
                closed_tenders.append(
                    UnicefTender(
                        reference=reference,
                        title=title,
                        summary=summary,
                        deadline=deadline,
                        source_url=_source_url(fragment),
                        application_url=_application_url(fragment),
                    )
                )
            continue
        tenders.append(
            UnicefTender(
                reference=reference,
                title=title,
                summary=summary,
                deadline=deadline,
                source_url=_source_url(fragment),
                application_url=_application_url(fragment),
            )
        )
    if tenders:
        return tenders
    if closed_tenders:
        closed_tenders.sort(
            key=lambda tender: tender.deadline or date.min, reverse=True
        )
        return closed_tenders[:1]
    return tenders


class UnicefKazakhstanSource(BaseSource):
    slug = "unicef_kazakhstan"
    name = "UNICEF Kazakhstan tenders"
    base_url = UNICEF_KAZAKHSTAN_TENDERS_URL
    default_tags: ClassVar[list[str]] = [
        "kazakhstan",
        "central_asia",
        "unicef",
        "tender",
        "procurement",
    ]

    async def fetch(self) -> AsyncIterator[Opportunity]:
        response = None
        for headers in UNICEF_FETCH_HEADERS:
            try:
                candidate = await self.client.get(
                    UNICEF_KAZAKHSTAN_TENDERS_URL,
                    headers=headers,
                )
            except Exception as exc:  # noqa: BLE001
                log.debug(
                    "unicef_kazakhstan.fetch_retry_failed",
                    error=str(exc),
                )
                continue

            if _is_blocked_page(candidate.text, candidate.status_code):
                log.debug(
                    "unicef_kazakhstan.fetch_blocked", status=candidate.status_code
                )
                continue
            response = candidate
            break

        if response is None:
            try:
                candidate = await self.client.get(
                    UNICEF_KAZAKHSTAN_TENDERS_READER_URL,
                    headers={
                        "User-Agent": UNICEF_FETCH_HEADERS[-1]["User-Agent"],
                        "Accept": "text/plain,text/markdown;q=0.9,*/*;q=0.8",
                    },
                )
            except Exception as exc:  # noqa: BLE001
                log.warning("unicef_kazakhstan.reader_fetch_failed", error=str(exc))
                return
            if _is_blocked_page(candidate.text, candidate.status_code):
                log.warning(
                    "unicef_kazakhstan.fetch_failed",
                    reader_status=candidate.status_code,
                )
                return
            log.info("unicef_kazakhstan.reader_fallback_used")
            response = candidate

        count = 0
        for tender in _extract_tenders(response.text):
            count += 1
            text = f"{tender.title} {tender.summary}"
            tags = _unique([*self.default_tags, *_infer_tags(text)])
            raw = {
                "external_id": tender.reference,
                "reference": tender.reference,
                "application_url": tender.application_url,
                "listing_url": UNICEF_KAZAKHSTAN_TENDERS_URL,
            }
            deadline_policy = (
                None
                if tender.deadline is None or tender.deadline >= date.today()
                else _policy_for_closed_deadline(tender.deadline)
            )
            if deadline_policy:
                raw["deadline_policy"] = deadline_policy
                tags.append("closed")

            yield Opportunity(
                source=self.slug,
                source_url=cast(
                    Any,
                    tender.source_url or UNICEF_KAZAKHSTAN_TENDERS_URL,
                ),
                type=OpportunityType.TENDER,
                title=tender.title,
                summary=tender.summary,
                funder="UNICEF Kazakhstan",
                deadline=tender.deadline,
                tags=_unique(tags),
                raw=raw,
            )

        log.info("unicef_kazakhstan.batch", count=count)


UnicefKazakhstanParser = UnicefKazakhstanSource
