"""Audit live QAZ.FUND content coverage and opportunity quality."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from api.dashboard import dashboard_copy

try:
    from datetime import UTC
except ImportError:  # pragma: no cover - Python < 3.11 compatibility
    UTC = timezone.utc

DEFAULT_FORBIDDEN_TERMS = (
    "AI3 Action Institute",
    "American Indians",
    "Native Americans",
    "federally recognized tribes",
    "Technical Difficulties",
)


@dataclass(frozen=True)
class ContentAuditResult:
    status: str
    source_count: int
    opportunity_count: int
    relevant_open_items: int
    zero_item_sources: list[str] = field(default_factory=list)
    stale_sources: list[str] = field(default_factory=list)
    missing_summary_titles: list[str] = field(default_factory=list)
    short_summary_titles: list[str] = field(default_factory=list)
    missing_deadline_titles: list[str] = field(default_factory=list)
    rootish_source_urls: list[str] = field(default_factory=list)
    html_entity_titles: list[str] = field(default_factory=list)
    missing_detail_status_titles: list[str] = field(default_factory=list)
    unlocalized_tags: dict[str, list[str]] = field(default_factory=dict)
    forbidden_hits: dict[str, list[str]] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)


def _url(base_url: str, path: str) -> str:
    return urljoin(f"{base_url.rstrip('/')}/", path.lstrip("/"))


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _item_text(item: dict[str, Any]) -> str:
    parts = [
        str(item.get("title") or ""),
        str(item.get("summary") or ""),
        " ".join(str(tag) for tag in item.get("tags") or []),
    ]
    raw = item.get("raw")
    if isinstance(raw, dict):
        parts.extend(str(value) for value in raw.values() if value is not None)
    return " ".join(parts)


def _visible_item_text(item: dict[str, Any]) -> str:
    parts = [
        str(item.get("title") or ""),
        str(item.get("summary") or ""),
        str(item.get("funder") or ""),
        " ".join(str(value) for value in item.get("eligibility") or []),
        " ".join(str(tag) for tag in item.get("tags") or []),
    ]
    return " ".join(parts)


def _rootish_source_url(value: Any) -> bool:
    if not value:
        return True
    parsed = urlparse(str(value))
    if not parsed.scheme or not parsed.netloc:
        return True
    path = (parsed.path or "/").strip("/").lower()
    return path in {
        "",
        "en",
        "ru",
        "programs",
        "services",
        "opportunities",
        "grants",
        "tenders",
        "funding",
        "support",
    }


def _raw_payload(item: dict[str, Any]) -> dict[str, Any]:
    raw = item.get("raw")
    return raw if isinstance(raw, dict) else {}


def _has_detail_contract(item: dict[str, Any]) -> bool:
    raw = _raw_payload(item)
    if str(raw.get("detail_text") or "").strip():
        return True
    sections = raw.get("detail_sections")
    if isinstance(sections, list) and any(
        isinstance(section, dict) and str(section.get("text") or "").strip()
        for section in sections
    ):
        return True
    return bool(str(raw.get("detail_fetch_status") or "").strip())


def _label_key(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _dashboard_label_maps() -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for lang in ("ru", "en"):
        raw = dashboard_copy(lang).get("label_map")
        result[lang] = dict(raw) if isinstance(raw, dict) else {}
    return result


def analyze_content(
    *,
    coverage: dict[str, Any],
    opportunities: list[dict[str, Any]],
    forbidden_terms: list[str],
    min_sources: int,
    min_opportunities: int,
    stale_after_days: int,
    label_maps: dict[str, dict[str, object]] | None = None,
    now: datetime | None = None,
) -> ContentAuditResult:
    now = now or datetime.now(UTC)
    source_rows = list(coverage.get("sources") or [])
    zero_item_sources: list[str] = []
    stale_sources: list[str] = []
    issues: list[str] = []

    stale_cutoff = now - timedelta(days=stale_after_days)
    for row in source_rows:
        slug = str(row.get("slug") or "")
        items = int(row.get("items") or 0)
        if row.get("enabled") and items == 0:
            zero_item_sources.append(slug)
        last_seen = _parse_datetime(row.get("last_discovered_at"))
        if row.get("enabled") and items > 0 and last_seen and last_seen < stale_cutoff:
            stale_sources.append(slug)

    source_count = int(coverage.get("enabled_sources") or 0)
    relevant_open_items = int(coverage.get("relevant_open_items") or 0)
    opportunity_count = len(opportunities)
    if zero_item_sources:
        issues.append(
            f"enabled sources with zero items: {', '.join(zero_item_sources)}"
        )
    if stale_sources:
        issues.append(f"enabled stale sources: {', '.join(stale_sources)}")
    if source_count < min_sources:
        issues.append(f"enabled source count {source_count} < {min_sources}")
    if opportunity_count < min_opportunities:
        issues.append(f"opportunity count {opportunity_count} < {min_opportunities}")

    missing_summary_titles = [
        str(item.get("title") or "")
        for item in opportunities
        if not str(item.get("summary") or "").strip()
    ][:20]
    if missing_summary_titles:
        issues.append(
            f"{len(missing_summary_titles)} opportunities are missing summary"
        )

    short_summary_titles = [
        str(item.get("title") or "")
        for item in opportunities
        if 0 < len(str(item.get("summary") or "").strip()) < 60
    ][:20]
    if short_summary_titles:
        issues.append(f"{len(short_summary_titles)} opportunities have short summary")

    missing_deadline_titles = [
        str(item.get("title") or "")
        for item in opportunities
        if not item.get("deadline") and "rolling" not in (item.get("tags") or [])
    ][:20]
    if missing_deadline_titles:
        issues.append(
            f"{len(missing_deadline_titles)} opportunities have no deadline policy"
        )

    rootish_source_urls = [
        str(item.get("source_url") or "")
        for item in opportunities
        if _rootish_source_url(item.get("source_url"))
    ][:20]
    if rootish_source_urls:
        issues.append(f"{len(rootish_source_urls)} opportunities have weak source_url")

    entity_re = re.compile(r"&(?:[a-zA-Z]+|#\d+|#x[0-9a-fA-F]+);")
    html_entity_titles = [
        str(item.get("title") or "")
        for item in opportunities
        if entity_re.search(_visible_item_text(item))
    ][:20]
    if html_entity_titles:
        issues.append(f"{len(html_entity_titles)} opportunities contain HTML entities")

    missing_detail_status_titles = [
        str(item.get("title") or "")
        for item in opportunities
        if str(item.get("source") or "") == "kazakhstan_domestic_support"
        and not _has_detail_contract(item)
    ][:20]
    if missing_detail_status_titles:
        issues.append(
            f"{len(missing_detail_status_titles)} domestic support items lack detail contract"
        )

    unlocalized_tags: dict[str, list[str]] = {}
    if label_maps:
        tags = {
            str(tag).strip()
            for item in opportunities
            for tag in item.get("tags") or []
            if str(tag).strip()
        }
        for lang, label_map in label_maps.items():
            normalized_labels = {_label_key(key) for key in label_map}
            missing = sorted(
                tag for tag in tags if _label_key(tag) not in normalized_labels
            )
            if missing:
                unlocalized_tags[lang] = missing
        if unlocalized_tags:
            issues.append("public tags are missing localized display labels")

    forbidden_hits: dict[str, list[str]] = {}
    for term in forbidden_terms:
        matches = [
            str(item.get("title") or "")
            for item in opportunities
            if term.lower() in _item_text(item).lower()
        ]
        if matches:
            forbidden_hits[term] = matches[:10]
    if forbidden_hits:
        issues.append("forbidden content terms found")

    status = "ok" if not issues else "needs_attention"
    return ContentAuditResult(
        status=status,
        source_count=source_count,
        opportunity_count=opportunity_count,
        relevant_open_items=relevant_open_items,
        zero_item_sources=zero_item_sources,
        stale_sources=stale_sources,
        missing_summary_titles=missing_summary_titles,
        short_summary_titles=short_summary_titles,
        missing_deadline_titles=missing_deadline_titles,
        rootish_source_urls=rootish_source_urls,
        html_entity_titles=html_entity_titles,
        missing_detail_status_titles=missing_detail_status_titles,
        unlocalized_tags=unlocalized_tags,
        forbidden_hits=forbidden_hits,
        issues=issues,
    )


def run_audit(
    *,
    base_url: str,
    deadline_after: str,
    min_sources: int,
    min_opportunities: int,
    stale_after_days: int,
    forbidden_terms: list[str],
    timeout: float,
) -> ContentAuditResult:
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        coverage = client.get(_url(base_url, "/coverage"))
        coverage.raise_for_status()
        opportunities = client.get(
            _url(
                base_url,
                (
                    "/opportunities?limit=1000&min_score=0.3"
                    f"&deadline_after={deadline_after}"
                ),
            )
        )
        opportunities.raise_for_status()
    return analyze_content(
        coverage=coverage.json(),
        opportunities=opportunities.json(),
        forbidden_terms=forbidden_terms,
        min_sources=min_sources,
        min_opportunities=min_opportunities,
        stale_after_days=stale_after_days,
        label_maps=_dashboard_label_maps(),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://qaz.fund")
    parser.add_argument("--deadline-after", default=date.today().isoformat())
    parser.add_argument("--min-sources", type=int, default=23)
    parser.add_argument("--min-opportunities", type=int, default=45)
    parser.add_argument("--stale-after-days", type=int, default=7)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument(
        "--forbid",
        action="append",
        default=list(DEFAULT_FORBIDDEN_TERMS),
        help="Text that must not appear in relevant open opportunities.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = run_audit(
            base_url=args.base_url,
            deadline_after=args.deadline_after,
            min_sources=args.min_sources,
            min_opportunities=args.min_opportunities,
            stale_after_days=args.stale_after_days,
            forbidden_terms=list(args.forbid or []),
            timeout=args.timeout,
        )
    except httpx.HTTPError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 1

    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    return 0 if result.status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
