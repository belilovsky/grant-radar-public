"""Active World Bank procurement notices for Kazakhstan and Central Asia."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import date, datetime, timedelta
from typing import Any

import structlog

from core.models import Opportunity, OpportunityType
from sources.base import BaseSource
from sources.world_bank import _infer_tags, _unique

log = structlog.get_logger()

WORLD_BANK_PROCUREMENT_API = "https://search.worldbank.org/api/v2/procnotices"
PROCUREMENT_DETAIL_URL = (
    "https://projects.worldbank.org/en/projects-operations/"
    "procurement-detail/{notice_id}"
)
TARGET_COUNTRIES = (
    "Kazakhstan",
    "Kyrgyz Republic",
    "Uzbekistan",
    "Tajikistan",
    "Turkmenistan",
    "Central Asia",
)
ACTIVE_NOTICE_TYPES = (
    "Request for Expression of Interest",
    "Invitation for Bids",
    "General Procurement Notice",
    "Invitation for Prequalification",
)
COUNTRY_TAGS = {
    "Kazakhstan": "kazakhstan",
    "Kyrgyz Republic": "kyrgyzstan",
    "Uzbekistan": "uzbekistan",
    "Tajikistan": "tajikistan",
    "Turkmenistan": "turkmenistan",
    "Central Asia": "central_asia",
}


def _iso_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _notice_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%d-%b-%Y").date()
    except ValueError:
        return _iso_date(text)


def _summary(notice: dict[str, Any]) -> str:
    project = " ".join(str(notice.get("project_name") or "").split())
    description = " ".join(str(notice.get("bid_description") or "").split())
    if project and description and project.lower() not in description.lower():
        text = f"{project}. {description}"
    else:
        text = description or project
    return text[:697].rstrip() + "..." if len(text) > 700 else text


def _is_current_notice(notice: dict[str, Any], today: date) -> bool:
    notice_type = str(notice.get("notice_type") or "").strip()
    if notice_type not in ACTIVE_NOTICE_TYPES:
        return False
    deadline = _iso_date(notice.get("submission_deadline_date"))
    if deadline is not None:
        return deadline >= today
    published = _notice_date(notice.get("noticedate"))
    return (
        notice_type == "General Procurement Notice"
        and published is not None
        and published >= today - timedelta(days=180)
    )


class WorldBankCentralAsiaProcurementSource(BaseSource):
    """Collect open World Bank-financed procurement notices in Central Asia."""

    slug = "world_bank_procurement_ca"
    name = "World Bank Central Asia procurement"
    base_url = "https://projects.worldbank.org/en/projects-operations/procurement"
    default_tags = [
        "central_asia",
        "world_bank",
        "tender",
        "procurement",
        "development",
    ]

    async def fetch(self) -> AsyncIterator[Opportunity]:
        params = {
            "format": "json",
            "rows": "250",
            "project_ctry_name_exact": "^".join(TARGET_COUNTRIES),
            "notice_type_exact": "^".join(ACTIVE_NOTICE_TYPES),
            "sort": "noticedate",
            "order": "desc",
        }
        try:
            response = await self.client.get(WORLD_BANK_PROCUREMENT_API, params=params)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:  # noqa: BLE001
            log.warning("world_bank_procurement.fetch_failed", error=str(exc))
            return

        notices = payload.get("procnotices")
        if not isinstance(notices, list):
            return

        today = date.today()
        count = 0
        for notice in notices:
            if not isinstance(notice, dict) or not _is_current_notice(notice, today):
                continue
            notice_id = str(notice.get("id") or "").strip()
            title = " ".join(str(notice.get("bid_description") or "").split())
            if not notice_id or not title:
                continue
            country = str(notice.get("project_ctry_name") or "").strip()
            notice_type = str(notice.get("notice_type") or "").strip()
            deadline = _iso_date(notice.get("submission_deadline_date"))
            text = " ".join(
                [title, _summary(notice), str(notice.get("project_name") or "")]
            )
            tags = _unique(
                [
                    *self.default_tags,
                    COUNTRY_TAGS.get(country, "central_asia"),
                    *_infer_tags(text),
                    "forecast" if deadline is None else "open",
                ]
            )
            count += 1
            yield Opportunity(
                source=self.slug,
                source_url=PROCUREMENT_DETAIL_URL.format(  # type: ignore[arg-type]
                    notice_id=notice_id
                ),
                type=OpportunityType.TENDER,
                title=title,
                summary=_summary(notice),
                funder="World Bank",
                deadline=deadline,
                tags=tags,
                opportunity_status="open",
                lifecycle="forecast" if deadline is None else "open",
                raw={
                    "external_id": notice_id,
                    "notice_type": notice_type,
                    "published": notice.get("noticedate"),
                    "project_id": notice.get("project_id"),
                    "project_name": notice.get("project_name"),
                    "country": country,
                    "reference": notice.get("bid_reference_no"),
                    "procurement_group": notice.get("procurement_group"),
                    "procurement_method": notice.get("procurement_method_name"),
                    "api_url": str(response.request.url),
                },
            )

        log.info("world_bank_procurement.batch", count=count)


WorldBankCentralAsiaProcurementParser = WorldBankCentralAsiaProcurementSource
