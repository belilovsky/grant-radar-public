"""Canada Fund for Local Initiatives annual Central Asia call monitor."""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from datetime import date
from decimal import Decimal
from typing import ClassVar
from urllib.parse import urljoin

import structlog
from bs4 import BeautifulSoup

from core.models import Opportunity, OpportunityType
from sources.base import BaseSource

log = structlog.get_logger()

CFLI_INDEX_URL = (
    "https://www.international.gc.ca/world-monde/funding-financement/"
    "cfli-fcil/index.aspx?lang=eng"
)
TARGET_COUNTRIES = {
    "kazakhstan",
    "kyrgyzstan",
    "tajikistan",
    "turkmenistan",
    "uzbekistan",
}


def _date_from_text(value: str) -> date | None:
    match = re.search(
        r"\b(?P<year>20\d{2})-(?P<month>\d{1,2})-(?P<day>\d{1,2})\b", value
    )
    if match is None:
        return None
    try:
        return date(
            int(match.group("year")),
            int(match.group("month")),
            int(match.group("day")),
        )
    except ValueError:
        return None


class CanadaCfliCentralAsiaSource(BaseSource):
    """Yield the regional CFLI call only while the official table marks it open."""

    slug = "canada_cfli_ca"
    name = "Canada Fund for Local Initiatives Central Asia"
    base_url = CFLI_INDEX_URL
    default_tags: ClassVar[list[str]] = [
        "central_asia",
        "grant",
        "ngo",
        "civil_society",
        "climate",
        "governance",
        "canada",
    ]

    async def fetch(self) -> AsyncIterator[Opportunity]:
        try:
            response = await self.client.get(CFLI_INDEX_URL)
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            log.warning("canada_cfli.fetch_failed", error=str(exc))
            return

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.select_one("#dataset-filter1")
        if table is None:
            return

        open_countries: list[str] = []
        deadlines: list[date] = []
        detail_url = ""
        raw_deadlines: list[str] = []
        for row in table.select("tbody tr"):
            cells = row.find_all("td")
            if len(cells) < 3:
                continue
            country = cells[0].get_text(" ", strip=True)
            if country.lower() not in TARGET_COUNTRIES:
                continue
            status_text = cells[1].get_text(" ", strip=True).lower()
            deadline_text = cells[2].get_text(" ", strip=True)
            deadline = _date_from_text(deadline_text)
            if status_text != "open" or deadline is None or deadline < date.today():
                continue
            link = cells[0].find("a", href=True)
            if link is not None:
                detail_url = urljoin(CFLI_INDEX_URL, str(link["href"]))
            open_countries.append(country)
            deadlines.append(deadline)
            raw_deadlines.append(deadline_text)

        if not open_countries or not detail_url:
            return

        deadline = min(deadlines)
        yield Opportunity(
            source=self.slug,
            source_url=detail_url,  # type: ignore[arg-type]
            type=OpportunityType.GRANT,
            title="Canada Fund for Local Initiatives - Central Asia",
            summary=(
                "Annual small-grants call for locally designed, high-impact projects "
                "in Kazakhstan and other Central Asian countries. Verify the current "
                "themes, applicant rules and submission process on the official page."
            ),
            funder="Global Affairs Canada",
            amount_max=Decimal("100000"),
            currency="CAD",
            deadline=deadline,
            eligibility=["local NGO", "nonprofit", "public institution"],
            tags=[*self.default_tags, "open"],
            opportunity_status="open",
            lifecycle="open",
            raw={
                "external_id": f"cfli-central-asia-{deadline.year}",
                "countries": open_countries,
                "deadline_labels": raw_deadlines,
                "index_url": CFLI_INDEX_URL,
                "source_title": "Canada Fund for Local Initiatives - Central Asia",
                "i18n": {
                    "ru": {
                        "title": "Канадский фонд местных инициатив – Центральная Азия",
                        "summary": (
                            "Ежегодный конкурс малых грантов для локальных проектов "
                            "с измеримым общественным результатом в странах "
                            "Центральной Азии. Актуальные темы, требования к "
                            "заявителям и порядок подачи необходимо сверить на "
                            "официальной странице."
                        ),
                    }
                },
            },
        )


CanadaCfliCentralAsiaParser = CanadaCfliCentralAsiaSource
