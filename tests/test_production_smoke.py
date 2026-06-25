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
    assert result.opportunities == 44
    assert all(result.dashboard_markers.values())
    assert result.english_dashboard is True


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
