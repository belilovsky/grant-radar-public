"""Production smoke checks for a live QAZ.FUND deployment."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import httpx

from api.integration_versions import AVDS_VERSION, QAZSTACK_VERSION
from core.public_clock import public_today
from scripts.http_utils import join_url as _url

DASHBOARD_MARKERS = (
    '<html lang="ru"',
    'data-avds="grant-radar"',
    'data-av-theme="light"',
    'data-lang="ru"',
    'data-avds-component="admin-shell"',
    'data-avds-component="hero-band"',
    'data-avds-component="sticky-shell"',
    'data-avds-component="filter-summary"',
    'class="toolbar avds-tabs-list"',
    "avds-tabs-trigger",
    "avds-field",
    'data-avds-component="opportunity-card"',
    'id="filter-disclosure"',
    "avds-document-row",
)
MARKETING_MARKERS = (
    "Sitemap:",
    "<urlset",
)
GENERATED_ASSET_PATTERN = re.compile(
    r'(?:href|src)="(?P<path>/assets/generated/[0-9a-f]{64}\.(?:css|js))"'
)


class SmokeError(RuntimeError):
    """Raised when a production smoke check fails."""


@dataclass(frozen=True)
class SmokeResult:
    base_url: str
    release_revision: str
    release_image_digest: str
    release_artifact_digest: str
    release_built_at: str
    release_deployed_at: str
    deadline_after: str
    health_items: int
    ready_backend: str
    coverage_sources: int
    coverage_relevant_open_items: int
    coverage_stale_sources: int
    coverage_unknown_freshness_sources: int
    opportunities: int
    ndjson_items: int
    digest_items: int
    media_items: int
    media_feed_items: int
    forbidden_hits: list[str]
    dashboard_markers: dict[str, bool]
    english_dashboard: bool
    discovery_surfaces: dict[str, bool]


def _get_json(client: httpx.Client, base_url: str, path: str) -> Any:
    response = client.get(_url(base_url, path))
    response.raise_for_status()
    return response.json()


def _get_text(client: httpx.Client, base_url: str, path: str) -> str:
    response = client.get(_url(base_url, path))
    response.raise_for_status()
    return response.text


def _head(client: httpx.Client, base_url: str, path: str) -> httpx.Response:
    response = client.head(_url(base_url, path))
    response.raise_for_status()
    return response


def _dashboard_assets(client: httpx.Client, base_url: str, dashboard_html: str) -> str:
    """Load only same-origin, content-hashed dashboard assets for UI markers."""
    paths = sorted(
        {
            match.group("path")
            for match in GENERATED_ASSET_PATTERN.finditer(dashboard_html)
        }
    )
    return "\n".join(_get_text(client, base_url, path) for path in paths)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeError(message)


def _release_timestamp(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
    except ValueError as exc:
        raise SmokeError(f"release {field} is not an ISO timestamp") from exc
    _require(parsed.tzinfo is not None, f"release {field} lacks a timezone")
    return parsed


def _is_public_cacheable(response: httpx.Response, min_age: int) -> bool:
    cache_control = response.headers.get("cache-control", "").lower()
    return "public" in cache_control and f"max-age={min_age}" in cache_control


def _contains_key(value: Any, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(
            _contains_key(child, key) for child in value.values()
        )
    if isinstance(value, list):
        return any(_contains_key(child, key) for child in value)
    return False


def run_smoke(
    *,
    base_url: str,
    deadline_after: str,
    min_sources: int,
    min_opportunities: int,
    min_digest_items: int,
    expect_backend: str | None,
    forbidden: list[str],
    timeout: float,
    transport: httpx.BaseTransport | None = None,
) -> SmokeResult:
    client_kwargs: dict[str, Any] = {
        "follow_redirects": True,
        "timeout": timeout,
    }
    if transport is not None:
        client_kwargs["transport"] = transport

    with httpx.Client(**client_kwargs) as client:
        dashboard = client.get(_url(base_url, "/"))
        dashboard.raise_for_status()
        dashboard_html = dashboard.text
        dashboard_surface = (
            dashboard_html + "\n" + _dashboard_assets(client, base_url, dashboard_html)
        )
        dashboard_en = client.get(_url(base_url, "/?lang=en"))
        dashboard_en.raise_for_status()
        dashboard_en_html = dashboard_en.text
        insights_page = _get_text(client, base_url, "/insights?lang=ru")
        insights_page_head = _head(client, base_url, "/insights?lang=ru")
        insights_snapshot = _get_json(client, base_url, "/insights.json?lang=ru")
        insights_snapshot_head = _head(client, base_url, "/insights.json?lang=ru")
        media_page = _get_text(client, base_url, "/media?lang=ru")
        media_page_head = _head(client, base_url, "/media?lang=ru")
        media_snapshot = _get_json(client, base_url, "/media.json?lang=ru")
        media_snapshot_head = _head(client, base_url, "/media.json?lang=ru")
        media_feed = _get_json(client, base_url, "/media/feed.json?lang=ru")
        media_feed_head = _head(client, base_url, "/media/feed.json?lang=ru")
        media_rss = _get_text(client, base_url, "/media/rss.xml?lang=ru")
        media_rss_head = _head(client, base_url, "/media/rss.xml?lang=ru")

        health = _get_json(client, base_url, "/health")
        release = _get_json(client, base_url, "/.well-known/release.json")
        ready = _get_json(client, base_url, "/ready")
        coverage = _get_json(client, base_url, "/coverage")
        opportunities = _get_json(
            client,
            base_url,
            (
                "/opportunities?limit=5000&min_score=0.3"
                f"&deadline_after={deadline_after}"
            ),
        )
        compare_ids = [
            str(item.get("id") or "")
            for item in opportunities[:4]
            if str(item.get("id") or "")
        ]
        history_id = compare_ids[0] if compare_ids else ""
        opportunity_id = history_id
        history = _get_json(
            client,
            base_url,
            f"/opportunities/{history_id}/history.json?lang=ru&limit=50",
        )
        history_head = _head(
            client,
            base_url,
            f"/opportunities/{history_id}/history.json?lang=ru&limit=50",
        )
        opportunity_page = _get_text(
            client,
            base_url,
            f"/opportunity/{history_id}?lang=ru",
        )
        opportunity_page_head = _head(
            client,
            base_url,
            f"/opportunity/{history_id}?lang=ru",
        )
        funder_slug = next(
            (
                str(item.get("funder_slug") or "").strip()
                for item in opportunities
                if str(item.get("funder_slug") or "").strip()
            ),
            "world-bank",
        )
        funder_page_en = _get_text(
            client,
            base_url,
            f"/funder/{funder_slug}?lang=en",
        )
        funder_page_en_head = _head(
            client,
            base_url,
            f"/funder/{funder_slug}?lang=en",
        )
        comparison = _get_json(
            client,
            base_url,
            f"/compare.json?ids={','.join(compare_ids)}&lang=ru",
        )
        comparison_head = _head(
            client,
            base_url,
            f"/compare.json?ids={','.join(compare_ids)}&lang=ru",
        )
        comparison_page = _get_text(
            client,
            base_url,
            f"/compare?ids={','.join(compare_ids)}&lang=ru",
        )
        comparison_page_head = _head(
            client,
            base_url,
            f"/compare?ids={','.join(compare_ids)}&lang=ru",
        )
        ndjson_response = client.get(
            _url(base_url, "/opportunities.ndjson?limit=20&min_score=0.3")
        )
        ndjson_response.raise_for_status()
        ndjson_items = [
            json.loads(line)
            for line in ndjson_response.text.splitlines()
            if line.strip()
        ]
        ndjson_head = _head(
            client,
            base_url,
            "/opportunities.ndjson?limit=20&min_score=0.3",
        )
        digest = _get_json(client, base_url, "/digest?limit=5&tag=ai")
        robots = _get_text(client, base_url, "/robots.txt")
        sitemap = _get_text(client, base_url, "/sitemap.xml")
        llms = _get_text(client, base_url, "/llms.txt")
        robots_head = _head(client, base_url, "/robots.txt")
        sitemap_head = _head(client, base_url, "/sitemap.xml")
        llms_head = _head(client, base_url, "/llms.txt")
        docs = _get_text(client, base_url, "/docs")
        docs_head = _head(client, base_url, "/docs")
        status_page = _get_text(client, base_url, "/status?lang=ru")
        status_head = _head(client, base_url, "/status?lang=ru")
        operator_page = _get_text(client, base_url, "/operator?lang=ru")
        operator_head = _head(client, base_url, "/operator?lang=ru")
        insights_head = _head(client, base_url, "/insights?lang=ru")
        detail_page = _get_text(
            client,
            base_url,
            f"/opportunity/{opportunity_id}?lang=ru",
        )
        detail_head = _head(
            client,
            base_url,
            f"/opportunity/{opportunity_id}?lang=ru",
        )
        prepare_page = _get_text(
            client,
            base_url,
            f"/opportunity/{opportunity_id}/prepare?lang=ru",
        )
        prepare_head = _head(
            client,
            base_url,
            f"/opportunity/{opportunity_id}/prepare?lang=ru",
        )
        funder_page_ru = _get_text(
            client,
            base_url,
            f"/funder/{funder_slug}?lang=ru",
        )
        policy_terms = _get_text(client, base_url, "/terms?lang=ru")
        policy_data = _get_text(client, base_url, "/data-policy?lang=ru")
        policy_attribution = _get_text(client, base_url, "/attribution?lang=ru")
        missing_page = client.get(
            _url(base_url, "/opportunity/not-a-valid-id?lang=ru"),
            headers={"Accept": "text/html"},
        )
        api_index = _get_json(client, base_url, "/api/v1")
        insights_api = _get_json(client, base_url, "/api/v1/insights?lang=ru")
        insights_api_head = _head(
            client,
            base_url,
            "/api/v1/insights?lang=ru",
        )
        api_v1_ndjson_head = _head(
            client,
            base_url,
            "/api/v1/opportunities.ndjson?lang=ru",
        )
        changes_api = _get_json(
            client,
            base_url,
            "/api/v1/changes?hours=24&lang=ru",
        )
        daily_digest = _get_json(
            client,
            base_url,
            "/media/v1/digest/daily.json?lang=ru",
        )
        discovery = _get_json(client, base_url, "/site-discovery.json")
        discovery_head = _head(client, base_url, "/site-discovery.json")
        qazstack_contract = _get_json(
            client, base_url, "/.well-known/qazstack-consumer.json"
        )
        qazstack_head = _head(client, base_url, "/.well-known/qazstack-consumer.json")
        avds_contract = _get_json(
            client, base_url, "/.well-known/avds-ui-contract.json"
        )
        avds_head = _head(client, base_url, "/.well-known/avds-ui-contract.json")
        qazpipe_contract = _get_json(
            client, base_url, "/.well-known/qazpipe-source.json"
        )
        qazpipe_head = _head(client, base_url, "/.well-known/qazpipe-source.json")
        qazcompute_contract = _get_json(
            client, base_url, "/.well-known/qazcompute-profiles.json"
        )
        qazcompute_head = _head(
            client, base_url, "/.well-known/qazcompute-profiles.json"
        )
        ecosystem = _get_json(client, base_url, "/.well-known/qdev-ecosystem.json")
        ecosystem_head = _head(client, base_url, "/.well-known/qdev-ecosystem.json")
        notification_contract = _get_json(
            client, base_url, "/.well-known/notification-contract.json"
        )
        notification_head = _head(
            client, base_url, "/.well-known/notification-contract.json"
        )
        source_onboarding = _get_json(
            client, base_url, "/.well-known/source-onboarding.json"
        )
        source_onboarding_head = _head(
            client, base_url, "/.well-known/source-onboarding.json"
        )

    _require(health.get("status") == "ok", "health status is not ok")
    revision = str(release.get("revision") or "")
    image_digest = str(release.get("imageDigest") or "")
    artifact_digest = str(release.get("artifactDigest") or "")
    built_at = str(release.get("builtAt") or "")
    deployed_at = str(release.get("deployedAt") or "")
    _require(
        release.get("schemaVersion") == "qaz-fund-release-v1"
        and release.get("service") == "qaz-fund"
        and bool(re.fullmatch(r"[0-9a-f]{40}", revision)),
        "release metadata is missing",
    )
    _require(release.get("sourceSha") == revision, "release source SHA mismatch")
    _require(release.get("sourceDirty") is False, "release source is dirty")
    _require(
        bool(re.fullmatch(r"sha256:[0-9a-f]{64}", image_digest)),
        "release image digest is missing",
    )
    _require(
        bool(re.fullmatch(r"sha256:[0-9a-f]{64}", artifact_digest)),
        "release artifact digest is missing",
    )
    built_timestamp = _release_timestamp(built_at, "builtAt")
    deployed_timestamp = _release_timestamp(deployed_at, "deployedAt")
    _require(built_timestamp <= deployed_timestamp, "release timestamps are reversed")
    _require(
        release.get("deployed_at") == deployed_at,
        "legacy and canonical deploy timestamps differ",
    )
    _require(ready.get("status") == "ok", "ready status is not ok")
    if expect_backend:
        _require(
            ready.get("backend") == expect_backend,
            f"ready backend is {ready.get('backend')!r}, expected {expect_backend!r}",
        )
    _require(
        int(coverage.get("enabled_sources") or 0) >= min_sources,
        "enabled source count is below production threshold",
    )
    _require(
        len(opportunities) >= min_opportunities,
        "opportunity count is below production threshold",
    )
    current_catalog_count = len(opportunities)
    coverage_current_count = int(coverage.get("relevant_open_items") or 0)
    insights_current_count = int(
        (insights_api.get("scope") or {}).get("current_catalog") or 0
    )
    _require(
        coverage_current_count == current_catalog_count,
        "coverage and deadline-filtered current catalog counts differ: "
        f"{coverage_current_count} != {current_catalog_count}",
    )
    _require(
        insights_current_count == current_catalog_count,
        "insights and deadline-filtered current catalog counts differ: "
        f"{insights_current_count} != {current_catalog_count}",
    )
    _require(bool(ndjson_items), "NDJSON export is empty")
    _require(
        all(
            item.get("evidence_state") in {"verified", "sourced"}
            for item in ndjson_items
        ),
        "NDJSON export contains records without public evidence state",
    )
    _require(
        len(digest.get("items") or []) >= min_digest_items,
        "digest item count is below production threshold",
    )
    for marker in MARKETING_MARKERS:
        _require(
            marker in robots or marker in sitemap,
            f"marketing marker missing: {marker}",
        )

    marker_status = {
        marker: marker in dashboard_surface for marker in DASHBOARD_MARKERS
    }
    missing_markers = [
        marker for marker, present in marker_status.items() if not present
    ]
    _require(not missing_markers, f"dashboard markers missing: {missing_markers}")
    english_dashboard = (
        '<html lang="en"' in dashboard_en_html and "Opportunities" in dashboard_en_html
    )
    _require(english_dashboard, "english dashboard variant is missing")

    discovery_status = {
        "insights_page": (
            '<html lang="ru"' in insights_page
            and 'data-avds-pattern="decision-readiness"' in insights_page
            and 'data-avds-component="DataViz"' in insights_page
            and _is_public_cacheable(insights_page_head, 60)
        ),
        "insights_snapshot": (
            insights_snapshot.get("schema_version") == "insights.v1"
            and isinstance(insights_snapshot.get("decision_readiness"), dict)
            and _is_public_cacheable(insights_snapshot_head, 60)
        ),
        "media_page": (
            '<html lang="ru"' in media_page
            and 'data-avds="grant-radar"' in media_page
            and 'data-avds-component="media-lead"' in media_page
            and 'type="application/feed+json"' in media_page
            and 'type="application/rss+xml"' in media_page
            and _is_public_cacheable(media_page_head, 60)
        ),
        "media_snapshot": (
            media_snapshot.get("schema_version") == "media.v1"
            and isinstance(media_snapshot.get("cards"), list)
            and not _contains_key(media_snapshot, "raw")
            and _is_public_cacheable(media_snapshot_head, 60)
        ),
        "media_json_feed": (
            media_feed.get("version") == "https://jsonfeed.org/version/1.1"
            and isinstance(media_feed.get("items"), list)
            and str(media_feed.get("language") or "") == "ru"
            and _is_public_cacheable(media_feed_head, 60)
        ),
        "media_rss": (
            '<rss version="2.0"' in media_rss
            and "<channel>" in media_rss
            and "raw" not in media_rss
            and _is_public_cacheable(media_rss_head, 60)
        ),
        "opportunity_history": (
            history.get("schema_version") == "history.v1"
            and history.get("status") in {"ready", "not_available"}
            and isinstance(history.get("items"), list)
            and _is_public_cacheable(history_head, 60)
        ),
        "opportunity_page": (
            '<html lang="ru"' in opportunity_page
            and 'data-avds="grant-radar"' in opportunity_page
            and _is_public_cacheable(opportunity_page_head, 60)
        ),
        "funder_page_en": (
            '<html lang="en"' in funder_page_en
            and 'data-avds="grant-radar"' in funder_page_en
            and _is_public_cacheable(funder_page_en_head, 60)
        ),
        "llms_home": f"Home: {_url(base_url, '/')}" in llms,
        "llms_sitemap": f"Sitemap: {_url(base_url, '/sitemap.xml')}" in llms,
        "llms_openapi": f"OpenAPI schema: {_url(base_url, '/openapi.json')}" in llms,
        "llms_coverage": f"Coverage JSON: {_url(base_url, '/coverage')}" in llms,
        "llms_media": f"Media page: {_url(base_url, '/media')}" in llms,
        "llms_media_json": f"Media JSON: {_url(base_url, '/media.json')}" in llms,
        "llms_media_feed": (
            f"Media JSON Feed: {_url(base_url, '/media/feed.json')}" in llms
        ),
        "llms_media_rss": f"Media RSS: {_url(base_url, '/media/rss.xml')}" in llms,
        "llms_opportunities": (
            f"Opportunities JSON: {_url(base_url, '/opportunities')}" in llms
        ),
        "llms_opportunities_ndjson": (
            f"Opportunities NDJSON: {_url(base_url, '/opportunities.ndjson')}" in llms
        ),
        "llms_compact_opportunities_ndjson": (
            "Compact Opportunities NDJSON: "
            f"{_url(base_url, '/opportunities.ndjson?compact=true')}" in llms
        ),
        "llms_ecosystem": (
            f"Ecosystem integration JSON: "
            f"{_url(base_url, '/.well-known/qdev-ecosystem.json')}" in llms
        ),
        "llms_release": (
            f"Release metadata JSON: "
            f"{_url(base_url, '/.well-known/release.json')}" in llms
        ),
        "llms_notification_contract": (
            f"Notification contract: "
            f"{_url(base_url, '/.well-known/notification-contract.json')}" in llms
        ),
        "llms_comparison": (
            "Comparison JSON: "
            f"{_url(base_url, '/compare.json')}?ids={{id}},{{id}}&lang=ru|kk|en" in llms
        ),
        "llms_history": (
            "Opportunity history JSON: "
            f"{_url(base_url, '/opportunities/{id}/history.json')}?lang=kk|ru|en&limit={{n}}"
            in llms
        ),
        "llms_source_onboarding": (
            "Source onboarding contract: "
            f"{_url(base_url, '/.well-known/source-onboarding.json')}" in llms
        ),
        "llms_ai_guidance": "## AI consumption guidance" in llms,
        "llms_ndjson_guidance": (
            "Prefer compact Opportunities NDJSON for bulk discovery reads" in llms
        ),
        "robots_cache": _is_public_cacheable(robots_head, 300),
        "sitemap_cache": _is_public_cacheable(sitemap_head, 300),
        "llms_cache": _is_public_cacheable(llms_head, 300),
        "docs_brand": "QAZ.FUND API" in docs,
        "docs_openapi": "/openapi.json" in docs,
        "docs_head": docs_head.headers.get("content-type", "").startswith("text/html"),
        "status_page": "Статус источников" in status_page,
        "status_head": status_head.headers.get("content-type", "").startswith(
            "text/html"
        ),
        "operator_shell": (
            "Контроль источников" in operator_page
            and "X-Grant-Radar-Admin-Token" in operator_page
            and 'content="noindex,nofollow"' in operator_page
        ),
        "operator_noindex": "noindex"
        in operator_head.headers.get("x-robots-tag", "").lower(),
        "insights_head": insights_head.headers.get("content-type", "").startswith(
            "text/html"
        ),
        "detail_page": (
            'data-avds-component="opportunity-page"' in detail_page
            and 'data-avds-component="opportunity-detail"' in detail_page
            and "Официальный источник" in detail_page
            and "\u2014" not in detail_page
        ),
        "detail_head": detail_head.headers.get("content-type", "").startswith(
            "text/html"
        ),
        "application_workspace": (
            'data-avds-component="application-workspace"' in prepare_page
            and "Данные остаются в этом браузере" in prepare_page
            and "localStorage.setItem" in prepare_page
            and "\u2014" not in prepare_page
        ),
        "application_workspace_head": prepare_head.headers.get(
            "content-type", ""
        ).startswith("text/html"),
        "funder_page_ru": (
            "QAZ.FUND" in funder_page_ru
            and 'data-avds="grant-radar"' in funder_page_ru
            and "\u2014" not in funder_page_ru
        ),
        "policy_routes": (
            "Условия использования" in policy_terms
            and "Политика данных" in policy_data
            and "Использование данных" in policy_attribution
        ),
        "browser_404": (
            missing_page.status_code == 404
            and "Такой страницы нет" in missing_page.text
            and "Вернуться в каталог" in missing_page.text
        ),
        "api_v1_daily_digest": (
            str((api_index.get("routes") or {}).get("daily_digest_json") or "")
            == _url(base_url, "/media/v1/digest/daily.json")
            and str((api_index.get("routes") or {}).get("daily_digest_text") or "")
            == _url(base_url, "/media/v1/digest/daily.txt")
        ),
        "insights_api": (
            insights_api.get("schema_version") == "qazfund-insights.v1"
            and int((insights_api.get("scope") or {}).get("current_catalog") or 0)
            == int(coverage.get("relevant_open_items") or 0)
            and int((insights_api.get("scope") or {}).get("active") or 0)
            == int(coverage.get("relevant_open_items") or 0)
            and int((insights_api.get("scope") or {}).get("indexed_relevant") or 0)
            >= int((insights_api.get("scope") or {}).get("current_catalog") or 0)
        ),
        "insights_api_head": (
            insights_api_head.headers.get("content-type", "").startswith(
                "application/json"
            )
            and _is_public_cacheable(insights_api_head, 60)
        ),
        "legacy_ndjson_head": (
            ndjson_head.headers.get("content-type", "").startswith(
                "application/x-ndjson"
            )
            and _is_public_cacheable(ndjson_head, 300)
        ),
        "api_v1_ndjson_head": (
            api_v1_ndjson_head.headers.get("content-type", "").startswith(
                "application/x-ndjson"
            )
            and _is_public_cacheable(api_v1_ndjson_head, 300)
        ),
        "changes_api": changes_api.get("schema_version") == "qazfund-changes.v1",
        "daily_digest": (
            daily_digest.get("schema_version") == "qazfund-daily-digest.v1"
            and daily_digest.get("state") in {"collecting", "no_changes", "ready"}
            and (daily_digest.get("delivery") or {}).get("automatic") is False
        ),
        "site_discovery_openapi": str(discovery.get("openapi") or "")
        == _url(base_url, "/openapi.json"),
        "site_discovery_llms": str(discovery.get("llms") or "")
        == _url(base_url, "/llms.txt"),
        "site_discovery_docs": str(discovery.get("api_docs") or "")
        == _url(base_url, "/docs"),
        "site_discovery_status": str(discovery.get("source_status") or "")
        == _url(base_url, "/status"),
        "site_discovery_languages": list(discovery.get("languages") or [])
        == ["kk", "ru", "en"],
        "site_discovery_release": str(discovery.get("release") or "")
        == _url(base_url, "/.well-known/release.json"),
        "site_discovery_coverage": str(
            (discovery.get("data_endpoints") or {}).get("coverage") or ""
        )
        == _url(base_url, "/coverage"),
        "site_discovery_opportunities": str(
            (discovery.get("data_endpoints") or {}).get("opportunities") or ""
        )
        == _url(base_url, "/opportunities"),
        "site_discovery_opportunities_ndjson": str(
            (discovery.get("data_endpoints") or {}).get("opportunities_ndjson") or ""
        )
        == _url(base_url, "/opportunities.ndjson"),
        "site_discovery_opportunities_ndjson_compact": str(
            (discovery.get("data_endpoints") or {}).get("opportunities_ndjson_compact")
            or ""
        )
        == _url(base_url, "/opportunities.ndjson?compact=true"),
        "site_discovery_history": str(
            (discovery.get("data_endpoints") or {}).get("opportunity_history") or ""
        )
        == _url(base_url, "/opportunities/{id}/history.json"),
        "site_discovery_media": str(
            (discovery.get("data_endpoints") or {}).get("media") or ""
        )
        == _url(base_url, "/media"),
        "site_discovery_media_json": str(
            (discovery.get("data_endpoints") or {}).get("media_json") or ""
        )
        == _url(base_url, "/media.json"),
        "site_discovery_media_feed": str(
            (discovery.get("data_endpoints") or {}).get("media_feed") or ""
        )
        == _url(base_url, "/media/feed.json"),
        "site_discovery_media_rss": str(
            (discovery.get("data_endpoints") or {}).get("media_rss") or ""
        )
        == _url(base_url, "/media/rss.xml"),
        "site_discovery_cache": _is_public_cacheable(discovery_head, 300),
        "site_discovery_ai_bulk_export": str(
            (discovery.get("ai_consumption") or {}).get("preferred_bulk_export") or ""
        )
        == _url(base_url, "/api/v1/opportunities.ndjson"),
        "site_discovery_ai_legacy_bulk_export": str(
            (discovery.get("ai_consumption") or {}).get("preferred_legacy_bulk_export")
            or ""
        )
        == _url(base_url, "/opportunities.ndjson?compact=true"),
        "site_discovery_ai_history_template": str(
            (discovery.get("ai_consumption") or {}).get("history_template") or ""
        )
        == _url(base_url, "/opportunities/{id}/history.json?lang={lang}&limit={n}"),
        "site_discovery_ai_cache_policy": int(
            ((discovery.get("ai_consumption") or {}).get("cache_policy") or {}).get(
                "ndjson_seconds"
            )
            or 0
        )
        >= 300,
        "site_discovery_qazstack": str(
            (discovery.get("contracts") or {}).get("qazstack") or ""
        )
        == _url(base_url, "/.well-known/qazstack-consumer.json"),
        "site_discovery_avds4": str(
            (discovery.get("contracts") or {}).get("avds4") or ""
        )
        == _url(base_url, "/.well-known/avds-ui-contract.json"),
        "site_discovery_notification_contract": str(
            (discovery.get("contracts") or {}).get("notifications") or ""
        )
        == _url(base_url, "/.well-known/notification-contract.json"),
        "site_discovery_source_onboarding": str(
            (discovery.get("data_endpoints") or {}).get("source_onboarding") or ""
        )
        == _url(base_url, "/.well-known/source-onboarding.json"),
        "site_discovery_comparison": str(
            (discovery.get("data_endpoints") or {}).get("compare_json") or ""
        )
        == _url(base_url, "/compare.json"),
        "comparison_contract": (
            comparison.get("schema_version") == "comparison.v1"
            and comparison.get("status") in {"ready", "partial", "insufficient"}
            and len(comparison.get("cards") or []) <= 4
            and _is_public_cacheable(comparison_head, 60)
        ),
        "comparison_page": (
            '<html lang="ru"' in comparison_page
            and 'data-avds-component="comparison-table"' in comparison_page
            and 'rel="alternate" type="application/json"' in comparison_page
            and _is_public_cacheable(comparison_page_head, 60)
        ),
        "qazstack_contract": (
            qazstack_contract.get("schema_version") == "qazstack-consumer-v1"
            and qazstack_contract.get("qazstack_version") == QAZSTACK_VERSION
            and {
                "opportunity-public-contract",
                "opportunity-ranking-evaluation",
            }.issubset(set(qazstack_contract.get("primitives") or []))
            and qazstack_contract.get("integration_mode") == "python-package"
            and _is_public_cacheable(qazstack_head, 60)
        ),
        "avds4_contract": (
            avds_contract.get("schema_version") == "avds-ui-contract-v1"
            and (avds_contract.get("avds_source") or {}).get("version") == AVDS_VERSION
            and (avds_contract.get("runtime_neutral_patterns") or {}).get("adopted")
            == [
                "evidence-summary",
                "filter-state-summary",
                "decision-summary",
                "evidence-disclosure",
                "action-path",
            ]
            and _is_public_cacheable(avds_head, 60)
        ),
        "qazpipe_contract": (
            qazpipe_contract.get("schema_version") == "qazpipe-pull-source-v1"
            and qazpipe_contract.get("mode") == "pull"
            and qazpipe_contract.get("direction") == "outbound-read-only"
            and (qazpipe_contract.get("qazlake_handoff") or {}).get("direct_write")
            is False
            and _is_public_cacheable(qazpipe_head, 60)
        ),
        "qazcompute_contract": (
            qazcompute_contract.get("schema_version")
            == "qazcompute-profile-contract-v1"
            and (qazcompute_contract.get("execution") or {}).get("runtime_status")
            == "proven"
            and (qazcompute_contract.get("execution") or {}).get(
                "remote_execution_active"
            )
            is False
            and _is_public_cacheable(qazcompute_head, 60)
        ),
        "notification_contract": (
            notification_contract.get("schema_version") == "notification-v1"
            and notification_contract.get("status") == "not_enabled"
            and (notification_contract.get("delivery") or {}).get("enabled") is False
            and (notification_contract.get("delivery") or {}).get("worker_running")
            is False
            and (notification_contract.get("identity") or {}).get("authenticated_owner")
            is False
            and (notification_contract.get("identity") or {}).get("cross_device_sync")
            is False
            and (notification_contract.get("consent") or {}).get("collection_enabled")
            is False
            and (notification_contract.get("consent") or {}).get("version") is None
            and _is_public_cacheable(notification_head, 60)
        ),
        "source_onboarding_contract": (
            source_onboarding.get("schema_version") == "source-onboarding.v1"
            and (source_onboarding.get("policy") or {}).get(
                "credentials_in_public_contract"
            )
            is False
            and isinstance(source_onboarding.get("candidates"), list)
            and _is_public_cacheable(source_onboarding_head, 60)
        ),
        "ecosystem_contract": (
            ecosystem.get("schema_version") == "qdev-ecosystem-integration-v1"
            and (ecosystem.get("integrations") or {}).get("qazstack", {}).get("status")
            == "runtime-proven"
            and (ecosystem.get("integrations") or {}).get("qazpipe", {}).get("status")
            == "producer-ready"
            and (ecosystem.get("integrations") or {})
            .get("qazlake", {})
            .get("direct_write")
            is False
            and (ecosystem.get("integrations") or {})
            .get("qazcompute", {})
            .get("status")
            == "local-runtime-proven"
            and _is_public_cacheable(ecosystem_head, 60)
        ),
    }
    missing_discovery = [
        marker for marker, present in discovery_status.items() if not present
    ]
    _require(
        not missing_discovery,
        f"discovery surfaces missing: {missing_discovery}",
    )

    opportunities_payload = json.dumps(opportunities, ensure_ascii=False)
    forbidden_hits = [needle for needle in forbidden if needle in opportunities_payload]
    _require(not forbidden_hits, f"forbidden content found: {forbidden_hits}")

    return SmokeResult(
        base_url=base_url.rstrip("/"),
        release_revision=revision,
        release_image_digest=image_digest,
        release_artifact_digest=artifact_digest,
        release_built_at=built_at,
        release_deployed_at=deployed_at,
        deadline_after=deadline_after,
        health_items=int(health.get("items") or 0),
        ready_backend=str(ready.get("backend") or ""),
        coverage_sources=int(coverage.get("enabled_sources") or 0),
        coverage_relevant_open_items=int(coverage.get("relevant_open_items") or 0),
        coverage_stale_sources=int(coverage.get("stale_sources") or 0),
        coverage_unknown_freshness_sources=int(
            coverage.get("unknown_freshness_sources") or 0
        ),
        opportunities=len(opportunities),
        ndjson_items=len(ndjson_items),
        digest_items=len(digest.get("items") or []),
        media_items=len(media_snapshot.get("cards") or []),
        media_feed_items=len(media_feed.get("items") or []),
        forbidden_hits=forbidden_hits,
        dashboard_markers=marker_status,
        english_dashboard=english_dashboard,
        discovery_surfaces=discovery_status,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default="https://qaz.fund",
        help="Deployment root URL, including any path prefix.",
    )
    parser.add_argument(
        "--deadline-after",
        default=public_today().isoformat(),
        help="ISO date used for open-opportunity filtering.",
    )
    parser.add_argument("--min-sources", type=int, default=26)
    parser.add_argument("--min-opportunities", type=int, default=40)
    parser.add_argument("--min-digest-items", type=int, default=1)
    parser.add_argument("--expect-backend", default="database")
    parser.add_argument(
        "--forbid",
        action="append",
        default=["AI3 Action Institute", "Technical Difficulties"],
        help="Text that must not appear in the current relevant opportunity feed.",
    )
    # The gate performs a deliberately sequential public-route matrix. Keep
    # enough headroom for a healthy deployment when the origin is cold.
    parser.add_argument("--timeout", type=float, default=60.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = run_smoke(
            base_url=args.base_url,
            deadline_after=args.deadline_after,
            min_sources=args.min_sources,
            min_opportunities=args.min_opportunities,
            min_digest_items=args.min_digest_items,
            expect_backend=args.expect_backend or None,
            forbidden=list(args.forbid or []),
            timeout=args.timeout,
        )
    except (SmokeError, httpx.HTTPError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 1

    print(json.dumps({"status": "ok", **asdict(result)}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
