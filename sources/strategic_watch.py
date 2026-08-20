"""Strategic official watch sources for high-value opportunity portals.

These adapters intentionally publish page-level monitored entry points, not
scraped application records. They are used for official portals where item-level
APIs either require a separate integration pass or where the source is valuable
as a recurring funding/procurement watch surface.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import ClassVar

import httpx
import structlog

from core.models import Opportunity, OpportunityType
from core.source_text import clean_source_text as _clean_text
from sources.base import BaseSource
from sources.parsing import html_title as _shared_html_title
from sources.parsing import unique_normalized as _unique

log = structlog.get_logger()


@dataclass(frozen=True)
class StrategicWatchSpec:
    slug: str
    name: str
    url: str
    title: str
    summary: str
    title_ru: str
    summary_ru: str
    funder: str
    type: OpportunityType
    eligibility: tuple[str, ...]
    tags: tuple[str, ...]
    lifecycle: str = "forecast"
    opportunity_status: str = "upcoming"
    blocked_ok: bool = False


STRATEGIC_WATCH_SPECS = {
    "ungm_opportunities": StrategicWatchSpec(
        slug="ungm_opportunities",
        name="UNGM procurement and partner calls",
        url="https://www.ungm.org/Public/Notice",
        title="UNGM procurement, grant-support and implementing-partner calls",
        summary=(
            "Official UN Global Marketplace opportunity surface. It exposes "
            "procurement notices, requests for proposals, grant-support calls, "
            "consultant calls and implementing-partner calls that can be filtered "
            "by beneficiary country, organization and opportunity type."
        ),
        title_ru="Закупки ООН, грантовые конкурсы и поиск партнёров",
        summary_ru=(
            "Официальный каталог Глобального рынка ООН: закупки, запросы "
            "предложений, грантовые конкурсы, услуги консультантов и поиск "
            "партнёров-исполнителей. Отбор доступен по стране, организации "
            "и виду возможности."
        ),
        funder="United Nations Global Marketplace",
        type=OpportunityType.TENDER,
        eligibility=("kazakhstan", "central_asia", "supplier_or_partner"),
        tags=(
            "un",
            "procurement",
            "rfp",
            "grant_support",
            "implementing_partner",
            "consulting",
            "central_asia",
        ),
    ),
    "osce_procurement": StrategicWatchSpec(
        slug="osce_procurement",
        name="OSCE open tenders",
        url="https://procurement.osce.org/tenders",
        title="OSCE open tenders and implementing-partner opportunities",
        summary=(
            "Official OSCE procurement surface with open tenders, RFPs, EOIs and "
            "office-level filters. It is relevant for Central Asia programme "
            "offices, research, training, civic technology and implementation "
            "partner routes."
        ),
        title_ru="Открытые тендеры и конкурсы для партнёров ОБСЕ",
        summary_ru=(
            "Официальный портал закупок ОБСЕ с тендерами, запросами предложений "
            "и выражениями заинтересованности. Для Казахстана и Центральной "
            "Азии здесь публикуются закупки, исследования, обучение, цифровые "
            "проекты и услуги исполнителей."
        ),
        funder="OSCE",
        type=OpportunityType.TENDER,
        eligibility=("kazakhstan", "central_asia", "supplier_or_partner"),
        tags=("osce", "procurement", "rfp", "eoi", "civic", "central_asia"),
    ),
    "iom_kazakhstan_procurement": StrategicWatchSpec(
        slug="iom_kazakhstan_procurement",
        name="IOM Kazakhstan procurement opportunities",
        url="https://kazakhstan.iom.int/procurement-opportunities",
        title="IOM Kazakhstan procurement and service opportunities",
        summary=(
            "Official IOM Kazakhstan procurement entry point for supplier, "
            "consulting, research, training and service opportunities. Some "
            "edge requests may be blocked by the source CDN, so QAZ.FUND keeps "
            "the official URL and explicit source status."
        ),
        title_ru="Закупки и услуги МОМ в Казахстане",
        summary_ru=(
            "Официальный раздел МОМ в Казахстане с закупками и конкурсами для "
            "поставщиков, консультантов, исследователей, учебных организаций "
            "и сервисных компаний."
        ),
        funder="IOM Kazakhstan",
        type=OpportunityType.TENDER,
        eligibility=("kazakhstan", "supplier_or_consultant"),
        tags=("iom", "procurement", "migration", "consulting", "kazakhstan"),
        blocked_ok=True,
    ),
    "edb_procurement": StrategicWatchSpec(
        slug="edb_procurement",
        name="Eurasian Development Bank procurement",
        url="https://eabr.org/en/procurement/",
        title="Eurasian Development Bank procurement and notices",
        summary=(
            "Official EDB procurement and notices page. It is relevant for "
            "Kazakhstan-based suppliers, consultants and regional development "
            "projects, including technical assistance and digital initiatives."
        ),
        title_ru="Закупки и объявления Евразийского банка развития",
        summary_ru=(
            "Официальный раздел закупок ЕАБР для поставщиков и консультантов. "
            "Здесь публикуются задания по региональным проектам развития, "
            "технической помощи и цифровизации."
        ),
        funder="Eurasian Development Bank",
        type=OpportunityType.TENDER,
        eligibility=("kazakhstan", "regional_supplier_or_consultant"),
        tags=("edb", "procurement", "consulting", "development", "kazakhstan"),
    ),
    "daad_central_asia": StrategicWatchSpec(
        slug="daad_central_asia",
        name="DAAD Central Asia funding",
        url="https://www.daad-kyrgyzstan.org/en/find-funding/",
        title="DAAD Central Asia scholarships and research funding",
        summary=(
            "DAAD Central Asia funding entry point for students, graduates, "
            "postdocs, researchers and alumni from Kazakhstan, Kyrgyzstan, "
            "Tajikistan and Uzbekistan."
        ),
        title_ru="Стипендии и финансирование исследований DAAD для Центральной Азии",
        summary_ru=(
            "Официальный раздел DAAD для студентов, выпускников, аспирантов, "
            "исследователей и преподавателей из Казахстана и других стран "
            "Центральной Азии."
        ),
        funder="DAAD Central Asia",
        type=OpportunityType.FELLOWSHIP,
        eligibility=("kazakhstan", "kyrgyzstan", "tajikistan", "uzbekistan"),
        tags=(
            "daad",
            "scholarship",
            "fellowship",
            "research",
            "higher_education",
            "central_asia",
        ),
    ),
    "gef_sgp_kazakhstan": StrategicWatchSpec(
        slug="gef_sgp_kazakhstan",
        name="GEF Small Grants Programme Kazakhstan",
        url=(
            "https://www.undp.org/kazakhstan/projects/"
            "seventh-operational-phase-gef-small-grants-programme-kazakhstan"
        ),
        title="GEF Small Grants Programme in Kazakhstan",
        summary=(
            "Official UNDP Kazakhstan project page for the GEF Small Grants "
            "Programme. It is a high-value watch source for environment, climate, "
            "community resilience, biodiversity and local civil-society projects."
        ),
        title_ru="Программа малых грантов ГЭФ в Казахстане",
        summary_ru=(
            "Официальная страница ПРООН о Программе малых грантов ГЭФ. "
            "Направления поддержки – экология, климат, биоразнообразие, "
            "устойчивость сообществ и местные инициативы гражданского сектора."
        ),
        funder="GEF Small Grants Programme / UNDP Kazakhstan",
        type=OpportunityType.GRANT,
        eligibility=("kazakhstan", "civil_society", "community_project"),
        tags=("gef", "undp", "grant", "environment", "climate", "kazakhstan"),
        blocked_ok=True,
    ),
    "global_innovation_fund": StrategicWatchSpec(
        slug="global_innovation_fund",
        name="Global Innovation Fund",
        url="https://www.globalinnovation.fund/apply-for-funding",
        title="Global Innovation Fund future funding calls",
        summary=(
            "Global Innovation Fund application page for scalable development "
            "solutions. The latest public page states that the previous window is "
            "closed, so QAZ.FUND treats this as a future-call watch source rather "
            "than an open application."
        ),
        title_ru="Будущие конкурсы Глобального инновационного фонда",
        summary_ru=(
            "Официальная страница фонда для масштабируемых решений в области "
            "развития. Предыдущий приём завершён; карточка отслеживает появление "
            "следующего конкурса и не является открытой заявкой."
        ),
        funder="Global Innovation Fund",
        type=OpportunityType.GRANT,
        eligibility=("global", "development_innovation"),
        tags=("gif", "innovation", "development", "grant", "future_call"),
        lifecycle="forecast",
        opportunity_status="upcoming",
    ),
}


def _html_title(html: str) -> str | None:
    return _shared_html_title(html, _clean_text)


class StrategicWatchSource(BaseSource):
    spec: StrategicWatchSpec
    default_tags: ClassVar[list[str]] = [
        "official_source",
        "central_asia_relevant",
        "source_watch",
    ]

    async def fetch(self) -> AsyncIterator[Opportunity]:
        response: httpx.Response | None = None
        blocked = False
        try:
            response = await self.client.get(self.spec.url)
            if response.status_code == 403:
                blocked = True
                if not self.spec.blocked_ok:
                    log.warning(
                        "strategic_watch.blocked_fetch",
                        source=self.spec.slug,
                        url=self.spec.url,
                        status_code=response.status_code,
                    )
            elif response.status_code >= 500:
                response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "strategic_watch.fetch_failed",
                source=self.spec.slug,
                url=self.spec.url,
                error=str(exc),
            )
            return

        page_title = _html_title(response.text) if response is not None else None
        status_code = response.status_code if response is not None else None
        tags = _unique([*self.default_tags, *self.spec.tags])
        raw = {
            "external_id": self.spec.slug,
            "program_url": self.spec.url,
            "page_title": page_title,
            "status_code": status_code,
            "source_watch": True,
            "item_level_parser": False,
            "blocked_fetch": blocked,
            "verification_note": (
                "Official monitored entry point. Verify current item-level "
                "conditions on the source before acting."
            ),
            "i18n": {
                "ru": {
                    "title": self.spec.title_ru,
                    "summary": self.spec.summary_ru,
                },
                "en": {
                    "title": self.spec.title,
                    "summary": self.spec.summary,
                },
            },
        }

        yield Opportunity(
            source=self.spec.slug,
            source_url=self.spec.url,  # type: ignore[arg-type]
            type=self.spec.type,
            title=self.spec.title,
            summary=self.spec.summary,
            funder=self.spec.funder,
            eligibility=list(self.spec.eligibility),
            tags=tags,
            opportunity_status=self.spec.opportunity_status,
            lifecycle=self.spec.lifecycle,
            raw=raw,
        )


class UngmOpportunitiesSource(StrategicWatchSource):
    spec = STRATEGIC_WATCH_SPECS["ungm_opportunities"]
    slug = spec.slug
    name = spec.name
    base_url = spec.url


class OsceProcurementSource(StrategicWatchSource):
    spec = STRATEGIC_WATCH_SPECS["osce_procurement"]
    slug = spec.slug
    name = spec.name
    base_url = spec.url


class IomKazakhstanProcurementSource(StrategicWatchSource):
    spec = STRATEGIC_WATCH_SPECS["iom_kazakhstan_procurement"]
    slug = spec.slug
    name = spec.name
    base_url = spec.url


class EdbProcurementSource(StrategicWatchSource):
    spec = STRATEGIC_WATCH_SPECS["edb_procurement"]
    slug = spec.slug
    name = spec.name
    base_url = spec.url


class DaadCentralAsiaSource(StrategicWatchSource):
    spec = STRATEGIC_WATCH_SPECS["daad_central_asia"]
    slug = spec.slug
    name = spec.name
    base_url = spec.url


class GefSgpKazakhstanSource(StrategicWatchSource):
    spec = STRATEGIC_WATCH_SPECS["gef_sgp_kazakhstan"]
    slug = spec.slug
    name = spec.name
    base_url = spec.url


class GlobalInnovationFundSource(StrategicWatchSource):
    spec = STRATEGIC_WATCH_SPECS["global_innovation_fund"]
    slug = spec.slug
    name = spec.name
    base_url = spec.url


UngmOpportunitiesParser = UngmOpportunitiesSource
OsceProcurementParser = OsceProcurementSource
IomKazakhstanProcurementParser = IomKazakhstanProcurementSource
EdbProcurementParser = EdbProcurementSource
DaadCentralAsiaParser = DaadCentralAsiaSource
GefSgpKazakhstanParser = GefSgpKazakhstanSource
GlobalInnovationFundParser = GlobalInnovationFundSource
