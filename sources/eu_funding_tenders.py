"""EU Funding & Tenders calls with explicit Central Asia search evidence."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import date, datetime
from typing import Any, ClassVar
from urllib.parse import quote

import structlog

from core.models import Opportunity, OpportunityType
from sources.base import BaseSource
from sources.world_bank import _infer_tags, _unique

log = structlog.get_logger()

EU_SEARCH_API = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
EU_TOPIC_URL = (
    "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/"
    "opportunities/topic-details/{topic_id}"
)
SEARCH_TERMS = (
    "Kazakhstan",
    "Central Asia",
    "Kyrgyzstan",
    "Uzbekistan",
    "Tajikistan",
    "Turkmenistan",
)
ACTIVE_QUERY = {
    "bool": {
        "must": [
            {"terms": {"type": ["1", "2", "8"]}},
            {"terms": {"status": ["31094501", "31094502"]}},
            {"term": {"language": "en"}},
        ]
    }
}


def _first(metadata: dict[str, Any], key: str) -> str:
    value = metadata.get(key)
    if isinstance(value, list) and value:
        return str(value[0] or "").strip()
    return str(value or "").strip()


def _deadline(metadata: dict[str, Any]) -> date | None:
    raw = _first(metadata, "deadlineDate")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _topic_id(metadata: dict[str, Any]) -> str:
    return _first(metadata, "identifier") or _first(metadata, "callIdentifier")


class EuFundingTendersCentralAsiaSource(BaseSource):
    """Monitor official EU calls that mention Central Asian eligibility or scope."""

    slug = "eu_funding_tenders_ca"
    name = "EU Funding & Tenders Central Asia"
    base_url = (
        "https://ec.europa.eu/info/funding-tenders/opportunities/portal/"
        "screen/opportunities/calls-for-proposals"
    )
    default_tags: ClassVar[list[str]] = [
        "central_asia",
        "eu",
        "grant",
        "research",
        "partnership",
        "eligibility_check_required",
    ]

    async def fetch(self) -> AsyncIterator[Opportunity]:
        seen: set[str] = set()
        count = 0
        today = date.today()
        for term in SEARCH_TERMS:
            try:
                response = await self.client.post(
                    EU_SEARCH_API,
                    params={"apiKey": "SEDIA", "text": term},
                    data={"pageSize": "50", "pageNumber": "1"},
                    files={
                        "query": (
                            "query.json",
                            json.dumps(ACTIVE_QUERY),
                            "application/json",
                        )
                    },
                )
                response.raise_for_status()
                payload = response.json()
            except Exception as exc:  # noqa: BLE001
                log.warning(
                    "eu_funding_tenders.fetch_failed", term=term, error=str(exc)
                )
                continue

            results = payload.get("results")
            if not isinstance(results, list):
                continue
            for result in results:
                if not isinstance(result, dict):
                    continue
                metadata = result.get("metadata")
                if (
                    not isinstance(metadata, dict)
                    or _first(metadata, "language") != "en"
                ):
                    continue
                topic_id = _topic_id(metadata)
                title = _first(metadata, "title")
                deadline = _deadline(metadata)
                if not topic_id or not title or topic_id in seen:
                    continue
                if deadline is None or deadline < today:
                    continue
                seen.add(topic_id)
                keywords = metadata.get("keywords")
                keyword_values = (
                    [str(value) for value in keywords]
                    if isinstance(keywords, list)
                    else []
                )
                framework = _first(metadata, "frameworkProgramme")
                summary = (
                    f"Official EU call matched by the {term} monitor. "
                    "Kazakhstan and Central Asia eligibility, consortium rules and "
                    "funding conditions must be verified on the call page."
                )
                tags = _unique(
                    [
                        *self.default_tags,
                        *_infer_tags(" ".join([title, *keyword_values])),
                        "open",
                    ]
                )
                count += 1
                yield Opportunity(
                    source=self.slug,
                    source_url=EU_TOPIC_URL.format(  # type: ignore[arg-type]
                        topic_id=quote(topic_id, safe="-_")
                    ),
                    type=OpportunityType.GRANT,
                    title=title,
                    summary=summary,
                    funder="European Commission",
                    deadline=deadline,
                    tags=tags,
                    opportunity_status="open",
                    lifecycle="open",
                    raw={
                        "external_id": topic_id,
                        "identifier": topic_id,
                        "call_identifier": _first(metadata, "callIdentifier"),
                        "framework_programme": framework,
                        "matched_term": term,
                        "keywords": keyword_values[:30],
                        "source_title": title,
                        "eligibility_note": (
                            "Search match is not proof of funding eligibility; verify "
                            "the official call conditions."
                        ),
                        "i18n": {
                            "ru": {
                                "title": f"Конкурс ЕС – {topic_id}",
                                "summary": (
                                    "Открытый конкурс на официальном портале ЕС, "
                                    "найденный по тематике Казахстана и Центральной "
                                    "Азии. Проверьте на странице конкурса допустимые "
                                    "страны, роль заявителя, требования к консорциуму "
                                    "и условия финансирования."
                                ),
                            }
                        },
                        "api_url": str(response.request.url),
                    },
                )

        log.info("eu_funding_tenders.batch", count=count)


EuFundingTendersCentralAsiaParser = EuFundingTendersCentralAsiaSource
