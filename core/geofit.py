"""Geographic fit helpers for the Kazakhstan/Central Asia radar focus."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Any

CENTRAL_ASIA_GEO_PATTERNS = (
    r"\bkazakhstan\b",
    r"\bcentral[\s_-]+asia\b",
    r"\bcentral[\s_-]+asian\b",
    r"\beurasia\b",
    r"\bcis\b",
    r"\buzbekistan\b",
    r"\bkyrgyzstan\b",
    r"\btajikistan\b",
    r"\bturkmenistan\b",
)

GLOBAL_GEO_PATTERNS = (
    r"\bglobal\b",
    r"\bworldwide\b",
    r"\binternational\b",
    r"\bany[\s_-]+country\b",
    r"\ball[\s_-]+countries\b",
)

POSITIVE_GEO_PATTERNS = CENTRAL_ASIA_GEO_PATTERNS + GLOBAL_GEO_PATTERNS

HARD_EXCLUSION_PATTERNS = (
    r"\((?:u\.?s\.?|usa|united[\s_-]+states|hungary|iraq|india)\)",
    r"\bamerican[\s_-]+indians?\b",
    r"\basean\b",
    r"\beast[\s_-]+asia\b",
    r"\bjakarta\b",
    r"\bnative[\s_-]+americans?\b",
    r"\balaska[\s_-]+natives?\b",
    r"\bnative[\s_-]+hawaiians?\b",
    r"\bfederally[\s_-]+recognized[\s_-]+tribes?\b",
    r"\bindian[\s_-]+tribes?\b",
    r"\btribal[\s_-]+governments?\b",
    r"\btribal[\s_-]+organizations?\b",
    r"\bu\.?s\.?[\s_-]+only\b",
    r"\bunited[\s_-]+states[\s_-]+only\b",
    r"\bu\.?s\.?[\s_-]+citizens?\b",
    r"\bunited[\s_-]+states[\s_-]+citizens?\b",
    r"\bu\.?s\.?[\s_-]+permanent[\s_-]+residents?\b",
    r"\bstate[\s_-]+governments?\b",
    r"\bcounty[\s_-]+governments?\b",
    r"\bcity[\s_-]+or[\s_-]+township[\s_-]+governments?\b",
    r"\bindependent[\s_-]+school[\s_-]+districts?\b",
    r"\bpublic[\s_-]+housing[\s_-]+authorities?\b",
    r"\bhungary\b",
    r"\biraq\b",
    r"\bindia\b",
    r"\buk[\s_-]+student[\s_-]+finance\b",
)

LOW_CONFIDENCE_SOURCE_SLUGS = {"grants_gov", "opportunity_desk", "fundsforngos"}
GLOBAL_BRIDGE_SOURCE_SLUGS = {"opportunity_desk", "fundsforngos"}

OUT_OF_REGION_ONLY_PATTERNS = (
    r"\bukraine\b",
    r"\bукраин\w*\b",
    r"\bmena\b",
    r"\bmiddle[\s_-]+east\b",
    r"\bближн\w+[\s_-]+восток\w*\b",
    r"\bnorth[\s_-]+africa\b",
    r"\bсеверн\w+[\s_-]+африк\w*\b",
    r"\bbrussels\b",
    r"\bбрюссел\w*\b",
    r"\bbelgium\b",
    r"\bбельги\w*\b",
)
OUT_OF_REGION_CHECK_SOURCE_SLUGS = {
    "grants_gov",
    "internews",
    "opportunity_desk",
    "fundsforngos",
}

GLOBAL_BRIDGE_REGION_EXCLUSIONS = (
    r"\bafrica\b",
    r"\bafrican\b",
    r"\bsouth[\s_-]+africa\b",
)

GLOBAL_BRIDGE_EVENT_ONLY_PATTERNS = (
    r"\bconference\b",
    r"\bfully[\s_-]+funded[\s_-]+trip\b",
    r"\bvideo[\s_-]+competition\b",
    r"\bphoto[\s_-]+competition\b",
)

PROCUREMENT_OPERATIONAL_SERVICE_PATTERNS = (
    r"\baccommodation\b",
    r"\bcatering\b",
    r"\bconference[\s_-]+hall\b",
    r"\bconference[\s_-]+package\b",
    r"\bconference[\s_-]+services\b",
    r"\bevent[\s_-]+management\b",
    r"\bhotel\b",
    r"\bhotel[\s_-]+services\b",
    r"\bmeeting[\s_-]+room\b",
    r"\blodging\b",
    r"\bvenue\b",
    r"\bпроживан\w*\b",
    r"\bгостини\w*\b",
    r"\bотел\w*\b",
    r"\bконференц\w*\b",
    r"\bразмещени\w*\b",
    r"\bкейтеринг\w*\b",
)

EEAS_NON_OPPORTUNITY_PATTERNS = (
    r"\bcontracts?[\s_-]+were[\s_-]+concluded\b",
    r"\blist[\s_-]+of[\s_-]+contracts?\b",
    r"\bcontracts?[\s_-]+concluded\b",
    r"\baward[\s_-]+notice\b",
    r"\bпереч\w+\s+контракт\w+\b",
    r"\bзаключенн\w+\s+в\s+рамках\b",
)

STATE_BORROWER_PATTERNS = (
    r"\brepublic[\s_-]+of[\s_-]+kazakhstan\b",
    r"\bministry[\s_-]+of[\s_-]+finance\b",
    r"\bgovernment[\s_-]+of[\s_-]+kazakhstan\b",
    r"\bnational[\s_-]+bank[\s_-]+of[\s_-]+kazakhstan\b",
)

STATE_LENDING_PATTERNS = (
    r"\bdevelopment[\s_-]+policy[\s_-]+financing\b",
    r"\bprogram-for-results\b",
    r"\bpforr\b",
)

GRANTS_GOV_PRODUCT_FOCUS_EXCLUSIONS = (
    r"\btourism[\s_-]+industry\b",
    r"\bstorytelling[\s_-]+to[\s_-]+safeguard[\s_-]+cultural[\s_-]+identity\b",
    r"\bpublic[\s_-]+diplomacy\b",
    r"\bu\.?s\.?[\s_-]+mission\b",
    r"\bu\.?s\.?[\s_-]+embassy\b",
    r"\bpas[\s_-]+annual[\s_-]+program[\s_-]+statement\b",
    r"\bhousing[\s_-]+construction\b",
    r"\bautomated[\s_-]+permitting[\s_-]+systems?\b",
    r"\bpolice(?:\s+recruitment)?\b",
    r"\bnarcotics[\s_-]+control\b",
    r"\bbureau[\s_-]+of[\s_-]+international[\s_-]+narcotics[\s_-]+[-–]?law[\s_-]+enforcement\b",
    r"\bbureau[\s_-]+of[\s_-]+arms[\s_-]+control[\s_-]+and[\s_-]+nonproliferation\b",
    r"\bfood[\s_-]+for[\s_-]+peace\b",
    r"\bmcgovern[\s_-]+dole\b",
    r"\btribal[\s_-]+students?\b",
    r"\bstudents?\s+from\s+tribes?\b",
    r"\bcounter[\s_-]*terroris[mt]\b",
    r"\bcounter(?:ing)?[\s_-]+terroris[mt]\b",
    r"\bterrorist[\s_-]+financing\b",
    r"\bterrorist[\s_-]+recruitment\b",
    r"\bforeign[\s_-]+terrorist[\s_-]+fighters?\b",
    r"\bобщественной[\s_-]+дипломат\w*\b",
    r"\bмисси[ия]\s+сша\b",
    r"\bпосольств\w+\s+сша\b",
    r"\bжилищн\w+\s+строительств\w*\b",
    r"\bавтоматизированн\w+\s+систем\w+\s+разрешен\w*\b",
    r"\bполицейск\w+\b",
    r"\bборьб\w+\s+с\s+fto\b",
    r"\bпитани\w+\s+для\s+мира\b",
    r"\bмакговерн[\s_-]*доул\b",
    r"\bстудент\w+\s+из\s+племен\w*\b",
)

HARD_EXCLUSION_RAW_VALUES = (
    "HHS-ACF-ANA",
    "Administration for Native Americans",
    "AI3 Action Institute",
    "Technical Difficulties",
    "experiencing technical difficulties",
)

GRANTS_GOV_DOMESTIC_AGENCY_PATTERNS = (
    r"\bbureau[\s_-]+of[\s_-]+educational[\s_-]+and[\s_-]+cultural[\s_-]+affairs\b",
    r"\bbureau[\s_-]+of[\s_-]+international[\s_-]+narcotics[\s_-]+[-–]?law[\s_-]+enforcement\b",
    r"\bnational[\s_-]+institute[\s_-]+of[\s_-]+food[\s_-]+and[\s_-]+agriculture\b",
    r"\bnational[\s_-]+institutes?[\s_-]+of[\s_-]+health\b",
    r"\bdept\.?[\s_-]+of[\s_-]+the[\s_-]+army\b",
    r"\bdepartment[\s_-]+of[\s_-]+education\b",
    r"\boffice[\s_-]+of[\s_-]+postsecondary[\s_-]+education\b",
    r"\boffice[\s_-]+of[\s_-]+elementary[\s_-]+and[\s_-]+secondary[\s_-]+education\b",
    r"\bemployment[\s_-]+and[\s_-]+training[\s_-]+administration\b",
    r"\bfaa[\s_-]+[\-–]\s+aviation[\s_-]+next[\s_-]+gen\b",
    r"\bdot[\s_-]*[\-–]\s*federal[\s_-]+motor[\s_-]+carrier[\s_-]+safety[\s_-]+administration\b",
    r"\bforeign[\s_-]+agricultural[\s_-]+service\b",
    r"\bbureau[\s_-]+of[\s_-]+reclamation\b",
    r"\bcenters?[\s_-]+for[\s_-]+disease[\s_-]+control(?:[\s_-]+and[\s_-]+prevention)?\b",
    r"\boffice[\s_-]+of[\s_-]+international[\s_-]+religious[\s_-]+freedom\b",
    r"\brural[\s_-]+utilities[\s_-]+service\b",
    r"\bnational[\s_-]+institute[\s_-]+of[\s_-]+standards[\s_-]+and[\s_-]+technology\b",
    r"\bconsumer[\s_-]+product[\s_-]+safety[\s_-]+commission\b",
    r"\brural[\s_-]+business[\s_-]+cooperative[\s_-]+service\b",
    r"\bgeological[\s_-]+survey\b",
    r"\bfish[\s_-]+and[\s_-]+wildlife[\s_-]+service\b",
    r"\bdepartment[\s_-]+of[\s_-]+homeland[\s_-]+security[\s_-]*[\-–]\s*fema\b",
    r"\bpipeline[\s_-]+and[\s_-]+hazardous[\s_-]+materials?[\s_-]+safety[\s_-]+admin\b",
    r"\bfood[\s_-]+and[\s_-]+nutrition[\s_-]+service\b",
    r"\banimal[\s_-]+and[\s_-]+plant[\s_-]+health[\s_-]+inspection[\s_-]+service\b",
    r"\bnational[\s_-]+institute[\s_-]+of[\s_-]+justice\b",
)


def _get(item: Any, key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)


def _flatten(value: Any) -> Iterable[str]:
    if value is None:
        return
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _flatten(nested)
        return
    if isinstance(value, Iterable):
        for nested in value:
            yield from _flatten(nested)
        return
    yield str(value)


def _text(item: Any, *, include_raw: bool, include_tags: bool) -> str:
    parts: list[str] = []
    for key in ("title", "summary", "description", "funder"):
        value = _get(item, key)
        if value:
            parts.extend(_flatten(value))
    parts.extend(_flatten(_get(item, "eligibility")))
    parts.extend(_flatten(_get(item, "languages")))
    if include_tags:
        parts.extend(_flatten(_get(item, "tags")))
    raw = _get(item, "raw") if include_raw else None
    if raw is not None:
        parts.extend(_flatten(raw))
    return " ".join(parts).lower()


def _raw_json(item: Any) -> str:
    raw = _get(item, "raw")
    try:
        return json.dumps(raw or {}, ensure_ascii=False, default=str)
    except TypeError:
        return str(raw or "")


def _raw_text_value(item: Any, *keys: str) -> str:
    raw = _get(item, "raw")
    if not isinstance(raw, dict):
        return ""
    parts: list[str] = []
    for key in keys:
        parts.extend(_flatten(raw.get(key)))
    return " ".join(parts).lower()


def _matches_any(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def has_positive_geo_signal(item: Any) -> bool:
    text = _text(item, include_raw=False, include_tags=False)
    return any(
        re.search(pattern, text, re.IGNORECASE) for pattern in POSITIVE_GEO_PATTERNS
    )


def has_central_asia_geo_signal(item: Any) -> bool:
    text = _text(item, include_raw=False, include_tags=False)
    return any(
        re.search(pattern, text, re.IGNORECASE) for pattern in CENTRAL_ASIA_GEO_PATTERNS
    )


def exclusion_reason(item: Any) -> str | None:
    source = str(_get(item, "source") or "").lower()
    text = _text(item, include_raw=True, include_tags=True)

    if source == "world_bank_kazakhstan":
        borrower = _raw_text_value(item, "borrower")
        lending = _raw_text_value(item, "lendinginstr")
        if _matches_any(borrower, STATE_BORROWER_PATTERNS):
            return "state-borrower project"
        if _matches_any(lending, STATE_LENDING_PATTERNS):
            return "state-lending instrument"

    if source == "grants_gov" and _matches_any(
        text, GRANTS_GOV_PRODUCT_FOCUS_EXCLUSIONS
    ):
        return "outside Grants.gov product focus"
    if source == "grants_gov" and not has_central_asia_geo_signal(item):
        agency_text = _raw_text_value(item, "agencyName", "agency", "agencyCode")
        if _matches_any(agency_text, GRANTS_GOV_DOMESTIC_AGENCY_PATTERNS):
            return "domestic Grants.gov agency"

    if source == "undp_procurement" and _matches_any(
        text, PROCUREMENT_OPERATIONAL_SERVICE_PATTERNS
    ):
        return "operational procurement service"

    if source == "eeas_kazakhstan" and _matches_any(
        text, EEAS_NON_OPPORTUNITY_PATTERNS
    ):
        return "eeas post-award page"

    if (
        source in OUT_OF_REGION_CHECK_SOURCE_SLUGS
        and not has_central_asia_geo_signal(item)
        and _matches_any(text, OUT_OF_REGION_ONLY_PATTERNS)
    ):
        return "outside Kazakhstan/Central Asia region"

    if source in GLOBAL_BRIDGE_SOURCE_SLUGS and not has_central_asia_geo_signal(item):
        source_text = _text(item, include_raw=False, include_tags=True)
        if _matches_any(source_text, GLOBAL_BRIDGE_REGION_EXCLUSIONS):
            return "outside Kazakhstan/Central Asia region"
        if source == "opportunity_desk" and _matches_any(
            source_text, GLOBAL_BRIDGE_EVENT_ONLY_PATTERNS
        ):
            return "event-only global bridge item"

    for pattern in HARD_EXCLUSION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return pattern

    raw_text = _raw_json(item)
    for value in HARD_EXCLUSION_RAW_VALUES:
        if value.lower() in raw_text.lower():
            return value
    return None


def is_excluded_for_kazakhstan_focus(item: Any) -> bool:
    return exclusion_reason(item) is not None


def is_low_confidence_for_kazakhstan_focus(item: Any) -> bool:
    source = str(_get(item, "source") or "").lower()
    return source in LOW_CONFIDENCE_SOURCE_SLUGS and not has_central_asia_geo_signal(
        item
    )


def is_relevant_for_kazakhstan_focus(item: Any) -> bool:
    return not (
        is_excluded_for_kazakhstan_focus(item)
        or is_low_confidence_for_kazakhstan_focus(item)
    )
