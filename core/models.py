"""Domain models for grant-radar.

Pydantic-модели используются внутри pipeline,
SQLAlchemy ORM-модели — в storage.py.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl


class StrEnum(str, Enum):
    """Compatibility alias for `enum.StrEnum`-style enums."""


class OpportunityType(StrEnum):
    GRANT = "grant"
    ACCELERATOR = "accelerator"
    CLOUD_CREDIT = "cloud_credit"
    TENDER = "tender"
    CONTEST = "contest"
    FELLOWSHIP = "fellowship"


class Opportunity(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source: str
    source_url: HttpUrl
    type: OpportunityType
    title: str
    summary: str = ""
    funder: str | None = None
    funder_slug: str | None = None
    amount_min: Decimal | None = None
    amount_max: Decimal | None = None
    currency: str = "USD"
    deadline: date | None = None
    eligibility: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    score: float = 0.0
    opportunity_status: str | None = None
    lifecycle: str | None = None
    discovered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    raw: dict = Field(default_factory=dict)

    def fingerprint(self) -> str:
        """Ключ для дедупликации."""
        raw = self.raw if isinstance(self.raw, dict) else {}
        external_id = str(raw.get("external_id") or raw.get("reference") or "").strip()
        if external_id:
            return f"{self.source}:{external_id}"
        return f"{self.source}:{self.source_url}"

    @property
    def url(self) -> str:
        """Compatibility alias used by the queue/parser layer."""
        return str(self.source_url)

    @property
    def external_id(self) -> str:
        """Stable string identifier for queue-oriented processors."""
        raw = self.raw if isinstance(self.raw, dict) else {}
        return str(raw.get("external_id") or raw.get("reference") or self.id)


class OpportunityDetailSection(BaseModel):
    heading: str = ""
    text: str


class OpportunityMetadataField(BaseModel):
    key: str
    value: str


class OpportunityDetail(Opportunity):
    application_url: str | None = None
    detail_available: bool = False
    detail_fetch_status: str = "structured_only"
    detail_excerpt_only: bool = False
    detail_fetched_at: datetime | None = None
    detail_text: str = ""
    detail_sections: list[OpportunityDetailSection] = Field(default_factory=list)
    metadata: list[OpportunityMetadataField] = Field(default_factory=list)


class Source(BaseModel):
    slug: str
    name: str
    base_url: HttpUrl
    enabled: bool = True
    schedule_cron: str = "0 */6 * * *"  # каждые 6ч
    tags: list[str] = Field(default_factory=list)


class Digest(BaseModel):
    generated_at: datetime
    period_from: datetime
    period_to: datetime
    items: list[Opportunity]
    channel: str  # 'api' | 'telegram' | 'email' | 'sheets'
