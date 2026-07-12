"""RSS-backed opportunity sources.

These adapters intentionally keep the parser small and conservative. RSS feeds
are useful as a production bridge while higher-value first-party integrations
are added one by one.
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Any

import feedparser
import structlog

from core.models import Opportunity, OpportunityType
from sources.base import BaseSource

log = structlog.get_logger()

OPPORTUNITY_DESK_FEED_URL = "https://www.opportunitydesk.org/feed/"
FUNDSFORNGOS_FEED_URLS = (
    "https://www2.fundsforngos.org/category/latest-funds-for-ngos/feed/",
    "https://www2.fundsforngos.org/category/education/feed/",
    "https://www2.fundsforngos.org/category/media/feed/",
    "https://www2.fundsforngos.org/category/agriculture/feed/",
    "https://www2.fundsforngos.org/category/environment/feed/",
    "https://www2.fundsforngos.org/category/climate-change/feed/",
    "https://www2.fundsforngos.org/category/animal-welfare/feed/",
)

DEADLINE_PATTERNS = (
    re.compile(
        r"(?:deadline|apply by|closes?|closing date)\s*[:\u2014–-]?\s*"
        r"(?P<d>\d{1,2})\s+(?P<m>jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
        r"[a-z]*\s+(?P<y>\d{4})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:deadline|apply by|closes?|closing date)\s*[:\u2014–-]?\s*"
        r"(?P<m>jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
        r"\s+(?P<d>\d{1,2}),?\s+(?P<y>\d{4})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:deadline|apply by|closes?|closing date)\s*[:\u2014–-]?\s*"
        r"(?P<d>\d{1,2})[-./](?P<m>jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
        r"[a-z]*[-./](?P<y>\d{4})",
        re.IGNORECASE,
    ),
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
THEME_KEYWORDS = {
    "ai": ("ai", "artificial intelligence", "machine learning", "data science"),
    "edtech": ("education", "edtech", "school", "teacher", "student", "learning"),
    "govtech": ("government", "governance", "public sector", "civic", "digital public"),
    "agrotech": (
        "agriculture",
        "agritech",
        "food systems",
        "farming",
        "irrigation",
        "livestock",
    ),
    "vettech": ("veterinary", "animal health", "livestock health", "zoonotic"),
    "ecotech": (
        "ecotech",
        "climate",
        "environment",
        "cleantech",
        "renewable",
        "biodiversity",
        "waste",
        "water",
    ),
    "media": ("media", "journalism", "newsroom", "misinformation", "press"),
    "digital_skills": ("digital skills", "coding", "stem", "technology", "innovation"),
    "startup": ("startup", "entrepreneur", "founder", "accelerator", "incubator"),
    "central_asia": (
        "kazakhstan",
        "uzbekistan",
        "kyrgyzstan",
        "tajikistan",
        "turkmenistan",
        "central asia",
    ),
}


@dataclass(frozen=True)
class FeedConfig:
    url: str
    tags: tuple[str, ...]


def _clean_text(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", unescape(without_tags)).strip()


def _clean_summary(value: str) -> str:
    text = _clean_text(value)
    for marker in (" The post ", " first appeared on "):
        if marker in text:
            text = text.split(marker, 1)[0].strip()
    return text


def _entry_categories(entry: Any) -> list[str]:
    out: list[str] = []
    for tag in entry.get("tags", []) or []:
        term = tag.get("term") if isinstance(tag, dict) else getattr(tag, "term", "")
        if term:
            out.append(str(term).strip().lower().replace(" ", "_"))
    return out


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


def _infer_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags: list[str] = []
    for tag, keywords in THEME_KEYWORDS.items():
        if any(_contains_term(lowered, keyword) for keyword in keywords):
            tags.append(tag)
    return tags


def _contains_term(text: str, keyword: str) -> bool:
    text = text.lower()
    normalized_keyword = re.escape(keyword.lower()).replace(r"\ ", r"[\s_-]+")
    pattern = rf"(?<![a-z0-9]){normalized_keyword}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def _infer_type(text: str, fallback: OpportunityType) -> OpportunityType:
    lowered = text.lower()
    if "fellowship" in lowered:
        return OpportunityType.FELLOWSHIP
    if "accelerator" in lowered or "incubator" in lowered:
        return OpportunityType.ACCELERATOR
    if any(word in lowered for word in ("competition", "challenge", "award", "prize")):
        return OpportunityType.CONTEST
    if any(word in lowered for word in ("grant", "fund", "funding")):
        return OpportunityType.GRANT
    return fallback


def _parse_deadline(text: str) -> date | None:
    for pattern in DEADLINE_PATTERNS:
        match = pattern.search(text)
        if match is None:
            continue
        try:
            day = int(match.group("d"))
            month = MONTHS[match.group("m").lower()[:3]]
            year = int(match.group("y"))
            return datetime(year, month, day).date()
        except (KeyError, ValueError):
            continue
    return None


def _parse_published(entry: Any) -> str | None:
    value = entry.get("published") or entry.get("updated")
    if not value:
        return None
    try:
        return parsedate_to_datetime(str(value)).isoformat()
    except (TypeError, ValueError):
        return str(value)


def _is_roundup_post(*, title: str, summary: str, categories: Iterable[str]) -> bool:
    normalized_title = title.lower().strip()
    normalized_summary = summary.lower().strip()
    normalized_categories = {value.strip().lower() for value in categories}
    if re.match(r"^\d+\s+opportunities?\b", normalized_title):
        return True
    if "currently open" in normalized_title and "opportunit" in normalized_title:
        return True
    if "our_blog" in normalized_categories and "opportunit" in normalized_title:
        return True
    if normalized_summary.startswith("here are"):
        return True
    return False


class RssFeedSource(BaseSource):
    feed_configs: tuple[FeedConfig, ...] = ()
    default_type = OpportunityType.GRANT
    entry_keywords: tuple[str, ...] = ()

    async def fetch(self) -> AsyncIterator[Opportunity]:
        seen: set[str] = set()
        count = 0
        for config in self.feed_configs:
            try:
                response = await self.client.get(config.url)
                response.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                log.warning("rss_feed.fetch_failed", source=self.slug, error=str(exc))
                continue

            parsed = feedparser.parse(response.text)
            for entry in parsed.entries[:40]:
                link = str(entry.get("link") or "").strip()
                title = _clean_text(str(entry.get("title") or ""))
                if not link or not title or link in seen:
                    continue
                seen.add(link)

                summary = _clean_summary(
                    str(entry.get("summary") or entry.get("description") or "")
                )
                categories = _entry_categories(entry)
                text = " ".join([title, summary])
                if self.entry_keywords and not any(
                    _contains_term(text, keyword) for keyword in self.entry_keywords
                ):
                    continue
                if _is_roundup_post(
                    title=title,
                    summary=summary,
                    categories=categories,
                ):
                    continue
                tags = _unique(
                    [
                        *self.default_tags,
                        *config.tags,
                        *_infer_tags(text),
                    ]
                )
                count += 1
                yield Opportunity(
                    source=self.slug,
                    source_url=link,  # type: ignore[arg-type]
                    type=_infer_type(text, self.default_type),
                    title=title,
                    summary=summary,
                    deadline=_parse_deadline(text),
                    tags=tags,
                    raw={
                        "external_id": str(entry.get("id") or link),
                        "feed": config.url,
                        "published": _parse_published(entry),
                        "categories": categories[:50],
                    },
                )

        log.info("rss_feed.batch", source=self.slug, count=count)


class OpportunityDeskSource(RssFeedSource):
    slug = "opportunity_desk"
    name = "Opportunity Desk"
    base_url = "https://www.opportunitydesk.org"
    default_tags = ["global", "opportunity_desk", "grant", "fellowship"]
    default_type = OpportunityType.CONTEST
    entry_keywords = (
        "accelerator",
        "award",
        "challenge",
        "competition",
        "fellowship",
        "funding",
        "grant",
        "prize",
        "program",
        "scholarship",
    )
    feed_configs = (
        FeedConfig(
            url=OPPORTUNITY_DESK_FEED_URL,
            tags=("global", "fellowship", "contest"),
        ),
    )


class FundsForNgosSource(RssFeedSource):
    slug = "fundsforngos"
    name = "FundsforNGOs"
    base_url = "https://www2.fundsforngos.org"
    default_tags = ["global", "ngo", "grant", "donor"]
    feed_configs = (
        FeedConfig(
            url=FUNDSFORNGOS_FEED_URLS[0],
            tags=("ngo", "grant"),
        ),
        FeedConfig(
            url=FUNDSFORNGOS_FEED_URLS[1],
            tags=("ngo", "grant", "education", "edtech"),
        ),
        FeedConfig(
            url=FUNDSFORNGOS_FEED_URLS[2],
            tags=("ngo", "grant", "media", "journalism"),
        ),
        FeedConfig(
            url=FUNDSFORNGOS_FEED_URLS[3],
            tags=("ngo", "grant", "agriculture", "agrotech"),
        ),
        FeedConfig(
            url=FUNDSFORNGOS_FEED_URLS[4],
            tags=("ngo", "grant", "environment", "ecotech"),
        ),
        FeedConfig(
            url=FUNDSFORNGOS_FEED_URLS[5],
            tags=("ngo", "grant", "climate", "ecotech"),
        ),
        FeedConfig(
            url=FUNDSFORNGOS_FEED_URLS[6],
            tags=("ngo", "grant", "animal_health", "vettech"),
        ),
    )


OpportunityDeskParser = OpportunityDeskSource
FundsForNgosParser = FundsForNgosSource
