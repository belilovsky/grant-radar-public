"""Production smoke checks for a live QAZ.FUND deployment."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from typing import Any
from urllib.parse import urljoin

import httpx

DASHBOARD_MARKERS = (
    '<html lang="ru"',
    'data-avds="grant-radar"',
    'data-av-theme="light"',
    'data-lang="ru"',
    'data-avds-component="admin-shell"',
    'data-avds-component="sticky-shell"',
    'data-avds-component="filter-summary"',
    'data-avds-component="quick-links-rail"',
    'data-avds-component="public-summary-strip"',
    'class="toolbar avds-tabs-list"',
    "avds-tabs-trigger",
    "avds-field",
    'data-avds-component="source-card"',
    'data-avds-component="source-icon"',
    "avds-source-card__arrow",
    'data-avds-component="source-url"',
    'data-avds-component="opportunity-card"',
    'data-avds-component="trust-library"',
    'id="workspace-filter"',
    'id="filter-disclosure"',
    "avds-document-row",
)
MARKETING_MARKERS = (
    "Sitemap:",
    "<urlset",
)


class SmokeError(RuntimeError):
    """Raised when a production smoke check fails."""


@dataclass(frozen=True)
class SmokeResult:
    base_url: str
    release_revision: str
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
    forbidden_hits: list[str]
    dashboard_markers: dict[str, bool]
    english_dashboard: bool
    discovery_surfaces: dict[str, bool]


def _url(base_url: str, path: str) -> str:
    return urljoin(f"{base_url.rstrip('/')}/", path.lstrip("/"))


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


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeError(message)


def _is_public_cacheable(response: httpx.Response, min_age: int) -> bool:
    cache_control = response.headers.get("cache-control", "").lower()
    return "public" in cache_control and f"max-age={min_age}" in cache_control


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
        dashboard_en = client.get(_url(base_url, "/?lang=en"))
        dashboard_en.raise_for_status()
        dashboard_en_html = dashboard_en.text

        health = _get_json(client, base_url, "/health")
        release = _get_json(client, base_url, "/.well-known/release.json")
        ready = _get_json(client, base_url, "/ready")
        coverage = _get_json(client, base_url, "/coverage")
        opportunities = _get_json(
            client,
            base_url,
            (
                "/opportunities?limit=1000&min_score=0.3"
                f"&deadline_after={deadline_after}"
            ),
        )
        _require(bool(opportunities), "opportunity list is empty")
        opportunity_id = str(opportunities[0].get("id") or "")
        _require(bool(opportunity_id), "opportunity list has no stable id")
        funders = _get_json(client, base_url, "/funders?limit=1")
        _require(bool(funders), "funder list is empty")
        funder_slug = str(funders[0].get("slug") or "")
        _require(bool(funder_slug), "funder list has no stable slug")
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
        insights_page = _get_text(client, base_url, "/insights?lang=ru")
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
        funder_page = _get_text(
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

    _require(health.get("status") == "ok", "health status is not ok")
    _require(
        release.get("service") == "qaz-fund"
        and bool(re.fullmatch(r"[0-9a-f]{40}", str(release.get("revision") or ""))),
        "release metadata is missing",
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

    marker_status = {marker: marker in dashboard_html for marker in DASHBOARD_MARKERS}
    missing_markers = [
        marker for marker, present in marker_status.items() if not present
    ]
    _require(not missing_markers, f"dashboard markers missing: {missing_markers}")
    english_dashboard = (
        '<html lang="en"' in dashboard_en_html and "Opportunities" in dashboard_en_html
    )
    _require(english_dashboard, "english dashboard variant is missing")

    discovery_status = {
        "dashboard_initial_current_metric": (
            f'id="metric-strong" data-catalog-count="'
            f'{int(coverage.get("relevant_open_items") or 0)}">'
            f'{int(coverage.get("relevant_open_items") or 0)}</strong>'
            in dashboard_html
        ),
        "dashboard_initial_source_metric": (
            f'<strong id="metric-sources">'
            f'{int(coverage.get("enabled_sources") or 0)}</strong>' in dashboard_html
        ),
        "llms_home": f"Home: {_url(base_url, '/')}" in llms,
        "llms_sitemap": f"Sitemap: {_url(base_url, '/sitemap.xml')}" in llms,
        "llms_openapi": f"OpenAPI schema: {_url(base_url, '/openapi.json')}" in llms,
        "llms_coverage": f"Coverage JSON: {_url(base_url, '/coverage')}" in llms,
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
        "llms_qazpipe": (
            f"QazPipe source contract: "
            f"{_url(base_url, '/.well-known/qazpipe-source.json')}" in llms
        ),
        "llms_qazcompute": (
            f"QazCompute profile contract: "
            f"{_url(base_url, '/.well-known/qazcompute-profiles.json')}" in llms
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
        "insights_page": (
            'data-avds-component="data-centre"' in insights_page
            and 'data-avds-pattern="data-quality-scorecard"' in insights_page
            and "В текущем каталоге" in insights_page
            and "Релевантных карточек в индексе" in insights_page
            and "\u2014" not in insights_page
        ),
        "insights_head": insights_head.headers.get("content-type", "").startswith(
            "text/html"
        ),
        "detail_page": (
            'data-avds-component="lite-reading-surface"' in detail_page
            and "Ключевые условия" in detail_page
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
        "funder_page": (
            "QAZ.FUND" in funder_page
            and 'data-avds="grant-radar"' in funder_page
            and "\u2014" not in funder_page
        ),
        "policy_routes": (
            "Условия использования" in policy_terms
            and "Политика данных" in policy_data
            and "Цитирование и повторное использование" in policy_attribution
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
        "site_discovery_api_v1": str(discovery.get("versioned_api") or "")
        == _url(base_url, "/api/v1"),
        "site_discovery_api_v1_ndjson": str(
            (discovery.get("data_endpoints") or {}).get("api_v1_opportunities_ndjson")
            or ""
        )
        == _url(base_url, "/api/v1/opportunities.ndjson"),
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
        "site_discovery_qazpipe": str(
            (discovery.get("contracts") or {}).get("qazpipe") or ""
        )
        == _url(base_url, "/.well-known/qazpipe-source.json"),
        "site_discovery_qazcompute": str(
            (discovery.get("contracts") or {}).get("qazcompute") or ""
        )
        == _url(base_url, "/.well-known/qazcompute-profiles.json"),
        "qazstack_contract": (
            qazstack_contract.get("schema_version") == "qazstack-consumer-v1"
            and qazstack_contract.get("qazstack_version") == "1.41.2"
            and {
                "opportunity-public-contract",
                "opportunity-ranking-evaluation",
            }.issubset(set(qazstack_contract.get("primitives") or []))
            and qazstack_contract.get("integration_mode") == "python-package"
            and _is_public_cacheable(qazstack_head, 60)
        ),
        "avds4_contract": (
            avds_contract.get("schema_version") == "avds-ui-contract-v1"
            and (avds_contract.get("avds_source") or {}).get("version") == "4.6.0"
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
            and (qazpipe_contract.get("endpoints") or {}).get("bulk_ndjson")
            == _url(base_url, "/api/v1/opportunities.ndjson")
            and (qazpipe_contract.get("qazlake_handoff") or {}).get("direct_write")
            is False
            and {
                "source.url",
                "provenance.content_hash",
                "provenance.verification_method",
            }.issubset(set(qazpipe_contract.get("required_provenance") or []))
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
            and (qazcompute_contract.get("execution") or {}).get("decision_ready")
            is False
            and {
                "evidence_readiness.v1",
                "deadline_anomaly.v1",
                "source_freshness.v1",
                "duplicate_cluster.v1",
            }
            == {
                str(profile.get("schema_version") or "")
                for profile in qazcompute_contract.get("profiles") or []
            }
            and _is_public_cacheable(qazcompute_head, 60)
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
        release_revision=str(release.get("revision") or ""),
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
        default=date.today().isoformat(),
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
    parser.add_argument("--timeout", type=float, default=20.0)
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
