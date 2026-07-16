"""grants.gov – выборка открытых grant opportunities.

Использует публичный search REST endpoint:
  POST https://api.grants.gov/v1/api/search2
фильтруем по ключевым словам (AI, media, education, governance, agrotech,
vettech, ecotech).
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from datetime import datetime
from typing import ClassVar

import structlog

from core.geofit import is_relevant_for_kazakhstan_focus
from core.models import Opportunity, OpportunityType
from core.source_text import clean_plain_source_text as _clean_text
from sources.base import BaseSource

log = structlog.get_logger()

SEARCH_URL = "https://api.grants.gov/v1/api/search2"
KEYWORDS = [
    "artificial intelligence",
    "media",
    "education",
    "governance",
    "open data",
    "agriculture",
    "veterinary",
    "environment",
    "climate",
]


def _keyword_is_visible(keyword: str, *values: str) -> bool:
    """Only expose a search keyword as a topic when public copy supports it."""

    normalized = re.escape(keyword.strip().lower()).replace(r"\ ", r"[\s_-]+")
    if not normalized:
        return False
    pattern = rf"(?<![a-z0-9]){normalized}(?![a-z0-9])"
    return any(re.search(pattern, value.lower()) for value in values if value)


class GrantsGovSource(BaseSource):
    slug = "grants_gov"
    name = "Grants.gov (US Federal)"
    base_url = "https://www.grants.gov"
    default_tags: ClassVar[list[str]] = ["us", "federal", "grant"]

    async def fetch(self) -> AsyncIterator[Opportunity]:
        for kw in KEYWORDS:
            payload = {
                "keyword": kw,
                "oppStatuses": "forecasted|posted",
                "rows": 50,
                "sortBy": "openDate|desc",
            }
            try:
                resp = await self.client.post(SEARCH_URL, json=payload)
                resp.raise_for_status()
            except Exception as e:
                log.warning("grants_gov.fetch_failed", keyword=kw, error=str(e))
                continue

            data = resp.json().get("data", {})
            hits = data.get("oppHits", [])
            log.info("grants_gov.batch", keyword=kw, count=len(hits))

            for h in hits:
                opportunity = self._to_opportunity(h, kw)
                if not is_relevant_for_kazakhstan_focus(opportunity):
                    log.info(
                        "grants_gov.skipped_geo_mismatch",
                        keyword=kw,
                        id=h.get("id") or h.get("oppNumber", ""),
                        title=h.get("title", ""),
                    )
                    continue
                yield opportunity

    def _to_opportunity(self, h: dict, kw: str) -> Opportunity:
        opp_id = h.get("id") or h.get("oppNumber", "")
        url = f"https://www.grants.gov/search-results-detail/{opp_id}"
        agency = _clean_text(
            h.get("agencyName") or h.get("agency") or h.get("agencyCode")
        )
        close_date = h.get("closeDate")
        title = _clean_text(h.get("title", ""))
        summary = _clean_text(h.get("description", "") or h.get("synopsis", ""))
        if not summary:
            parts = ["Grants.gov opportunity"]
            if agency:
                parts.append(f"from {agency}")
            if close_date:
                parts.append(f"closing {close_date}")
            summary = " ".join(parts) + "."
        deadline = None
        if cd := close_date:
            try:
                deadline = datetime.strptime(cd, "%m/%d/%Y").date()
            except ValueError:
                pass
        topic_tags = [kw] if _keyword_is_visible(kw, title, summary) else []
        return Opportunity(
            source=self.slug,
            source_url=url,  # type: ignore[arg-type]
            type=OpportunityType.GRANT,
            title=title,
            summary=summary,
            funder=agency,
            deadline=deadline,
            tags=[*self.default_tags, *topic_tags],
            raw=h,
        )


GrantsGovParser = GrantsGovSource
