"""Official global training opportunities relevant to Kazakhstan applicants."""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import date

import httpx
import structlog

from core.models import Opportunity, OpportunityType
from core.source_text import clean_source_text
from sources.base import BaseSource

log = structlog.get_logger()


@dataclass(frozen=True)
class GlobalTrainingProgram:
    url: str
    title: str
    summary: str
    title_ru: str
    summary_ru: str
    funder: str
    deadline: date
    tags: tuple[str, ...]
    eligibility: tuple[str, ...]
    amount_raw: str
    application_url: str


PROGRAMS = (
    GlobalTrainingProgram(
        url=(
            "https://gpad.hiroshima-u.ac.jp/"
            "fy2026-mid-career-course-%E2%80%95call-for-applicants/"
        ),
        title="FY2026 Mid-Career Course for peacebuilding and development professionals",
        summary=(
            "Official Hiroshima University GPAD call for the FY2026 Mid-Career "
            "Course, implemented with UNITAR Hiroshima for mid-level "
            "professionals in peacebuilding and international development. "
            "The in-person course runs in Japan from 7 to 13 January 2027; "
            "applications are accepted until 31 August 2026 at 5:00 PM Japan time."
        ),
        title_ru=(
            "FY2026 Mid-Career Course для специалистов по миростроительству "
            "и развитию"
        ),
        summary_ru=(
            "Официальный конкурс Hiroshima University GPAD на курс FY2026 "
            "Mid-Career Course, который проводится совместно с UNITAR Hiroshima "
            "для специалистов среднего уровня в миростроительстве и международном "
            "развитии. Очная программа пройдёт в Японии 7–13 января 2027 года; "
            "заявки принимаются до 31 августа 2026 года, 17:00 по японскому времени."
        ),
        funder="Hiroshima University GPAD / UNITAR Hiroshima",
        deadline=date(2026, 8, 31),
        tags=(
            "global",
            "international",
            "japan",
            "unitar",
            "fellowship",
            "education",
            "capacity_building",
            "professional_development",
            "peacebuilding",
            "international_development",
        ),
        eligibility=(
            "Applicants from diverse countries with at least seven years of "
            "professional experience in peacebuilding or international development, "
            "fluency in English and availability for the full course",
        ),
        amount_raw=(
            "no participation fee; for non-Japanese participants the programme "
            "covers Tokyo-Higashi-Hiroshima transport and accommodation during "
            "training, while travel to and from Japan, food and personal expenses "
            "are not covered"
        ),
        application_url="mailto:gpad-midcareer@office.hiroshima-u.ac.jp",
    ),
)


def _html_title(html: str) -> str | None:
    match = re.search(
        r"<title[^>]*>(?P<title>.*?)</title>", html, re.IGNORECASE | re.DOTALL
    )
    if match is None:
        return None
    return clean_source_text(match.group("title")) or None


class GlobalTrainingOpportunitiesSource(BaseSource):
    slug = "global_training_opportunities"
    name = "Global Training Opportunities"
    base_url = "https://gpad.hiroshima-u.ac.jp/"

    async def fetch(self) -> AsyncIterator[Opportunity]:
        count = 0
        for program in PROGRAMS:
            page_title: str | None = None
            status_code: int | None = None
            try:
                response = await self.client.get(program.url)
                status_code = response.status_code
                response.raise_for_status()
                page_title = _html_title(response.text)
            except httpx.HTTPError as exc:
                log.warning(
                    "global_training.fetch_failed",
                    url=program.url,
                    error=str(exc),
                )
                continue

            count += 1
            yield Opportunity(
                source=self.slug,
                source_url=program.url,  # type: ignore[arg-type]
                type=OpportunityType.FELLOWSHIP,
                title=program.title,
                summary=program.summary,
                funder=program.funder,
                deadline=program.deadline,
                eligibility=list(program.eligibility),
                tags=["official_source", *program.tags],
                opportunity_status="open",
                lifecycle="open",
                raw={
                    "external_id": program.url,
                    "page_title": page_title,
                    "status_code": status_code,
                    "amount_raw": program.amount_raw,
                    "application_url": program.application_url,
                    "deadline": program.deadline.isoformat(),
                    "opportunity_status": "open",
                    "lifecycle": "open",
                    "i18n": {
                        "ru": {
                            "title": program.title_ru,
                            "summary": program.summary_ru,
                        },
                        "en": {
                            "title": program.title,
                            "summary": program.summary,
                        },
                    },
                },
            )

        log.info("global_training.batch", count=count)


GlobalTrainingOpportunitiesParser = GlobalTrainingOpportunitiesSource
