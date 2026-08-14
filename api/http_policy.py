"""HTTP security, embedding, and cache policy for public responses."""

from __future__ import annotations

from fastapi import Request
from starlette.responses import Response

PUBLIC_FAST_CACHE = "public, max-age=60, stale-while-revalidate=300"
PUBLIC_DISCOVERY_CACHE = "public, max-age=300, stale-while-revalidate=1800"
PUBLIC_LONG_CACHE = "public, max-age=3600, stale-while-revalidate=86400"
PUBLIC_NO_STORE = "no-store"

_MACHINE_ROUTE_PREFIXES = (
    "/.well-known",
    "/compare.json",
    "/coverage",
    "/digest",
    "/funders",
    "/health",
    "/insights.json",
    "/openapi.json",
    "/opportunities",
    "/operator/health",
    "/ready",
    "/refresh",
    "/site-discovery.json",
    "/sources",
    "/media/v1",
)
_FAST_CACHE_PATHS = {
    "/.well-known/avds-ui-contract.json",
    "/.well-known/qazcompute-profiles.json",
    "/.well-known/qazpipe-source.json",
    "/.well-known/qazstack-consumer.json",
    "/.well-known/qdev-ecosystem.json",
    "/.well-known/notification-contract.json",
    "/.well-known/source-onboarding.json",
    "/compare",
    "/compare.json",
    "/insights.json",
    "/opportunities.ndjson",
}
_LIVE_DASHBOARD_PATHS = {
    "/",
    "/coverage",
    "/funders",
    "/health",
    "/opportunities",
}
_DISCOVERY_CACHE_PATHS = {
    "/llms.txt",
    "/robots.txt",
    "/site-discovery.json",
    "/sitemap.xml",
    "/sources",
}


def is_machine_route(path: str) -> bool:
    return path.startswith(_MACHINE_ROUTE_PREFIXES)


def cache_control_for(path: str) -> str | None:
    # The landing screen hydrates from these endpoints. Serving them from a
    # browser's stale-while-revalidate cache mixes old totals with a fresh
    # catalogue and creates visibly contradictory metrics after an update.
    if path in _LIVE_DASHBOARD_PATHS:
        return PUBLIC_NO_STORE
    if path.startswith("/assets/branding/"):
        return PUBLIC_LONG_CACHE
    if path in _FAST_CACHE_PATHS:
        return PUBLIC_FAST_CACHE
    if path in _DISCOVERY_CACHE_PATHS:
        return PUBLIC_DISCOVERY_CACHE
    if path in {
        "/favicon.ico",
        "/og-image.png",
        "/og-image.svg",
        "/google6ce0cb641d438c0c.html",
    }:
        return PUBLIC_LONG_CACHE
    return None


def apply_public_headers(request: Request, response: Response) -> Response:
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    if request.url.path.startswith("/embed/"):
        if "X-Frame-Options" in response.headers:
            del response.headers["X-Frame-Options"]
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; script-src 'none'; style-src 'unsafe-inline'; "
            "img-src 'none'; font-src 'none'; connect-src 'none'; object-src 'none'; "
            "base-uri 'none'; form-action 'none'; "
            "frame-ancestors https://qaz.support https://www.qaz.support"
        )
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
    else:
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=(), payment=()",
    )
    if request.method in {"GET", "HEAD"}:
        cache_control = cache_control_for(request.url.path)
        if cache_control:
            response.headers.setdefault("Cache-Control", cache_control)
    return response
