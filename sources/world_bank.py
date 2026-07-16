"""World Bank Kazakhstan project pipeline parser."""

from __future__ import annotations

import re
from collections.abc import AsyncIterator, Iterable
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, ClassVar

import structlog

from core.models import Opportunity, OpportunityType
from sources.base import BaseSource

log = structlog.get_logger()

WORLD_BANK_PROJECTS_API = (
    "https://search.worldbank.org/api/v3/projects"
    "?format=json&rows=20"
    "&fl=id,project_name,countryshortname,projectstatusdisplay,pdo,url,"
    "closingdate,totalamt,grantamt,boardapprovaldate,project_abstract,"
    "borrower,lendinginstr,regionname,countrycode"
    "&countrycode_exact=KZ&srt=boardapprovaldate&order=desc"
)
PROJECT_DETAIL_URL = (
    "https://projects.worldbank.org/en/projects-operations/project-detail/{project_id}"
)

THEME_KEYWORDS = {
    "ai": ("ai", "artificial intelligence", "machine learning"),
    "edtech": ("education", "learning", "skills", "training"),
    "govtech": ("government", "public sector", "digital public", "governance"),
    "agrotech": (
        "agriculture",
        "agritech",
        "food systems",
        "irrigation",
        "livestock",
        "agribusiness",
    ),
    "vettech": ("veterinary", "animal health", "livestock health", "zoonotic"),
    "ecotech": (
        "climate",
        "environment",
        "sustainable",
        "biodiversity",
        "water",
        "waste",
        "renewable",
    ),
    "digital": ("digital", "technology", "ict", "cloud", "data"),
    "startup": ("startup", "entrepreneur", "venture capital", "innovation"),
    "infrastructure": ("infrastructure", "connectivity", "transport", "rail"),
    "green_transition": ("green", "climate", "sustainable", "emission"),
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


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _parse_amount(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return amount if amount > 0 else None


def _summary(project: dict[str, Any]) -> str:
    value = project.get("pdo") or project.get("project_abstract") or ""
    text = " ".join(str(value).split())
    if len(text) > 700:
        return f"{text[:697].rstrip()}..."
    return text


def _infer_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags: list[str] = []
    for tag, keywords in THEME_KEYWORDS.items():
        if any(_contains_term(lowered, keyword) for keyword in keywords):
            tags.append(tag)
    return tags


def _contains_term(text: str, keyword: str) -> bool:
    normalized_keyword = re.escape(keyword.lower()).replace(r"\ ", r"[\s_-]+")
    pattern = rf"(?<![a-z0-9]){normalized_keyword}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def _project_url(project: dict[str, Any]) -> str:
    raw_url = str(project.get("url") or "").strip()
    if raw_url.startswith("http"):
        return raw_url
    project_id = str(project.get("id") or project.get("proj_id") or "").strip()
    return PROJECT_DETAIL_URL.format(project_id=project_id)


class WorldBankKazakhstanSource(BaseSource):
    slug = "world_bank_kazakhstan"
    name = "World Bank Kazakhstan projects"
    base_url = (
        "https://projects.worldbank.org/en/projects-operations/projects-list"
        "?countrycode_exact=KZ"
    )
    default_tags: ClassVar[list[str]] = [
        "kazakhstan",
        "central_asia",
        "world_bank",
        "project_pipeline",
        "public_sector",
        "development",
    ]

    async def fetch(self) -> AsyncIterator[Opportunity]:
        try:
            response = await self.client.get(WORLD_BANK_PROJECTS_API)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:  # noqa: BLE001
            log.warning("world_bank_kazakhstan.fetch_failed", error=str(exc))
            return

        projects = payload.get("projects")
        if not isinstance(projects, dict):
            return

        count = 0
        for project in projects.values():
            if not isinstance(project, dict):
                continue
            title = str(project.get("project_name") or "").strip()
            project_id = str(project.get("id") or project.get("proj_id") or "").strip()
            if not title or not project_id:
                continue
            text = " ".join(
                [
                    title,
                    _summary(project),
                    str(project.get("project_abstract") or ""),
                    str(project.get("borrower") or ""),
                ]
            )
            tags = _unique([*self.default_tags, *_infer_tags(text)])
            amount = _parse_amount(project.get("grantamt")) or _parse_amount(
                project.get("totalamt")
            )
            deadline = _parse_date(project.get("closingdate")) or _parse_date(
                project.get("boardapprovaldate")
            )
            count += 1
            yield Opportunity(
                source=self.slug,
                source_url=_project_url(project),  # type: ignore[arg-type]
                type=OpportunityType.TENDER,
                title=title,
                summary=_summary(project),
                funder="World Bank",
                amount_max=amount,
                currency="USD",
                deadline=deadline,
                tags=tags,
                raw={
                    "external_id": project_id,
                    "project_id": project_id,
                    "country": project.get("countryshortname"),
                    "countrycode": project.get("countrycode"),
                    "status": project.get("projectstatusdisplay"),
                    "boardapprovaldate": project.get("boardapprovaldate"),
                    "closingdate": project.get("closingdate"),
                    "borrower": project.get("borrower"),
                    "lendinginstr": project.get("lendinginstr"),
                    "region": project.get("regionname"),
                    "totalamt": project.get("totalamt"),
                    "grantamt": project.get("grantamt"),
                    "api_url": WORLD_BANK_PROJECTS_API,
                },
            )

        log.info("world_bank_kazakhstan.batch", count=count)


WorldBankKazakhstanParser = WorldBankKazakhstanSource
