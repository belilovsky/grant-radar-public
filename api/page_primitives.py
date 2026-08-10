"""Shared URL and display primitives for server-rendered public pages."""

from __future__ import annotations

from datetime import date


def absolute_href(origin: str, path: str) -> str:
    """Resolve a public path without changing already absolute URLs."""

    clean_origin = origin.rstrip("/")
    if path.startswith(("http://", "https://")):
        return path
    if not clean_origin:
        return path or "/"
    return f"{clean_origin}{path}" if path else clean_origin


def catalog_path(root_path: str, lang: str) -> str:
    """Build the localized catalog anchor under an optional ASGI root path."""

    base = root_path.rstrip("/")
    return (
        f"{base}/?lang={lang}#opportunities" if base else f"/?lang={lang}#opportunities"
    )


def format_deadline(value: date | None, lang: str, rolling_label: str) -> str:
    """Format public deadlines consistently across detail and funder pages."""

    if value is None:
        return rolling_label
    if lang == "en":
        return value.strftime("%b %d, %Y")
    return value.strftime("%d.%m.%Y")
