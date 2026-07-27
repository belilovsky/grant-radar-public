"""Business clock for Kazakhstan-facing public dates."""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger(__name__)

DEFAULT_PUBLIC_TIME_ZONE = "Asia/Almaty"
PUBLIC_TIME_ZONE_ENV = "GRANT_RADAR_TIME_ZONE"


@lru_cache(maxsize=8)
def _time_zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        logger.warning(
            "public_time_zone_invalid name=%s fallback=%s",
            name,
            DEFAULT_PUBLIC_TIME_ZONE,
        )
        return ZoneInfo(DEFAULT_PUBLIC_TIME_ZONE)


def public_time_zone_name() -> str:
    """Return the configured IANA zone, falling back to Kazakhstan time."""

    configured = os.environ.get(PUBLIC_TIME_ZONE_ENV, "").strip()
    candidate = configured or DEFAULT_PUBLIC_TIME_ZONE
    zone = _time_zone(candidate)
    return getattr(zone, "key", DEFAULT_PUBLIC_TIME_ZONE)


def public_now(now: datetime | None = None) -> datetime:
    """Return an aware timestamp in the public business time zone."""

    source = now or datetime.now(timezone.utc)
    if source.tzinfo is None:
        source = source.replace(tzinfo=timezone.utc)
    return source.astimezone(_time_zone(public_time_zone_name()))


def public_today(now: datetime | None = None) -> date:
    """Return the current Kazakhstan-facing calendar day."""

    return public_now(now).date()


__all__ = [
    "DEFAULT_PUBLIC_TIME_ZONE",
    "PUBLIC_TIME_ZONE_ENV",
    "public_now",
    "public_time_zone_name",
    "public_today",
]
