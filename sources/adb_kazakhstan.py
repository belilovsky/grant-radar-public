"""ADB Kazakhstan IATI project pipeline parser."""

from __future__ import annotations

import re
from collections.abc import AsyncIterator, Iterable
from datetime import date
from decimal import Decimal, InvalidOperation

import structlog
from lxml import etree as ET

from core.models import Opportunity, OpportunityType
from sources.base import BaseSource

log = structlog.get_logger()

ADB_KAZAKHSTAN_IATI_URL = "https://www.adb.org/iati/iati-activities-kz.xml"
ADB_PROJECT_URL = "https://www.adb.org/projects/{project_id}/main"
ACTIVE_STATUS_CODES = {"1", "2"}
TRANSACTION_COMMITMENT_CODE = "2"

THEME_KEYWORDS = {
    "ai": ("ai", "artificial intelligence", "machine learning"),
    "edtech": ("education", "learning", "skills", "training", "human capital"),
    "govtech": ("government", "governance", "public investment", "capacity"),
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
        "water",
        "waste",
        "biodiversity",
        "renewable",
        "decarbonization",
    ),
    "digital": ("digital", "technology", "ict", "smart", "data", "metering"),
    "startup": ("startup", "entrepreneur", "msme", "small and medium"),
    "finance": ("finance", "financial", "credit", "microfinance", "mortgage"),
    "infrastructure": (
        "infrastructure",
        "connectivity",
        "transport",
        "road",
        "rail",
        "urban",
        "housing",
        "grid",
    ),
    "green_transition": (
        "green",
        "climate",
        "renewable",
        "energy transition",
        "sustainable",
        "resilience",
        "decarbonization",
    ),
}

MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def _secure_xml_parser() -> ET.XMLParser:
    return ET.XMLParser(
        resolve_entities=False,
        no_network=True,
        huge_tree=False,
    )


def _clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


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


def _contains_term(text: str, keyword: str) -> bool:
    normalized_keyword = re.escape(keyword.lower()).replace(r"\ ", r"[\s_-]+")
    pattern = rf"(?<![a-z0-9]){normalized_keyword}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def _infer_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags: list[str] = []
    for tag, keywords in THEME_KEYWORDS.items():
        if any(_contains_term(lowered, keyword) for keyword in keywords):
            tags.append(tag)
    return tags


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _parse_text_date(value: str) -> date | None:
    match = re.search(
        r"(?P<day>\d{1,2})\s+(?P<month>[A-Za-z]+)\s+(?P<year>20\d{2})",
        value,
        re.IGNORECASE,
    )
    if match is None:
        return None
    month = MONTHS.get(match.group("month").lower())
    if month is None:
        return None
    try:
        return date(int(match.group("year")), month, int(match.group("day")))
    except ValueError:
        return None


def _parse_decimal(value: str | None) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return amount if amount > 0 else None


def _text(node: ET.Element, path: str) -> str:
    return _clean_text(node.findtext(path))


def _activity_date(activity: ET.Element, type_code: str) -> date | None:
    for node in activity.findall("activity-date"):
        if node.attrib.get("type") == type_code:
            return _parse_date(node.attrib.get("iso-date"))
    return None


def _status_code(activity: ET.Element) -> str:
    node = activity.find("activity-status")
    return node.attrib.get("code", "") if node is not None else ""


def _project_id(activity: ET.Element) -> str | None:
    values = [_text(activity, "iati-identifier")]
    values.extend(
        node.attrib.get("url", "") for node in activity.findall("document-link")
    )
    haystack = " ".join(values)
    match = re.search(r"(?<!\d)(\d{5}-\d{3})(?!\d)", haystack)
    return match.group(1) if match is not None else None


def _commitment(activity: ET.Element) -> Decimal | None:
    amounts: list[Decimal] = []
    for transaction in activity.findall("transaction"):
        transaction_type = transaction.find("transaction-type")
        if (
            transaction_type is None
            or transaction_type.attrib.get("code") != TRANSACTION_COMMITMENT_CODE
        ):
            continue
        amount = _parse_decimal(transaction.findtext("value"))
        if amount is not None:
            amounts.append(amount)
    return max(amounts) if amounts else None


def _partner(activity: ET.Element) -> str | None:
    for node in activity.findall("participating-org"):
        if node.attrib.get("role") == "4":
            value = _text(node, "narrative")
            if value:
                return value
    return None


def _document_urls(activity: ET.Element) -> list[str]:
    urls: list[str] = []
    for node in activity.findall("document-link"):
        raw = node.attrib.get("url", "")
        for url in raw.split(";"):
            url = url.strip()
            if url.startswith("https://"):
                urls.append(url)
    return urls[:10]


def _rolling_tags(tags: list[str], deadline: date | None) -> list[str]:
    if deadline is not None:
        return tags
    return _unique([*tags, "rolling"])


class AdbKazakhstanSource(BaseSource):
    slug = "adb_kazakhstan"
    name = "ADB Kazakhstan projects"
    base_url = "https://data.adb.org/dataset/adb-projects-kazakhstan"
    default_tags = [
        "kazakhstan",
        "central_asia",
        "adb",
        "project_pipeline",
        "public_sector",
        "development",
    ]

    async def fetch(self) -> AsyncIterator[Opportunity]:
        try:
            response = await self.client.get(ADB_KAZAKHSTAN_IATI_URL)
            response.raise_for_status()
            root = ET.fromstring(response.content, parser=_secure_xml_parser())
        except Exception as exc:  # noqa: BLE001
            log.warning("adb_kazakhstan.fetch_failed", error=str(exc))
            return

        count = 0
        generated_at = root.attrib.get("generated-datetime")
        for activity in root.findall("iati-activity"):
            if _status_code(activity) not in ACTIVE_STATUS_CODES:
                continue

            title = _text(activity, "title/narrative")
            if not title:
                continue

            project_id = _project_id(activity)
            summary = _text(activity, "description/narrative")
            deadline = _activity_date(activity, "3") or _activity_date(activity, "4")
            planned_start = _activity_date(activity, "1")
            text = " ".join([title, summary, _partner(activity) or ""])
            document_urls = _document_urls(activity)
            if deadline is None:
                for url in document_urls:
                    deadline = _parse_text_date(url)
                    if deadline is not None:
                        break
            tags = _rolling_tags(
                _unique([*self.default_tags, *_infer_tags(text)]), deadline
            )
            url = (
                ADB_PROJECT_URL.format(project_id=project_id)
                if project_id
                else self.base_url
            )
            count += 1
            yield Opportunity(
                source=self.slug,
                source_url=url,  # type: ignore[arg-type]
                type=OpportunityType.TENDER,
                title=title,
                summary=summary or "ADB Kazakhstan project pipeline item.",
                funder="Asian Development Bank",
                amount_max=_commitment(activity),
                currency=activity.attrib.get("default-currency", "USD") or "USD",
                deadline=deadline,
                tags=tags,
                raw={
                    "external_id": _text(activity, "iati-identifier")
                    or project_id
                    or url,
                    "project_id": project_id,
                    "status_code": _status_code(activity),
                    "planned_start": (
                        planned_start.isoformat() if planned_start else None
                    ),
                    "planned_end": deadline.isoformat() if deadline else None,
                    "partner": _partner(activity),
                    "dataset_url": ADB_KAZAKHSTAN_IATI_URL,
                    "generated_at": generated_at,
                    "documents": document_urls,
                    "deadline_policy": "rolling" if deadline is None else None,
                },
            )

        log.info("adb_kazakhstan.batch", count=count)


AdbKazakhstanParser = AdbKazakhstanSource
