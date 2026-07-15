"""Astana Hub source parser.

Fetches grant/program opportunities from the Astana Hub portal.
Reference: https://astanahub.com
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from datetime import date, datetime

import structlog

from core.models import Opportunity, OpportunityType
from core.source_text import clean_source_text as _clean_text
from sources.base import BaseSource

log = structlog.get_logger()

LISTING_URL = "https://astanahub.com/ru/service/programs/"
DETAIL_PREFIX = "https://astanahub.com"
FALLBACK_PROGRAM_URLS = (
    "https://astanahub.com/ru/l/TechOrda2025",
    "https://astanahub.com/ru/l/silkwayaccelerator2025",
    "https://astanahub.com/en/l/regional/develop",
)
FALLBACK_PROGRAM_SUMMARIES = {
    "https://astanahub.com/ru/l/TechOrda2025": (
        "Astana Hub education-support program for Kazakhstan IT talent. "
        "The route helps learners access training through partner schools and "
        "supports companies that need a stronger local digital-skills pipeline."
    ),
    "https://astanahub.com/ru/l/silkwayaccelerator2025": (
        "Astana Hub and Google for Startups accelerator for technology startups "
        "from Central Asia. The program focuses on mentoring, product growth, "
        "market validation and investor-readiness for regional founders."
    ),
    "https://astanahub.com/en/l/regional/develop": (
        "Astana Hub regional IT ecosystem program for Kazakhstan teams outside "
        "the capital. It is a practical entry point for startup support, local "
        "community development, acceleration and partner programs."
    ),
}
FALLBACK_PROGRAM_EXTRA_TAGS = {
    "https://astanahub.com/ru/l/TechOrda2025": [
        "education",
        "digital_skills",
        "startup_support",
    ],
    "https://astanahub.com/ru/l/silkwayaccelerator2025": [
        "startup",
        "accelerator",
        "central_asia_eligible",
    ],
    "https://astanahub.com/en/l/regional/develop": [
        "startup_support",
        "regional_development",
        "kazakhstan",
    ],
}

# Very lightweight HTML extraction patterns; resilient to small layout changes.
CARD_RE = re.compile(
    r'<a[^>]+href="(?P<href>/(?:ru|en)/(?:service/programs|l)/[^"]+)"[^>]*>\s*'
    r"(?:<[^>]+>\s*)*?(?P<title>[^<]{5,200})",
    re.IGNORECASE | re.DOTALL,
)
TITLE_RE = re.compile(r"<title[^>]*>(?P<title>.*?)</title>", re.IGNORECASE | re.DOTALL)
DEADLINE_RE = re.compile(
    r"(?:до|deadline|дедлайн)\s*[:\u2014–-]?\s*(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{2,4})",
    re.IGNORECASE,
)
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
    "янв": 1,
    "января": 1,
    "фев": 2,
    "февраля": 2,
    "мар": 3,
    "марта": 3,
    "апр": 4,
    "апреля": 4,
    "мая": 5,
    "май": 5,
    "июн": 6,
    "июня": 6,
    "июл": 7,
    "июля": 7,
    "авг": 8,
    "августа": 8,
    "сен": 9,
    "сентября": 9,
    "окт": 10,
    "октября": 10,
    "ноя": 11,
    "ноября": 11,
    "дек": 12,
    "декабря": 12,
}
TEXTUAL_DEADLINE_PATTERNS = (
    re.compile(
        r"(?:прием|приём)\s+заявок[^.]{0,160}?\b(?:до|по)\s*"
        r"(?P<day>\d{1,2})\s+(?P<month>[A-Za-zА-Яа-я]+)\s+(?P<year>20\d{2})",
        re.IGNORECASE,
    ),
    re.compile(
        r"deadline[^.\n]{0,120}?(?P<month>[A-Za-z]+)\s+(?P<day>\d{1,2}),\s*(?P<year>20\d{2})",
        re.IGNORECASE,
    ),
    re.compile(
        r'new\s+Date\("(?P<month>[A-Za-z]+)\s+(?P<day>\d{1,2}),\s*(?P<year>20\d{2})',
        re.IGNORECASE,
    ),
)


def _parse_month_token(token: str) -> int | None:
    return MONTHS.get(token.strip().lower().rstrip(".,"))


def _parse_textual_deadline(raw: str) -> date | None:
    for pattern in TEXTUAL_DEADLINE_PATTERNS:
        match = pattern.search(raw)
        if match is None:
            continue
        month = _parse_month_token(match.group("month"))
        if month is None:
            continue
        try:
            return date(int(match.group("year")), month, int(match.group("day")))
        except ValueError:
            continue
    return None


class AstanaHubSource(BaseSource):
    slug = "astana_hub"
    name = "Astana Hub"
    base_url = "https://astanahub.com"
    default_tags = ["kz", "astana_hub", "program"]

    async def fetch(self) -> AsyncIterator[Opportunity]:
        try:
            resp = await self.client.get(LISTING_URL)
            if resp.status_code == 404:
                async for item in self._fetch_fallback_programs():
                    yield item
                return
            resp.raise_for_status()
        except Exception as e:  # noqa: BLE001
            log.warning("astana_hub.fetch_failed", error=str(e))
            return

        html = resp.text
        seen: set[str] = set()
        count = 0
        for m in CARD_RE.finditer(html):
            href = m.group("href").strip()
            if href in seen:
                continue
            seen.add(href)

            title = re.sub(r"\s+", " ", m.group("title")).strip()
            if not title:
                continue

            url = href if href.startswith("http") else DETAIL_PREFIX + href
            opp = self._to_opportunity(
                url=url, title=title, raw=html[m.start() : m.end() + 600]
            )
            count += 1
            yield opp

        log.info("astana_hub.batch", count=count)

    async def _fetch_fallback_programs(self) -> AsyncIterator[Opportunity]:
        count = 0
        for url in FALLBACK_PROGRAM_URLS:
            try:
                resp = await self.client.get(url)
                resp.raise_for_status()
            except Exception as e:  # noqa: BLE001
                log.warning("astana_hub.fallback_failed", url=url, error=str(e))
                continue

            title = (
                self._title_from_html(resp.text) or url.rstrip("/").rsplit("/", 1)[-1]
            )
            count += 1
            yield self._to_opportunity(url=url, title=title, raw=resp.text[:2000])

        log.info("astana_hub.fallback_batch", count=count)

    def _title_from_html(self, html: str) -> str | None:
        match = TITLE_RE.search(html)
        if match is None:
            return None
        title = _clean_text(match.group("title"))
        return title or None

    def _to_opportunity(self, *, url: str, title: str, raw: str) -> Opportunity:
        deadline = None
        dm = DEADLINE_RE.search(raw)
        if dm:
            try:
                day, month, year = (int(x) for x in dm.groups())
                if year < 100:
                    year += 2000
                deadline = datetime(year, month, day).date()
            except ValueError:
                deadline = None
        if deadline is None:
            deadline = _parse_textual_deadline(raw)

        opp_id = re.sub(r"[^a-zA-Z0-9_-]+", "_", url.split("/")[-1] or url)[:64]
        tags = list(self.default_tags)
        tags.extend(tag for tag in FALLBACK_PROGRAM_EXTRA_TAGS.get(url, []) if tag)
        if deadline is None and url in FALLBACK_PROGRAM_URLS:
            tags.append("rolling")
        summary = FALLBACK_PROGRAM_SUMMARIES.get(url, "Astana Hub program")
        return Opportunity(
            source=self.slug,
            source_url=url,  # type: ignore[arg-type]
            type=OpportunityType.ACCELERATOR,
            title=title,
            summary=summary,
            deadline=deadline,
            tags=tags,
            raw={
                "external_id": opp_id,
                "snippet": raw,
                "description": summary,
                "country_scope": "Kazakhstan / Central Asia",
                "eligibility": (
                    "Check the current Astana Hub program page for applicant "
                    "requirements, dates and partner-school or startup criteria."
                ),
                "deadline_policy": (
                    "rolling"
                    if deadline is None and url in FALLBACK_PROGRAM_URLS
                    else None
                ),
            },
        )

    async def healthcheck(self) -> bool:
        try:
            resp = await self.client.get(self.base_url)
            return resp.status_code < 500
        except Exception:  # noqa: BLE001
            return False


AstanaHubParser = AstanaHubSource
