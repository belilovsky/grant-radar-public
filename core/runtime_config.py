"""Shared runtime configuration owned by the application core."""

from __future__ import annotations

import os


def resolve_database_url(explicit: str | None = None) -> str:
    """Resolve database configuration with one precedence rule for all layers."""

    value = explicit
    if value is None:
        value = os.environ.get("GRANT_RADAR_DB_URL") or os.environ.get("DATABASE_URL")
    return (value or "").strip()
