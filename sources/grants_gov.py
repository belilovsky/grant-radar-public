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
from decimal import Decimal
from typing import ClassVar, TypedDict

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
    "kazakhstan",
]

KAZAKHSTAN_AGENCY_CODES = {"DOS-KAZ"}
KAZAKHSTAN_AGENCY_NAMES = {"u.s. mission to kazakhstan"}


class CuratedGrantsGovOpportunity(TypedDict):
    summary: str
    amount_min: Decimal
    amount_max: Decimal
    tags: list[str]
    eligibility: list[str]
    application_url: str


CURATED_KAZAKHSTAN_OPPORTUNITIES: dict[str, CuratedGrantsGovOpportunity] = {
    "DOS-KAZ-ALM-PDS-26-001": {
        "summary": (
            "U.S. Mission to Kazakhstan cooperative agreement for Access Alumni "
            "Outreach and Engagement and the English Access Scholarship Program "
            "in South Kazakhstan. The 2026-2028 project targets Access alumni "
            "in Shymkent, Kyzylorda, Taraz, Turkistan and Almaty, plus new "
            "Access students from Shymkent or Taraz."
        ),
        "amount_min": Decimal("30000"),
        "amount_max": Decimal("50000"),
        "tags": [
            "kazakhstan",
            "south_kazakhstan",
            "education",
            "youth",
            "public_diplomacy",
            "cooperative_agreement",
        ],
        "eligibility": [
            "Not-for-profit organizations in Kazakhstan, including think tanks "
            "and civil society or non-governmental organizations",
            "U.S. government-sponsored program alumni associations in Kazakhstan",
        ],
        "application_url": (
            "https://simpler.grants.gov/opportunity/"
            "da9ea956-a099-4ac0-ae24-3f9b001ee9a0"
        ),
    },
    "DOS-KAZ-AST-PDS-26-003": {
        "summary": (
            "U.S. Mission to Kazakhstan cooperative agreement for administrative "
            "and programming support to eight American Spaces in Kazakhstan. The "
            "award covers coordinator stipends and benefits, outreach costs, "
            "mobile plans, branded materials and monthly programming focused on "
            "U.S. culture, education, technology and innovation."
        ),
        "amount_min": Decimal("120000"),
        "amount_max": Decimal("150000"),
        "tags": [
            "kazakhstan",
            "education",
            "youth",
            "public_diplomacy",
            "cooperative_agreement",
            "administrative_support",
            "american_spaces",
        ],
        "eligibility": [
            "Not-for-profit organizations based in Kazakhstan, including think "
            "tanks and civil society or non-governmental organizations",
            "For-profit entities are not eligible under the official notice",
        ],
        "application_url": (
            "https://simpler.grants.gov/opportunity/"
            "bea4fe72-2418-4ad1-83cd-cf6a9ee15a20"
        ),
    },
}


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
        seen: set[str] = set()
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
                self._mark_fetch_error(e)
                log.warning("grants_gov.fetch_failed", keyword=kw, error=str(e))
                continue

            data = resp.json().get("data", {})
            hits = data.get("oppHits", [])
            log.info("grants_gov.batch", keyword=kw, count=len(hits))

            for h in hits:
                opportunity_number = _opportunity_number(h)
                if opportunity_number in seen:
                    continue
                opportunity = self._to_opportunity(h, kw)
                if not _has_kazakhstan_official_signal(
                    h
                ) and not is_relevant_for_kazakhstan_focus(opportunity):
                    log.info(
                        "grants_gov.skipped_geo_mismatch",
                        keyword=kw,
                        id=h.get("id") or h.get("oppNumber", ""),
                        title=h.get("title", ""),
                    )
                    continue
                seen.add(opportunity_number)
                yield opportunity

    def _to_opportunity(self, h: dict, kw: str) -> Opportunity:
        opp_id = h.get("id") or h.get("oppNumber", "")
        opportunity_number = _opportunity_number(h)
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
        curated = CURATED_KAZAKHSTAN_OPPORTUNITIES.get(opportunity_number)
        if curated:
            summary = curated["summary"]
        deadline = None
        if cd := close_date:
            try:
                deadline = datetime.strptime(cd, "%m/%d/%Y").date()
            except ValueError:
                pass
        topic_tags = [kw.lower()] if _keyword_is_visible(kw, title, summary) else []
        curated_tags = curated["tags"] if curated else []
        return Opportunity(
            source=self.slug,
            source_url=url,  # type: ignore[arg-type]
            type=OpportunityType.GRANT,
            title=title,
            summary=summary,
            funder=agency,
            amount_min=curated["amount_min"] if curated else None,
            amount_max=curated["amount_max"] if curated else None,
            currency="USD",
            deadline=deadline,
            eligibility=curated["eligibility"] if curated else [],
            tags=list(dict.fromkeys([*self.default_tags, *topic_tags, *curated_tags])),
            raw={
                **h,
                "external_id": opportunity_number,
                "application_url": curated.get("application_url") if curated else None,
                "amount_min": str(curated["amount_min"]) if curated else None,
                "amount_max": str(curated["amount_max"]) if curated else None,
            },
        )


GrantsGovParser = GrantsGovSource


def _opportunity_number(h: dict) -> str:
    return _clean_text(h.get("oppNumber") or h.get("number") or h.get("id", ""))


def _has_kazakhstan_official_signal(h: dict) -> bool:
    agency_code = _clean_text(h.get("agencyCode", "")).upper()
    agency_name = _clean_text(h.get("agency") or h.get("agencyName", "")).lower()
    opportunity_number = _opportunity_number(h).upper()
    return (
        agency_code in KAZAKHSTAN_AGENCY_CODES
        or agency_name in KAZAKHSTAN_AGENCY_NAMES
        or opportunity_number.startswith("DOS-KAZ-")
    )
