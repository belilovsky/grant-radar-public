"""Production smoke checks for a live QAZ.FUND deployment."""

from __future__ import annotations

import argparse
import json
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
    'class="toolbar avds-tabs-list"',
    "avds-tabs-trigger",
    "avds-field",
    'data-avds-component="source-card"',
    'data-avds-component="source-icon"',
    "avds-source-card__arrow",
    'data-avds-component="source-url"',
    'data-avds-component="opportunity-card"',
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
    deadline_after: str
    health_items: int
    ready_backend: str
    coverage_sources: int
    coverage_relevant_open_items: int
    opportunities: int
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


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeError(message)


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
        digest = _get_json(client, base_url, "/digest?limit=5&tag=ai")
        robots = _get_text(client, base_url, "/robots.txt")
        sitemap = _get_text(client, base_url, "/sitemap.xml")
        llms = _get_text(client, base_url, "/llms.txt")
        docs = _get_text(client, base_url, "/docs")
        discovery = _get_json(client, base_url, "/site-discovery.json")

    _require(health.get("status") == "ok", "health status is not ok")
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
        "llms_home": f"Home: {_url(base_url, '/')}" in llms,
        "llms_sitemap": f"Sitemap: {_url(base_url, '/sitemap.xml')}" in llms,
        "llms_openapi": f"OpenAPI schema: {_url(base_url, '/openapi.json')}" in llms,
        "docs_brand": "QAZ.FUND API" in docs,
        "docs_openapi": "/openapi.json" in docs,
        "site_discovery_openapi": str(discovery.get("openapi") or "")
        == _url(base_url, "/openapi.json"),
        "site_discovery_llms": str(discovery.get("llms") or "")
        == _url(base_url, "/llms.txt"),
        "site_discovery_docs": str(discovery.get("api_docs") or "")
        == _url(base_url, "/docs"),
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
        deadline_after=deadline_after,
        health_items=int(health.get("items") or 0),
        ready_backend=str(ready.get("backend") or ""),
        coverage_sources=int(coverage.get("enabled_sources") or 0),
        coverage_relevant_open_items=int(coverage.get("relevant_open_items") or 0),
        opportunities=len(opportunities),
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
    parser.add_argument("--min-sources", type=int, default=23)
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
