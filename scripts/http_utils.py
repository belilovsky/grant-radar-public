"""Shared HTTP URL helpers for read-only operator scripts."""

from __future__ import annotations

from urllib.parse import urljoin


def join_url(base_url: str, path: str) -> str:
    """Join an operator-supplied base URL with a relative public route."""

    return urljoin(f"{base_url.rstrip('/')}/", path.lstrip("/"))
