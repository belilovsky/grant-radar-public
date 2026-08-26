"""Generated registry of public route surfaces and their declared states."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute

from api.http_policy import cache_control_for, is_machine_route

PUBLIC_LANGUAGES = ("ru", "kk", "en")
PUBLIC_VIEWPORTS = ("393x852", "768x1024", "1440x960", "320x800", "1920x1080")


@dataclass(frozen=True, slots=True)
class RouteSurface:
    path: str
    name: str
    methods: tuple[str, ...]
    content_type: str
    cache_policy: str
    authentication: str
    languages: tuple[str, ...]
    viewports: tuple[str, ...]
    states: tuple[str, ...]


def _states_for(path: str) -> tuple[str, ...]:
    if path == "/":
        return ("open", "closing", "rolling", "forecast", "closed", "empty")
    if path in {"/opportunities", "/funders", "/media"}:
        return ("populated", "empty")
    if path.startswith("/opportunity/"):
        return (
            "open",
            "closing",
            "rolling",
            "forecast",
            "closed",
            "missing",
            "404",
        )
    if path.startswith("/funder/"):
        return ("populated", "empty", "missing", "404")
    if path.startswith("/operator"):
        return ("operator-authorized", "operator-unauthorized")
    if path in {"/ready", "/status"}:
        return ("healthy", "semantic-degraded")
    return ("default",)


def build_route_registry(app: FastAPI) -> tuple[RouteSurface, ...]:
    """Build deterministic route metadata from the running FastAPI application."""

    surfaces: dict[tuple[str, str], RouteSurface] = {}
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        path = str(route.path)
        name = str(route.name)
        methods = tuple(
            sorted(method for method in route.methods if method != "OPTIONS")
        )
        machine = is_machine_route(path) or path.endswith((".json", ".xml", ".txt"))
        html = not machine and not path.startswith("/assets/")
        key = (path, name)
        previous = surfaces.get(key)
        if previous is not None:
            methods = tuple(sorted(set(previous.methods).union(methods)))
        surfaces[key] = RouteSurface(
            path=path,
            name=name,
            methods=methods,
            content_type="text/html" if html else "machine",
            cache_policy=cache_control_for(path) or "endpoint-defined",
            authentication=(
                "admin-token"
                if path.startswith("/operator/") or path.startswith("/refresh")
                else "public-shell" if path == "/operator" else "public"
            ),
            languages=PUBLIC_LANGUAGES if html else (),
            viewports=PUBLIC_VIEWPORTS if html else (),
            states=_states_for(path),
        )
    return tuple(
        sorted(surfaces.values(), key=lambda item: (item.path, item.methods, item.name))
    )


def route_coverage(surfaces: tuple[RouteSurface, ...]) -> dict[str, Any]:
    """Report real GET/HEAD coverage and explicit gaps across the route registry."""

    methods_by_path: dict[str, set[str]] = {}
    for surface in surfaces:
        methods_by_path.setdefault(surface.path, set()).update(surface.methods)
    required: list[str] = []
    covered: list[str] = []
    for path, methods in methods_by_path.items():
        if "GET" not in methods:
            continue
        for method in ("GET", "HEAD"):
            key = f"{method} {path}"
            required.append(key)
            if method in methods:
                covered.append(key)
    missing = sorted(set(required) - set(covered))
    total = len(required)
    covered_count = len(covered)
    return {
        "basis": "generated-fastapi-route-method-registry",
        "route_count": len(surfaces),
        "covered": covered_count,
        "total": total,
        "percent": round((covered_count / total * 100), 2) if total else 100.0,
        "gaps": missing,
        "languages": list(PUBLIC_LANGUAGES),
        "viewports": list(PUBLIC_VIEWPORTS),
        "routes": [asdict(surface) for surface in surfaces],
    }
