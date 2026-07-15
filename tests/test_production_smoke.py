from __future__ import annotations

import json

import httpx
import pytest

from scripts.production_smoke import SmokeError, run_smoke


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
                    {"title": opportunity_title, "source": "world_bank_kazakhstan"}
                    for _ in range(44)
                ],
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
            )
        if endpoint_path == "/sitemap.xml" or path == "/sitemap.xml":
            return httpx.Response(
                200,
                text='<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>',
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
                    f"- QazStack consumer contract: "
                    f"{public_root}/.well-known/qazstack-consumer.json\n"
                    f"- AV DS 4 UI contract: "
                    f"{public_root}/.well-known/avds-ui-contract.json\n"
                    f"- Source status page: {public_root}/status\n"
                    f"- Coverage JSON: {public_root}/coverage\n"
                    f"- Opportunities JSON: {public_root}/opportunities\n"
                    f"- Opportunities NDJSON: {public_root}/opportunities.ndjson\n"
                    f"- Digest JSON: {public_root}/digest\n"
                ),
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
                    "ecosystem": (f"{public_root}/.well-known/qdev-ecosystem.json"),
                    "contracts": {
                        "qazstack": (
                            f"{public_root}/.well-known/qazstack-consumer.json"
                        ),
                        "avds4": (f"{public_root}/.well-known/avds-ui-contract.json"),
                    },
                    "languages": ["ru", "en"],
                    "routes": {
                        "home": "/?lang={lang}",
                        "coverage": "/coverage",
                        "opportunities": "/opportunities?lang={lang}",
                        "opportunities_ndjson": "/opportunities.ndjson?lang={lang}",
                        "opportunity_api": "/opportunities/{id}?lang={lang}",
                        "opportunity": "/opportunity/{id}?lang={lang}",
                        "funder": "/funder/{slug}?lang={lang}",
                        "digest": "/digest?lang={lang}",
                    },
                    "data_endpoints": {
                        "coverage": f"{public_root}/coverage",
                        "opportunities": f"{public_root}/opportunities",
                        "opportunities_ndjson": (f"{public_root}/opportunities.ndjson"),
                        "digest": f"{public_root}/digest",
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
                        "machine-readable source coverage",
                        "official source links",
                        "read-only public catalog",
                    ],
                },
            )
        if endpoint_path == "/.well-known/qazstack-consumer.json":
            return httpx.Response(
                200,
                json={
                    "schema_version": "qazstack-consumer-v1",
                    "qazstack_version": "1.37.2",
                    "integration_mode": "python-package",
                },
            )
        if endpoint_path == "/.well-known/avds-ui-contract.json":
            return httpx.Response(
                200,
                json={
                    "schema_version": "avds-ui-contract-v1",
                    "avds_source": {"version": "4.3.2"},
                },
            )
        if endpoint_path == "/.well-known/qdev-ecosystem.json":
            return httpx.Response(
                200,
                json={
                    "schema_version": "qdev-ecosystem-integration-v1",
                    "integrations": {
                        "qazstack": {"status": "runtime-proven"},
                        "qazlake": {"direct_write": False},
                    },
                },
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
    assert result.ready_backend == "database"
    assert result.coverage_sources == 23
    assert result.coverage_stale_sources == 1
    assert result.coverage_unknown_freshness_sources == 2
    assert result.opportunities == 44
    assert result.ndjson_items == 1
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
