"""Orthogonal opportunity taxonomy used by public and social contracts."""

from __future__ import annotations

from typing import Any

from core.models import Opportunity

TAXONOMY_VERSION = "1.0.0"

MAIN_SOCIAL_TRACKS = {
    "grants",
    "subsidies",
    "competitions",
    "scholarships",
    "procurement",
    "finance",
    "programmes",
}

TEMPLATE_TRACKS = {
    "grant_day": {"grants"},
    "subsidy_day": {"subsidies"},
    "procurement_day": {"procurement"},
    "finance_day": {"finance"},
    "education_day": {"education", "scholarships"},
    "opportunity_day": MAIN_SOCIAL_TRACKS,
    "deadline_7d": MAIN_SOCIAL_TRACKS,
    "deadline_2d": MAIN_SOCIAL_TRACKS,
    "weekly": MAIN_SOCIAL_TRACKS,
}


def _tags(item: Opportunity) -> set[str]:
    return {str(tag).strip().lower() for tag in item.tags if str(tag).strip()}


def _raw(item: Opportunity) -> dict[str, Any]:
    return item.raw if isinstance(item.raw, dict) else {}


def _explicit(item: Opportunity) -> dict[str, Any]:
    value = _raw(item).get("opportunity_taxonomy")
    return value if isinstance(value, dict) else {}


def _instrument(item: Opportunity, tags: set[str]) -> str:
    explicit = str(_explicit(item).get("instrument") or "").strip()
    if explicit:
        return explicit
    type_value = str(getattr(item.type, "value", item.type)).lower()
    signals = (
        ("education_admission", {"education_admission", "state_funded_seat"}),
        ("reimbursement", {"reimbursement", "cost_reimbursement"}),
        ("subsidy", {"subsidy"}),
        ("guarantee", {"loan_guarantee", "guarantee"}),
        ("leasing", {"leasing"}),
        ("loan", {"preferential_financing", "loan", "credit"}),
        ("tax_benefit", {"tax_benefit", "tax_benefits"}),
        ("scholarship", {"scholarship", "fellowship"}),
        ("prize", {"contest", "competition", "prize"}),
        ("procurement", {"tender", "procurement"}),
        ("accelerator", {"accelerator", "incubator"}),
        ("in_kind_support", {"cloud_credit", "cloud_credits", "in_kind_support"}),
        ("grant", {"grant"}),
    )
    for instrument, matches in signals:
        if tags.intersection(matches):
            return instrument
    return {
        "contest": "prize",
        "fellowship": "scholarship",
        "tender": "procurement",
        "accelerator": "accelerator",
        "cloud_credit": "in_kind_support",
        "grant": "grant",
    }.get(type_value, "unknown")


def _benefit_type(instrument: str) -> str:
    return {
        "grant": "cash_nonrepayable",
        "subsidy": "cash_nonrepayable",
        "prize": "cash_nonrepayable",
        "scholarship": "cash_nonrepayable",
        "reimbursement": "cost_reimbursement",
        "procurement": "commercial_contract",
        "loan": "debt_finance",
        "leasing": "debt_finance",
        "guarantee": "guarantee",
        "tax_benefit": "tax_relief",
        "education_admission": "tuition_coverage",
        "accelerator": "training_support",
        "in_kind_support": "in_kind_support",
    }.get(instrument, "unknown")


def _content_track(instrument: str) -> str:
    return {
        "grant": "grants",
        "subsidy": "subsidies",
        "reimbursement": "subsidies",
        "prize": "competitions",
        "scholarship": "scholarships",
        "procurement": "procurement",
        "loan": "finance",
        "leasing": "finance",
        "guarantee": "finance",
        "tax_benefit": "finance",
        "education_admission": "education",
        "accelerator": "programmes",
        "in_kind_support": "programmes",
    }.get(instrument, "unknown")


def _application_mode(item: Opportunity, instrument: str) -> str:
    explicit = str(_explicit(item).get("application_mode") or "").strip()
    if explicit:
        return explicit
    if instrument == "education_admission":
        return "admission"
    if instrument == "procurement":
        return "tender"
    if item.lifecycle == "rolling" or _raw(item).get("deadline_policy") == "rolling":
        return "rolling_eligibility"
    if instrument != "unknown":
        return "competitive_call"
    return "unknown"


def _deadline_model(item: Opportunity) -> str:
    explicit = str(_explicit(item).get("deadline_model") or "").strip()
    if explicit:
        return explicit
    if _raw(item).get("application_windows"):
        return "multiple"
    if item.lifecycle == "rolling" or _raw(item).get("deadline_policy") == "rolling":
        return "rolling"
    if item.deadline is not None:
        return "fixed"
    return "unknown"


def classify_opportunity(item: Opportunity) -> dict[str, Any]:
    """Return taxonomy without conflating the funding mechanism with the topic."""

    tags = _tags(item)
    instrument = _instrument(item, tags)
    content_track = _content_track(instrument)
    application_mode = _application_mode(item, instrument)
    deadline_model = _deadline_model(item)
    findings: list[str] = []
    if instrument == "unknown":
        findings.append("instrument_unknown")
    if content_track == "unknown":
        findings.append("content_track_unknown")
    if application_mode == "unknown":
        findings.append("application_mode_unknown")
    if deadline_model == "unknown":
        findings.append("deadline_model_unknown")
    return {
        "version": TAXONOMY_VERSION,
        "instrument": instrument,
        "benefit_type": _benefit_type(instrument),
        "application_mode": application_mode,
        "deadline_model": deadline_model,
        "content_track": content_track,
        "publication_scope": (
            "main" if content_track in MAIN_SOCIAL_TRACKS else "dedicated"
        ),
        "decision": "pass" if not findings else "blocked",
        "finding_ids": findings,
    }


def template_accepts_taxonomy(template: str, taxonomy: dict[str, Any]) -> bool:
    return taxonomy.get("content_track") in TEMPLATE_TRACKS.get(template, set())


__all__ = [
    "MAIN_SOCIAL_TRACKS",
    "TAXONOMY_VERSION",
    "TEMPLATE_TRACKS",
    "classify_opportunity",
    "template_accepts_taxonomy",
]
