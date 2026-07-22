"""Deterministic, explainable relevance and action-priority scoring."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

from core.geofit import (
    exclusion_reason,
    has_positive_geo_signal,
    is_low_confidence_for_kazakhstan_focus,
)
from core.models import Opportunity
from qazstack.opportunities import is_rolling_item

MODEL_VERSION = "qazfund-relevance-v2"
PUBLIC_RELEVANCE_THRESHOLD = 0.3
LOW_CONFIDENCE_CAP = PUBLIC_RELEVANCE_THRESHOLD - 0.01
THEMATIC_COMPONENT_CAP = 0.56
SUMMARY_ONLY_WEIGHT = 0.55

# Synonyms are grouped so one concept is never counted repeatedly. Weights express
# public-catalog relevance, not a probability of award or legal eligibility.
THEME_GROUPS: dict[str, tuple[float, tuple[str, ...]]] = {
    "ai": (0.28, ("ai", "artificial intelligence", "machine learning")),
    "digital_infrastructure": (
        0.22,
        ("cloud", "cloud credit", "cloud credits", "digitalization"),
    ),
    "agriculture_food": (
        0.24,
        ("agrotech", "agritech", "agriculture", "food systems", "irrigation"),
    ),
    "animal_health": (
        0.22,
        ("livestock", "vettech", "veterinary", "animal health", "zoonotic"),
    ),
    "climate_environment": (
        0.22,
        (
            "ecotech",
            "cleantech",
            "climate tech",
            "environment",
            "biodiversity",
            "circular economy",
            "waste management",
            "water resilience",
        ),
    ),
    "media_civic": (
        0.22,
        ("media", "journalism", "data journalism", "civic", "open data"),
    ),
    "governance": (
        0.20,
        ("govtech", "governance", "democracy", "anti-corruption", "transparency"),
    ),
    "education_skills": (
        0.18,
        ("edtech", "education", "digital skills", "stem"),
    ),
    "startup_innovation": (
        0.18,
        (
            "startup",
            "accelerator",
            "it hub",
            "innovation",
            "innovation grant",
            "commercialization",
        ),
    ),
    "business_support": (
        0.20,
        (
            "subsidy",
            "sme",
            "business support",
            "domestic support",
            "state program",
            "reimbursement",
            "preferential financing",
            "leasing",
            "tax benefit",
            "loan guarantee",
        ),
    ),
    "finance_growth": (
        0.14,
        ("venture", "private equity", "export", "industry", "investment"),
    ),
}

KAZAKHSTAN_TERMS = ("kazakhstan", "казахстан", "қазақстан", "kz")
CENTRAL_ASIA_TERMS = (
    "central asia",
    "central asian",
    "центральная азия",
    "центральной азии",
    "орталық азия",
)
REGIONAL_TERMS = ("cis", "eurasia", "uzbekistan", "kyrgyzstan", "tajikistan")
GLOBAL_TERMS = ("global", "worldwide", "international", "all countries")
LOCAL_SOURCE_SLUGS = {
    "astana_hub",
    "eeas_kazakhstan",
    "kazakhstan_domestic_support",
    "kazakhstan_watch",
    "unesco_iite",
}


@dataclass(frozen=True)
class ScoreBreakdown:
    """Auditable score components returned by the deterministic v2 model."""

    model_version: str
    thematic: float
    geographic: float
    source_context: float
    deadline_actionability: float
    relevance: float
    priority: float
    matched_themes: tuple[str, ...]
    geography: str
    confidence: str
    exclusion_reason: str | None


def _contains_keyword(text: str, keyword: str) -> bool:
    normalized_keyword = re.escape(keyword.lower()).replace(r"\ ", r"[\s_-]+")
    pattern = rf"(?<![a-z0-9]){normalized_keyword}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def _primary_theme_text(opp: Opportunity) -> str:
    return f"{opp.title} {' '.join(opp.tags)}".lower()


def _thematic_component(opp: Opportunity) -> tuple[float, tuple[str, ...]]:
    primary_text = _primary_theme_text(opp)
    summary_text = str(opp.summary or "").lower()
    matches: list[str] = []
    total = 0.0
    for name, (weight, terms) in THEME_GROUPS.items():
        if any(_contains_keyword(primary_text, term) for term in terms):
            matches.append(name)
            total += weight
        elif any(_contains_keyword(summary_text, term) for term in terms):
            matches.append(name)
            total += weight * SUMMARY_ONLY_WEIGHT
    return round(min(THEMATIC_COMPONENT_CAP, total), 4), tuple(matches)


def _geographic_component(opp: Opportunity, text: str) -> tuple[float, str]:
    source = str(opp.source or "").lower()
    if source in LOCAL_SOURCE_SLUGS or any(
        _contains_keyword(text, term) for term in KAZAKHSTAN_TERMS
    ):
        return 0.30, "kazakhstan"
    if any(_contains_keyword(text, term) for term in CENTRAL_ASIA_TERMS):
        return 0.24, "central_asia"
    if any(_contains_keyword(text, term) for term in REGIONAL_TERMS):
        return 0.08, "regional"
    if has_positive_geo_signal(opp) or any(
        _contains_keyword(text, term) for term in GLOBAL_TERMS
    ):
        return 0.10, "global"
    return 0.0, "unspecified"


def _deadline_actionability(opp: Opportunity, today: date) -> tuple[float, str]:
    if is_rolling_item(opp):
        return 0.04, "rolling"
    if opp.deadline is None:
        return 0.0, "unknown"
    days = (opp.deadline - today).days
    if days < 0:
        return 0.0, "closed"
    if days <= 2:
        return 0.02, "very_short_runway"
    if days <= 7:
        return 0.05, "short_runway"
    if days <= 21:
        return 0.10, "actionable"
    if days <= 45:
        return 0.08, "planned"
    if days <= 90:
        return 0.05, "longer_horizon"
    return 0.02, "future"


def score_breakdown(opp: Opportunity, today: date | None = None) -> ScoreBreakdown:
    """Calculate bounded relevance and a separate action-priority score."""

    today = today or date.today()
    text = f"{_primary_theme_text(opp)} {opp.summary}".lower()
    thematic, matched_themes = _thematic_component(opp)
    geographic, geography = _geographic_component(opp, text)
    source_context = 0.06 if str(opp.source).lower() in LOCAL_SOURCE_SLUGS else 0.0
    deadline_actionability, _ = _deadline_actionability(opp, today)
    reason = exclusion_reason(opp)
    low_confidence = is_low_confidence_for_kazakhstan_focus(opp)

    relevance = round(min(1.0, thematic + geographic + source_context), 4)
    confidence = "supported"
    if reason is not None:
        relevance = 0.0
        confidence = "excluded"
    elif low_confidence:
        relevance = min(relevance, LOW_CONFIDENCE_CAP)
        confidence = "review_required"

    priority = round(min(1.0, relevance * 0.90 + deadline_actionability), 4)
    if confidence in {"excluded", "review_required"}:
        priority = min(priority, relevance)

    return ScoreBreakdown(
        model_version=MODEL_VERSION,
        thematic=thematic,
        geographic=geographic,
        source_context=source_context,
        deadline_actionability=deadline_actionability,
        relevance=relevance,
        priority=priority,
        matched_themes=matched_themes,
        geography=geography,
        confidence=confidence,
        exclusion_reason=reason,
    )


def score(opp: Opportunity, today: date | None = None) -> float:
    """Return catalog relevance, not award probability or legal eligibility."""

    return score_breakdown(opp, today=today).relevance


def priority_score(opp: Opportunity, today: date | None = None) -> float:
    """Return action priority using relevance plus bounded deadline runway."""

    return score_breakdown(opp, today=today).priority


def ranking_payload(opp: Opportunity, today: date | None = None) -> dict[str, Any]:
    """Return a JSON-safe explanation for public and operator interfaces."""

    payload = asdict(score_breakdown(opp, today=today))
    payload["matched_themes"] = list(payload["matched_themes"])
    return payload
