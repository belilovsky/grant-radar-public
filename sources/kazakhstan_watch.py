"""Curated Kazakhstan/Central Asia watch pages.

This source is a production bridge for high-value donor, procurement, and
grant pages that do not yet have stable item-level APIs in this project.
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from typing import Any

import httpx
import structlog

from core.models import Opportunity, OpportunityType
from core.source_text import clean_plain_source_text as _clean_text
from sources.base import BaseSource

log = structlog.get_logger()


@dataclass(frozen=True)
class WatchPage:
    url: str
    title: str
    summary: str
    tags: tuple[str, ...]
    type: OpportunityType
    rolling: bool = False
    retain_on_fetch_error: bool = False
    title_ru: str = ""
    summary_ru: str = ""


WATCH_PAGES = (
    WatchPage(
        url="https://kz.usembassy.gov/education-culture/grants/",
        title="U.S. Embassy Kazakhstan grants",
        summary=(
            "Small grants and public-diplomacy opportunities for Kazakhstan. Review "
            "official eligibility, deadlines, themes and application terms on the Embassy page."
        ),
        tags=("grant", "public_diplomacy", "education"),
        type=OpportunityType.GRANT,
        rolling=True,
        title_ru="Гранты Посольства США в Казахстане",
        summary_ru=(
            "Малые гранты и возможности общественной дипломатии для Казахстана. "
            "Перед подачей проверьте на странице Посольства требования, темы, сроки "
            "и порядок оформления заявки."
        ),
    ),
    WatchPage(
        url="https://www.ebrd.com/kazakhstan.html",
        title="EBRD Kazakhstan",
        summary=(
            "EBRD Kazakhstan investment, advisory and SME support context. Review "
            "current financing, consulting and eligibility routes on the official page."
        ),
        tags=("grant", "startup", "sme", "development"),
        type=OpportunityType.GRANT,
        rolling=True,
    ),
    WatchPage(
        url="https://www.ebrd.com/work-with-us/advice-for-small-businesses/kazakhstan.html",
        title="EBRD Kazakhstan SME advice and access to finance",
        summary=(
            "EBRD support paths for startups, SMEs and business advisory services in "
            "Kazakhstan. Review the official route for current eligibility and contacts."
        ),
        tags=("grant", "startup", "sme", "business_support"),
        type=OpportunityType.GRANT,
        rolling=True,
    ),
    WatchPage(
        url="https://kazakhstan.britishcouncil.org/programmes/education/going-global-partnerships",
        title="British Council Kazakhstan Going Global Partnerships",
        summary=(
            "Higher-education partnership and small-grant route for UK-Kazakhstan "
            "university collaboration and transnational education work."
        ),
        tags=("grant", "education", "partnership", "higher_education"),
        type=OpportunityType.GRANT,
        rolling=True,
    ),
    WatchPage(
        url="https://kazakhstan.britishcouncil.org/programmes/arts/connections-through-culture",
        title="British Council Connections Through Culture Grants Kazakhstan",
        summary=(
            "Creative collaboration grants that include Kazakhstan and can support "
            "digital culture, inclusion, climate and education-adjacent projects."
        ),
        tags=("grant", "creative_industries", "partnership", "culture"),
        type=OpportunityType.GRANT,
        rolling=True,
    ),
    WatchPage(
        url="https://kazakhstan.britishcouncil.org/newton-al-farabi",
        title="Newton - Al-Farabi Partnership Programme",
        summary=(
            "Research, innovation and professional-development partnership track "
            "between the UK and Kazakhstan."
        ),
        tags=("grant", "research", "innovation", "higher_education"),
        type=OpportunityType.GRANT,
        rolling=True,
    ),
)

ACTIVE_WATCH_URLS = frozenset(page.url for page in WATCH_PAGES)


def _html_title(html: str) -> str | None:
    match = re.search(
        r"<title[^>]*>(?P<title>.*?)</title>", html, re.IGNORECASE | re.DOTALL
    )
    if match is None:
        return None
    return _clean_text(re.sub(r"<[^>]+>", " ", match.group("title")))


def _is_unavailable_page(html: str) -> bool:
    title = (_html_title(html) or "").lower()
    text = _clean_text(re.sub(r"<[^>]+>", " ", html)).lower()
    return "technical difficulties" in title or (
        "experiencing technical difficulties" in text and "please try again" in text
    )


def _is_blocked_fetch(status_code: int, page_title: str | None) -> bool:
    title = (page_title or "").strip().lower()
    return status_code in {401, 403, 429} or title in {
        "access denied",
        "403 forbidden",
        "too many requests",
    }


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


def _page_tags(page: WatchPage, default_tags: Iterable[str]) -> list[str]:
    tags = [*default_tags, *page.tags]
    if page.rolling:
        tags.append("rolling")
    return _unique(tags)


class KazakhstanWatchSource(BaseSource):
    slug = "kazakhstan_watch"
    name = "Kazakhstan opportunity watch"
    base_url = "https://qaz.fund/"
    default_tags = ["kazakhstan", "central_asia", "watchlist"]
    pages = WATCH_PAGES

    def _opportunity(
        self,
        page: WatchPage,
        *,
        raw: dict[str, Any],
    ) -> Opportunity:
        raw_payload = dict(raw)
        if page.title_ru or page.summary_ru:
            i18n = raw_payload.get("i18n")
            localized = dict(i18n) if isinstance(i18n, dict) else {}
            ru = localized.get("ru")
            ru_payload = dict(ru) if isinstance(ru, dict) else {}
            if page.title_ru:
                ru_payload["title"] = page.title_ru
            if page.summary_ru:
                ru_payload["summary"] = page.summary_ru
            localized["ru"] = ru_payload
            raw_payload["i18n"] = localized

        return Opportunity(
            source=self.slug,
            source_url=page.url,  # type: ignore[arg-type]
            type=page.type,
            title=page.title,
            summary=page.summary,
            tags=_page_tags(page, self.default_tags),
            raw=raw_payload,
        )

    async def fetch(self) -> AsyncIterator[Opportunity]:
        count = 0
        for page in self.pages:
            try:
                response = await self.client.get(page.url)
                if response.status_code == 404 or response.status_code >= 500:
                    response.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                if page.retain_on_fetch_error and not isinstance(
                    exc, httpx.HTTPStatusError
                ):
                    log.info(
                        "kazakhstan_watch.fetch_retained",
                        url=page.url,
                        reason=type(exc).__name__,
                    )
                    count += 1
                    yield self._opportunity(
                        page,
                        raw={
                            "external_id": page.url,
                            "page_title": page.title,
                            "status_code": None,
                            "deadline_policy": "rolling" if page.rolling else None,
                            "status_note": (
                                "official curated page retained; automated fetch "
                                f"failed with {type(exc).__name__}"
                            ),
                        },
                    )
                    continue
                log.warning(
                    "kazakhstan_watch.fetch_failed",
                    url=page.url,
                    error=repr(exc),
                )
                continue
            if _is_unavailable_page(response.text):
                log.info("kazakhstan_watch.unavailable_page", url=page.url)
                continue

            page_title = _html_title(response.text)
            raw = {
                "external_id": page.url,
                "page_title": page_title,
                "status_code": response.status_code,
                "deadline_policy": "rolling" if page.rolling else None,
            }
            if _is_blocked_fetch(response.status_code, page_title):
                raw.update(
                    {
                        "page_title": page.title,
                        "status_note": (
                            "official curated page retained; automated fetch "
                            "was blocked or rate limited"
                        ),
                    }
                )

            count += 1
            yield self._opportunity(page, raw=raw)

        log.info("kazakhstan_watch.batch", count=count)


KazakhstanWatchParser = KazakhstanWatchSource
WATCH_PAGE_BY_URL = {page.url: page for page in WATCH_PAGES}
WATCH_PAGE_TAGS = {
    page.url: _page_tags(page, KazakhstanWatchSource.default_tags)
    for page in WATCH_PAGES
}
