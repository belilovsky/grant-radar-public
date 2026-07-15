"""Shared source-text normalization for collector adapters."""

from __future__ import annotations

from html import unescape

from qazstack.content import normalize_text, strip_html


def clean_source_text(value: object | None) -> str:
    """Return decoded, tag-free and whitespace-normalized source text."""

    return strip_html("" if value is None else str(value))


def clean_plain_source_text(value: object | None) -> str:
    """Decode entities and normalize spacing while preserving literal markup."""

    return normalize_text(unescape("" if value is None else str(value)))
