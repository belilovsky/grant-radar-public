"""Google.org philanthropy and AI education opportunity monitor."""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from typing import ClassVar

import structlog

from core.models import Opportunity, OpportunityType
from core.source_text import clean_source_text as _clean_text
from sources.base import BaseSource

log = structlog.get_logger()

GOOGLE_ORG_KNOWLEDGE_URL = (
    "https://www.google.org/intl/en_us/knowledge-skills-and-learning/"
)


def _html_title(html: str) -> str | None:
    match = re.search(
        r"<title[^>]*>(?P<title>.*?)</title>", html, re.IGNORECASE | re.DOTALL
    )
    if match is None:
        return None
    return _clean_text(match.group("title")) or None


class GoogleOrgAiOpportunitySource(BaseSource):
    slug = "google_org_ai_opportunity"
    name = "Google.org AI Opportunity Fund"
    base_url = GOOGLE_ORG_KNOWLEDGE_URL
    default_tags: ClassVar[list[str]] = [
        "global",
        "central_asia_eligible",
        "ai",
        "education",
        "digital_skills",
        "nonprofit_required",
        "partnership",
        "rolling",
    ]

    async def fetch(self) -> AsyncIterator[Opportunity]:
        try:
            response = await self.client.get(GOOGLE_ORG_KNOWLEDGE_URL)
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "google_org_ai_opportunity.fetch_failed",
                url=GOOGLE_ORG_KNOWLEDGE_URL,
                error=str(exc),
            )
            return

        yield Opportunity(
            source=self.slug,
            source_url=GOOGLE_ORG_KNOWLEDGE_URL,  # type: ignore[arg-type]
            type=OpportunityType.GRANT,
            title="Google.org global AI Opportunity Fund and AI literacy grants",
            summary=(
                "Google.org AI and education philanthropy watch for nonprofit, "
                "government, and academic partners. The page tracks global AI "
                "skills, learning, workforce readiness, and education initiatives "
                "that may become partner-led grant or program opportunities for "
                "Central Asia projects."
            ),
            funder="Google.org",
            eligibility=["global", "nonprofit", "education_partner"],
            tags=self.default_tags,
            raw={
                "external_id": self.slug,
                "page_title": _html_title(response.text),
                "status_code": response.status_code,
                "program_url": GOOGLE_ORG_KNOWLEDGE_URL,
                "deadline_policy": "rolling",
            },
        )


GoogleOrgAiOpportunityParser = GoogleOrgAiOpportunitySource
