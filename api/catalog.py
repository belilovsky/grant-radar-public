"""Pure catalog grouping, search, and related-item policies."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from collections.abc import Iterable
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

from qazstack.opportunities import public_lifecycle

from core.models import Opportunity
from core.public_clock import public_today
from core.scoring import priority_score
from sources import PARSERS


def normalized_token(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def source_name(source_slug: str) -> str:
    source_cls = PARSERS.get(source_slug)
    if source_cls is not None:
        return str(source_cls.name)
    return source_slug.replace("_", " ").strip() or "Unknown source"


def funder_name(item: Opportunity) -> str:
    return str(item.funder or "").strip() or source_name(item.source)


def slugify_funder(value: str) -> str:
    normalized = normalized_token(value)
    ascii_value = (
        unicodedata.normalize("NFKD", normalized).encode("ascii", "ignore").decode()
    )
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    if slug:
        return slug
    return f"funder-{uuid5(NAMESPACE_URL, normalized or value).hex[:10]}"


def funder_region_tokens(item: Opportunity) -> set[str]:
    tags = {normalized_token(tag) for tag in item.tags if normalized_token(tag)}
    raw = item.raw if isinstance(item.raw, dict) else {}
    blob = " ".join(
        [
            str(raw.get("country") or ""),
            str(raw.get("region") or ""),
            str(raw.get("borrower") or ""),
            str(item.summary or ""),
            str(item.title or ""),
        ]
    ).lower()
    regions: set[str] = set()
    if (
        "kazakhstan" in tags
        or "kazakhstan" in blob
        or "казахстан" in blob
        or "қазақстан" in blob
    ):
        regions.add("kazakhstan")
    if (
        "central_asia" in tags
        or "central_asia_eligible" in tags
        or "central asia" in blob
        or "центральн" in blob
    ):
        regions.add("central_asia")
    if "global" in tags and not regions:
        regions.add("global")
    if not regions:
        regions.add("global")
    return regions


def opportunity_search_blob(item: Opportunity) -> str:
    raw = item.raw if isinstance(item.raw, dict) else {}
    values: list[Any] = [
        item.title,
        item.summary,
        item.funder,
        item.source,
        *item.tags,
        *item.eligibility,
        *(
            raw.get(key)
            for key in ("page_title", "listing_title", "reference", "agency", "country")
        ),
    ]
    return normalized_token(" ".join(str(value or "") for value in values))


def matches_opportunity_query(item: Opportunity, query: str) -> bool:
    tokens = [token for token in normalized_token(query).split(" ") if token]
    if not tokens:
        return True
    blob = opportunity_search_blob(item)
    return all(token in blob for token in tokens)


def funder_tag_tokens(item: Opportunity) -> list[str]:
    ignored = {
        "rolling",
        "closed",
        "watchlist",
        "global",
        "kazakhstan",
        "central_asia",
        "central_asia_eligible",
    }
    return [
        normalized_token(tag)
        for tag in item.tags
        if normalized_token(tag) and normalized_token(tag) not in ignored
    ]


def build_funder_index(items: Iterable[Opportunity]) -> dict[str, dict[str, Any]]:
    today = public_today()
    groups: dict[str, dict[str, Any]] = {}
    for item in items:
        name = funder_name(item)
        slug = slugify_funder(name)
        group = groups.setdefault(
            slug,
            {
                "slug": slug,
                "name": name,
                "items": [],
                "types": Counter(),
                "tags": Counter(),
                "regions": Counter(),
                "sources": {},
                "open_items": 0,
                "closing_soon_items": 0,
                "rolling_items": 0,
                "forecast_items": 0,
                "closed_items": 0,
                "awarded_items": 0,
                "current_items": 0,
                "score_sum": 0.0,
                "next_deadline": None,
            },
        )
        group["items"].append(item)
        group["score_sum"] += float(item.score or 0.0)
        group["types"].update([item.type.value])
        group["tags"].update(funder_tag_tokens(item))
        group["regions"].update(funder_region_tokens(item))
        source_slug = str(item.source)
        if source_slug not in group["sources"]:
            group["sources"][source_slug] = {
                "slug": source_slug,
                "name": source_name(source_slug),
                "base_url": getattr(PARSERS.get(source_slug), "base_url", ""),
            }
        lifecycle = public_lifecycle(item, today=today)
        count_key = f"{lifecycle}_items"
        group[count_key] = int(group.get(count_key, 0)) + 1
        if lifecycle in {"open", "closing_soon", "rolling"}:
            group["current_items"] += 1
        if item.deadline and item.deadline >= today:
            current_next_deadline = group["next_deadline"]
            if current_next_deadline is None or item.deadline < current_next_deadline:
                group["next_deadline"] = item.deadline

    for group in groups.values():
        rows = cast(list[Opportunity], group["items"])
        rows.sort(
            key=lambda row: (
                priority_score(row, today=today),
                row.score,
                row.discovered_at,
            ),
            reverse=True,
        )
        total_items = len(rows)
        group["total_items"] = total_items
        group["avg_score"] = (
            round(group["score_sum"] / total_items, 3) if total_items else 0
        )
        group["top_tags"] = [
            tag for tag, _ in cast(Counter[str], group["tags"]).most_common(4)
        ]
        group["top_regions"] = [
            region for region, _ in cast(Counter[str], group["regions"]).most_common(3)
        ]
        group["top_types"] = [
            kind for kind, _ in cast(Counter[str], group["types"]).most_common(3)
        ]
        group["sources"] = sorted(
            cast(dict[str, dict[str, str]], group["sources"]).values(),
            key=lambda row: (row["name"], row["slug"]),
        )
    return groups


def funder_payload(group: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "slug",
        "name",
        "total_items",
        "current_items",
        "open_items",
        "closing_soon_items",
        "rolling_items",
        "forecast_items",
        "closed_items",
        "awarded_items",
        "avg_score",
        "next_deadline",
        "top_tags",
        "top_regions",
        "top_types",
        "sources",
    )
    return {key: group[key] for key in keys}


def similarity_tokens(item: Opportunity) -> set[str]:
    raw = item.raw if isinstance(item.raw, dict) else {}
    tokens = {
        f"tag:{normalized_token(tag)}" for tag in item.tags if normalized_token(tag)
    }
    for key in ("country", "region", "borrower", "notice_type", "deadline_policy"):
        normalized = normalized_token(raw.get(key))
        if normalized:
            tokens.add(f"{key}:{normalized}")
    return tokens


def related_reason_key(target: Opportunity, candidate: Opportunity) -> str:
    if candidate.source == target.source:
        return "related_reason_source"
    if normalized_token(candidate.funder) and normalized_token(
        candidate.funder
    ) == normalized_token(target.funder):
        return "related_reason_funder"
    if similarity_tokens(target) & similarity_tokens(candidate):
        return "related_reason_theme"
    return "related_reason_format"


def related_relevance(target: Opportunity, candidate: Opportunity) -> float:
    target_tokens = similarity_tokens(target)
    candidate_tokens = similarity_tokens(candidate)
    union = target_tokens | candidate_tokens
    jaccard = len(target_tokens & candidate_tokens) / len(union) if union else 0.0
    same_funder = bool(
        normalized_token(target.funder)
        and normalized_token(target.funder) == normalized_token(candidate.funder)
    )
    same_type = target.type == candidate.type
    same_source = target.source == candidate.source
    value = (
        jaccard * 0.40
        + float(same_funder) * 0.30
        + float(same_type) * 0.15
        + float(same_source) * 0.10
        + float(candidate.score or 0.0) * 0.05
    )
    return round(min(1.0, value), 4)
