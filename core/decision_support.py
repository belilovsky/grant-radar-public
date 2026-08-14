"""Honest decision support for public funding and procurement records.

The catalog deliberately does not decide legal eligibility.  This module makes
the boundary useful instead of vague: it distinguishes a live call from a
standing service or a reference page, then reports only the signals that can
be grounded in the public record and an anonymous browser profile.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from core.models import Opportunity

PROGRAM_KINDS = frozenset(
    {
        "application_call",
        "standing_service",
        "regulatory_guidance",
        "procurement_notice",
        "procurement_plan",
        "award_result",
        "information",
    }
)

PROFILE_FIELDS = (
    "applicant",
    "legal_form",
    "region",
    "sector",
    "stage",
    "support_need",
    "has_eds",
)

_GUIDANCE_TERMS = (
    "criteria",
    "rules",
    "guidance",
    "how to apply",
    "критер",
    "правил",
    "руководств",
    "порядок",
    "как подать",
)
_RESULT_TERMS = (
    "award result",
    "awarded",
    "winner",
    "results",
    "итоги",
    "результат",
    "победител",
)
_PLAN_TERMS = (
    "procurement plan",
    "annual plan",
    "план закуп",
    "годовой план",
)

_AUDIENCE_TERMS = {
    "startup": ("startup", "start-up", "стартап", "founder", "предприним"),
    "business": ("business", "sme", "entrepreneur", "бизнес", "предприним"),
    "farmer": (
        "farmer",
        "agriculture",
        "agro",
        "livestock",
        "фермер",
        "сельск",
        "животновод",
        "растениевод",
        "апк",
    ),
    "ngo": ("ngo", "nonprofit", "civil society", "нко", "нпо", "обществен"),
    "researcher": (
        "research",
        "science",
        "university",
        "academic",
        "исслед",
        "наук",
        "университет",
        "вуз",
    ),
    "student": ("student", "scholarship", "education grant", "студент", "стипенд"),
    "individual": ("individual", "citizen", "physical person", "физическ", "граждан"),
    "supplier": (
        "tender",
        "procurement",
        "supplier",
        "закуп",
        "поставщик",
        "подрядчик",
    ),
}

_LEGAL_FORM_TERMS = {
    "ip": ("ип", "individual entrepreneur", "sole proprietor"),
    "too": ("тоо", "llp", "limited liability"),
    "kfh": ("кх", "фх", "farm enterprise", "peasant farm", "фермерск"),
    "ngo": ("нко", "нпо", "ngo", "nonprofit", "общественн"),
    "university": ("вуз", "университет", "university", "research institute"),
    "individual": ("физическ", "individual", "citizen", "граждан"),
    "government": ("government", "state body", "государствен", "акимат"),
}

_SECTOR_TERMS = {
    "agro": ("agro", "agriculture", "crop", "сельск", "растениевод", "апк"),
    "livestock": ("livestock", "animal", "vet", "животновод", "вет"),
    "climate": ("climate", "green", "carbon", "климат", "зелён"),
    "ecology": (
        "ecology",
        "environment",
        "waste",
        "biodiversity",
        "эколог",
        "отход",
        "биоразнообраз",
    ),
    "it": ("it", "digital", "software", "ai", "technology", "цифров", "технолог", "ии"),
    "science": ("science", "research", "r&d", "наук", "исслед"),
    "social": ("social", "inclusion", "community", "социаль", "обществен"),
    "manufacturing": (
        "industry",
        "manufacturing",
        "production",
        "промышлен",
        "производств",
    ),
    "export": ("export", "trade", "экспорт", "внешн"),
}

_SUPPORT_TERMS = {
    "grant": ("grant", "contest", "competition", "грант", "конкурс"),
    "subsidy": ("subsidy", "reimbursement", "субсид", "возмещен"),
    "loan": ("loan", "credit", "guarantee", "лизинг", "заем", "кредит", "гаранти"),
    "accelerator": ("accelerator", "incubator", "акселератор", "инкубатор"),
    "procurement": ("tender", "procurement", "rfp", "закуп", "тендер"),
    "tax": ("tax", "preference", "льгот", "налог"),
}

# The browser profile stores stable slugs while source records can use Russian,
# Kazakh or English regional names.  Keep the mapping deliberately limited to
# names, rather than trying to infer a region from an organisation or URL.
_REGION_TERMS = {
    "almaty_city": ("г алматы", "город алматы", "алматы", "almaty city"),
    "astana": ("астана", "astana"),
    "shymkent": ("шымкент", "shymkent"),
    "almaty_region": (
        "алматинская область",
        "алматы облысы",
        "almaty region",
    ),
    "abay": ("область абай", "абай облысы", "abai region", "abay region"),
    "akmola": ("акмолинская область", "ақмола облысы", "akmola region"),
    "aktobe": ("актюбинская область", "ақтөбе облысы", "aktobe region"),
    "atyrau": ("атырауская область", "атырау облысы", "atyrau region"),
    "east_kazakhstan": (
        "восточно казахстанская область",
        "шығыс қазақстан облысы",
        "east kazakhstan region",
    ),
    "zhambyl": ("жамбылская область", "жамбыл облысы", "zhambyl region"),
    "zhetysu": ("область жетісу", "жетісу облысы", "zhetysu region"),
    "west_kazakhstan": (
        "западно казахстанская область",
        "батыс қазақстан облысы",
        "west kazakhstan region",
    ),
    "karaganda": ("карагандинская область", "қарағанды облысы", "karaganda region"),
    "kostanay": ("костанайская область", "қостанай облысы", "kostanay region"),
    "kyzylorda": ("кызылординская область", "қызылорда облысы", "kyzylorda region"),
    "mangystau": ("мангистауская область", "маңғыстау облысы", "mangystau region"),
    "pavlodar": ("павлодарская область", "павлодар облысы", "pavlodar region"),
    "north_kazakhstan": (
        "северо казахстанская область",
        "солтүстік қазақстан облысы",
        "north kazakhstan region",
    ),
    "turkistan": ("туркестанская область", "түркістан облысы", "turkistan region"),
    "ulytau": ("область улытау", "ұлытау облысы", "ulytau region"),
}


def _text(value: object) -> str:
    return str(value or "").strip()


def _raw(item: Opportunity) -> Mapping[str, Any]:
    return item.raw if isinstance(item.raw, Mapping) else {}


def _normalized(value: object) -> str:
    return re.sub(r"[^a-zа-яёәғқңөұүһі0-9]+", " ", _text(value).casefold()).strip()


def _blob(item: Opportunity) -> str:
    raw = _raw(item)
    values = [
        item.title,
        item.summary,
        item.type.value if hasattr(item.type, "value") else item.type,
        " ".join(item.tags),
        " ".join(item.eligibility),
        raw.get("notice_type"),
        raw.get("program_kind"),
        raw.get("record_kind"),
        raw.get("country"),
        raw.get("region"),
    ]
    return _normalized(" ".join(_text(value) for value in values))


def _contains_any(blob: str, terms: tuple[str, ...]) -> bool:
    return any(_normalized(term) in blob for term in terms)


def _lifecycle(item: Opportunity, lifecycle: str | None) -> str:
    raw = _raw(item)
    return _normalized(
        lifecycle
        or item.lifecycle
        or item.opportunity_status
        or raw.get("lifecycle")
        or raw.get("opportunity_status")
        or raw.get("status")
    ).replace(" ", "_")


def record_kind(item: Opportunity, *, lifecycle: str | None = None) -> str:
    """Classify the record without claiming that a guide is an open call."""

    raw = _raw(item)
    declared = _normalized(raw.get("record_kind") or raw.get("program_kind")).replace(
        " ", "_"
    )
    if declared in PROGRAM_KINDS:
        return declared

    blob = _blob(item)
    item_lifecycle = _lifecycle(item, lifecycle)
    type_value = _normalized(
        item.type.value if hasattr(item.type, "value") else item.type
    ).replace(" ", "_")
    if item_lifecycle == "awarded" or _contains_any(blob, _RESULT_TERMS):
        return "award_result"
    if _contains_any(blob, _PLAN_TERMS):
        return "procurement_plan"
    if type_value == "tender":
        return "procurement_notice"
    if (
        _contains_any(blob, _GUIDANCE_TERMS)
        and item.deadline is None
        and not raw.get("application_url")
    ):
        return "regulatory_guidance"
    if item.deadline is not None:
        return "application_call"
    if raw.get("application_url") or raw.get("deadline_policy") == "rolling":
        return "standing_service"
    if type_value in {"accelerator", "cloud_credit"}:
        return "standing_service"
    return "information"


def program_truth(item: Opportunity, *, lifecycle: str | None = None) -> dict[str, Any]:
    """Return a machine-readable, intentionally conservative action state."""

    raw = _raw(item)
    kind = record_kind(item, lifecycle=lifecycle)
    item_lifecycle = _lifecycle(item, lifecycle)
    application_url = _text(
        getattr(item, "application_url", "") or raw.get("application_url")
    )
    known = {
        "source": bool(_text(item.source_url)),
        "deadline": bool(item.deadline or raw.get("deadline_policy") == "rolling"),
        "amount": bool(
            item.amount_min is not None
            or item.amount_max is not None
            or raw.get("amount_raw")
        ),
        "eligibility": bool(item.eligibility or raw.get("eligibility")),
        "application_route": bool(application_url),
        "region": bool(_text(raw.get("region") or raw.get("country"))),
    }
    if item_lifecycle in {"closed", "awarded"}:
        actionability = "closed"
    elif kind == "award_result":
        actionability = "results"
    elif kind == "regulatory_guidance":
        actionability = "reference"
    elif kind == "procurement_plan":
        actionability = "plan"
    elif kind == "information":
        actionability = "monitor"
    elif application_url:
        actionability = "apply"
    else:
        actionability = "verify"
    return {
        "kind": kind,
        "actionability": actionability,
        "application_url": application_url or None,
        "known_fields": known,
        "missing_fields": [key for key, value in known.items() if not value],
    }


def normalize_profile(profile: Mapping[str, object] | None) -> dict[str, str]:
    """Keep the anonymous profile small, local and safe for a query string."""

    values = profile or {}
    normalized: dict[str, str] = {}
    for field in PROFILE_FIELDS:
        value = _normalized(values.get(field)).replace(" ", "_")
        if value and value not in {"all", "unknown", "none"}:
            normalized[field] = value
    return normalized


def _matches_profile_value(
    blob: str,
    value: str,
    mapping: Mapping[str, tuple[str, ...]],
) -> bool:
    terms = mapping.get(value)
    return bool(terms and _contains_any(blob, terms))


def _matches_region(source_region: str, region: str) -> bool:
    """Match only an explicit oblast/city name, with the Almaty exception."""

    if region == "almaty_city" and _matches_profile_value(
        source_region, "almaty_region", _REGION_TERMS
    ):
        return False
    return _matches_profile_value(source_region, region, _REGION_TERMS)


def assess_profile(
    item: Opportunity,
    profile: Mapping[str, object] | None,
    *,
    lifecycle: str | None = None,
) -> dict[str, Any]:
    """Assess observable fit signals, never a legal eligibility verdict."""

    values = normalize_profile(profile)
    truth = program_truth(item, lifecycle=lifecycle)
    blob = _blob(item)
    positives: list[str] = []
    checks: list[str] = []

    if truth["actionability"] in {"reference", "results", "plan", "monitor", "closed"}:
        checks.append(f"record_{truth['actionability']}")

    for field, mapping in (
        ("applicant", _AUDIENCE_TERMS),
        ("legal_form", _LEGAL_FORM_TERMS),
        ("sector", _SECTOR_TERMS),
        ("support_need", _SUPPORT_TERMS),
    ):
        value = values.get(field)
        if not value:
            continue
        if _matches_profile_value(blob, value, mapping):
            positives.append(f"{field}_signal")
        else:
            checks.append(f"{field}_verify")

    region = values.get("region")
    if region:
        raw = _raw(item)
        source_region = _normalized(raw.get("region") or raw.get("country"))
        if _matches_region(source_region, region):
            positives.append("region_signal")
        elif "kazakhstan" in source_region or "казахстан" in source_region:
            positives.append("kazakhstan_scope")
        else:
            checks.append("region_verify")

    if values.get("has_eds") == "yes" and truth["kind"] in {
        "standing_service",
        "application_call",
        "procurement_notice",
    }:
        positives.append("eds_ready")
    elif truth["kind"] in {"standing_service", "procurement_notice"}:
        checks.append("eds_verify")

    if not truth["known_fields"]["eligibility"]:
        checks.append("eligibility_missing")
    if (
        not truth["known_fields"]["application_route"]
        and truth["actionability"] == "apply"
    ):
        checks.append("application_route_verify")
    if truth["missing_fields"]:
        checks.append("programme_facts_missing")

    if truth["actionability"] in {"reference", "results", "plan", "monitor", "closed"}:
        status = "not_an_application"
    elif not values:
        status = "profile_needed"
    elif len(positives) >= 2 and "eligibility_missing" not in checks:
        status = "potential_fit"
    else:
        status = "verification_needed"

    return {
        "status": status,
        "profile": values,
        "truth": truth,
        "positive_signals": positives,
        "checks": list(dict.fromkeys(checks)),
        "legal_boundary": "This is a source-based pre-check, not a confirmation of eligibility.",
    }
