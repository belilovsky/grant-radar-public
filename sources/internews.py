"""Internews source parser.

Fetches grant/opportunity announcements from Internews.
Reference: https://internews.org/opportunities/
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from datetime import date, datetime

import structlog
from lxml import etree as ET

from core.models import Opportunity, OpportunityType
from core.source_text import clean_source_text as _clean_text
from sources.base import BaseSource

log = structlog.get_logger()

LISTING_URL = "https://internews.org/opportunities/"
FEED_URL = "https://internews.org/feed/"

# Match opportunity links pointing to internews.org/opportunity/* or /resource/*
LINK_RE = re.compile(
    r'<a[^>]+href="(?P<href>https?://(?:www\.)?internews\.org/'
    r'(?:opportunity|resource|grant|opportunities)/[^"#?]+)"[^>]*>'
    r"(?P<title>[^<]{5,250})</a>",
    re.IGNORECASE | re.DOTALL,
)
OPPORTUNITY_KEYWORDS = (
    "call for proposals",
    "competition",
    "fellowship",
    "grant",
    "opportunit",
    "request for applications",
    "rfa",
    "terms of reference",
)
ROLLING_HINTS = (
    "rolling",
    "open call",
    "applications open",
    "request for proposals",
    "request for proposal",
    "terms of reference",
)
DEADLINE_RE = re.compile(
    r"(?:deadline|apply by|closes?)\s*[:\u2014–-]?\s*"
    r"(?P<d>\d{1,2})\s+(?P<m>jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(?P<y>\d{4})",
    re.IGNORECASE,
)
DEADLINE_DOTTED_RE = re.compile(
    r"(?:deadline|apply by|closes?)\s*[:\u2014–-]?\s*"
    r"(?P<d>\d{1,2})[.\-/](?P<m>\d{1,2})[.\-/](?P<y>\d{4})",
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


def _secure_xml_parser() -> ET.XMLParser:
    return ET.XMLParser(
        resolve_entities=False,
        no_network=True,
        huge_tree=False,
    )


def _is_rolling_title(raw: str, title: str) -> bool:
    haystack = f"{raw} {title}".lower()
    return any(hint in haystack for hint in ROLLING_HINTS)


def _deadline(raw: str) -> date | None:
    for pattern in (DEADLINE_RE, DEADLINE_DOTTED_RE):
        match = pattern.search(raw)
        if match is None:
            continue
        try:
            day = int(match.group("d"))
            if pattern is DEADLINE_DOTTED_RE:
                month = int(match.group("m"))
            else:
                month = MONTHS[match.group("m").lower()[:3]]
            year = int(match.group("y"))
            return datetime(year, month, day).date()
        except (ValueError, KeyError):
            continue
    return None


def _type_for(title: str) -> OpportunityType:
    lowered = title.lower()
    if "fellowship" in lowered:
        return OpportunityType.FELLOWSHIP
    if "terms of reference" in lowered or "request for proposal" in lowered:
        return OpportunityType.TENDER
    return OpportunityType.GRANT


def _deadline_meta(raw: str, title: str) -> tuple[date | None, bool]:
    deadline = _deadline(raw)
    if deadline is not None:
        return deadline, False
    return None, _is_rolling_title(raw, title)


class InternewsSource(BaseSource):
    slug = "internews"
    name = "Internews"
    base_url = "https://internews.org"
    default_tags = ["international", "internews", "media"]

    async def fetch(self) -> AsyncIterator[Opportunity]:
        try:
            resp = await self.client.get(LISTING_URL)
            if resp.status_code == 403:
                async for item in self._fetch_feed_fallback():
                    yield item
                return
            resp.raise_for_status()
        except Exception as e:  # noqa: BLE001
            log.warning("internews.fetch_failed", error=str(e))
            return

        html = resp.text
        seen: set[str] = set()
        count = 0
        matches = list(LINK_RE.finditer(html))
        for index, match in enumerate(matches):
            url = match.group("href").strip()
            if url in seen:
                continue
            seen.add(url)

            title = re.sub(r"\s+", " ", match.group("title")).strip()
            if not title:
                continue

            next_start = (
                matches[index + 1].start() if index + 1 < len(matches) else len(html)
            )
            ctx = html[match.start() : min(len(html), next_start + 300)]
            opp = self._to_opportunity(url=url, title=title, raw=ctx)
            count += 1
            yield opp

        log.info("internews.batch", count=count)

    async def _fetch_feed_fallback(self) -> AsyncIterator[Opportunity]:
        try:
            resp = await self.client.get(FEED_URL)
            resp.raise_for_status()
        except Exception as e:  # noqa: BLE001
            log.warning("internews.feed_failed", error=str(e))
            return

        count = 0
        try:
            root = ET.fromstring(resp.content, parser=_secure_xml_parser())
        except ET.ParseError as e:
            log.warning("internews.feed_parse_failed", error=str(e))
            return

        channel = root.find("channel")
        if channel is None:
            return

        for item in channel.findall("item"):
            title = _clean_text(item.findtext("title") or "")
            url = (item.findtext("link") or "").strip()
            categories = [
                _clean_text(category.text or "")
                for category in item.findall("category")
            ]
            description = _clean_text(item.findtext("description") or "")
            haystack = " ".join([title, url, description, *categories]).lower()
            if not url or not title:
                continue
            if not any(keyword in haystack for keyword in OPPORTUNITY_KEYWORDS):
                continue

            raw = " ".join([description, *categories])
            count += 1
            yield self._to_opportunity(url=url, title=title, raw=raw)

        log.info("internews.feed_batch", count=count)

    def _to_opportunity(self, *, url: str, title: str, raw: str) -> Opportunity:
        slug = url.rstrip("/").rsplit("/", 1)[-1]
        opp_id = re.sub(r"[^a-zA-Z0-9_-]+", "_", slug)[:64] or "internews"
        deadline, is_rolling = _deadline_meta(raw, title)
        summary = _clean_text(raw)
        if len(summary) > 320:
            summary = f"{summary[:317].rstrip()}..."
        tags = list(self.default_tags)
        raw_deadline_policy = None
        if is_rolling and deadline is None:
            tags.append("rolling")
            raw_deadline_policy = "rolling"
        return Opportunity(
            source=self.slug,
            source_url=url,  # type: ignore[arg-type]
            type=_type_for(title),
            title=title,
            summary=summary or "Internews opportunity",
            deadline=deadline,
            tags=tags,
            raw={
                "external_id": opp_id,
                "snippet": raw,
                **(
                    {"deadline_policy": raw_deadline_policy}
                    if raw_deadline_policy
                    else {}
                ),
            },
        )

    async def healthcheck(self) -> bool:
        try:
            resp = await self.client.get(self.base_url)
            return resp.status_code < 500
        except Exception:  # noqa: BLE001
            return False


InternewsParser = InternewsSource
