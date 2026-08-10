"""Safe client for the optional internal semantic-search service.

The public API never sends source ``raw`` payloads to this service.  It only
asks the internal service to rank UUIDs already present in the public catalog;
the API applies all lifecycle and public-scope filters itself afterwards.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable
from uuid import UUID

import httpx

from core.models import Opportunity

logger = logging.getLogger(__name__)


def _enabled() -> bool:
    return os.environ.get("GRANT_RADAR_SEMANTIC_SEARCH_ENABLED", "0").strip() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _service_url() -> str:
    return os.environ.get("GRANT_RADAR_SEMANTIC_SEARCH_URL", "").strip().rstrip("/")


def _timeout_seconds() -> float:
    try:
        return min(
            10.0,
            max(
                0.2, float(os.environ.get("GRANT_RADAR_SEMANTIC_TIMEOUT_SECONDS", "2"))
            ),
        )
    except ValueError:
        return 2.0


@dataclass(frozen=True)
class SemanticSearchHit:
    """One ranking decision made by the internal semantic service."""

    opportunity_id: UUID
    score: float


@lru_cache(maxsize=8)
def _client(url: str, timeout_seconds: float) -> httpx.Client:
    return httpx.Client(base_url=url, timeout=timeout_seconds)


def clear_semantic_search_client_cache() -> None:
    """Reset environment-dependent clients for tests and runtime reconfiguration."""

    _client.cache_clear()


def search_opportunities(
    query: str,
    items: Iterable[Opportunity],
    *,
    limit: int,
) -> list[SemanticSearchHit]:
    """Return ordered public UUIDs, or an empty list for lexical fallback.

    The service receives an allowlist of IDs from the already-filtered public
    catalog.  This makes stale vector points harmless and prevents a semantic
    response from bypassing a lifecycle, relevance, or regional filter.
    """

    normalized_query = query.strip()
    service_url = _service_url()
    allowed_ids = [str(item.id) for item in items]
    if not normalized_query or not service_url or not _enabled() or not allowed_ids:
        return []

    try:
        response = _client(service_url, _timeout_seconds()).post(
            "/search",
            json={
                "query": normalized_query,
                "allowed_ids": allowed_ids,
                "limit": max(1, min(limit, len(allowed_ids), 5000)),
            },
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("semantic_search_unavailable: %s", exc)
        return []

    rows = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        logger.warning("semantic_search_invalid_response")
        return []

    allowed = set(allowed_ids)
    hits: list[SemanticSearchHit] = []
    seen: set[UUID] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw_id = str(row.get("id") or "")
        if raw_id not in allowed:
            continue
        try:
            opportunity_id = UUID(raw_id)
            raw_score = row.get("score")
            if raw_score is None:
                continue
            score = float(raw_score)
        except (TypeError, ValueError):
            continue
        if opportunity_id in seen:
            continue
        seen.add(opportunity_id)
        hits.append(SemanticSearchHit(opportunity_id=opportunity_id, score=score))
    return hits
