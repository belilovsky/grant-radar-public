"""Environment-backed runtime configuration with deterministic normalization."""

from __future__ import annotations

import os
from urllib.parse import urlparse

from core.runtime_config import resolve_database_url


def database_url() -> str:
    return resolve_database_url()


def public_base_url() -> str:
    return os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")


def allowed_hosts() -> list[str]:
    hosts = {"localhost", "127.0.0.1", "::1", "testserver", "qaz.fund"}
    for raw in os.environ.get("GRANT_RADAR_ALLOWED_HOSTS", "").split(","):
        host = raw.strip().lower()
        if host:
            hosts.add(host)
    configured_base = public_base_url()
    if configured_base:
        host = (urlparse(configured_base).hostname or "").strip().lower()
        if host:
            hosts.add(host)
    return sorted(hosts)


def admin_token() -> str:
    return os.environ.get("GRANT_RADAR_ADMIN_TOKEN", "").strip()


def bearer_token(authorization: str | None) -> str:
    if not authorization:
        return ""
    scheme, _, token = authorization.partition(" ")
    return token.strip() if scheme.lower() == "bearer" else ""
