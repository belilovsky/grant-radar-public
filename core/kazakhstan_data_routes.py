"""Transparent routes to Kazakhstan's official public-data surfaces."""

from __future__ import annotations

import json
from copy import deepcopy
from functools import cache
from pathlib import Path
from typing import Any

from core.localization import normalize_content_lang

DATA_ROUTE_SCHEMA_VERSION = "kazakhstan-data-routes.v1"
_DATA_FILE = Path(__file__).with_name("kazakhstan_data_routes.json")


@cache
def _registry() -> dict[str, Any]:
    """Load the reviewed public copy once per process."""

    with _DATA_FILE.open(encoding="utf-8") as handle:
        loaded = json.load(handle)
    return loaded if isinstance(loaded, dict) else {}


def _localized(section: str, lang: str | None) -> dict[str, Any]:
    active_lang = normalize_content_lang(lang)
    values = _registry().get(section)
    if not isinstance(values, dict):
        return {}
    selected = values.get(active_lang) or values.get("ru") or {}
    return deepcopy(selected) if isinstance(selected, dict) else {}


def data_routes(lang: str | None = None) -> list[dict[str, Any]]:
    """Return official verification routes in the requested public language."""

    active_lang = normalize_content_lang(lang)
    raw_routes = _registry().get("routes")
    if not isinstance(raw_routes, list):
        return []
    rows: list[dict[str, Any]] = []
    for route in raw_routes:
        if not isinstance(route, dict):
            continue
        localized = route.get("copy")
        if not isinstance(localized, dict):
            continue
        copy = localized.get(active_lang) or localized.get("ru") or {}
        if not isinstance(copy, dict):
            continue
        rows.append(
            {
                "id": str(route.get("id") or ""),
                "coverage": str(route.get("coverage") or "not_indexed"),
                "url": str(route.get("url") or ""),
                "roles": list(route.get("roles") or ()),
                **deepcopy(copy),
            }
        )
    return rows


def data_routes_page_copy(lang: str | None = None) -> dict[str, Any]:
    """Return the source-first page copy in the requested language."""

    return _localized("page_copy", lang)


def data_routes_contract(origin: str) -> dict[str, Any]:
    """Expose the honest data-coverage boundary for public API consumers."""

    base = origin.rstrip("/")
    return {
        "schema_version": DATA_ROUTE_SCHEMA_VERSION,
        "product": "qaz-fund",
        "purpose": "official-verification-routes",
        "catalog_boundary": (
            "These routes are public verification surfaces. They are not all "
            "automatically ingested as QAZ.FUND opportunities."
        ),
        "human_page": f"{base}/data-routes?lang=ru",
        "routes": data_routes("en"),
    }
