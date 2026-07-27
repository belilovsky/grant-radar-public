from __future__ import annotations

import json

import httpx
import pytest

from scripts.production_smoke import SmokeError, run_smoke


def _transport(
    *,
    opportunity_title: str = "Kazakhstan AI grant",
    opportunity_count: int = 44,
    coverage_current: int = 44,
    insights_current: int = 44,
) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        sample_id = "00000000-0000-4000-8000-000000000001"
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
                '<div data-avds-component="quick-links-rail"></div>'
                '<div data-avds-component="public-summary-strip">'
                '<strong id="metric-strong" data-catalog-count="44">44</strong>'
                '<strong id="metric-sources">23</strong>'
                "</div>"
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
                    "relevant_open_items": coverage_current,
                    "stale_sources": 1,
                    "unknown_freshness_sources": 2,
                },
            )
        if endpoint_path == "/opportunities":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": sample_id,
                        "title": opportunity_title,
                        "source": "world_bank_kazakhstan",
                    }
                    for _ in range(opportunity_count)
                ],
            )
        if endpoint_path == "/funders":
            return httpx.Response(
                200,
                json=[
                    {
                        "slug": "development-fund",
                        "name": "Development Fund",
                        "current_items": 3,
                    }
                ],
            )
        if endpoint_path == "/opportunities.ndjson":
            return httpx.Response(
                200,
                text=(
                    '{"title":"Kazakhstan AI grant","source":"world_bank_kazakhstan",'
                    '"evidence_state":"sourced"}\n'
                ),
                headers={
                    "content-type": "application/x-ndjson",
                    "cache-control": "public, max-age=300",
                },
            )
        if endpoint_path == "/api/v1/opportunities.ndjson":
            return httpx.Response(
                200,
                text="",
                headers={
                    "content-type": "application/x-ndjson; charset=utf-8",
                    "cache-control": "public, max-age=300",
                },
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
                    f"- QazPipe source contract: "
                    f"{public_root}/.well-known/qazpipe-source.json\n"
                    f"- QazCompute profile contract: "
                    f"{public_root}/.well-known/qazcompute-profiles.json\n"
                    f"- Source status page: {public_root}/status\n"
                    f"- Coverage JSON: {public_root}/coverage\n"
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
        if endpoint_path == "/insights":
            return httpx.Response(
                200,
                text=(
                    '<html lang="ru" data-avds="grant-radar">'
                    '<main data-avds-component="data-centre">'
                    "<span>В текущем каталоге</span>"
                    "<span>Релевантных карточек в индексе</span>"
                    '<section data-avds-pattern="data-quality-scorecard"></section>'
                    "</main></html>"
                ),
                headers={"content-type": "text/html; charset=utf-8"},
            )
        if endpoint_path == f"/opportunity/{sample_id}":
            return httpx.Response(
                200,
                text=(
                    '<html lang="ru" data-avds="grant-radar">'
                    '<main data-avds-component="lite-reading-surface">'
                    "<h1>Kazakhstan AI grant</h1><h2>Ключевые условия</h2>"
                    "</main></html>"
                ),
                headers={"content-type": "text/html; charset=utf-8"},
            )
        if endpoint_path == f"/opportunity/{sample_id}/prepare":
            return httpx.Response(
                200,
                text=(
                    '<html lang="ru" data-avds="grant-radar">'
                    '<main data-avds-component="application-workspace">'
                    "<p>Данные остаются в этом браузере</p>"
                    "<script>localStorage.setItem('draft','value')</script>"
                    "</main></html>"
                ),
                headers={"content-type": "text/html; charset=utf-8"},
            )
        if endpoint_path == "/funder/development-fund":
            return httpx.Response(
                200,
                text=(
                    '<html lang="ru" data-avds="grant-radar">'
                    "<main><h1>Development Fund</h1><span>QAZ.FUND</span></main>"
                    "</html>"
                ),
                headers={"content-type": "text/html; charset=utf-8"},
            )
        if endpoint_path in {"/terms", "/data-policy", "/attribution"}:
            labels = {
                "/terms": "Условия использования",
                "/data-policy": "Политика данных",
                "/attribution": "Цитирование и повторное использование",
            }
            return httpx.Response(
                200,
                text=f"<html lang='ru'><h1>{labels[endpoint_path]}</h1></html>",
                headers={"content-type": "text/html; charset=utf-8"},
            )
        if endpoint_path == "/opportunity/not-a-valid-id":
            return httpx.Response(
                404,
                text=(
                    "<html lang='ru'><h1>Такой страницы нет</h1>"
                    "<a href='/'>Вернуться в каталог</a></html>"
                ),
                headers={"content-type": "text/html; charset=utf-8"},
            )
        if endpoint_path == "/api/v1":
            return httpx.Response(
                200,
                json={
                    "routes": {
                        "daily_digest_json": (
                            f"{public_root}/media/v1/digest/daily.json"
                        ),
                        "daily_digest_text": (
                            f"{public_root}/media/v1/digest/daily.txt"
                        ),
                    }
                },
            )
        if endpoint_path == "/api/v1/insights":
            return httpx.Response(
                200,
                json={
                    "schema_version": "qazfund-insights.v1",
                    "scope": {
                        "indexed_relevant": 55,
                        "current_catalog": insights_current,
                        "active": insights_current,
                    },
                },
                headers={
                    "content-type": "application/json",
                    "cache-control": "public, max-age=60",
                },
            )
        if endpoint_path == "/api/v1/changes":
            return httpx.Response(
                200,
                json={"schema_version": "qazfund-changes.v1"},
            )
        if endpoint_path == "/media/v1/digest/daily.json":
            return httpx.Response(
                200,
                json={
                    "schema_version": "qazfund-daily-digest.v1",
                    "state": "collecting",
                    "delivery": {"automatic": False},
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
                        "qazpipe": (f"{public_root}/.well-known/qazpipe-source.json"),
                        "qazcompute": (
                            f"{public_root}/.well-known/qazcompute-profiles.json"
                        ),
                    },
                    "languages": ["ru", "en"],
                    "routes": {
                        "home": "/?lang={lang}",
                        "coverage": "/coverage",
                        "opportunities": "/opportunities?lang={lang}",
                        "opportunities_ndjson": "/opportunities.ndjson?lang={lang}",
                        "opportunities_ndjson_compact": (
                            "/opportunities.ndjson?lang={lang}&compact=true"
                        ),
                        "opportunity_api": "/opportunities/{id}?lang={lang}",
                        "opportunity": "/opportunity/{id}?lang={lang}",
                        "funder": "/funder/{slug}?lang={lang}",
                        "digest": "/digest?lang={lang}",
                    },
                    "data_endpoints": {
                        "coverage": f"{public_root}/coverage",
                        "opportunities": f"{public_root}/opportunities",
                        "opportunities_ndjson": (f"{public_root}/opportunities.ndjson"),
                        "opportunities_ndjson_compact": (
                            f"{public_root}/opportunities.ndjson?compact=true"
                        ),
                        "api_v1_opportunities_ndjson": (
                            f"{public_root}/api/v1/opportunities.ndjson"
                        ),
                        "digest": f"{public_root}/digest",
                    },
                    "versioned_api": f"{public_root}/api/v1",
                    "ai_consumption": {
                        "preferred_bulk_export": (
                            f"{public_root}/api/v1/opportunities.ndjson"
                        ),
                        "preferred_legacy_bulk_export": (
                            f"{public_root}/opportunities.ndjson?compact=true"
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
                        "machine-readable source coverage",
                        "official source links",
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
                    "qazstack_version": "1.41.2",
                    "integration_mode": "python-package",
                    "primitives": [
                        "opportunity-public-contract",
                        "opportunity-ranking-evaluation",
                    ],
                },
                headers={"cache-control": "public, max-age=60"},
            )
        if endpoint_path == "/.well-known/avds-ui-contract.json":
            return httpx.Response(
                200,
                json={
                    "schema_version": "avds-ui-contract-v1",
                    "avds_source": {"version": "4.6.0"},
                    "runtime_neutral_patterns": {
                        "adopted": [
                            "evidence-summary",
                            "filter-state-summary",
                            "decision-summary",
                            "evidence-disclosure",
                            "action-path",
                        ]
                    },
                },
                headers={"cache-control": "public, max-age=60"},
            )
        if endpoint_path == "/.well-known/qazpipe-source.json":
            return httpx.Response(
                200,
                json={
                    "schema_version": "qazpipe-pull-source-v1",
                    "mode": "pull",
                    "direction": "outbound-read-only",
                    "endpoints": {
                        "bulk_ndjson": (f"{public_root}/api/v1/opportunities.ndjson")
                    },
                    "required_provenance": [
                        "source.url",
                        "provenance.content_hash",
                        "provenance.verification_method",
                    ],
                    "qazlake_handoff": {"direct_write": False},
                },
                headers={"cache-control": "public, max-age=60"},
            )
        if endpoint_path == "/.well-known/qazcompute-profiles.json":
            return httpx.Response(
                200,
                json={
                    "schema_version": "qazcompute-profile-contract-v1",
                    "execution": {
                        "runtime_status": "proven",
                        "remote_execution_active": False,
                        "decision_ready": False,
                    },
                    "profiles": [
                        {"schema_version": "evidence_readiness.v1"},
                        {"schema_version": "deadline_anomaly.v1"},
                        {"schema_version": "source_freshness.v1"},
                        {"schema_version": "duplicate_cluster.v1"},
                    ],
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
                        "qazpipe": {"status": "producer-ready"},
                        "qazlake": {"direct_write": False},
                        "qazcompute": {"status": "local-runtime-proven"},
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


def test_run_smoke_rejects_cross_surface_current_catalog_mismatch():
    with pytest.raises(SmokeError, match="coverage and deadline-filtered"):
        run_smoke(
            base_url="https://example.org/grant-radar",
            deadline_after="2026-05-23",
            min_sources=23,
            min_opportunities=40,
            min_digest_items=1,
            expect_backend="database",
            forbidden=[],
            timeout=1.0,
            transport=_transport(coverage_current=45),
        )

    with pytest.raises(SmokeError, match="insights and deadline-filtered"):
        run_smoke(
            base_url="https://example.org/grant-radar",
            deadline_after="2026-05-23",
            min_sources=23,
            min_opportunities=40,
            min_digest_items=1,
            expect_backend="database",
            forbidden=[],
            timeout=1.0,
            transport=_transport(insights_current=45),
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
