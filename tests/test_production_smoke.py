from __future__ import annotations

import json

import httpx
import pytest

from scripts.production_smoke import SmokeError, _contains_key, run_smoke


def test_contains_key_checks_nested_structures_without_matching_text() -> None:
    assert _contains_key({"cards": [{"title": "raw materials"}]}, "raw") is False
    assert _contains_key({"cards": [{"raw": {"title": "private"}}]}, "raw") is True


def _transport(
    *, opportunity_title: str = "Kazakhstan AI grant"
) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        root = str(request.url.copy_with(path="/", query=None)).rstrip("/")
        base_prefix = "/grant-radar" if path.startswith("/grant-radar") else ""
        public_root = f"{root}{base_prefix}"
        endpoint_path = path.removeprefix("/grant-radar")
        if path in {"/", "/grant-radar/"} and request.url.params.get("lang") == "en":
            return httpx.Response(
                200,
                text=(
                    '<html lang="en" data-avds="grant-radar" data-av-theme="light">'
                    "<body>Opportunities</body>"
                    "</html>"
                ),
            )
        if path in {"/", "/grant-radar/"}:
            html = (
                '<html lang="ru" data-avds="grant-radar" data-av-theme="light">'
                '<main data-lang="ru" data-avds-component="admin-shell">'
                '<div data-avds-component="sticky-shell"></div>'
                '<nav class="toolbar avds-tabs-list">'
                '<button class="button tab avds-tabs-trigger"></button>'
                "</nav>"
                '<input class="field avds-field">'
                '<div data-avds-component="filter-summary"></div>'
                '<div data-avds-component="source-card"></div>'
                '<span data-avds-component="source-icon"></span>'
                '<span class="avds-source-card__arrow"></span>'
                '<a data-avds-component="source-url"></a>'
                '<details data-avds-component="trust-library"></details>'
                '<button id="workspace-filter"></button>'
                '<details id="filter-disclosure"></details>'
                '<article class="avds-document-row"'
                ' data-avds-component="opportunity-card"></article>'
                "</main>"
                "</html>"
            )
            return httpx.Response(200, text=html)
        if endpoint_path == "/health":
            return httpx.Response(200, json={"status": "ok", "items": 55})
        if endpoint_path == "/.well-known/release.json":
            return httpx.Response(
                200,
                json={
                    "service": "qaz-fund",
                    "revision": "a" * 40,
                    "deployed_at": "2026-07-15T00:00:00Z",
                },
            )
        if endpoint_path == "/ready":
            return httpx.Response(
                200,
                json={"status": "ok", "backend": "database", "items": 55},
            )
        if endpoint_path == "/coverage":
            return httpx.Response(
                200,
                json={
                    "status": "ok",
                    "enabled_sources": 23,
                    "relevant_open_items": 44,
                    "stale_sources": 1,
                    "unknown_freshness_sources": 2,
                },
            )
        if endpoint_path == "/opportunities":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": f"00000000-0000-0000-0000-{index + 1:012d}",
                        "title": opportunity_title,
                        "source": "world_bank_kazakhstan",
                        "funder_slug": "world-bank",
                    }
                    for index in range(44)
                ],
            )
        if endpoint_path.startswith("/opportunities/") and endpoint_path.endswith(
            "/history.json"
        ):
            return httpx.Response(
                200,
                json={
                    "schema_version": "history.v1",
                    "status": "ready",
                    "items": [
                        {
                            "version": 1,
                            "changed_fields": ["initial"],
                            "fields": {"title": opportunity_title},
                        }
                    ],
                },
                headers={"cache-control": "public, max-age=60"},
            )
        if endpoint_path.startswith("/opportunity/"):
            return httpx.Response(
                200,
                text=(
                    '<html lang="ru" data-avds="grant-radar">'
                    "<body>Opportunity page</body></html>"
                ),
                headers={
                    "content-type": "text/html; charset=utf-8",
                    "cache-control": "public, max-age=60",
                },
            )
        if endpoint_path.startswith("/funder/"):
            return httpx.Response(
                200,
                text=(
                    '<html lang="en" data-avds="grant-radar">'
                    "<body>Funder page</body></html>"
                ),
                headers={
                    "content-type": "text/html; charset=utf-8",
                    "cache-control": "public, max-age=60",
                },
            )
        if endpoint_path == "/compare.json":
            return httpx.Response(
                200,
                json={
                    "schema_version": "comparison.v1",
                    "status": "ready",
                    "cards": [{"id": "sample"}, {"id": "sample-2"}],
                },
                headers={"cache-control": "public, max-age=60"},
            )
        if endpoint_path == "/insights":
            return httpx.Response(
                200,
                text=(
                    '<html lang="ru" data-avds="grant-radar">'
                    '<svg data-avds-pattern="decision-readiness"></svg>'
                    "</html>"
                ),
                headers={
                    "content-type": "text/html; charset=utf-8",
                    "cache-control": "public, max-age=60",
                },
            )
        if endpoint_path == "/insights.json":
            return httpx.Response(
                200,
                json={
                    "schema_version": "insights.v1",
                    "decision_readiness": {"complete": 1, "partial": 1},
                },
                headers={"cache-control": "public, max-age=60"},
            )
        if endpoint_path == "/media":
            return httpx.Response(
                200,
                text=(
                    '<html lang="ru" data-avds="grant-radar">'
                    '<section data-avds-component="media-lead">'
                    '<link rel="alternate" type="application/feed+json">'
                    '<link rel="alternate" type="application/rss+xml">'
                    "</section></html>"
                ),
                headers={
                    "content-type": "text/html; charset=utf-8",
                    "cache-control": "public, max-age=60",
                },
            )
        if endpoint_path == "/media.json":
            return httpx.Response(
                200,
                json={
                    "schema_version": "media.v1",
                    "language": "ru",
                    "cards": [{"id": "sample", "title": "AI grant"}],
                },
                headers={"cache-control": "public, max-age=60"},
            )
        if endpoint_path == "/media/feed.json":
            return httpx.Response(
                200,
                json={
                    "version": "https://jsonfeed.org/version/1.1",
                    "language": "ru",
                    "items": [
                        {"id": "sample", "url": f"{public_root}/opportunity/sample"}
                    ],
                },
                headers={"cache-control": "public, max-age=60"},
            )
        if endpoint_path == "/media/rss.xml":
            return httpx.Response(
                200,
                text=(
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    '<rss version="2.0"><channel><title>Media</title></channel></rss>'
                ),
                headers={
                    "content-type": "application/rss+xml",
                    "cache-control": "public, max-age=60",
                },
            )
        if endpoint_path == "/compare":
            return httpx.Response(
                200,
                text=(
                    '<html lang="ru" data-avds="grant-radar">'
                    '<link rel="alternate" type="application/json">'
                    '<table data-avds-component="comparison-table"></table>'
                    "</html>"
                ),
                headers={
                    "content-type": "text/html; charset=utf-8",
                    "cache-control": "public, max-age=60",
                },
            )
        if endpoint_path == "/opportunities.ndjson":
            return httpx.Response(
                200,
                text=(
                    '{"title":"Kazakhstan AI grant","source":"world_bank_kazakhstan",'
                    '"evidence_state":"sourced"}\n'
                ),
                headers={"content-type": "application/x-ndjson"},
            )
        if endpoint_path == "/digest":
            return httpx.Response(200, json={"items": [{"title": "AI digest"}]})
        if endpoint_path == "/robots.txt" or path == "/robots.txt":
            return httpx.Response(
                200,
                text=(
                    "User-agent: *\n"
                    "Allow: /\n"
                    "Disallow: /health\n"
                    "Disallow: /ready\n"
                    "Disallow: /refresh\n"
                    "Sitemap: https://example.org/grant-radar/sitemap.xml\n"
                ),
                headers={"cache-control": "public, max-age=300"},
            )
        if endpoint_path == "/sitemap.xml" or path == "/sitemap.xml":
            return httpx.Response(
                200,
                text='<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>',
                headers={"cache-control": "public, max-age=300"},
            )
        if endpoint_path == "/llms.txt" or path == "/llms.txt":
            return httpx.Response(
                200,
                text=(
                    "# QAZ.FUND\n"
                    "> Public funding navigator.\n\n"
                    "## Public entry points\n"
                    f"- Home: {public_root}/\n"
                    f"- Sitemap: {public_root}/sitemap.xml\n"
                    f"- API docs: {public_root}/docs\n"
                    f"- OpenAPI schema: {public_root}/openapi.json\n"
                    f"- Site discovery JSON: {public_root}/site-discovery.json\n"
                    f"- Ecosystem integration JSON: "
                    f"{public_root}/.well-known/qdev-ecosystem.json\n"
                    f"- Release metadata JSON: "
                    f"{public_root}/.well-known/release.json\n"
                    f"- QazStack consumer contract: "
                    f"{public_root}/.well-known/qazstack-consumer.json\n"
                    f"- AV DS 4 UI contract: "
                    f"{public_root}/.well-known/avds-ui-contract.json\n"
                    f"- Notification contract: "
                    f"{public_root}/.well-known/notification-contract.json\n"
                    f"- Source onboarding contract: "
                    f"{public_root}/.well-known/source-onboarding.json\n"
                    f"- Comparison JSON: "
                    f"{public_root}/compare.json?ids={{id}},{{id}}&lang=ru|kk|en\n"
                    f"- Opportunity history JSON: "
                    f"{public_root}/opportunities/{{id}}/history.json?lang=kk|ru|en&limit={{n}}\n"
                    f"- Source status page: {public_root}/status\n"
                    f"- Coverage JSON: {public_root}/coverage\n"
                    f"- Media page: {public_root}/media\n"
                    f"- Media JSON: {public_root}/media.json\n"
                    f"- Media JSON Feed: {public_root}/media/feed.json\n"
                    f"- Media RSS: {public_root}/media/rss.xml\n"
                    f"- Opportunities JSON: {public_root}/opportunities\n"
                    f"- Opportunities NDJSON: {public_root}/opportunities.ndjson\n"
                    "- Compact Opportunities NDJSON: "
                    f"{public_root}/opportunities.ndjson?compact=true\n"
                    f"- Digest JSON: {public_root}/digest\n"
                    "\n## AI consumption guidance\n"
                    "- Prefer compact Opportunities NDJSON for bulk discovery reads; "
                    "use the full NDJSON export when raw source payloads are needed.\n"
                ),
                headers={"cache-control": "public, max-age=300"},
            )
        if endpoint_path == "/docs" or path == "/docs":
            return httpx.Response(
                200,
                text=(
                    "<html><head><title>QAZ.FUND API</title></head>"
                    "<body>QAZ.FUND API /openapi.json</body></html>"
                ),
                headers={"content-type": "text/html; charset=utf-8"},
            )
        if endpoint_path == "/status" or path == "/status":
            return httpx.Response(
                200,
                text="<html><body><h1>Статус источников</h1></body></html>",
                headers={"content-type": "text/html; charset=utf-8"},
            )
        if endpoint_path == "/operator" or path == "/operator":
            return httpx.Response(
                200,
                text=(
                    '<html><head><meta name="robots" content="noindex,nofollow">'
                    "</head><body><h1>Контроль источников</h1>"
                    "X-Grant-Radar-Admin-Token</body></html>"
                ),
                headers={
                    "content-type": "text/html; charset=utf-8",
                    "x-robots-tag": "noindex, nofollow",
                },
            )
        if endpoint_path == "/site-discovery.json" or path == "/site-discovery.json":
            return httpx.Response(
                200,
                json={
                    "site": "QAZ.FUND",
                    "type": "public-funding-navigator",
                    "home": f"{public_root}/",
                    "sitemap": f"{public_root}/sitemap.xml",
                    "llms": f"{public_root}/llms.txt",
                    "api_docs": f"{public_root}/docs",
                    "openapi": f"{public_root}/openapi.json",
                    "source_status": f"{public_root}/status",
                    "release": f"{public_root}/.well-known/release.json",
                    "ecosystem": (f"{public_root}/.well-known/qdev-ecosystem.json"),
                    "contracts": {
                        "qazstack": (
                            f"{public_root}/.well-known/qazstack-consumer.json"
                        ),
                        "avds4": (f"{public_root}/.well-known/avds-ui-contract.json"),
                        "notifications": (
                            f"{public_root}/.well-known/notification-contract.json"
                        ),
                        "source_onboarding": (
                            f"{public_root}/.well-known/source-onboarding.json"
                        ),
                    },
                    "languages": ["kk", "ru", "en"],
                    "routes": {
                        "home": "/?lang={lang}",
                        "coverage": "/coverage",
                        "opportunities": "/opportunities?lang={lang}",
                        "opportunities_ndjson": "/opportunities.ndjson?lang={lang}",
                        "opportunities_ndjson_compact": (
                            "/opportunities.ndjson?lang={lang}&compact=true"
                        ),
                        "opportunity_api": "/opportunities/{id}?lang={lang}",
                        "opportunity_history": (
                            "/opportunities/{id}/history.json?lang={lang}&limit={n}"
                        ),
                        "opportunity": "/opportunity/{id}?lang={lang}",
                        "funder": "/funder/{slug}?lang={lang}",
                        "digest": "/digest?lang={lang}",
                        "insights": "/insights?lang={lang}",
                        "insights_json": "/insights.json?lang={lang}",
                        "media": "/media?lang={lang}",
                        "media_json": "/media.json?lang={lang}",
                        "media_feed": "/media/feed.json?lang={lang}",
                        "media_rss": "/media/rss.xml?lang={lang}",
                        "compare": "/compare?ids={id},{id}&lang={lang}",
                        "compare_json": "/compare.json?ids={id},{id}&lang={lang}",
                        "notification_contract": (
                            "/.well-known/notification-contract.json"
                        ),
                        "source_onboarding": "/.well-known/source-onboarding.json",
                    },
                    "data_endpoints": {
                        "coverage": f"{public_root}/coverage",
                        "opportunities": f"{public_root}/opportunities",
                        "opportunities_ndjson": (f"{public_root}/opportunities.ndjson"),
                        "opportunities_ndjson_compact": (
                            f"{public_root}/opportunities.ndjson?compact=true"
                        ),
                        "opportunity_history": (
                            f"{public_root}/opportunities/{{id}}/history.json"
                        ),
                        "digest": f"{public_root}/digest",
                        "insights": f"{public_root}/insights",
                        "insights_json": f"{public_root}/insights.json",
                        "media": f"{public_root}/media",
                        "media_json": f"{public_root}/media.json",
                        "media_feed": f"{public_root}/media/feed.json",
                        "media_rss": f"{public_root}/media/rss.xml",
                        "compare": f"{public_root}/compare.json",
                        "compare_json": f"{public_root}/compare.json",
                        "notification_contract": (
                            f"{public_root}/.well-known/notification-contract.json"
                        ),
                        "source_onboarding": (
                            f"{public_root}/.well-known/source-onboarding.json"
                        ),
                    },
                    "ai_consumption": {
                        "preferred_bulk_export": (
                            f"{public_root}/opportunities.ndjson?compact=true"
                        ),
                        "history_template": (
                            f"{public_root}/opportunities/{{id}}/history.json"
                            "?lang={lang}&limit={n}"
                        ),
                        "cache_policy": {"ndjson_seconds": 300},
                    },
                    "query_templates": {
                        "opportunities_recent": (
                            "/opportunities?lang=ru&limit=50&min_score=0.5"
                            "&deadline_after={yyyy-mm-dd}"
                        ),
                        "opportunities_by_tag": "/opportunities?lang=ru&limit=50&tag={tag}",
                        "digest_ai": "/digest?lang=ru&limit=5&tag=ai",
                    },
                    "capabilities": [
                        "public opportunity pages",
                        "public funder pages",
                        "machine-readable opportunity api",
                        "machine-readable opportunity comparison",
                        "public opportunity change history",
                        "machine-readable source coverage",
                        "official source links",
                        "notification contract (delivery disabled)",
                        "source onboarding contract",
                        "read-only public catalog",
                    ],
                },
                headers={"cache-control": "public, max-age=300"},
            )
        if endpoint_path == "/.well-known/qazstack-consumer.json":
            return httpx.Response(
                200,
                json={
                    "schema_version": "qazstack-consumer-v1",
                    "qazstack_version": "1.40.0",
                    "integration_mode": "python-package",
                },
                headers={"cache-control": "public, max-age=60"},
            )
        if endpoint_path == "/.well-known/avds-ui-contract.json":
            return httpx.Response(
                200,
                json={
                    "schema_version": "avds-ui-contract-v1",
                    "avds_source": {"version": "4.3.2"},
                },
                headers={"cache-control": "public, max-age=60"},
            )
        if endpoint_path == "/.well-known/notification-contract.json":
            return httpx.Response(
                200,
                json={
                    "schema_version": "notification-v1",
                    "status": "not_enabled",
                    "delivery": {"enabled": False, "worker_running": False},
                    "identity": {
                        "authenticated_owner": False,
                        "cross_device_sync": False,
                    },
                    "consent": {"collection_enabled": False, "version": None},
                },
                headers={"cache-control": "public, max-age=60"},
            )
        if endpoint_path == "/.well-known/source-onboarding.json":
            return httpx.Response(
                200,
                json={
                    "schema_version": "source-onboarding.v1",
                    "policy": {"credentials_in_public_contract": False},
                    "candidates": [{"slug": "openalex_context"}],
                },
                headers={"cache-control": "public, max-age=60"},
            )
        if endpoint_path == "/.well-known/qdev-ecosystem.json":
            return httpx.Response(
                200,
                json={
                    "schema_version": "qdev-ecosystem-integration-v1",
                    "integrations": {
                        "qazstack": {"status": "runtime-proven"},
                        "qazlake": {"direct_write": False},
                        "notifications": {"delivery_enabled": False},
                    },
                },
                headers={"cache-control": "public, max-age=60"},
            )
        return httpx.Response(404, json={"detail": "not found"})

    return httpx.MockTransport(handler)


def test_run_smoke_passes_for_expected_live_contract():
    result = run_smoke(
        base_url="https://example.org/grant-radar",
        deadline_after="2026-05-23",
        min_sources=23,
        min_opportunities=40,
        min_digest_items=1,
        expect_backend="database",
        forbidden=["AI3 Action Institute"],
        timeout=1.0,
        transport=_transport(),
    )

    assert result.health_items == 55
    assert result.release_revision == "a" * 40
    assert result.ready_backend == "database"
    assert result.coverage_sources == 23
    assert result.coverage_stale_sources == 1
    assert result.coverage_unknown_freshness_sources == 2
    assert result.opportunities == 44
    assert result.ndjson_items == 1
    assert result.media_items == 1
    assert result.media_feed_items == 1
    assert all(result.dashboard_markers.values())
    assert result.english_dashboard is True
    assert all(result.discovery_surfaces.values())


def test_run_smoke_supports_dedicated_domain_root():
    result = run_smoke(
        base_url="https://grant.example.org",
        deadline_after="2026-05-23",
        min_sources=23,
        min_opportunities=40,
        min_digest_items=1,
        expect_backend="database",
        forbidden=[],
        timeout=1.0,
        transport=_transport(),
    )

    assert result.base_url == "https://grant.example.org"
    assert result.opportunities == 44
    assert all(result.dashboard_markers.values())
    assert all(result.discovery_surfaces.values())


def test_run_smoke_rejects_forbidden_content():
    with pytest.raises(SmokeError, match="forbidden content"):
        run_smoke(
            base_url="https://example.org/grant-radar",
            deadline_after="2026-05-23",
            min_sources=23,
            min_opportunities=40,
            min_digest_items=1,
            expect_backend="database",
            forbidden=["AI3 Action Institute"],
            timeout=1.0,
            transport=_transport(
                opportunity_title="AI3 Action Institute - Artificial Intelligence"
            ),
        )


def test_run_smoke_result_is_json_serializable():
    result = run_smoke(
        base_url="https://example.org/grant-radar",
        deadline_after="2026-05-23",
        min_sources=23,
        min_opportunities=40,
        min_digest_items=1,
        expect_backend="database",
        forbidden=[],
        timeout=1.0,
        transport=_transport(),
    )

    assert "Kazakhstan AI grant" not in json.dumps(result.__dict__)
