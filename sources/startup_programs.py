"""Evergreen startup and cloud-credit program monitors.

These sources are not grant feeds in the narrow sense. They are stable support
programs that matter for Kazakhstan/Central Asia AI, EdTech and GovTech teams:
cloud credits, startup support, AI tooling, mentorship, and partner ecosystems.
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from decimal import Decimal
from html import unescape

import structlog

from core.models import Opportunity, OpportunityType
from sources.base import BaseSource

log = structlog.get_logger()


@dataclass(frozen=True)
class StartupProgramSpec:
    slug: str
    name: str
    url: str
    title: str
    summary: str
    funder: str
    tags: tuple[str, ...]
    amount_max: Decimal | None = None


PROGRAM_SPECS = {
    "google_cloud_startup": StartupProgramSpec(
        slug="google_cloud_startup",
        name="Google for Startups Cloud Program",
        url="https://startup.google.com/cloud/",
        title="Google for Startups Cloud Program",
        summary=(
            "Global startup support program with Google Cloud and Firebase "
            "credits, AI startup benefits, technical support and community "
            "resources for eligible startups."
        ),
        funder="Google for Startups",
        tags=("google", "cloud_credits", "startup", "ai", "firebase"),
        amount_max=Decimal("350000"),
    ),
    "microsoft_founders_hub": StartupProgramSpec(
        slug="microsoft_founders_hub",
        name="Microsoft for Startups Founders Hub",
        url="https://www.microsoft.com/en/startups",
        title="Microsoft for Startups Founders Hub",
        summary=(
            "Global startup support program with Azure credits, AI services, "
            "developer tools, mentorship and go-to-market resources for "
            "eligible startups."
        ),
        funder="Microsoft for Startups",
        tags=("microsoft", "azure", "cloud_credits", "startup", "ai"),
    ),
    "aws_activate": StartupProgramSpec(
        slug="aws_activate",
        name="AWS Activate credits",
        url="https://aws.amazon.com/startups/credits/?lang=en-US",
        title="AWS Activate credits",
        summary=(
            "AWS startup credit program for eligible founders, including cloud "
            "infrastructure and AI services such as managed foundation-model "
            "tooling."
        ),
        funder="Amazon Web Services",
        tags=("aws", "cloud_credits", "startup", "ai", "infrastructure"),
    ),
    "nvidia_inception": StartupProgramSpec(
        slug="nvidia_inception",
        name="NVIDIA Inception",
        url="https://www.nvidia.com/en-us/startups/",
        title="NVIDIA Inception Program",
        summary=(
            "Global program for AI and data-science startups with developer "
            "tools, technical resources, preferred pricing and investor "
            "ecosystem exposure."
        ),
        funder="NVIDIA",
        tags=("nvidia", "startup", "ai", "developer_tools", "gpu"),
    ),
    "cloudflare_startups": StartupProgramSpec(
        slug="cloudflare_startups",
        name="Cloudflare for Startups",
        url="https://www.cloudflare.com/startups/",
        title="Cloudflare for Startups",
        summary=(
            "Startup credit program for eligible teams building on Cloudflare "
            "with edge, security, storage, serverless and Workers AI services."
        ),
        funder="Cloudflare",
        tags=(
            "cloudflare",
            "cloud_credits",
            "startup",
            "ai",
            "serverless",
            "security",
        ),
        amount_max=Decimal("350000"),
    ),
    "mongodb_startups": StartupProgramSpec(
        slug="mongodb_startups",
        name="MongoDB for Startups",
        url="https://www.mongodb.com/startups",
        title="MongoDB for Startups",
        summary=(
            "Startup program for eligible companies using MongoDB Atlas, with "
            "database credits, technical resources and partner ecosystem "
            "support."
        ),
        funder="MongoDB",
        tags=("mongodb", "cloud_credits", "startup", "database", "developer_tools"),
    ),
}


def _clean_text(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", unescape(without_tags)).strip()


def _html_title(html: str) -> str | None:
    match = re.search(
        r"<title[^>]*>(?P<title>.*?)</title>", html, re.IGNORECASE | re.DOTALL
    )
    if match is None:
        return None
    title = _clean_text(match.group("title"))
    return title or None


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


class StartupProgramSource(BaseSource):
    program: StartupProgramSpec
    default_tags = ["global", "central_asia_eligible", "startup_support", "rolling"]

    async def fetch(self) -> AsyncIterator[Opportunity]:
        try:
            response = await self.client.get(self.program.url)
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "startup_program.fetch_failed",
                source=self.program.slug,
                url=self.program.url,
                error=str(exc),
            )
            return

        yield Opportunity(
            source=self.program.slug,
            source_url=self.program.url,  # type: ignore[arg-type]
            type=OpportunityType.CLOUD_CREDIT,
            title=self.program.title,
            summary=self.program.summary,
            funder=self.program.funder,
            amount_max=self.program.amount_max,
            currency="USD",
            eligibility=["global", "startup"],
            tags=_unique([*self.default_tags, *self.program.tags]),
            raw={
                "external_id": self.program.slug,
                "deadline_policy": "rolling",
                "page_title": _html_title(response.text),
                "status_code": response.status_code,
                "program_url": self.program.url,
            },
        )


class GoogleCloudStartupSource(StartupProgramSource):
    program = PROGRAM_SPECS["google_cloud_startup"]
    slug = program.slug
    name = program.name
    base_url = program.url


class MicrosoftFoundersHubSource(StartupProgramSource):
    program = PROGRAM_SPECS["microsoft_founders_hub"]
    slug = program.slug
    name = program.name
    base_url = program.url


class AwsActivateSource(StartupProgramSource):
    program = PROGRAM_SPECS["aws_activate"]
    slug = program.slug
    name = program.name
    base_url = program.url


class NvidiaInceptionSource(StartupProgramSource):
    program = PROGRAM_SPECS["nvidia_inception"]
    slug = program.slug
    name = program.name
    base_url = program.url


class CloudflareStartupsSource(StartupProgramSource):
    program = PROGRAM_SPECS["cloudflare_startups"]
    slug = program.slug
    name = program.name
    base_url = program.url


class MongoDbStartupsSource(StartupProgramSource):
    program = PROGRAM_SPECS["mongodb_startups"]
    slug = program.slug
    name = program.name
    base_url = program.url


GoogleCloudStartupParser = GoogleCloudStartupSource
MicrosoftFoundersHubParser = MicrosoftFoundersHubSource
AwsActivateParser = AwsActivateSource
NvidiaInceptionParser = NvidiaInceptionSource
CloudflareStartupsParser = CloudflareStartupsSource
MongoDbStartupsParser = MongoDbStartupsSource
