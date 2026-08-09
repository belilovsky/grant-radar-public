"""Versioned public data contract for QAZ.FUND machine consumers.

The legacy API remains available for compatibility.  This module projects the
same public records into a documented, stable contract without exposing the
source-specific ``raw`` payload as the primary interface.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from qazstack.opportunities import (
    OPPORTUNITY_SCHEMA_VERSION,
    FundingAmount,
    LocalizedText,
    OpportunityLinks,
    OpportunityProvenance,
    OpportunityQuality,
    OpportunityTimestamps,
    OpportunityV1,
    SourceReference,
    opportunity_dataset_revision,
    semantic_payload_hash,
)
from qazstack.opportunities import source_host as _source_host

from core.models import Opportunity

SCHEMA_VERSION = OPPORTUNITY_SCHEMA_VERSION
DATASET_SCHEMA_VERSION = "qazfund-dataset.v1"


def _string(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = []
    out: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = _string(item)
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            out.append(text)
    return out


def _datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _localized(raw: dict[str, Any], field: str) -> LocalizedText:
    localized: dict[str, str | None] = {"ru": None, "kk": None, "en": None}
    i18n = raw.get("i18n")
    if isinstance(i18n, dict):
        for lang in localized:
            value = i18n.get(lang)
            if isinstance(value, dict):
                localized[lang] = _string(value.get(field)) or None
    for lang in localized:
        direct = _string(raw.get(f"{field}_{lang}"))
        if direct:
            localized[lang] = direct
    return LocalizedText(**localized)


def _formats(item: Opportunity) -> list[str]:
    tags = {str(tag).strip().lower() for tag in item.tags}
    formats: list[str] = []
    mapping = (
        ("reimbursement", {"reimbursement", "cost_reimbursement"}),
        ("subsidy", {"subsidy"}),
        ("loan_guarantee", {"loan_guarantee", "guarantee"}),
        ("preferential_finance", {"preferential_financing", "loan"}),
        ("leasing", {"leasing"}),
        ("tax_benefit", {"tax_benefit", "tax_benefits"}),
        ("grant", {"grant"}),
        ("accelerator", {"accelerator", "incubator"}),
        ("cloud_credit", {"cloud_credit", "cloud_credits"}),
        ("procurement", {"tender", "procurement"}),
        ("fellowship", {"fellowship"}),
        ("contest", {"contest", "competition"}),
    )
    for name, signals in mapping:
        if tags.intersection(signals):
            formats.append(name)
    type_value = str(getattr(item.type, "value", item.type))
    fallback = "procurement" if type_value == "tender" else type_value
    if fallback and fallback not in formats:
        formats.append(fallback)
    return formats


def _audiences(item: Opportunity) -> list[str]:
    tags = {str(tag).strip().lower() for tag in item.tags}
    groups = (
        ("startups", {"startup", "founder", "accelerator"}),
        ("business", {"business", "sme", "msme", "entrepreneur"}),
        ("farmers", {"farmer", "agriculture", "agrotech", "livestock"}),
        ("nonprofits", {"ngo", "nonprofit", "civil_society", "civic"}),
        ("researchers", {"research", "science", "university", "higher_education"}),
        ("public_sector", {"government", "public_sector", "municipal"}),
        ("media", {"media", "journalism"}),
    )
    return [name for name, signals in groups if tags.intersection(signals)]


def _themes(item: Opportunity, raw: dict[str, Any]) -> list[str]:
    ranking = raw.get("ranking")
    if isinstance(ranking, dict):
        matched = _string_list(ranking.get("matched_themes"))
        if matched:
            return matched
    ignored = {
        "kazakhstan",
        "central_asia",
        "global",
        "rolling",
        "grant",
        "tender",
        "procurement",
        "subsidy",
        "reimbursement",
        "state_program",
    }
    return [tag for tag in _string_list(item.tags) if tag.lower() not in ignored][:12]


def _regions(item: Opportunity, raw: dict[str, Any]) -> list[str]:
    tags = {str(tag).strip().lower() for tag in item.tags}
    regions: list[str] = []
    if tags.intersection({"kazakhstan", "kz"}) or item.source.endswith("kazakhstan"):
        regions.append("kazakhstan")
    if tags.intersection({"central_asia", "ca"}):
        regions.append("central_asia")
    if tags.intersection({"global", "international", "central_asia_eligible"}):
        regions.append("global")
    ranking = raw.get("ranking")
    if isinstance(ranking, dict):
        geography = _string(ranking.get("geography"))
        if geography and geography not in regions:
            regions.append(geography)
    return regions or ["unspecified"]


def _application_url(raw: dict[str, Any]) -> str | None:
    for key in ("application_url", "apply_url", "submission_url"):
        value = _string(raw.get(key))
        if value.startswith(("http://", "https://")):
            return value
    return None


def _deadline_type(
    item: Opportunity, raw: dict[str, Any]
) -> Literal["fixed", "rolling", "unknown"]:
    policy = _string(raw.get("deadline_policy")).lower()
    if item.deadline is not None:
        return "fixed"
    if policy == "rolling" or "rolling" in {str(tag).lower() for tag in item.tags}:
        return "rolling"
    return "unknown"


def _quality(item: Opportunity, raw: dict[str, Any]) -> OpportunityQuality:
    readiness = raw.get("decision_readiness")
    missing: list[str] = []
    status = "partial"
    if isinstance(readiness, dict):
        missing = _string_list(readiness.get("missing_fields"))
        raw_status = _string(readiness.get("status")).lower()
        if raw_status in {"complete", "ready"}:
            status = "complete"
        elif raw_status in {"review_required", "needs_review"}:
            status = "review_required"
    if not missing:
        if item.deadline is None and _deadline_type(item, raw) == "unknown":
            missing.append("deadline")
        if not item.eligibility:
            missing.append("eligibility")
        if (
            item.amount_min is None
            and item.amount_max is None
            and not raw.get("amount_raw")
        ):
            missing.append("amount")

    evidence = raw.get("qazcompute_evidence_readiness")
    warnings: list[str] = []
    confidence = max(0.0, min(1.0, float(item.score or 0.0)))
    if isinstance(evidence, dict):
        try:
            confidence = max(0.0, min(1.0, float(evidence.get("score", 0.0)) / 100.0))
        except (TypeError, ValueError):
            pass
        warnings = _string_list(evidence.get("warnings"))
    elif missing:
        confidence = max(0.0, 1.0 - (0.18 * len(missing)))
    return OpportunityQuality(
        status=status,  # type: ignore[arg-type]
        confidence_score=round(confidence, 4),
        missing_fields=missing,
        warnings=warnings,
    )


def _verification_method(item: Opportunity, raw: dict[str, Any]) -> str:
    explicit = _string(raw.get("verification_method"))
    if explicit:
        return explicit
    if raw.get("detail_fetch_status") == "ok":
        return "official_source_fetch"
    if item.source in {"kazakhstan_domestic_support", "kazakhstan_watch"}:
        return "curated_official_source"
    return "source_adapter"


def _evidence_state(
    raw: dict[str, Any],
) -> Literal["verified", "sourced", "archival", "compiled", "unlinked"]:
    value = _string(raw.get("evidence_state")).lower()
    if value in {"verified", "sourced", "archival", "compiled", "unlinked"}:
        return value  # type: ignore[return-value]
    return "sourced"


def to_opportunity_v1(
    item: Opportunity,
    *,
    source_name: str | None = None,
    public_base_url: str = "https://qaz.fund",
) -> OpportunityV1:
    raw = item.raw if isinstance(item.raw, dict) else {}
    application_url = _application_url(raw)
    amount_display = _string(raw.get("amount_raw")) or None
    eligibility = _string_list(item.eligibility or raw.get("eligibility_raw"))
    eligibility_summary = _string(raw.get("eligibility_summary")) or None
    if eligibility_summary is None and eligibility:
        eligibility_summary = "; ".join(eligibility[:3])

    source_checked_at = (
        _datetime(raw.get("source_checked_at"))
        or _datetime(raw.get("detail_fetched_at"))
        or item.discovered_at
    )
    last_verified_at = _datetime(raw.get("last_verified_at"))
    title_i18n = _localized(raw, "title")
    summary_i18n = _localized(raw, "summary")
    semantic = {
        "id": str(item.id),
        "title": item.title,
        "summary": item.summary,
        "status": item.opportunity_status or item.lifecycle or "unknown",
        "deadline": item.deadline.isoformat() if item.deadline else None,
        "formats": _formats(item),
        "audiences": _audiences(item),
        "themes": _themes(item, raw),
        "regions": _regions(item, raw),
        "source_url": str(item.source_url),
        "application_url": application_url,
        "eligibility": eligibility,
        "amount_min": item.amount_min,
        "amount_max": item.amount_max,
        "amount_raw": amount_display,
    }
    content_hash = semantic_payload_hash(semantic)
    base = public_base_url.rstrip("/")
    source_label = (
        source_name
        or _string(raw.get("source_name"))
        or item.source.replace("_", " ").title()
    )
    snapshot_hash = (
        _string(raw.get("detail_html_sha256"))
        or _string(raw.get("snapshot_hash"))
        or None
    )

    return OpportunityV1(
        id=item.id,
        title=item.title,
        title_i18n=title_i18n,
        summary=item.summary,
        summary_i18n=summary_i18n,
        status=item.opportunity_status or item.lifecycle or "unknown",
        deadline=item.deadline,
        deadline_type=_deadline_type(item, raw),
        formats=_formats(item),
        target_audience=_audiences(item),
        themes=_themes(item, raw),
        regions=_regions(item, raw),
        source=SourceReference(
            id=item.source,
            name=source_label,
            url=str(item.source_url),
        ),
        funder=item.funder,
        funding_amount=FundingAmount(
            minimum=item.amount_min,
            maximum=item.amount_max,
            currency=(
                item.currency
                if item.amount_min is not None or item.amount_max is not None
                else None
            ),
            display=amount_display,
        ),
        eligibility_summary=eligibility_summary,
        eligibility=eligibility,
        timestamps=OpportunityTimestamps(
            discovered_at=item.discovered_at,
            source_checked_at=source_checked_at,
            last_verified_at=last_verified_at,
        ),
        provenance=OpportunityProvenance(
            evidence_state=_evidence_state(raw),
            verification_method=_verification_method(item, raw),
            adapter=item.source,
            snapshot_hash=snapshot_hash,
            content_hash=content_hash,
        ),
        quality=_quality(item, raw),
        links=OpportunityLinks(
            public_page=f"{base}/opportunity/{item.id}",
            api=f"{base}/api/v1/opportunities/{item.id}",
            official_source=str(item.source_url),
            application=application_url,
        ),
    )


def dataset_revision(items: list[OpportunityV1]) -> str:
    return opportunity_dataset_revision(
        items,
        schema_version=DATASET_SCHEMA_VERSION,
    )


def source_host(url: str) -> str:
    return _source_host(url)
