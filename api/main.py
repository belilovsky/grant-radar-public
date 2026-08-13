"""FastAPI app for grant-radar."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import threading
from collections.abc import Awaitable, Callable, Iterable, Mapping
from contextlib import asynccontextmanager, suppress
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from hmac import compare_digest
from html import escape
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from pydantic import TypeAdapter
from qazstack.content import diversify_ranked_items
from qazstack.evidence import count_evidence_states, resolve_public_evidence_state
from qazstack.export import cached_body_response
from qazstack.opportunities import public_lifecycle
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from api.application_prep_page import render_application_prep_page
from api.avds import AVDS_CSS
from api.catalog import build_funder_index as _build_funder_index
from api.catalog import funder_name as _funder_name
from api.catalog import funder_payload as _funder_payload
from api.catalog import funder_region_tokens as _funder_region_tokens
from api.catalog import matches_opportunity_query as _matches_opportunity_query
from api.catalog import normalized_token as _normalized_token
from api.catalog import related_reason_key as _related_reason_key
from api.catalog import related_relevance as _related_relevance
from api.catalog import slugify_funder as _slugify_funder
from api.catalog import source_name as _source_name
from api.comparison import (
    MAX_COMPARISON_ITEMS,
    build_comparison_snapshot,
    parse_comparison_ids,
)
from api.comparison_page import render_comparison_page
from api.daily_digest import daily_digest_payload, daily_digest_text
from api.dashboard import (
    GOOGLE_SITE_VERIFICATION_CONTENT,
    GOOGLE_SITE_VERIFICATION_FILENAME,
    render_dashboard,
)
from api.dashboard_copy import dashboard_copy as localized_dashboard_copy
from api.ecosystem import (
    avds_ui_contract,
    ecosystem_manifest,
    qazcompute_profile_contract,
    qazpipe_source_contract,
    qazstack_consumer_contract,
)
from api.embed_page import render_coverage_embed, render_opportunities_embed
from api.error_page import render_not_found_page
from api.funder_page import render_funder_page
from api.history import build_history_snapshot
from api.http_policy import PUBLIC_DISCOVERY_CACHE as _PUBLIC_DISCOVERY_CACHE
from api.http_policy import PUBLIC_FAST_CACHE as _PUBLIC_FAST_CACHE
from api.http_policy import apply_public_headers, is_machine_route
from api.insights import build_insights_payload
from api.insights_page import build_insights_snapshot, render_insights_page
from api.media import (
    CARD_FORMATS,
    CHART_TYPES,
    chart_csv,
    chart_rows,
    chart_title,
    citation_text,
    content_payload,
    json_dumps,
    json_feed,
    render_chart_svg,
    render_opportunity_card_svg,
    rss_feed,
)
from api.media_page import (
    build_media_feed,
    build_media_rss,
    build_media_snapshot,
    media_feed_metadata,
    render_media_page,
)
from api.notification_contract import notification_contract
from api.operator_page import render_operator_page
from api.opportunity_detail import build_opportunity_detail
from api.opportunity_mapping import display_summary as _display_summary
from api.opportunity_mapping import display_text as _display_text
from api.opportunity_mapping import fallback_summary as _fallback_summary
from api.opportunity_mapping import list_value as _list_value
from api.opportunity_mapping import opportunity_type as _opportunity_type
from api.opportunity_mapping import public_raw as _public_raw
from api.opportunity_page import render_opportunity_page
from api.public_info_page import render_public_info_page
from api.public_meta import OG_IMAGE_PNG, OG_IMAGE_SVG
from api.qpost_feed import QPOST_TEMPLATES, build_qpost_draft_feed
from api.runtime_config import admin_token as _admin_token
from api.runtime_config import allowed_hosts as _allowed_hosts
from api.runtime_config import bearer_token as _bearer_token
from api.runtime_config import database_url as _database_url
from api.runtime_config import public_base_url as _public_base_url
from api.source_onboarding import source_onboarding_contract
from api.status_page import render_status_page
from core.content_safety import is_publication_blocked
from core.geofit import (
    is_excluded_for_kazakhstan_focus,
    is_relevant_for_kazakhstan_focus,
)
from core.localization import (
    _localized_value,
    localize_opportunity,
    normalize_content_lang,
)
from core.models import Digest, Opportunity, OpportunityDetail
from core.persistence import Repository
from core.pipeline import run_all
from core.provenance import provenance_profile
from core.public_clock import public_today
from core.public_contract import (
    DATASET_SCHEMA_VERSION,
    SCHEMA_VERSION,
    OpportunityV1,
    dataset_revision,
    to_opportunity_v1,
)
from core.qazcompute_bridge import (
    duplicate_cluster_envelope,
    opportunity_deadline_anomaly,
    opportunity_evidence_readiness,
    source_freshness_envelope,
)
from core.repository_factory import make_repository
from core.scoring import PUBLIC_RELEVANCE_THRESHOLD, priority_score, ranking_payload
from core.scoring import score as score_opportunity
from core.semantic_search import clear_semantic_search_client_cache
from core.semantic_search import search_opportunities as _search_semantic_opportunities
from sources import PARSERS
from sources.kazakhstan_domestic import (
    ACTIVE_DOMESTIC_URLS,
    DOMESTIC_PROGRAM_BY_URL,
    DOMESTIC_PROGRAM_TAGS,
)
from sources.kazakhstan_watch import (
    ACTIVE_WATCH_URLS,
    WATCH_PAGE_BY_URL,
    WATCH_PAGE_TAGS,
)
from sources.unesco_iite import UNESCO_IITE_ANNOUNCEMENTS_URL

try:
    from datetime import UTC
except ImportError:  # pragma: no cover - Python < 3.11 compatibility
    UTC = timezone.utc

log = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    _warm_public_sitemap_cache()
    _warm_public_items_cache()
    refresh_task = asyncio.create_task(_periodic_public_cache_refresh())
    try:
        yield
    finally:
        refresh_task.cancel()
        with suppress(asyncio.CancelledError):
            await refresh_task


app = FastAPI(
    title="QAZ.FUND",
    description=(
        "Open support-program navigator for Kazakhstan: public opportunities, "
        "source links, data status, and reproducible working routes"
    ),
    version="0.2.0",
    root_path=os.environ.get("ROOT_PATH", ""),
    lifespan=_lifespan,
    docs_url=None,
    redoc_url=None,
)
_OPPORTUNITY_LIST_ADAPTER = TypeAdapter(list[Opportunity])


@app.exception_handler(StarletteHTTPException)
async def public_http_exception_page(
    request: Request,
    exc: StarletteHTTPException,
) -> Response:
    """Keep API errors structured while giving browser 404s a useful exit."""

    accepts_html = "text/html" in request.headers.get("accept", "").lower()
    machine_route = is_machine_route(request.url.path)
    if (
        exc.status_code != status.HTTP_404_NOT_FOUND
        or not accepts_html
        or machine_route
    ):
        return await http_exception_handler(request, exc)
    active_lang = _public_lang(str(request.query_params.get("lang") or ""))
    response = HTMLResponse(
        render_not_found_page(
            lang=active_lang,
            root_path=_root_path(request),
        ),
        status_code=exc.status_code,
        headers=exc.headers,
    )
    response.headers["X-Robots-Tag"] = "noindex, follow"
    return response


@app.exception_handler(RequestValidationError)
async def public_validation_error_page(
    request: Request,
    exc: RequestValidationError,
) -> Response:
    """Turn malformed human permalinks into a navigable recovery page."""

    accepts_html = "text/html" in request.headers.get("accept", "").lower()
    human_permalink = request.url.path.startswith(("/opportunity/", "/funder/"))
    if not accepts_html or not human_permalink:
        return await request_validation_exception_handler(request, exc)
    active_lang = _public_lang(str(request.query_params.get("lang") or ""))
    response = HTMLResponse(
        render_not_found_page(
            lang=active_lang,
            root_path=_root_path(request),
        ),
        status_code=status.HTTP_404_NOT_FOUND,
    )
    response.headers["X-Robots-Tag"] = "noindex, follow"
    return response


# in-memory cache на M0
_cache: list[Opportunity] = []
_SITEMAP_CACHE_TTL = timedelta(minutes=30)
_sitemap_cache_lock = threading.Lock()
_sitemap_cache: dict[tuple[str, str], tuple[datetime, str]] = {}
_PUBLIC_ITEMS_CACHE_TTL = timedelta(
    seconds=max(30, int(os.environ.get("PUBLIC_ITEMS_CACHE_TTL_SECONDS", "300")))
)
_PUBLIC_QUERY_CACHE_TTL = timedelta(
    seconds=max(10, int(os.environ.get("PUBLIC_QUERY_CACHE_TTL_SECONDS", "45")))
)
_INSIGHTS_CACHE_TTL = timedelta(
    seconds=max(15, int(os.environ.get("INSIGHTS_CACHE_TTL_SECONDS", "60")))
)
_NDJSON_CACHE_MAX_ENTRIES = 8
_public_items_cache_lock = threading.Lock()
_public_items_cache: dict[str, tuple[datetime, list[Opportunity]]] = {}
_public_scope_cache: dict[tuple[str, bool], tuple[datetime, list[Opportunity]]] = {}
_public_query_cache: dict[
    tuple[object, ...], tuple[datetime, tuple[tuple[Opportunity, ...], int]]
] = {}
_public_prepared_cache: dict[tuple[str, bool], tuple[datetime, list[Opportunity]]] = {}
_public_current_catalog_cache: dict[str, tuple[datetime, list[Opportunity]]] = {}
_public_v1_cache: dict[
    tuple[str, bool, str], tuple[datetime, dict[UUID, OpportunityV1]]
] = {}
_funder_index_cache: dict[str, tuple[datetime, dict[str, dict[str, Any]]]] = {}
_insights_cache: dict[tuple[str, str], tuple[datetime, dict[str, Any]]] = {}
_ndjson_body_cache: dict[
    tuple[str, str, tuple[tuple[str, str], ...]],
    tuple[datetime, str, datetime | date | None],
] = {}
_coverage_cache: tuple[datetime, dict[str, Any]] | None = None
LEGACY_FUNDER_REDIRECTS: dict[str, str] = {
    "dod-amraa": "DOD-AMRAA",
}
_DASHBOARD_RAW_FIELDS = frozenset(
    {
        "agency",
        "agencyCode",
        "application_url",
        "country",
        "deadline_policy",
        "decision_readiness",
        "funder_slug",
        "lifecycle",
        "notice_type",
        "opportunity_status",
        "provenance",
        "project_status",
        "projectstatusdisplay",
        "qazcompute_evidence_readiness",
        "qazcompute_deadline_anomaly",
        "ranking",
        "region",
        "status",
        "status_raw",
    }
)

_FAVICON_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#0f172a"/>
  <path d="M18 38 29 17h7L25 38h13l-3 6H15l3-6Z" fill="#f8fafc"/>
  <path d="M39 17h7L36 47h-7l10-30Z" fill="#22c55e"/>
</svg>
"""


@app.middleware("http")
async def add_security_headers(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    response = await call_next(request)
    return apply_public_headers(request, response)


app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts())
app.add_middleware(GZipMiddleware, minimum_size=1_000, compresslevel=5)


async def require_admin_token(
    authorization: str | None = Header(default=None),
    x_grant_radar_admin_token: str | None = Header(default=None),
) -> None:
    expected = _admin_token()
    if not expected:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    provided = (x_grant_radar_admin_token or "").strip() or _bearer_token(authorization)
    if not provided or not compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@lru_cache(maxsize=8)
def _repository_for_url(url: str) -> Repository:
    return make_repository(url)


def _configured_repository() -> Repository | None:
    url = _database_url()
    if url in ("", "memory", ":memory:"):
        return None
    return _repository_for_url(url)


def _stored_opportunity(row: Any, *, content_lang: str = "en") -> Opportunity:
    raw = getattr(row, "raw", None)
    if not isinstance(raw, dict):
        raw = {}
    else:
        raw = dict(raw)

    dedup_key = str(getattr(row, "dedup_key", None) or getattr(row, "id", ""))
    source_url: Any = str(getattr(row, "source_url", None) or raw.get("url") or "")
    first_seen_at = getattr(row, "first_seen_at", None)
    last_seen_at = getattr(row, "last_seen_at", None)
    discovered_at = (
        first_seen_at
        if isinstance(first_seen_at, datetime)
        else getattr(row, "discovered_at", None)
    )
    if not isinstance(discovered_at, datetime):
        discovered_at = datetime.now(UTC)
    if isinstance(last_seen_at, datetime) and not raw.get("source_checked_at"):
        raw["source_checked_at"] = last_seen_at.isoformat()
    existing_id = getattr(row, "id", None)
    stable_id = existing_id if isinstance(existing_id, UUID) else None

    opportunity = Opportunity(
        id=stable_id or uuid5(NAMESPACE_URL, dedup_key or source_url),
        source=str(getattr(row, "source", None) or raw.get("source") or "unknown"),
        source_url=source_url,
        type=getattr(row, "type", None) or _opportunity_type(raw),
        title=_display_text(getattr(row, "title", None) or raw.get("title")),
        summary=_display_summary(
            getattr(row, "summary", None)
            or raw.get("summary")
            or raw.get("description")
            or _fallback_summary(raw, content_lang=content_lang)
        ),
        funder=_display_text(getattr(row, "funder", None) or raw.get("funder")) or None,
        funder_slug=getattr(row, "funder_slug", None),
        amount_min=getattr(row, "amount_min", None) or raw.get("amount_min"),
        amount_max=getattr(row, "amount_max", None) or raw.get("amount_max"),
        currency=str(getattr(row, "currency", None) or raw.get("currency") or "USD"),
        deadline=getattr(row, "deadline", None) or raw.get("deadline"),
        eligibility=_list_value(
            getattr(row, "eligibility", None) or raw.get("eligibility")
        ),
        tags=_list_value(getattr(row, "tags", None) or raw.get("tags")),
        languages=_list_value(getattr(row, "languages", None) or raw.get("languages")),
        score=float(getattr(row, "score", None) or raw.get("score") or 0.0),
        opportunity_status=(
            getattr(row, "opportunity_status", None) or raw.get("opportunity_status")
        ),
        lifecycle=getattr(row, "lifecycle", None) or raw.get("lifecycle"),
        discovered_at=discovered_at,
        raw=_public_raw(raw),
    )
    if opportunity.source == "kazakhstan_watch":
        page = WATCH_PAGE_BY_URL.get(str(opportunity.source_url))
        if page is not None:
            opportunity.type = page.type
            opportunity.title = page.title
            opportunity.summary = page.summary
            opportunity.tags = list(WATCH_PAGE_TAGS.get(page.url, opportunity.tags))
            if page.rolling:
                opportunity.raw = {
                    **opportunity.raw,
                    "deadline_policy": "rolling",
                }
    if opportunity.source == "kazakhstan_domestic_support":
        program = DOMESTIC_PROGRAM_BY_URL.get(str(opportunity.source_url))
        if program is not None:
            opportunity.type = program.type
            opportunity.title = program.title
            opportunity.summary = program.summary
            opportunity.tags = list(
                DOMESTIC_PROGRAM_TAGS.get(program.url, opportunity.tags)
            )
            opportunity.amount_min = opportunity.amount_min or program.amount_min
            opportunity.amount_max = opportunity.amount_max or program.amount_max
            opportunity.deadline = opportunity.deadline or program.deadline
            opportunity.opportunity_status = (
                opportunity.opportunity_status or program.opportunity_status
            )
            opportunity.lifecycle = opportunity.lifecycle or program.lifecycle
            if program.amount_min is not None or program.amount_max is not None:
                opportunity.currency = program.currency
            if program.rolling:
                domestic_raw = {
                    **opportunity.raw,
                    "deadline_policy": "rolling",
                }
                if program.amount_raw:
                    domestic_raw["amount_raw"] = program.amount_raw
                if program.amount_min is not None:
                    domestic_raw["amount_min"] = str(program.amount_min)
                if program.amount_max is not None:
                    domestic_raw["amount_max"] = str(program.amount_max)
                if program.amount_min is not None or program.amount_max is not None:
                    domestic_raw["currency"] = program.currency
                opportunity.raw = {
                    key: value
                    for key, value in domestic_raw.items()
                    if value not in (None, "")
                }
    opportunity.funder_slug = opportunity.funder_slug or _slugify_funder(
        _funder_name(opportunity)
    )
    # Lifecycle is date-sensitive. Keep source-provided state and derive the
    # public lifecycle at query time using the Kazakhstan business date.
    # Recompute with the current deterministic model so persisted scores from an
    # older release cannot silently survive a methodology change.
    opportunity.score = score_opportunity(opportunity)
    return opportunity


def _public_dedup_key(item: Opportunity) -> str:
    raw = item.raw if isinstance(item.raw, dict) else {}
    source_url = str(item.source_url).rstrip("/").lower()
    if item.source == "undp_procurement" and "nego_id=" in source_url:
        # UNDP may revise the reference number without changing the notice URL.
        return f"{item.source}:url:{source_url}"
    external_id = str(
        raw.get("external_id")
        or raw.get("reference")
        or (raw.get("number") if item.source == "grants_gov" else "")
        or ""
    ).strip()
    if external_id:
        return f"{item.source}:{external_id.lower()}"
    return f"{item.source}:{source_url}"


def _public_dedup_rank(
    item: Opportunity, *, content_lang: str
) -> tuple[float, int, int, float]:
    raw = item.raw if isinstance(item.raw, dict) else {}
    localized_title = _display_text(_localized_value(raw, content_lang, "title"))
    has_matching_localized_title = int(
        bool(localized_title) and localized_title == item.title
    )
    summary_length = len(str(item.summary or "").strip())
    discovered_at = item.discovered_at
    discovered_ts = (
        discovered_at.timestamp() if isinstance(discovered_at, datetime) else 0.0
    )
    return (
        float(item.score or 0.0),
        has_matching_localized_title,
        summary_length,
        discovered_ts,
    )


def _dedupe_public_items(
    items: list[Opportunity], *, content_lang: str
) -> list[Opportunity]:
    best_by_key: dict[str, Opportunity] = {}
    for item in items:
        key = _public_dedup_key(item)
        current = best_by_key.get(key)
        if current is None or _public_dedup_rank(
            item, content_lang=content_lang
        ) > _public_dedup_rank(current, content_lang=content_lang):
            best_by_key[key] = item
    return list(best_by_key.values())


def _public_scope_items(
    items: list[Opportunity], *, include_irrelevant: bool
) -> list[Opportunity]:
    if include_irrelevant:
        return [item for item in items if not is_excluded_for_kazakhstan_focus(item)]
    return [item for item in items if is_relevant_for_kazakhstan_focus(item)]


def _stored_items(content_lang: str = "en") -> list[Opportunity]:
    repository = _configured_repository()
    if repository is None:
        return _dedupe_public_items(
            [
                item
                for item in (
                    _stored_opportunity(row, content_lang=content_lang)
                    for row in _cache
                )
                if _is_active_item(item) and not is_publication_blocked(item)
            ],
            content_lang=content_lang,
        )
    return _dedupe_public_items(
        [
            item
            for item in (
                _stored_opportunity(row, content_lang=content_lang)
                for row in repository.all()
            )
            if _is_active_item(item) and not is_publication_blocked(item)
        ],
        content_lang=content_lang,
    )


def _cached_public_items(content_lang: str = "en") -> list[Opportunity]:
    """Return the last complete public read model without request-time expiry.

    A periodic refresh swaps this snapshot atomically. Serving the last complete
    snapshot prevents both Uvicorn workers from rebuilding the full database
    projection on a visitor request when the former TTL expires.
    """
    normalized_lang = _public_lang(content_lang)
    with _public_items_cache_lock:
        cached = _public_items_cache.get(normalized_lang)
        if cached is not None:
            return list(cached[1])

    items = _stored_items(content_lang=normalized_lang)
    with _public_items_cache_lock:
        _public_items_cache[normalized_lang] = (datetime.now(UTC), items)
    return list(items)


def _refresh_public_items_cache() -> None:
    """Build fresh language snapshots off-lock, then replace them atomically."""

    global _coverage_cache
    snapshots = {lang: _stored_items(content_lang=lang) for lang in ("en", "ru", "kk")}
    refreshed_at = datetime.now(UTC)
    with _public_items_cache_lock:
        _public_items_cache.clear()
        _public_items_cache.update(
            {lang: (refreshed_at, items) for lang, items in snapshots.items()}
        )
        _public_scope_cache.clear()
        _public_query_cache.clear()
        _public_prepared_cache.clear()
        _public_current_catalog_cache.clear()
        _public_v1_cache.clear()
        _funder_index_cache.clear()
        _insights_cache.clear()
        _ndjson_body_cache.clear()
        _coverage_cache = None
    clear_semantic_search_client_cache()
    _clear_sitemap_cache()
    _warm_public_items_cache()
    _warm_public_sitemap_cache()


async def _periodic_public_cache_refresh() -> None:
    """Refresh public snapshots away from latency-sensitive request handlers."""

    interval = _PUBLIC_ITEMS_CACHE_TTL.total_seconds()
    while True:
        await asyncio.sleep(interval)
        try:
            await asyncio.to_thread(_refresh_public_items_cache)
        except Exception:  # noqa: BLE001
            log.exception("public cache background refresh failed")


def _cached_public_scope_items(
    content_lang: str = "en", *, include_irrelevant: bool = False
) -> list[Opportunity]:
    """Cache the expensive Kazakhstan/Central Asia applicability pass."""
    normalized_lang = _public_lang(content_lang)
    cache_key = (normalized_lang, include_irrelevant)
    now = datetime.now(UTC)
    with _public_items_cache_lock:
        cached = _public_scope_cache.get(cache_key)
        if cached is not None and now - cached[0] < _PUBLIC_ITEMS_CACHE_TTL:
            return list(cached[1])

    scoped_items = _public_scope_items(
        _cached_public_items(normalized_lang),
        include_irrelevant=include_irrelevant,
    )
    with _public_items_cache_lock:
        _public_scope_cache[cache_key] = (now, scoped_items)
    return list(scoped_items)


def _clear_public_items_cache() -> None:
    global _coverage_cache
    with _public_items_cache_lock:
        _public_items_cache.clear()
        _public_scope_cache.clear()
        _public_query_cache.clear()
        _public_prepared_cache.clear()
        _public_current_catalog_cache.clear()
        _public_v1_cache.clear()
        _funder_index_cache.clear()
        _insights_cache.clear()
        _ndjson_body_cache.clear()
        _coverage_cache = None
    clear_semantic_search_client_cache()


def _ndjson_cache_key(
    request: Request,
) -> tuple[str, str, tuple[tuple[str, str], ...]]:
    public_origin = _public_base_url() or str(request.base_url).rstrip("/")
    return (
        public_origin,
        request.url.path,
        tuple(sorted(request.query_params.multi_items())),
    )


def _cached_ndjson_export(
    request: Request,
    *,
    filename: str,
    prefix: str,
) -> Response | None:
    cache_key = _ndjson_cache_key(request)
    now = datetime.now(UTC)
    with _public_items_cache_lock:
        cached = _ndjson_body_cache.get(cache_key)
        if cached is None:
            return None
        if now - cached[0] >= _PUBLIC_ITEMS_CACHE_TTL:
            _ndjson_body_cache.pop(cache_key, None)
            return None
        _, body, last_modified = cached
    return cached_body_response(
        request,
        body=body,
        media_type="application/x-ndjson; charset=utf-8",
        last_modified=last_modified,
        prefix=prefix,
        filename=filename,
    )


def _store_ndjson_export(
    request: Request,
    *,
    rows: Iterable[Mapping[str, Any]],
    filename: str,
    prefix: str,
    last_modified: datetime | date | None,
) -> Response:
    body = "".join(
        json.dumps(
            dict(row),
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )
        + "\n"
        for row in rows
    )
    cache_key = _ndjson_cache_key(request)
    now = datetime.now(UTC)
    with _public_items_cache_lock:
        if (
            cache_key not in _ndjson_body_cache
            and len(_ndjson_body_cache) >= _NDJSON_CACHE_MAX_ENTRIES
        ):
            oldest_key = min(
                _ndjson_body_cache,
                key=lambda key: _ndjson_body_cache[key][0],
            )
            _ndjson_body_cache.pop(oldest_key, None)
        _ndjson_body_cache[cache_key] = (now, body, last_modified)
    return cached_body_response(
        request,
        body=body,
        media_type="application/x-ndjson; charset=utf-8",
        last_modified=last_modified,
        prefix=prefix,
        filename=filename,
    )


def _warm_public_items_cache() -> None:
    """Warm expensive public projections before the first visitor arrives."""
    public_base_url = _public_base_url()
    for content_lang in ("en", "ru", "kk"):
        with suppress(Exception):
            _cached_public_items(content_lang)
            _cached_public_scope_items(content_lang)
            _cached_prepared_scope_items(content_lang)
            _cached_current_catalog_items(content_lang)
            if public_base_url:
                _cached_public_v1_index(
                    content_lang=content_lang,
                    include_irrelevant=False,
                    public_base_url=public_base_url,
                )
    with suppress(Exception):
        _cached_coverage_payload()


def _compact_dashboard_item(item: Opportunity) -> Opportunity:
    """Strip large ingestion-only payloads from the dashboard collection response."""
    raw = item.raw if isinstance(item.raw, dict) else {}
    compact_raw = {
        key: value for key, value in raw.items() if key in _DASHBOARD_RAW_FIELDS
    }
    return item.model_copy(update={"raw": compact_raw})


def _with_decision_readiness(
    item: Opportunity,
    *,
    ranking_subject: Opportunity | None = None,
) -> Opportunity:
    """Expose which application facts are present without inventing missing data."""
    raw = item.raw if isinstance(item.raw, dict) else {}
    present = {
        "deadline": bool(item.deadline or raw.get("deadline_policy") == "rolling"),
        "amount": bool(
            item.amount_min is not None
            or item.amount_max is not None
            or raw.get("amount_raw")
        ),
        "eligibility": bool(item.eligibility or raw.get("eligibility")),
        "application": bool(item.source_url or raw.get("application_url")),
    }
    missing_fields = [name for name, available in present.items() if not available]
    readiness = {
        "status": "complete" if not missing_fields else "partial",
        "known_fields": sum(present.values()),
        "total_fields": len(present),
        "missing_fields": missing_fields,
    }
    lifecycle = _effective_public_lifecycle(item, today=public_today())
    return item.model_copy(
        update={
            "lifecycle": lifecycle,
            "raw": {
                **raw,
                "provenance": provenance_profile(item),
                "decision_readiness": readiness,
                "qazcompute_evidence_readiness": opportunity_evidence_readiness(item),
                "qazcompute_deadline_anomaly": opportunity_deadline_anomaly(item),
                "ranking": ranking_payload(ranking_subject or item),
            },
        }
    )


def _cached_prepared_scope_items(
    content_lang: str = "en", *, include_irrelevant: bool = False
) -> list[Opportunity]:
    """Cache localized ranking and evidence projections shared by public routes."""
    normalized_lang = _public_lang(content_lang)
    cache_key = (normalized_lang, include_irrelevant)
    now = datetime.now(UTC)
    with _public_items_cache_lock:
        cached = _public_prepared_cache.get(cache_key)
        if cached is not None and now - cached[0] < _PUBLIC_ITEMS_CACHE_TTL:
            return list(cached[1])

    today = public_today()
    prepared = [
        _with_decision_readiness(
            localize_opportunity(item, normalized_lang),
            ranking_subject=item,
        )
        for item in _cached_public_scope_items(
            content_lang=normalized_lang,
            include_irrelevant=include_irrelevant,
        )
    ]
    prepared.sort(
        key=lambda item: (
            priority_score(item, today=today),
            item.score,
            item.discovered_at,
        ),
        reverse=True,
    )
    with _public_items_cache_lock:
        _public_prepared_cache[cache_key] = (now, prepared)
    return list(prepared)


def _cached_current_catalog_items(content_lang: str = "en") -> list[Opportunity]:
    """Return the exact current public catalog used by the dashboard and insights."""
    normalized_lang = _public_lang(content_lang)
    now = datetime.now(UTC)
    with _public_items_cache_lock:
        cached = _public_current_catalog_cache.get(normalized_lang)
        if cached is not None and now - cached[0] < _PUBLIC_ITEMS_CACHE_TTL:
            return list(cached[1])

    today = public_today()
    current_items = [
        item
        for item in _cached_prepared_scope_items(normalized_lang)
        if _is_open(item, today) and item.score >= PUBLIC_RELEVANCE_THRESHOLD
    ]
    with _public_items_cache_lock:
        _public_current_catalog_cache[normalized_lang] = (now, current_items)
    return list(current_items)


def _find_opportunity(
    opportunity_id: UUID,
    content_lang: str = "en",
) -> Opportunity | None:
    requested_lang = _public_lang(content_lang)
    for candidate_lang in dict.fromkeys((requested_lang, "en", "ru")):
        match = next(
            (
                item
                for item in _cached_public_items(content_lang=candidate_lang)
                if item.id == opportunity_id
            ),
            None,
        )
        if match is not None:
            return match
    return None


def _is_active_item(item: Opportunity) -> bool:
    if item.source == "kazakhstan_watch":
        return str(item.source_url) in ACTIVE_WATCH_URLS
    if item.source == "kazakhstan_domestic_support":
        return str(item.source_url) in ACTIVE_DOMESTIC_URLS
    if item.source == "unesco_iite":
        return str(item.source_url).rstrip("/") != UNESCO_IITE_ANNOUNCEMENTS_URL.rstrip(
            "/"
        )
    return True


def _is_open(item: Opportunity, today: date) -> bool:
    return _effective_public_lifecycle(item, today=today) not in {
        "closed",
        "awarded",
    }


def _effective_public_lifecycle(item: Opportunity, *, today: date) -> str:
    """Resolve date-sensitive lifecycle without treating 'closing' as 'closed'."""

    raw = item.raw if isinstance(item.raw, dict) else {}
    explicit_state = " ".join(
        str(value or "").strip().lower()
        for value in (
            item.opportunity_status,
            item.lifecycle,
            raw.get("status"),
            raw.get("opportunity_status"),
            raw.get("lifecycle"),
        )
        if str(value or "").strip()
    )
    if any(token in explicit_state for token in ("closed", "awarded", "archived")):
        return "awarded" if "awarded" in explicit_state else "closed"
    if item.deadline is not None:
        if item.deadline < today:
            return "closed"
        if (item.deadline - today).days <= 14:
            return "closing_soon"
        return "open"
    return public_lifecycle(item, today=today)


def _funder_index(content_lang: str = "en") -> dict[str, dict[str, Any]]:
    normalized_lang = _public_lang(content_lang)
    now = datetime.now(UTC)
    with _public_items_cache_lock:
        cached = _funder_index_cache.get(normalized_lang)
        if cached is not None and now - cached[0] < _PUBLIC_ITEMS_CACHE_TTL:
            return cached[1]

    groups = _build_funder_index(
        _cached_prepared_scope_items(
            content_lang=normalized_lang,
            include_irrelevant=False,
        )
    )
    with _public_items_cache_lock:
        _funder_index_cache[normalized_lang] = (now, groups)
    return groups


def _related_opportunities(
    target: Opportunity,
    *,
    lang: str,
    limit: int = 3,
) -> list[tuple[Opportunity, str]]:
    today = public_today()
    rows: list[tuple[float, Opportunity]] = []
    for candidate in _cached_public_items(content_lang=lang):
        if candidate.id == target.id or not _is_open(candidate, today):
            continue
        related_score = _related_relevance(target, candidate)
        if related_score < 0.20:
            continue
        rows.append((related_score, candidate))
    rows.sort(
        key=lambda row: (row[0], row[1].score, row[1].discovered_at),
        reverse=True,
    )

    diversified_candidates = diversify_ranked_items(
        [candidate for _, candidate in rows],
        key=lambda item: item.source,
        max_per_key=1,
        limit=limit,
    )
    if len(diversified_candidates) < limit:
        selected_ids = {item.id for item in diversified_candidates}
        diversified_candidates.extend(
            candidate for _, candidate in rows if candidate.id not in selected_ids
        )

    related: list[tuple[Opportunity, str]] = []
    seen: set[UUID] = set()
    for candidate in diversified_candidates:
        if candidate.id in seen:
            continue
        seen.add(candidate.id)
        related.append(
            (
                localize_opportunity(candidate, lang),
                _related_reason_key(target, candidate),
            )
        )
        if len(related) >= limit:
            break
    return related


def _source_coverage(
    items: list[Opportunity],
    source_checks: Mapping[str, datetime] | None = None,
) -> list[dict[str, Any]]:
    today = public_today()
    source_checks = source_checks or {}
    by_source: dict[str, list[Opportunity]] = {}
    for item in items:
        by_source.setdefault(item.source, []).append(item)

    rows: list[dict[str, Any]] = []
    for slug, source_cls in PARSERS.items():
        source_items = by_source.pop(slug, [])
        open_items = [item for item in source_items if _is_open(item, today)]
        relevant_open_items = [
            item
            for item in open_items
            if is_relevant_for_kazakhstan_focus(item)
            and item.score >= PUBLIC_RELEVANCE_THRESHOLD
        ]
        last_seen = max(
            (item.discovered_at for item in source_items),
            default=None,
        )
        last_checked = source_checks.get(slug)
        freshness_at = _newest_timestamp(last_seen, last_checked)
        freshness = _source_freshness(
            freshness_at,
            source_id=slug,
        )
        normalized_last_seen = _normalized_utc(last_seen)
        normalized_last_checked = _normalized_utc(last_checked)
        uses_source_check = normalized_last_checked is not None and (
            normalized_last_seen is None
            or normalized_last_checked >= normalized_last_seen
        )
        rows.append(
            {
                "slug": slug,
                "name": source_cls.name,
                "base_url": source_cls.base_url,
                "tags": list(source_cls.default_tags),
                "enabled": True,
                "items": len(source_items),
                "open_items": len(open_items),
                "relevant_open_items": len(relevant_open_items),
                "last_discovered_at": last_seen.isoformat() if last_seen else None,
                "last_checked_at": (last_checked.isoformat() if last_checked else None),
                "freshness_basis": (
                    "source_check"
                    if uses_source_check
                    else "discovered_record" if last_seen is not None else "unknown"
                ),
                **freshness,
            }
        )

    for slug, source_items in sorted(by_source.items()):
        open_items = [item for item in source_items if _is_open(item, today)]
        relevant_open_items = [
            item
            for item in open_items
            if is_relevant_for_kazakhstan_focus(item)
            and item.score >= PUBLIC_RELEVANCE_THRESHOLD
        ]
        last_seen = max((item.discovered_at for item in source_items), default=None)
        freshness = _source_freshness(
            last_seen,
            source_id=slug,
        )
        rows.append(
            {
                "slug": slug,
                "name": slug.replace("_", " ").title(),
                "base_url": "",
                "tags": [],
                "enabled": False,
                "items": len(source_items),
                "open_items": len(open_items),
                "relevant_open_items": len(relevant_open_items),
                "last_discovered_at": last_seen.isoformat() if last_seen else None,
                "last_checked_at": None,
                "freshness_basis": "discovered_record" if last_seen else "unknown",
                **freshness,
            }
        )

    return rows


def _normalized_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _newest_timestamp(
    left: datetime | None,
    right: datetime | None,
) -> datetime | None:
    values = [value for value in map(_normalized_utc, (left, right)) if value]
    return max(values, default=None)


def _source_freshness(
    last_seen: datetime | None,
    *,
    source_id: str = "source",
    item_count_24h: int | None = None,
) -> dict[str, Any]:
    """Return stable public freshness signals without exposing run errors."""
    normalized = _normalized_utc(last_seen)
    envelope = source_freshness_envelope(
        source_id=source_id,
        last_success_at=normalized,
        expected_interval_hours=72.0,
        item_count_24h=item_count_24h,
    )
    features = envelope.get("features") if isinstance(envelope, dict) else {}
    age_hours = features.get("age_hours") if isinstance(features, dict) else None
    tier = str(envelope.get("tier") or "unknown")
    return {
        "freshness_status": (
            "stale"
            if tier == "stale" or (age_hours is not None and float(age_hours) > 72)
            else (
                "fresh"
                if tier == "fresh"
                else "unknown" if tier == "unknown" else "watch"
            )
        ),
        "age_hours": round(float(age_hours), 1) if age_hours is not None else None,
        "qazcompute_source_freshness": envelope,
    }


def _latest_successful_source_checks() -> dict[str, datetime]:
    """Return latest successful parser checks without exposing run errors."""

    repository = _configured_repository()
    engine = getattr(repository, "engine", None)
    if engine is None:
        return {}
    try:
        from sqlalchemy import MetaData, Table, func, select

        runs = Table("runs", MetaData(), autoload_with=engine)
        statement = (
            select(runs.c.source, func.max(runs.c.finished_at).label("checked_at"))
            .where(runs.c.status == "ok", runs.c.source.in_(tuple(PARSERS)))
            .group_by(runs.c.source)
        )
        with engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
    except Exception:
        return {}
    return {
        str(row["source"]): row["checked_at"]
        for row in rows
        if isinstance(row.get("checked_at"), datetime)
    }


def _cached_coverage_payload() -> dict[str, Any]:
    """Reuse source aggregation while the public item cache is fresh."""
    global _coverage_cache
    now = datetime.now(UTC)
    with _public_items_cache_lock:
        cached = _coverage_cache
        if cached is not None and now - cached[0] < _PUBLIC_ITEMS_CACHE_TTL:
            return dict(cached[1])

    public_items = _cached_public_items()
    source_rows = _source_coverage(public_items, _latest_successful_source_checks())
    payload = {
        "status": "ok",
        "items": len(public_items),
        "sources": source_rows,
        "evidence_states": count_evidence_states(
            resolve_public_evidence_state(direct_source_url=item.source_url)
            for item in public_items
        ),
        "enabled_sources": sum(1 for row in source_rows if row["enabled"]),
        "relevant_open_items": sum(row["relevant_open_items"] for row in source_rows),
        "fresh_sources": sum(
            1
            for row in source_rows
            if row.get("enabled") and row.get("freshness_status") == "fresh"
        ),
        "stale_sources": sum(
            1
            for row in source_rows
            if row.get("enabled") and row.get("freshness_status") == "stale"
        ),
        "unknown_freshness_sources": sum(
            1
            for row in source_rows
            if row.get("enabled") and row.get("freshness_status") == "unknown"
        ),
    }
    with _public_items_cache_lock:
        _coverage_cache = (now, payload)
    return dict(payload)


def _operator_run_rows(limit: int = 50) -> list[dict[str, Any]]:
    """Read recent run metadata for the protected operator surface."""
    repository = _configured_repository()
    engine = getattr(repository, "engine", None)
    if engine is None:
        return []
    try:
        from sqlalchemy import MetaData, Table, select

        runs = Table("runs", MetaData(), autoload_with=engine)
        statement = select(runs).order_by(runs.c.started_at.desc()).limit(limit)
        with engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
    except Exception:
        return []
    result: list[dict[str, Any]] = []
    for row in rows:
        error_text = str(row.get("error") or "").strip()
        result.append(
            {
                "id": row.get("id"),
                "source": row.get("source"),
                "status": row.get("status"),
                "started_at": (
                    row["started_at"].isoformat() if row.get("started_at") else None
                ),
                "finished_at": (
                    row["finished_at"].isoformat() if row.get("finished_at") else None
                ),
                "items_seen": int(row.get("items_seen") or 0),
                "items_new": int(row.get("items_new") or 0),
                "items_dup": int(row.get("items_dup") or 0),
                "error": error_text.splitlines()[0][:240] if error_text else "",
            }
        )
    return result


def _root_path(request: Request) -> str:
    return str(request.scope.get("root_path") or "").rstrip("/")


def _site_origin(request: Request, root_path: str) -> str:
    site_origin = _public_base_url() or str(request.base_url).rstrip("/")
    if not _public_base_url() and root_path and site_origin.endswith(root_path):
        site_origin = site_origin[: -len(root_path)].rstrip("/")
    return site_origin


def _public_root_base(request: Request, root_path: str) -> str:
    site_origin = _site_origin(request, root_path).rstrip("/")
    if not root_path:
        return site_origin
    root = root_path.rstrip("/")
    if site_origin.endswith(root):
        return site_origin
    return f"{site_origin}{root_path}"


def _public_url(request: Request, root_path: str, path: str) -> str:
    if path.startswith(("http://", "https://")):
        return path
    base = _public_root_base(request, root_path).rstrip("/")
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base}{path}" if base else path


def _public_url_from_base(base: str, path: str) -> str:
    if path.startswith(("http://", "https://")):
        return path
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base.rstrip('/')}{path}" if base else path


def _public_lang(value: str | None, default: str = "ru") -> str:
    return normalize_content_lang(value if value is not None else default)


def _lastmod_for(item_discovered_at: Any) -> str | None:
    if isinstance(item_discovered_at, datetime):
        return item_discovered_at.date().isoformat()
    if isinstance(item_discovered_at, date):
        return item_discovered_at.isoformat()
    return None


def _sitemap_entry(
    url: str,
    *,
    lastmod: str | None = None,
    changefreq: str = "weekly",
    priority: str = "0.6",
    alternates: dict[str, str] | None = None,
) -> str:
    safe_url = escape(url, quote=True)
    chunks = ["  <url>", f"    <loc>{safe_url}</loc>"]
    for hreflang, alternate_url in (alternates or {}).items():
        chunks.append(
            '    <xhtml:link rel="alternate" hreflang="{hreflang}" href="{href}" />'.format(
                hreflang=escape(hreflang, quote=True),
                href=escape(alternate_url, quote=True),
            )
        )
    if lastmod:
        chunks.append(f"    <lastmod>{escape(lastmod, quote=True)}</lastmod>")
    chunks.append(f"    <changefreq>{escape(changefreq, quote=True)}</changefreq>")
    chunks.append(f"    <priority>{escape(priority, quote=True)}</priority>")
    chunks.append("  </url>")
    return "\n".join(chunks)


def _clear_sitemap_cache() -> None:
    with _sitemap_cache_lock:
        _sitemap_cache.clear()


def _render_sitemap_xml(base_url: str) -> str:
    root_kk = _public_url_from_base(base_url, "/?lang=kk")
    root_ru = _public_url_from_base(base_url, "/?lang=ru")
    root_en = _public_url_from_base(base_url, "/?lang=en")
    opportunities = sorted(
        [
            item
            for item in _cached_public_scope_items(content_lang="en")
            if _is_open(item, public_today())
        ],
        key=lambda item: (item.discovered_at, item.score, str(item.title).lower()),
        reverse=True,
    )
    funders = _build_funder_index(opportunities)

    rows: list[str] = [
        _sitemap_entry(
            root_ru,
            changefreq="daily",
            priority="1.0",
            alternates={
                "kk": root_kk,
                "ru": root_ru,
                "en": root_en,
                "x-default": root_ru,
            },
        ),
    ]
    for path, priority in (
        ("/media?lang=ru", "0.85"),
        ("/insights?lang=ru", "0.8"),
        ("/terms?lang=ru", "0.4"),
        ("/data-policy?lang=ru", "0.4"),
        ("/attribution?lang=ru", "0.4"),
    ):
        ru_url = _public_url_from_base(base_url, path)
        kk_url = ru_url.replace("lang=ru", "lang=kk")
        en_url = ru_url.replace("lang=ru", "lang=en")
        rows.append(
            _sitemap_entry(
                ru_url,
                changefreq="monthly",
                priority=priority,
                alternates={
                    "kk": kk_url,
                    "ru": ru_url,
                    "en": en_url,
                    "x-default": ru_url,
                },
            )
        )

    insights_ru = _public_url_from_base(base_url, "/insights?lang=ru")
    insights_en = _public_url_from_base(base_url, "/insights?lang=en")
    rows.append(
        _sitemap_entry(
            insights_ru,
            changefreq="daily",
            priority="0.8",
            alternates={
                "ru": insights_ru,
                "en": insights_en,
                "x-default": insights_ru,
            },
        )
    )

    for page in ("status", "terms", "data-policy", "attribution"):
        ru_url = _public_url_from_base(base_url, f"/{page}?lang=ru")
        en_url = _public_url_from_base(base_url, f"/{page}?lang=en")
        rows.append(
            _sitemap_entry(
                ru_url,
                changefreq="monthly",
                priority="0.4",
                alternates={
                    "ru": ru_url,
                    "en": en_url,
                    "x-default": ru_url,
                },
            )
        )

    for item in opportunities[:500]:
        kk_url = _public_url_from_base(base_url, f"/opportunity/{item.id}?lang=kk")
        ru_url = _public_url_from_base(base_url, f"/opportunity/{item.id}?lang=ru")
        en_url = _public_url_from_base(base_url, f"/opportunity/{item.id}?lang=en")
        rows.append(
            _sitemap_entry(
                ru_url,
                lastmod=_lastmod_for(item.discovered_at),
                changefreq="weekly",
                priority="0.8",
                alternates={
                    "kk": kk_url,
                    "ru": ru_url,
                    "en": en_url,
                    "x-default": ru_url,
                },
            )
        )

    for slug in sorted(funders.keys())[:200]:
        kk_url = _public_url_from_base(base_url, f"/funder/{slug}?lang=kk")
        ru_url = _public_url_from_base(base_url, f"/funder/{slug}?lang=ru")
        en_url = _public_url_from_base(base_url, f"/funder/{slug}?lang=en")
        rows.append(
            _sitemap_entry(
                ru_url,
                changefreq="monthly",
                priority="0.5",
                alternates={
                    "kk": kk_url,
                    "ru": ru_url,
                    "en": en_url,
                    "x-default": ru_url,
                },
            )
        )

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += (
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    )
    xml += "\n".join(rows)
    xml += "\n</urlset>"
    return xml


def _cached_sitemap_xml(base_url: str) -> str:
    cache_key = ("sitemap.xml", base_url.rstrip("/"))
    now = datetime.now(UTC)
    with _sitemap_cache_lock:
        cached = _sitemap_cache.get(cache_key)
        if cached is not None:
            cached_at, xml = cached
            if now - cached_at < _SITEMAP_CACHE_TTL:
                return xml
    xml = _render_sitemap_xml(base_url)
    with _sitemap_cache_lock:
        _sitemap_cache[cache_key] = (now, xml)
    return xml


def _warm_public_sitemap_cache() -> None:
    public_base = _public_base_url()
    if not public_base:
        return
    # Warmup is an SEO latency optimization; API startup must not depend on it.
    with suppress(Exception):
        _cached_sitemap_xml(public_base)


@app.head("/", include_in_schema=False)
async def root_head() -> Response:
    return Response(status_code=200)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root(request: Request) -> HTMLResponse:
    root_path = _root_path(request)
    site_origin = _site_origin(request, root_path)
    repository = _configured_repository()
    items = repository.size() if repository is not None else len(_cache)
    relevant_items = len(_cached_current_catalog_items(content_lang="en"))
    source_count = len(PARSERS)
    lang = str(request.query_params.get("lang") or "").strip().lower()
    dashboard_lang = _public_lang(lang)
    return HTMLResponse(
        render_dashboard(
            root_path=root_path,
            items=items,
            relevant_items=relevant_items,
            source_count=source_count,
            lang=dashboard_lang,
            site_origin=site_origin,
        )
    )


@app.api_route(
    "/media",
    methods=["GET", "HEAD"],
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def public_media_page(request: Request) -> HTMLResponse:
    """Render the editorial-style public media surface."""

    root_path = _root_path(request)
    active_lang = _public_lang(str(request.query_params.get("lang") or "").strip())
    response = HTMLResponse(
        render_media_page(
            items=_cached_public_scope_items(content_lang=active_lang),
            lang=active_lang,
            root_path=root_path,
            site_origin=_site_origin(request, root_path),
        )
    )
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response


@app.api_route("/media.json", methods=["GET", "HEAD"], include_in_schema=False)
async def public_media_json(request: Request) -> JSONResponse:
    """Return the source-grounded media read model for people and AI systems."""

    root_path = _root_path(request)
    active_lang = _public_lang(str(request.query_params.get("lang") or "").strip())
    payload = build_media_snapshot(
        items=_cached_public_scope_items(content_lang=active_lang),
        lang=active_lang,
        root_path=root_path,
    )
    payload["links"] = {
        "human": _public_url(request, root_path, f"/media?lang={active_lang}"),
        "catalog": _public_url(
            request, root_path, f"/?lang={active_lang}#opportunities"
        ),
    }
    response = JSONResponse(payload)
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response


@app.api_route("/media/feed.json", methods=["GET", "HEAD"], include_in_schema=False)
async def public_media_feed(request: Request) -> Response:
    """Return a standard JSON Feed projection of public media records."""

    root_path = _root_path(request)
    active_lang = _public_lang(str(request.query_params.get("lang") or "").strip())
    human_url = _public_url(request, root_path, f"/media?lang={active_lang}")
    feed_url = _public_url(request, root_path, f"/media/feed.json?lang={active_lang}")
    snapshot = build_media_snapshot(
        items=_cached_public_scope_items(content_lang=active_lang),
        lang=active_lang,
        root_path=root_path,
    )
    feed_title, feed_description = media_feed_metadata(active_lang)
    payload = build_media_feed(
        snapshot=snapshot,
        lang=active_lang,
        human_url=human_url,
        feed_url=feed_url,
        public_root=_public_root_base(request, root_path),
        title=feed_title,
        description=feed_description,
    )
    response = JSONResponse(payload, media_type="application/feed+json")
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response


@app.api_route("/media/rss.xml", methods=["GET", "HEAD"], include_in_schema=False)
async def public_media_rss(request: Request) -> Response:
    """Return an RSS 2.0 projection for newsroom and digest integrations."""

    root_path = _root_path(request)
    active_lang = _public_lang(str(request.query_params.get("lang") or "").strip())
    human_url = _public_url(request, root_path, f"/media?lang={active_lang}")
    feed_url = _public_url(request, root_path, f"/media/rss.xml?lang={active_lang}")
    snapshot = build_media_snapshot(
        items=_cached_public_scope_items(content_lang=active_lang),
        lang=active_lang,
        root_path=root_path,
    )
    feed_title, feed_description = media_feed_metadata(active_lang)
    payload = build_media_rss(
        snapshot=snapshot,
        human_url=human_url,
        feed_url=feed_url,
        public_root=_public_root_base(request, root_path),
        title=feed_title,
        description=feed_description,
    )
    response = Response(payload, media_type="application/rss+xml")
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response


@app.api_route(
    "/insights",
    methods=["GET", "HEAD"],
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def public_insights_page(request: Request) -> HTMLResponse:
    """Render a public, source-grounded visual summary of the catalogue."""
    root_path = _root_path(request)
    active_lang = _public_lang(str(request.query_params.get("lang") or "").strip())
    response = HTMLResponse(
        render_insights_page(
            items=_cached_public_scope_items(content_lang=active_lang),
            coverage=_cached_coverage_payload(),
            lang=active_lang,
            root_path=root_path,
            site_origin=_site_origin(request, root_path),
        )
    )
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response


@app.api_route(
    "/embed/opportunities",
    methods=["GET", "HEAD"],
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def public_opportunities_embed(request: Request) -> HTMLResponse:
    """Render a compact, read-only opportunity list for trusted consumers."""
    active_lang = _public_lang(str(request.query_params.get("lang") or "").strip())
    response = HTMLResponse(
        render_opportunities_embed(
            items=_cached_public_scope_items(content_lang=active_lang),
            lang=active_lang,
            catalog_url=_public_url(
                request, _root_path(request), f"/?lang={active_lang}#opportunities"
            ),
        )
    )
    response.headers["Cache-Control"] = (
        "public, max-age=300, stale-while-revalidate=1800"
    )
    return response


@app.api_route(
    "/embed/coverage",
    methods=["GET", "HEAD"],
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def public_coverage_embed(request: Request) -> HTMLResponse:
    """Render compact source-freshness signals for trusted consumers."""
    active_lang = _public_lang(str(request.query_params.get("lang") or "").strip())
    response = HTMLResponse(
        render_coverage_embed(
            coverage=_cached_coverage_payload(),
            lang=active_lang,
            catalog_url=_public_url(
                request, _root_path(request), f"/status?lang={active_lang}"
            ),
        )
    )
    response.headers["Cache-Control"] = (
        "public, max-age=300, stale-while-revalidate=1800"
    )
    return response


@app.api_route("/insights.json", methods=["GET", "HEAD"], include_in_schema=False)
async def public_insights_json(request: Request) -> JSONResponse:
    """Return the same reproducible analytics read model used by ``/insights``."""

    root_path = _root_path(request)
    active_lang = _public_lang(str(request.query_params.get("lang") or "").strip())
    payload = build_insights_snapshot(
        items=_cached_public_scope_items(content_lang=active_lang),
        coverage=_cached_coverage_payload(),
    )
    payload["language"] = active_lang
    payload["links"] = {
        "human": _public_url(request, root_path, f"/insights?lang={active_lang}"),
        "catalog": _public_url(
            request, root_path, f"/?lang={active_lang}#opportunities"
        ),
    }
    response = JSONResponse(payload)
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response


@app.api_route("/compare.json", methods=["GET", "HEAD"], include_in_schema=False)
async def public_compare_json(
    request: Request,
    ids: str | None = Query(None, max_length=2000),
    lang: str | None = Query(None),
) -> JSONResponse:
    """Return a source-grounded comparison of up to four public cards."""

    try:
        requested_ids = parse_comparison_ids(ids)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    if len(requested_ids) > MAX_COMPARISON_ITEMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"comparison supports at most {MAX_COMPARISON_ITEMS} items",
        )

    root_path = _root_path(request)
    active_lang = _public_lang(str(lang or request.query_params.get("lang") or ""))
    selected_items = _cached_public_scope_items(content_lang=active_lang)
    payload = build_comparison_snapshot(
        selected_items,
        requested_ids,
        lang=active_lang,
        links={
            "human": _public_url(
                request,
                root_path,
                f"/compare?ids={','.join(requested_ids)}&lang={active_lang}",
            ),
            "catalog": _public_url(
                request,
                root_path,
                f"/?lang={active_lang}#opportunities",
            ),
        },
    )
    response = JSONResponse(payload)
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response


@app.api_route(
    "/compare",
    methods=["GET", "HEAD"],
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def public_compare_page(
    request: Request,
    ids: str | None = Query(None, max_length=2000),
    lang: str | None = Query(None),
) -> HTMLResponse:
    """Render the AVDS4 comparison view backed by the public read model."""

    try:
        requested_ids = parse_comparison_ids(ids)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    if len(requested_ids) > MAX_COMPARISON_ITEMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"comparison supports at most {MAX_COMPARISON_ITEMS} items",
        )
    root_path = _root_path(request)
    active_lang = _public_lang(str(lang or request.query_params.get("lang") or ""))
    payload = build_comparison_snapshot(
        _cached_public_scope_items(content_lang=active_lang),
        requested_ids,
        lang=active_lang,
        links={
            "human": _public_url(
                request,
                root_path,
                f"/compare?ids={','.join(requested_ids)}&lang={active_lang}",
            ),
            "catalog": _public_url(
                request,
                root_path,
                f"/?lang={active_lang}#opportunities",
            ),
        },
    )
    response = HTMLResponse(
        render_comparison_page(
            payload=payload,
            lang=active_lang,
            root_path=root_path,
            site_origin=_site_origin(request, root_path),
        )
    )
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response


@app.api_route(
    "/terms",
    methods=["GET", "HEAD"],
    response_class=HTMLResponse,
    include_in_schema=False,
)
@app.api_route(
    "/data-policy",
    methods=["GET", "HEAD"],
    response_class=HTMLResponse,
    include_in_schema=False,
)
@app.api_route(
    "/attribution",
    methods=["GET", "HEAD"],
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def public_info_page(request: Request) -> HTMLResponse:
    """Render concise public guidance pages linked from the catalogue footer."""
    info_kind = request.url.path.rstrip("/").rsplit("/", 1)[-1]
    if info_kind not in {"terms", "data-policy", "attribution"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    root_path = _root_path(request)
    active_lang = _public_lang(str(request.query_params.get("lang") or "").strip())
    response = HTMLResponse(
        render_public_info_page(
            kind=info_kind,
            lang=active_lang,
            root_path=root_path,
            site_origin=_site_origin(request, root_path),
        )
    )
    response.headers["Cache-Control"] = (
        "public, max-age=300, stale-while-revalidate=900"
    )
    return response


@app.api_route("/docs", methods=["GET", "HEAD"], include_in_schema=False)
async def swagger_docs(request: Request) -> HTMLResponse:
    root_path = _root_path(request).rstrip("/")
    docs_lang = _public_lang(str(request.query_params.get("lang") or "").strip())
    if request.method == "HEAD":
        return HTMLResponse("")
    home_href = f"{root_path}/?lang={docs_lang}" if root_path else f"/?lang={docs_lang}"
    openapi_href = f"{root_path}/openapi.json" if root_path else "/openapi.json"
    docs_copy = {
        "ru": {
            "back": "Вернуться на сайт",
            "heading": "Документация API",
            "description": (
                "Публичный API QAZ.FUND: каталог, источники, возможности и статус данных."
            ),
        },
        "en": {
            "back": "Back to site",
            "heading": "API documentation",
            "description": (
                "Public QAZ.FUND API reference for the catalog, sources, opportunities, "
                "and data status."
            ),
        },
        "kk": {
            "back": "Сайтқа оралу",
            "heading": "API құжаттамасы",
            "description": (
                "QAZ.FUND ашық API: каталог, дереккөздер, мүмкіндіктер және "
                "деректер мәртебесі."
            ),
        },
    }[docs_lang]
    docs_hrefs = {
        locale: (
            f"{root_path}/docs?lang={locale}" if root_path else f"/docs?lang={locale}"
        )
        for locale in ("kk", "ru", "en")
    }
    canonical_href = _public_url(request, root_path, f"/docs?lang={docs_lang}")
    swagger = get_swagger_ui_html(
        openapi_url=openapi_href,
        title="QAZ.FUND API",
        swagger_favicon_url=f"{root_path}/favicon.ico" if root_path else "/favicon.ico",
        swagger_ui_parameters={"deepLinking": False},
    )
    docs_languages = "".join(
        f'<a href="{escape(docs_hrefs[locale], quote=True)}" lang="{locale}"'
        f'{" aria-current=\"page\"" if docs_lang == locale else ""}>'
        f'{"KAZ" if locale == "kk" else locale.upper()}</a>'
        for locale in ("kk", "ru", "en")
    )
    page_header = (
        '<header class="qazfund-docs-header" data-avds-component="api-docs">'
        f'<a href="{escape(home_href, quote=True)}" '
        f'aria-label="{escape(str(docs_copy["back"]), quote=True)}">'
        f'← {escape(str(docs_copy["back"]))}</a>'
        f'<span class="qazfund-docs-title">{escape(str(docs_copy["heading"]))}</span>'
        f'<nav class="qazfund-docs-langs" aria-label="Language">{docs_languages}</nav>'
        "</header>"
    )
    head_markup = f"""
  <meta name="description" content="{escape(str(docs_copy["description"]), quote=True)}">
  <link rel="canonical" href="{escape(canonical_href, quote=True)}">
  <style>
    {AVDS_CSS}
    html, body {{
      margin: 0;
      overflow-x: clip;
      background:
        radial-gradient(circle at 12% 0%, var(--color-accent-subtle), transparent 28rem),
        var(--color-bg);
      color: var(--color-text);
      font-family: var(--av-font-sans);
    }}
    .qazfund-docs-header {{
      box-sizing: border-box;
      position: sticky;
      top: 12px;
      z-index: 20;
      width: min(var(--av-container-dashboard), calc(100% - 64px));
      margin: 18px auto;
      padding: 10px 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      border: 1px solid var(--color-border);
      border-radius: var(--av-radius-lg);
      background: color-mix(in oklab, var(--color-surface), transparent 7%);
      box-shadow: var(--av-shadow-sm);
      backdrop-filter: blur(16px);
    }}
    .qazfund-docs-header a {{
      color: inherit;
      font-weight: 650;
      text-decoration: none;
    }}
    .qazfund-docs-title {{
      margin: 0;
      color: inherit;
      font-size: 14px;
      line-height: 1.3;
      font-weight: 700;
    }}
    .qazfund-docs-langs {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-left: auto;
    }}
    .qazfund-docs-langs a {{
      min-width: 32px;
      padding: 6px 4px;
      color: var(--color-muted);
      font-size: 11px;
      font-weight: 700;
      text-align: center;
      text-decoration: none;
      border-bottom: 2px solid transparent;
    }}
    .qazfund-docs-langs a[aria-current="page"] {{
      color: var(--color-text);
      border-bottom-color: var(--av-color-blue-700);
    }}
    .qazfund-docs-header a:focus-visible {{
      outline: 2px solid currentColor;
      outline-offset: 4px;
    }}
    .swagger-ui {{
      max-width: var(--av-container-dashboard);
      margin: 0 auto;
      padding: 0 24px 40px;
      font-family: var(--av-font-sans);
      color: var(--color-text);
    }}
    .swagger-ui .info {{
      margin: 0 0 18px;
      padding: 24px;
      border: 1px solid var(--color-border);
      border-radius: var(--av-radius-lg);
      background: var(--color-surface);
      box-shadow: var(--av-shadow-xs);
    }}
    .swagger-ui .info .title,
    .swagger-ui .opblock-tag,
    .swagger-ui .opblock-summary-method,
    .swagger-ui button,
    .swagger-ui input,
    .swagger-ui select,
    .swagger-ui textarea {{ font-family: var(--av-font-sans); }}
    .swagger-ui .scheme-container {{
      margin: 0 0 16px;
      padding: 12px 0;
      background: transparent;
      box-shadow: none;
      border-block: 1px solid var(--color-border);
    }}
    .swagger-ui .opblock-tag {{ border-bottom-color: var(--color-border); }}
    .swagger-ui .info .title small pre,
    .swagger-ui .info .title .version-stamp pre,
    .swagger-ui .info .url,
    .swagger-ui .info .base-url,
    .swagger-ui .info .base-url a,
    .swagger-ui .json-schema-2020-12-expand-deep-button {{
      color: var(--color-text);
    }}
    .swagger-ui .opblock.opblock-get .opblock-summary-method {{
      background: var(--av-color-blue-700);
      color: var(--av-color-white);
    }}
    .swagger-ui .opblock.opblock-post .opblock-summary-method {{
      background: var(--av-color-emerald-700);
      color: var(--av-color-white);
    }}
    @media (max-width: 820px) {{
      .qazfund-docs-header a,
      .swagger-ui .opblock .opblock-summary,
      .swagger-ui .opblock-summary-control,
      .swagger-ui .opblock-control-arrow,
      .swagger-ui .expand-operation,
      .swagger-ui .models-control,
      .swagger-ui .json-schema-2020-12-accordion,
      .swagger-ui .json-schema-2020-12-expand-deep-button {{
        min-height: var(--av-control-height-lg);
      }}
      .swagger-ui .opblock-control-arrow,
      .swagger-ui .expand-operation {{ min-width: var(--av-control-height-lg); }}
      .qazfund-docs-langs a {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: var(--av-control-height-lg);
      }}
    }}
    @media (max-width: 520px) {{
      .qazfund-docs-header {{
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 6px 12px;
        top: 8px;
        width: min(calc(100% - 24px), var(--av-container-dashboard));
        margin: 14px auto;
        align-items: center;
        padding: 8px 10px;
      }}
      .qazfund-docs-header > a {{
        min-width: 0;
        display: inline-flex;
        align-items: center;
        white-space: nowrap;
      }}
      .qazfund-docs-langs {{
        grid-column: 2;
        grid-row: 1;
        gap: 2px;
        margin-left: 0;
      }}
      .qazfund-docs-langs a {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: var(--av-control-height-lg);
        padding-inline: 0;
      }}
      .swagger-ui {{ padding-inline: 12px; }}
      .qazfund-docs-title {{
        grid-column: 1 / -1;
        grid-row: 2;
        max-width: none;
        text-align: left;
      }}
    }}
  </style>
"""
    raw_body = (
        swagger.body.tobytes() if isinstance(swagger.body, memoryview) else swagger.body
    )
    body = raw_body.decode("utf-8")
    body = body.replace(
        "<html>",
        f'<html lang="{docs_lang}" data-avds="grant-radar" '
        'data-av-theme="light" data-theme="light">',
        1,
    )
    body = body.replace("</head>", f"{head_markup}</head>", 1)
    body = body.replace("<body>", f"<body>{page_header}", 1)
    body = body.replace(
        '<div id="swagger-ui">\n    </div>',
        '<main id="swagger-ui" data-avds-component="api-docs"></main>',
        1,
    )
    headers = dict(swagger.headers)
    headers.pop("content-length", None)
    return HTMLResponse(body, status_code=swagger.status_code, headers=headers)


@app.api_route(
    "/opportunity/{opportunity_id}",
    methods=["GET", "HEAD"],
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def opportunity_page(
    request: Request,
    opportunity_id: UUID,
    lang: str | None = Query(None),
) -> HTMLResponse:
    content_lang = _public_lang(lang)
    item = _find_opportunity(opportunity_id, content_lang=content_lang)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if request.method == "HEAD":
        return HTMLResponse("", headers={"Cache-Control": _PUBLIC_FAST_CACHE})
    root_path = _root_path(request)
    site_origin = _site_origin(request, root_path)
    related_items = _related_opportunities(item, lang=content_lang)
    detail = await build_opportunity_detail(
        localize_opportunity(item, content_lang),
        lang=content_lang,
        allow_remote_fetch=False,
    )
    response = HTMLResponse(
        render_opportunity_page(
            detail=detail,
            lang=content_lang,
            root_path=root_path,
            site_origin=site_origin,
            related_items=related_items,
            lifecycle=public_lifecycle(item),
        )
    )
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response


@app.api_route(
    "/opportunity/{opportunity_id}/prepare",
    methods=["GET", "HEAD"],
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def opportunity_prepare_page(
    request: Request,
    opportunity_id: UUID,
    lang: str | None = Query(None),
) -> HTMLResponse:
    content_lang = _public_lang(lang)
    item = _find_opportunity(opportunity_id, content_lang=content_lang)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    root_path = _root_path(request)
    if request.method == "HEAD":
        return HTMLResponse("", headers={"Cache-Control": _PUBLIC_FAST_CACHE})
    detail = await build_opportunity_detail(
        localize_opportunity(item, content_lang),
        lang=content_lang,
        allow_remote_fetch=False,
    )
    response = HTMLResponse(
        render_application_prep_page(
            detail=detail,
            lang=content_lang,
            root_path=root_path,
            site_origin=_site_origin(request, root_path),
            lifecycle=public_lifecycle(item),
        )
    )
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response


@app.api_route("/robots.txt", methods=["GET", "HEAD"], include_in_schema=False)
async def robots_txt(request: Request) -> Response:
    root_path = _root_path(request)
    sitemap = _public_url(request, root_path, "/sitemap.xml")
    return Response(
        "\n".join(
            [
                "User-agent: *",
                "Allow: /",
                "Disallow: /health",
                "Disallow: /ready",
                "Disallow: /refresh",
                "",
                f"Sitemap: {sitemap}",
                "",
            ]
        ),
        media_type="text/plain; charset=utf-8",
    )


@app.api_route("/llms.txt", methods=["GET", "HEAD"], include_in_schema=False)
async def llms_txt(request: Request) -> Response:
    root_path = _root_path(request)
    home = _public_url(request, root_path, "/")
    sitemap = _public_url(request, root_path, "/sitemap.xml")
    docs = _public_url(request, root_path, "/docs")
    openapi_url = _public_url(request, root_path, "/openapi.json")
    discovery = _public_url(request, root_path, "/site-discovery.json")
    ecosystem = _public_url(request, root_path, "/.well-known/qdev-ecosystem.json")
    release = _public_url(request, root_path, "/.well-known/release.json")
    qazstack_contract = _public_url(
        request, root_path, "/.well-known/qazstack-consumer.json"
    )
    avds_contract = _public_url(
        request, root_path, "/.well-known/avds-ui-contract.json"
    )
    qazpipe_contract_url = _public_url(
        request, root_path, "/.well-known/qazpipe-source.json"
    )
    qazcompute_contract_url = _public_url(
        request, root_path, "/.well-known/qazcompute-profiles.json"
    )
    notification_contract_url = _public_url(
        request, root_path, "/.well-known/notification-contract.json"
    )
    source_onboarding_url = _public_url(
        request, root_path, "/.well-known/source-onboarding.json"
    )
    insights = _public_url(request, root_path, "/insights")
    media = _public_url(request, root_path, "/media")
    terms = _public_url(request, root_path, "/terms")
    data_policy = _public_url(request, root_path, "/data-policy")
    attribution = _public_url(request, root_path, "/attribution")
    status_page = _public_url(request, root_path, "/status")
    coverage = _public_url(request, root_path, "/coverage")
    insights_json = _public_url(request, root_path, "/insights.json")
    media_json = _public_url(request, root_path, "/media.json")
    media_feed = _public_url(request, root_path, "/media/feed.json")
    media_rss = _public_url(request, root_path, "/media/rss.xml")
    compare_json = _public_url(request, root_path, "/compare.json")
    opportunities = _public_url(request, root_path, "/opportunities")
    opportunities_ndjson = _public_url(request, root_path, "/opportunities.ndjson")
    opportunities_ndjson_compact = _public_url(
        request, root_path, "/opportunities.ndjson?compact=true"
    )
    history_template = _public_url(
        request, root_path, "/opportunities/{id}/history.json"
    )
    digest = _public_url(request, root_path, "/digest")
    return Response(
        "\n".join(
            [
                "# QAZ.FUND",
                (
                    "> Open support-program navigator for Kazakhstan: public "
                    "opportunities, source links, data status, and reproducible "
                    "working routes."
                ),
                "",
                "## Public entry points",
                f"- Home: {home}",
                f"- Sitemap: {sitemap}",
                f"- API docs: {docs}",
                f"- OpenAPI schema: {openapi_url}",
                f"- Site discovery JSON: {discovery}",
                f"- Ecosystem integration JSON: {ecosystem}",
                f"- Release metadata JSON: {release}",
                f"- QazStack consumer contract: {qazstack_contract}",
                f"- AV DS 4 UI contract: {avds_contract}",
                f"- QazPipe source contract: {qazpipe_contract_url}",
                f"- QazCompute profile contract: {qazcompute_contract_url}",
                f"- Notification contract: {notification_contract_url}",
                f"- Source onboarding contract: {source_onboarding_url}",
                f"- Source status page: {status_page}",
                f"- Catalog insights: {insights}",
                f"- Media page: {media}",
                f"- Catalog insights JSON: {insights_json}",
                f"- Media JSON: {media_json}",
                f"- Media JSON Feed: {media_feed}",
                f"- Media RSS: {media_rss}",
                f"- Comparison JSON: {compare_json}?ids={{id}},{{id}}&lang=ru|kk|en",
                f"- Terms of use: {terms}",
                f"- Data policy: {data_policy}",
                f"- Data attribution: {attribution}",
                "",
                "## Public data endpoints",
                f"- Coverage JSON: {coverage}",
                f"- Opportunities JSON: {opportunities}",
                f"- Opportunities NDJSON: {opportunities_ndjson}",
                f"- Compact Opportunities NDJSON: {opportunities_ndjson_compact}",
                "- Opportunity detail JSON: /opportunities/{id}?lang=kk|ru|en",
                f"- Opportunity history JSON: {history_template}?lang=kk|ru|en&limit={{n}}",
                f"- Digest JSON: {digest}",
                f"- Insights JSON: {insights_json}?lang=ru|kk|en",
                f"- Comparison JSON: {compare_json}?ids={{id}},{{id}}&lang=ru|kk|en",
                f"- Notification contract JSON: {notification_contract_url}",
                f"- Source onboarding contract JSON: {source_onboarding_url}",
                "",
                "## AI consumption guidance",
                (
                    "- Prefer compact Opportunities NDJSON for bulk discovery reads; "
                    "use the full NDJSON export when raw source payloads are needed."
                ),
                (
                    "- Use Site discovery JSON for route templates, query templates, "
                    "cache expectations, and contract URLs."
                ),
                (
                    "- Cache public discovery documents for at least 300 seconds "
                    "unless HTTP headers say otherwise."
                ),
                "- Notifications are not enabled; do not infer subscriptions from local saves.",
                "",
                "## Public route templates",
                "- Opportunity page: /opportunity/{id}?lang=kk|ru|en",
                "- Opportunity history: /opportunities/{id}/history.json?lang=kk|ru|en&limit={n}",
                "- Funder page: /funder/{slug}?lang=kk|ru|en",
                "- Insights page: /insights?lang=kk|ru|en",
                "- Media page: /media?lang=kk|ru|en",
                "- Insights JSON: /insights.json?lang=kk|ru|en",
                "- Media JSON: /media.json?lang=kk|ru|en",
                "- Media JSON Feed: /media/feed.json?lang=kk|ru|en",
                "- Media RSS: /media/rss.xml?lang=kk|ru|en",
                "- Comparison JSON: /compare.json?ids={id},{id}&lang=kk|ru|en",
                "- Notification contract: /.well-known/notification-contract.json",
                "- Source onboarding contract: /.well-known/source-onboarding.json",
                "- Terms page: /terms?lang=kk|ru|en",
                "- Data policy page: /data-policy?lang=kk|ru|en",
                "- Attribution page: /attribution?lang=kk|ru|en",
                "",
                "## Query hints",
                (
                    "- Opportunities filters: q, source, lifecycle, region, tag, "
                    "min_score, deadline_before, deadline_after, limit, offset, lang, "
                    "compact"
                ),
                "- Digest filters: limit, min_score, tag, lang",
                "",
                "## What this site is for",
                (
                    "- Find open support programs for Kazakhstan-focused tasks, "
                    "teams, and institutions."
                ),
                "- Check source links, data status, deadlines, and the next step.",
                "- Save, share, export, and cite a working route.",
                "",
                "## Operator notes for AI systems",
                (
                    "- Treat QAZ.FUND as a public discovery and preparation surface, "
                    "not as an application submission system."
                ),
                "- Prefer the public opportunity and funder pages over guessed program details.",
                (
                    "- Do not invent eligibility, deadlines, or award amounts "
                    "beyond the published page content."
                ),
                (
                    "- evidence_state=sourced means that a direct public source link "
                    "is present; it does not mean independent verification."
                ),
                "",
            ]
        ),
        media_type="text/plain; charset=utf-8",
    )


@app.api_route("/site-discovery.json", methods=["GET", "HEAD"], include_in_schema=False)
async def site_discovery(request: Request) -> Response:
    root_path = _root_path(request)
    home = _public_url(request, root_path, "/")
    sitemap = _public_url(request, root_path, "/sitemap.xml")
    docs = _public_url(request, root_path, "/docs")
    openapi_url = _public_url(request, root_path, "/openapi.json")
    llms = _public_url(request, root_path, "/llms.txt")
    api_v1 = _public_url(request, root_path, "/api/v1")
    api_v1_schema = _public_url(request, root_path, "/api/v1/schema")
    status_page = _public_url(request, root_path, "/status")
    coverage = _public_url(request, root_path, "/coverage")
    insights_json = _public_url(request, root_path, "/insights.json")
    insights_page = _public_url(request, root_path, "/insights")
    media = _public_url(request, root_path, "/media")
    media_json = _public_url(request, root_path, "/media.json")
    media_feed = _public_url(request, root_path, "/media/feed.json")
    media_rss = _public_url(request, root_path, "/media/rss.xml")
    media_feed_json = _public_url(request, root_path, "/media/v1/feed.json")
    media_feed_rss = _public_url(request, root_path, "/media/v1/feed.rss")
    daily_digest_json = _public_url(request, root_path, "/media/v1/digest/daily.json")
    daily_digest_text_url = _public_url(
        request, root_path, "/media/v1/digest/daily.txt"
    )
    qpost_drafts = _public_url(request, root_path, "/media/v1/qpost/drafts.json")
    compare_json = _public_url(request, root_path, "/compare.json")
    opportunities = _public_url(request, root_path, "/opportunities")
    opportunities_ndjson = _public_url(request, root_path, "/opportunities.ndjson")
    opportunities_ndjson_compact = _public_url(
        request, root_path, "/opportunities.ndjson?compact=true"
    )
    history_template = _public_url(
        request, root_path, "/opportunities/{id}/history.json"
    )
    digest = _public_url(request, root_path, "/digest")
    ecosystem = _public_url(request, root_path, "/.well-known/qdev-ecosystem.json")
    release = _public_url(request, root_path, "/.well-known/release.json")
    qazstack_contract = _public_url(
        request, root_path, "/.well-known/qazstack-consumer.json"
    )
    avds_contract = _public_url(
        request, root_path, "/.well-known/avds-ui-contract.json"
    )
    qazpipe_contract = _public_url(
        request, root_path, "/.well-known/qazpipe-source.json"
    )
    qazcompute_contract = _public_url(
        request, root_path, "/.well-known/qazcompute-profiles.json"
    )
    notification_contract_url = _public_url(
        request, root_path, "/.well-known/notification-contract.json"
    )
    source_onboarding_url = _public_url(
        request, root_path, "/.well-known/source-onboarding.json"
    )
    insights = _public_url(request, root_path, "/insights")
    terms = _public_url(request, root_path, "/terms")
    data_policy = _public_url(request, root_path, "/data-policy")
    attribution = _public_url(request, root_path, "/attribution")
    payload = {
        "site": "QAZ.FUND",
        "type": "public-funding-navigator",
        "home": home,
        "sitemap": sitemap,
        "llms": llms,
        "api_docs": docs,
        "openapi": openapi_url,
        "versioned_api": api_v1,
        "api_v1_schema": api_v1_schema,
        "insights": insights_page,
        "source_status": status_page,
        "terms": terms,
        "data_policy": data_policy,
        "attribution": attribution,
        "ecosystem": ecosystem,
        "release": release,
        "contracts": {
            "qazstack": qazstack_contract,
            "avds4": avds_contract,
            "qazpipe": qazpipe_contract,
            "qazcompute": qazcompute_contract,
            "notifications": notification_contract_url,
            "source_onboarding": source_onboarding_url,
        },
        "languages": ["kk", "ru", "en"],
        "routes": {
            "home": "/?lang={lang}",
            "coverage": "/coverage",
            "source_status": "/status?lang={lang}",
            "opportunities": "/opportunities?lang={lang}",
            "opportunities_ndjson": "/opportunities.ndjson?lang={lang}",
            "opportunities_ndjson_compact": (
                "/opportunities.ndjson?lang={lang}&compact=true"
            ),
            "opportunity_api": "/opportunities/{id}?lang={lang}",
            "opportunity_history": (
                "/opportunities/{id}/history.json?lang={lang}&limit={n}"
            ),
            "opportunity": "/opportunity/{id}?lang={lang}",
            "opportunity_prepare": "/opportunity/{id}/prepare?lang={lang}",
            "api_v1": "/api/v1",
            "api_v1_schema": "/api/v1/schema",
            "api_v1_opportunities": "/api/v1/opportunities?lang={lang}",
            "api_v1_opportunities_ndjson": "/api/v1/opportunities.ndjson?lang={lang}",
            "api_v1_opportunity": "/api/v1/opportunities/{id}?lang={lang}",
            "insights": "/insights?lang={lang}",
            "api_v1_insights": "/api/v1/insights?lang={lang}",
            "api_v1_changes": "/api/v1/changes?lang={lang}&hours={hours}",
            "media_content": "/media/v1/opportunities/{id}/content.json?lang={lang}",
            "media_citation": "/media/v1/opportunities/{id}/citation.txt?lang={lang}",
            "media_card": "/media/v1/opportunities/{id}/card.svg?lang={lang}",
            "media_chart_svg": "/media/v1/charts/{chart_type}.svg?lang={lang}",
            "media_chart_csv": "/media/v1/charts/{chart_type}.csv?lang={lang}",
            "media_feed_json": "/media/v1/feed.json?lang={lang}",
            "media_feed_rss": "/media/v1/feed.rss?lang={lang}",
            "media_daily_digest_json": "/media/v1/digest/daily.json?lang={lang}",
            "media_daily_digest_text": "/media/v1/digest/daily.txt?lang={lang}",
            "media_qpost_drafts": (
                "/media/v1/qpost/drafts.json?lang={lang}&template={template}"
            ),
            "terms": "/terms?lang={lang}",
            "data_policy": "/data-policy?lang={lang}",
            "attribution": "/attribution?lang={lang}",
            "funder": "/funder/{slug}?lang={lang}",
            "digest": "/digest?lang={lang}",
            "insights": "/insights?lang={lang}",
            "insights_json": "/insights.json?lang={lang}",
            "media": "/media?lang={lang}",
            "media_json": "/media.json?lang={lang}",
            "media_feed": "/media/feed.json?lang={lang}",
            "media_rss": "/media/rss.xml?lang={lang}",
            "compare": "/compare?ids={id},{id}&lang={lang}",
            "compare_json": "/compare.json?ids={id},{id}&lang={lang}",
            "notification_contract": "/.well-known/notification-contract.json",
            "source_onboarding": "/.well-known/source-onboarding.json",
            "terms": "/terms?lang={lang}",
            "data_policy": "/data-policy?lang={lang}",
            "attribution": "/attribution?lang={lang}",
        },
        "data_endpoints": {
            "coverage": coverage,
            "opportunities": opportunities,
            "opportunities_ndjson": opportunities_ndjson,
            "opportunities_ndjson_compact": opportunities_ndjson_compact,
            "api_v1": api_v1,
            "api_v1_schema": api_v1_schema,
            "api_v1_opportunities": _public_url(
                request, root_path, "/api/v1/opportunities"
            ),
            "api_v1_opportunities_ndjson": _public_url(
                request, root_path, "/api/v1/opportunities.ndjson"
            ),
            "api_v1_insights": _public_url(request, root_path, "/api/v1/insights"),
            "api_v1_changes": _public_url(request, root_path, "/api/v1/changes"),
            "qpost_drafts": qpost_drafts,
            "opportunity_history": history_template,
            "digest": digest,
            "insights": insights,
            "insights_json": insights_json,
            "media": media,
            "media_json": media_json,
            "media_feed": media_feed,
            "media_rss": media_rss,
            "compare": compare_json,
            "compare_json": compare_json,
            "notification_contract": notification_contract_url,
            "source_onboarding": source_onboarding_url,
            "terms": terms,
            "data_policy": data_policy,
            "attribution": attribution,
        },
        "media_endpoints": {
            "feed_json": media_feed_json,
            "feed_rss": media_feed_rss,
            "daily_digest_json": daily_digest_json,
            "daily_digest_text": daily_digest_text_url,
            "qpost_drafts": qpost_drafts,
            "content_template": "/media/v1/opportunities/{id}/content.json?lang=ru|en",
            "citation_template": (
                "/media/v1/opportunities/{id}/citation.txt?lang=ru|en"
            ),
            "card_template": "/media/v1/opportunities/{id}/card.svg?format=og",
            "chart_svg_template": "/media/v1/charts/{chart_type}.svg?lang=ru|en",
            "chart_csv_template": "/media/v1/charts/{chart_type}.csv?lang=ru|en",
        },
        "ai_consumption": {
            "preferred_bulk_export": _public_url(
                request, root_path, "/api/v1/opportunities.ndjson"
            ),
            "preferred_legacy_bulk_export": opportunities_ndjson_compact,
            "preferred_detail_template": "/opportunities/{id}?lang=kk|ru|en",
            "preferred_v1_detail_template": "/api/v1/opportunities/{id}?lang=kk|ru|en",
            "preferred_human_template": "/opportunity/{id}?lang=kk|ru|en",
            "history_template": history_template + "?lang={lang}&limit={n}",
            "recommended_language_order": ["kk", "ru", "en"],
            "cache_policy": {
                "discovery_seconds": 300,
                "catalog_seconds": 60,
                "ndjson_seconds": 300,
            },
            "public_evidence_fields": [
                "source",
                "source_url",
                "discovered_at",
                "deadline",
                "score",
                "evidence_state",
                "raw.provenance",
                "raw.decision_readiness",
                "raw.qazcompute_evidence_readiness",
                "raw.ranking",
            ],
            "do_not_infer": [
                "eligibility",
                "deadline",
                "award amount",
                "application result",
            ],
        },
        "query_templates": {
            "opportunities_recent": (
                "/opportunities?lang=ru&limit=50&min_score=0.5"
                "&deadline_after={yyyy-mm-dd}"
            ),
            "opportunities_by_tag": "/opportunities?lang=ru&limit=50&tag={tag}",
            "opportunities_search": "/opportunities?lang=ru&limit=50&q={query}",
            "opportunities_by_source": (
                "/opportunities?lang=ru&limit=50&source={source}"
            ),
            "opportunities_by_lifecycle": (
                "/opportunities?lang=ru&limit=50&lifecycle={lifecycle}"
            ),
            "opportunities_ai_export": (
                "/opportunities.ndjson?lang=ru&limit=500&min_score=0.3" "&compact=true"
            ),
            "opportunities_v1_export": (
                "/api/v1/opportunities.ndjson?lang=ru&limit=500&min_score=0.3"
            ),
            "opportunity_v1_detail": "/api/v1/opportunities/{id}?lang=ru",
            "insights": "/api/v1/insights?lang=ru",
            "changes_last_day": "/api/v1/changes?lang=ru&hours=24",
            "opportunity_citation": (
                "/media/v1/opportunities/{id}/citation.txt?lang=ru&style=citation"
            ),
            "digest_ai": "/digest?lang=ru&limit=5&tag=ai",
        },
        "capabilities": [
            "public opportunity pages",
            "private-by-default application preparation",
            "public funder pages",
            "public insights page",
            "public media page",
            "machine-readable insights snapshot",
            "machine-readable media snapshot",
            "machine-readable media JSON Feed",
            "machine-readable media RSS",
            "machine-readable opportunity comparison",
            "notification contract (delivery disabled)",
            "public data-policy pages",
            "machine-readable opportunity api",
            "versioned public data contract",
            "derived public analytics",
            "semantic change ledger",
            "source attribution and citation helpers",
            "machine-readable media feeds",
            "daily semantic-change digest",
            "cache-aware ndjson export",
            "machine-readable source coverage",
            "public source freshness status",
            "public opportunity change history",
            "official source links",
            "read-only public catalog",
            "qdev ecosystem contract",
            "qazpipe pull-source contract",
            "qazcompute profile contract",
            "source onboarding contract",
        ],
    }
    return JSONResponse(payload)


@app.api_route(
    "/.well-known/qazstack-consumer.json",
    methods=["GET", "HEAD"],
    include_in_schema=False,
)
async def public_qazstack_consumer_contract(request: Request) -> Response:
    root_path = _root_path(request)
    origin = _public_root_base(request, root_path)
    return JSONResponse(qazstack_consumer_contract(origin))


@app.api_route(
    "/.well-known/avds-ui-contract.json",
    methods=["GET", "HEAD"],
    include_in_schema=False,
)
async def public_avds_ui_contract() -> Response:
    return JSONResponse(avds_ui_contract())


@app.api_route(
    "/.well-known/qazpipe-source.json",
    methods=["GET", "HEAD"],
    include_in_schema=False,
)
async def public_qazpipe_source_contract(request: Request) -> Response:
    root_path = _root_path(request)
    origin = _public_root_base(request, root_path)
    return JSONResponse(qazpipe_source_contract(origin))


@app.api_route(
    "/.well-known/qazcompute-profiles.json",
    methods=["GET", "HEAD"],
    include_in_schema=False,
)
async def public_qazcompute_profile_contract(request: Request) -> Response:
    root_path = _root_path(request)
    origin = _public_root_base(request, root_path)
    return JSONResponse(qazcompute_profile_contract(origin))


@app.api_route(
    "/.well-known/notification-contract.json",
    methods=["GET", "HEAD"],
    include_in_schema=False,
)
async def public_notification_contract(request: Request) -> Response:
    root_path = _root_path(request)
    return JSONResponse(notification_contract(_public_root_base(request, root_path)))


@app.api_route(
    "/.well-known/source-onboarding.json",
    methods=["GET", "HEAD"],
    include_in_schema=False,
)
async def public_source_onboarding_contract(request: Request) -> Response:
    root_path = _root_path(request)
    origin = _public_root_base(request, root_path)
    return JSONResponse(source_onboarding_contract(origin, PARSERS.keys()))


@app.api_route(
    "/.well-known/qdev-ecosystem.json",
    methods=["GET", "HEAD"],
    include_in_schema=False,
)
async def public_ecosystem_manifest(request: Request) -> Response:
    root_path = _root_path(request)
    origin = _public_root_base(request, root_path)
    return JSONResponse(ecosystem_manifest(origin))


@app.api_route(
    "/.well-known/release.json",
    methods=["GET", "HEAD"],
    include_in_schema=False,
)
async def public_release_metadata() -> Response:
    """Expose the immutable revision needed for end-to-end deploy proof."""

    configured_revision = os.environ.get("APP_REVISION", "").strip().lower()
    revision = (
        configured_revision
        if re.fullmatch(r"[0-9a-f]{40}", configured_revision)
        else "development"
    )
    payload = {
        "service": "qaz-fund",
        "revision": revision,
        "deployed_at": os.environ.get("APP_DEPLOYED_AT", "").strip() or None,
    }
    return JSONResponse(payload, headers={"Cache-Control": "no-store"})


@app.api_route("/favicon.ico", methods=["GET", "HEAD"], include_in_schema=False)
async def favicon() -> Response:
    return Response(_FAVICON_SVG, media_type="image/svg+xml")


@app.api_route("/og-image.svg", methods=["GET", "HEAD"], include_in_schema=False)
async def og_image() -> Response:
    return Response(OG_IMAGE_SVG, media_type="image/svg+xml")


@app.api_route("/og-image.png", methods=["GET", "HEAD"], include_in_schema=False)
async def og_image_png() -> Response:
    return Response(OG_IMAGE_PNG, media_type="image/png")


@app.get(f"/{GOOGLE_SITE_VERIFICATION_FILENAME}", include_in_schema=False)
async def google_site_verification() -> Response:
    return Response(
        GOOGLE_SITE_VERIFICATION_CONTENT,
        media_type="text/plain; charset=utf-8",
    )


@app.api_route("/sitemap.xml", methods=["GET", "HEAD"], include_in_schema=False)
async def sitemap_xml(request: Request) -> Response:
    root_path = _root_path(request)
    xml = _cached_sitemap_xml(_public_root_base(request, root_path))
    return Response(xml, media_type="application/xml; charset=utf-8")


@app.get("/health")
async def health() -> dict:
    repository = _configured_repository()
    items = repository.size() if repository is not None else len(_cache)
    return {"status": "ok", "items": items}


@app.head("/health", include_in_schema=False)
async def health_head() -> Response:
    await health()
    return Response(status_code=200)


@app.get("/ready")
async def ready() -> dict[str, Any]:
    try:
        repository = _configured_repository()
        backend = "database" if repository is not None else "memory"
        items = repository.size() if repository is not None else len(_cache)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "error", "backend": "database"},
        ) from exc
    return {"status": "ok", "backend": backend, "items": items}


@app.head("/ready", include_in_schema=False)
async def ready_head() -> Response:
    await ready()
    return Response(status_code=200)


@app.get("/sources")
async def list_sources() -> list[dict[str, Any]]:
    return [
        {
            "slug": slug,
            "name": source_cls.name,
            "base_url": source_cls.base_url,
            "tags": list(source_cls.default_tags),
            "enabled": True,
        }
        for slug, source_cls in PARSERS.items()
    ]


@app.get("/coverage")
async def coverage() -> dict[str, Any]:
    return _cached_coverage_payload()


@app.head("/coverage", include_in_schema=False)
async def coverage_head() -> Response:
    return Response(status_code=200, media_type="application/json")


@app.api_route("/status", methods=["GET", "HEAD"], include_in_schema=False)
async def public_status_page(request: Request) -> HTMLResponse:
    """Render a public, cacheable source-freshness view."""
    if request.method == "HEAD":
        return HTMLResponse(
            "",
            headers={"Cache-Control": "public, max-age=60, stale-while-revalidate=300"},
        )
    root_path = _root_path(request)
    active_lang = _public_lang(str(request.query_params.get("lang") or "").strip())
    response = HTMLResponse(
        render_status_page(
            coverage=_cached_coverage_payload(),
            lang=active_lang,
            root_path=root_path,
            site_origin=_site_origin(request, root_path),
        )
    )
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response


@app.api_route("/operator", methods=["GET", "HEAD"], include_in_schema=False)
async def operator_page(request: Request) -> HTMLResponse:
    """Render the noindex operator shell without embedding credentials."""
    response = (
        HTMLResponse("")
        if request.method == "HEAD"
        else HTMLResponse(
            render_operator_page(
                lang=_public_lang(str(request.query_params.get("lang") or "").strip()),
                root_path=_root_path(request),
            )
        )
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response


@app.get("/operator/health", include_in_schema=False)
async def operator_health(_: None = Depends(require_admin_token)) -> dict[str, Any]:
    """Protected operational summary for source and pipeline supervision."""
    coverage_payload = _cached_coverage_payload()
    recent_runs = _operator_run_rows()
    stale_sources = [
        {
            "slug": row.get("slug"),
            "name": row.get("name"),
            "last_discovered_at": row.get("last_discovered_at"),
            "last_checked_at": row.get("last_checked_at"),
            "age_hours": row.get("age_hours"),
        }
        for row in coverage_payload.get("sources", [])
        if row.get("enabled") and row.get("freshness_status") == "stale"
    ]
    # Keep the full run history for diagnosis, but do not leave the operator
    # surface in an alert state after a source has recovered.  A failure is
    # unresolved only while it is the latest observed run for that source.
    latest_run_by_source: dict[str, dict[str, Any]] = {}
    for row in recent_runs:
        source = str(row.get("source") or "").strip()
        if source and source not in latest_run_by_source:
            latest_run_by_source[source] = row
    failed_runs = [
        row
        for row in recent_runs
        if row.get("status") == "error"
        and latest_run_by_source.get(str(row.get("source") or "").strip()) is row
    ]
    return {
        "status": "attention" if stale_sources or failed_runs else "ok",
        "generated_at": datetime.now(UTC).isoformat(),
        "catalog_items": coverage_payload.get("items", 0),
        "relevant_open_items": coverage_payload.get("relevant_open_items", 0),
        "enabled_sources": coverage_payload.get("enabled_sources", 0),
        "fresh_sources": coverage_payload.get("fresh_sources", 0),
        "stale_sources": stale_sources,
        "unknown_freshness_sources": coverage_payload.get(
            "unknown_freshness_sources", 0
        ),
        "failed_runs": failed_runs[:10],
        "recent_runs": recent_runs[:20],
    }


@app.get("/funders")
async def list_funders(
    limit: int = Query(24, ge=1, le=200),
) -> list[dict[str, Any]]:
    groups = sorted(
        _funder_index("en").values(),
        key=lambda row: (
            -int(row["current_items"]),
            -float(row["avg_score"]),
            -int(row["total_items"]),
            str(row["name"]).lower(),
        ),
    )
    return [_funder_payload(group) for group in groups[:limit]]


@app.api_route(
    "/funder/{funder_slug}",
    methods=["GET", "HEAD"],
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def funder_page(
    request: Request,
    funder_slug: str,
    lang: str | None = Query(None),
) -> Response:
    content_lang = _public_lang(lang)
    group = _funder_index(content_lang=content_lang).get(funder_slug)
    if group is None:
        legacy_query = LEGACY_FUNDER_REDIRECTS.get(funder_slug)
        if legacy_query:
            return RedirectResponse(
                url=f"/?lang={content_lang}&q={legacy_query}",
                status_code=status.HTTP_302_FOUND,
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if request.method == "HEAD":
        return HTMLResponse("", headers={"Cache-Control": _PUBLIC_FAST_CACHE})
    root_path = _root_path(request)
    site_origin = _site_origin(request, root_path)
    items = cast(list[Opportunity], group["items"])
    live_items = [
        localize_opportunity(item, content_lang)
        for item in items
        if public_lifecycle(item) in {"open", "closing_soon", "rolling", "forecast"}
    ][:8]
    archive_items = [
        localize_opportunity(item, content_lang)
        for item in items
        if public_lifecycle(item) in {"closed", "awarded"}
    ][:6]
    response = HTMLResponse(
        render_funder_page(
            funder=_funder_payload(group),
            live_items=live_items,
            archive_items=archive_items,
            lang=content_lang,
            root_path=root_path,
            site_origin=site_origin,
        )
    )
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response


def _persist_items(items: list[Opportunity]) -> None:
    repository = _configured_repository()
    if repository is None:
        return
    for item in items:
        repository.upsert(item)


@app.post("/refresh")
async def refresh(_: None = Depends(require_admin_token)) -> dict:
    global _cache
    sources = [source_cls() for source_cls in PARSERS.values()]  # type: ignore[abstract]
    _cache = await run_all(sources)
    _persist_items(_cache)
    _clear_sitemap_cache()
    _clear_public_items_cache()
    _warm_public_items_cache()
    _warm_public_sitemap_cache()
    return {"refreshed": len(_cache)}


def _query_opportunities(
    *,
    tag: str | None = Query(None),
    q: str | None = Query(None, max_length=200),
    source: str | None = Query(None, max_length=120),
    lifecycle: str | None = Query(
        None,
        pattern="^(open|closing_soon|rolling|forecast|closed|awarded)$",
    ),
    region: str | None = Query(
        None,
        pattern="^(kazakhstan|central_asia|global)$",
    ),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    deadline_before: date | None = None,
    deadline_after: date | None = None,
    include_irrelevant: bool = False,
    limit: int = Query(50, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    lang: str | None = Query(None),
    compact: bool = Query(False),
) -> tuple[list[Opportunity], int]:
    content_lang = _public_lang(lang)
    query_key = (
        tag,
        q,
        source,
        lifecycle,
        region,
        min_score,
        deadline_before,
        deadline_after,
        include_irrelevant,
        limit,
        offset,
        content_lang,
        compact,
    )
    now = datetime.now(UTC)
    with _public_items_cache_lock:
        cached_query = _public_query_cache.get(query_key)
        if cached_query is not None and now - cached_query[0] < _PUBLIC_QUERY_CACHE_TTL:
            cached_items, cached_total = cached_query[1]
            return list(cached_items), cached_total
    items = _cached_prepared_scope_items(
        content_lang=content_lang, include_irrelevant=include_irrelevant
    )
    if tag:
        items = [o for o in items if tag.lower() in (t.lower() for t in o.tags)]
    if source:
        normalized_source = _normalized_token(source)
        items = [
            item
            for item in items
            if _normalized_token(item.source) == normalized_source
        ]
    if lifecycle:
        items = [item for item in items if public_lifecycle(item) == lifecycle]
    if region:
        items = [item for item in items if region in _funder_region_tokens(item)]
    items = [o for o in items if o.score >= min_score]
    if deadline_before:
        items = [o for o in items if o.deadline and o.deadline <= deadline_before]
    if deadline_after:
        items = [o for o in items if _is_open(o, deadline_after)]
    if q:
        lexical_items = [item for item in items if _matches_opportunity_query(item, q)]
        semantic_hits = _search_semantic_opportunities(
            q,
            items,
            limit=min(len(items), max(100, offset + limit)),
        )
        if semantic_hits:
            items = _fuse_hybrid_query_results(items, lexical_items, semantic_hits)
        else:
            items = lexical_items
    total_count = len(items)
    results = items[offset : offset + limit]
    if compact:
        results = [_compact_dashboard_item(item) for item in results]
    with _public_items_cache_lock:
        if len(_public_query_cache) >= 256:
            _public_query_cache.pop(next(iter(_public_query_cache)))
        _public_query_cache[query_key] = (now, (tuple(results), total_count))
    return results, total_count


def _fuse_hybrid_query_results(
    items: list[Opportunity],
    lexical_items: list[Opportunity],
    semantic_hits: list[Any],
) -> list[Opportunity]:
    """Fuse lexical and semantic rankings without letting either bypass filters."""

    by_id = {item.id: item for item in items}
    semantic_rank = {
        hit.opportunity_id: rank
        for rank, hit in enumerate(semantic_hits, start=1)
        if hit.opportunity_id in by_id
    }
    lexical_rank = {item.id: rank for rank, item in enumerate(lexical_items, start=1)}
    candidate_ids = set(semantic_rank) | set(lexical_rank)
    if not candidate_ids:
        return lexical_items
    original_rank = {item.id: rank for rank, item in enumerate(items, start=1)}

    def rrf_score(item_id: UUID) -> float:
        value = 0.0
        if item_id in semantic_rank:
            value += 1.0 / (60 + semantic_rank[item_id])
        if item_id in lexical_rank:
            value += 1.0 / (60 + lexical_rank[item_id])
        return value

    return sorted(
        (by_id[item_id] for item_id in candidate_ids),
        key=lambda item: (-rrf_score(item.id), original_rank[item.id]),
    )


def _opportunities_json_response(
    items: list[Opportunity],
    *,
    total_count: int,
) -> Response:
    """Serialize the catalog once, bypassing duplicate FastAPI model encoding."""

    return Response(
        content=_OPPORTUNITY_LIST_ADAPTER.dump_json(items),
        media_type="application/json",
        headers={
            "X-Total-Count": str(total_count),
            "X-Result-Count": str(len(items)),
        },
    )


def _opportunity_v1_from_item(
    item: Opportunity,
    *,
    request: Request,
    root_path: str,
) -> OpportunityV1:
    return to_opportunity_v1(
        item,
        source_name=_source_name(item.source),
        public_base_url=_public_root_base(request, root_path),
    )


def _cached_public_v1_index(
    *,
    content_lang: str,
    include_irrelevant: bool,
    public_base_url: str,
) -> dict[UUID, OpportunityV1]:
    """Cache the versioned machine projection by language, scope, and origin."""
    normalized_lang = _public_lang(content_lang)
    normalized_base = public_base_url.rstrip("/")
    cache_key = (normalized_lang, include_irrelevant, normalized_base)
    now = datetime.now(UTC)
    with _public_items_cache_lock:
        cached = _public_v1_cache.get(cache_key)
        if cached is not None and now - cached[0] < _PUBLIC_ITEMS_CACHE_TTL:
            return cached[1]

    index = {
        item.id: to_opportunity_v1(
            item,
            source_name=_source_name(item.source),
            public_base_url=normalized_base,
        )
        for item in _cached_prepared_scope_items(
            content_lang=normalized_lang,
            include_irrelevant=include_irrelevant,
        )
    }
    with _public_items_cache_lock:
        _public_v1_cache[cache_key] = (now, index)
    return index


def _versioned_json_response(payload: dict[str, Any]) -> JSONResponse:
    return JSONResponse(
        jsonable_encoder(payload),
        headers={
            "X-Dataset-Schema-Version": DATASET_SCHEMA_VERSION,
            "X-Opportunity-Schema-Version": SCHEMA_VERSION,
        },
    )


def _query_opportunities_v1(
    request: Request,
    *,
    tag: str | None = None,
    q: str | None = None,
    source: str | None = None,
    lifecycle: str | None = None,
    region: str | None = None,
    min_score: float = 0.0,
    deadline_before: date | None = None,
    deadline_after: date | None = None,
    include_irrelevant: bool = False,
    limit: int = 50,
    offset: int = 0,
    lang: str | None = None,
) -> tuple[list[OpportunityV1], int, str]:
    root_path = _root_path(request)
    content_lang = _public_lang(lang)
    items, total_count = _query_opportunities(
        tag=tag,
        q=q,
        source=source,
        lifecycle=lifecycle,
        region=region,
        min_score=min_score,
        deadline_before=deadline_before,
        deadline_after=deadline_after,
        include_irrelevant=include_irrelevant,
        limit=limit,
        offset=offset,
        lang=content_lang,
        compact=False,
    )
    index = _cached_public_v1_index(
        content_lang=content_lang,
        include_irrelevant=include_irrelevant,
        public_base_url=_public_root_base(request, root_path),
    )
    rows = [
        index.get(item.id)
        or _opportunity_v1_from_item(item, request=request, root_path=root_path)
        for item in items
    ]
    return rows, total_count, root_path


def _find_opportunity_v1(
    request: Request,
    opportunity_id: UUID,
    *,
    lang: str | None = None,
) -> OpportunityV1:
    content_lang = _public_lang(lang)
    item = _find_opportunity(opportunity_id, content_lang=content_lang)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    root_path = _root_path(request)
    cached = _cached_public_v1_index(
        content_lang=content_lang,
        include_irrelevant=False,
        public_base_url=_public_root_base(request, root_path),
    ).get(item.id)
    if cached is not None:
        return cached
    localized = _with_decision_readiness(
        localize_opportunity(item, content_lang),
        ranking_subject=item,
    )
    return _opportunity_v1_from_item(localized, request=request, root_path=root_path)


def _localized_chart_rows(
    rows: list[dict[str, int | str]],
    *,
    lang: str,
) -> list[dict[str, int | str]]:
    copy = localized_dashboard_copy(lang)
    label_map = copy.get("label_map")
    if not isinstance(label_map, dict):
        return rows
    localized_rows: list[dict[str, int | str]] = []
    for row in rows:
        label = str(row["label"])
        localized = label_map.get(label, label.replace("_", " "))
        localized_rows.append({"label": str(localized), "value": int(row["value"])})
    return localized_rows


def _media_opportunity_rows(
    request: Request,
    *,
    lang: str | None = None,
    limit: int = 500,
) -> list[OpportunityV1]:
    rows, _, _ = _query_opportunities_v1(
        request,
        lifecycle=None,
        min_score=0.0,
        include_irrelevant=False,
        limit=limit,
        offset=0,
        lang=lang,
    )
    return rows


def _observation_title(snapshot: dict[str, Any], lang: str) -> str:
    i18n = snapshot.get("i18n")
    localized = i18n.get(lang) if isinstance(i18n, dict) else None
    title = localized.get("title") if isinstance(localized, dict) else None
    return _display_text(title or snapshot.get("title"))


def _change_history_payload(
    request: Request,
    *,
    hours: int,
    limit: int,
    lang: str,
) -> dict[str, Any]:
    now = datetime.now(UTC)
    since_aware = now - timedelta(hours=hours)
    since = since_aware.replace(tzinfo=None)
    repository = _configured_repository()
    observations_since = getattr(repository, "observations_since", None)
    if not callable(observations_since):
        return {
            "schema_version": "qazfund-changes.v1",
            "available": False,
            "state": "collecting",
            "period_hours": hours,
            "period_from": since_aware.isoformat(),
            "period_to": now.isoformat(),
            "created": 0,
            "changed": 0,
            "items": [],
        }

    observations = list(observations_since(since, limit=limit))
    ledger_rows = list(
        observations_since(
            datetime(1970, 1, 1),
            limit=1,
            include_baselines=True,
        )
    )
    root_path = _root_path(request)
    items: list[dict[str, Any]] = []
    for observation in observations:
        snapshot_value = getattr(observation, "snapshot", None)
        snapshot = snapshot_value if isinstance(snapshot_value, dict) else {}
        dedup_key = str(getattr(observation, "dedup_key", "") or "")
        source_url = str(snapshot.get("source_url") or "")
        stable_id = uuid5(NAMESPACE_URL, dedup_key or source_url)
        observed_at = getattr(observation, "observed_at", None)
        if isinstance(observed_at, datetime):
            if observed_at.tzinfo is None:
                observed_at = observed_at.replace(tzinfo=UTC)
            observed_at_text = observed_at.isoformat()
        else:
            observed_at_text = None
        items.append(
            {
                "id": str(stable_id),
                "change_type": str(
                    getattr(observation, "change_type", "changed") or "changed"
                ),
                "observed_at": observed_at_text,
                "source": {
                    "id": str(getattr(observation, "source", "") or ""),
                    "name": _source_name(str(getattr(observation, "source", "") or "")),
                    "url": source_url,
                },
                "title": _observation_title(snapshot, lang),
                "changed_fields": list(
                    getattr(observation, "changed_fields", None) or []
                ),
                "content_hash": str(getattr(observation, "content_hash", "") or ""),
                "public_page": _public_url(
                    request,
                    root_path,
                    f"/opportunity/{stable_id}?lang={lang}",
                ),
                "api": _public_url(
                    request,
                    root_path,
                    f"/api/v1/opportunities/{stable_id}?lang={lang}",
                ),
            }
        )
    return {
        "schema_version": "qazfund-changes.v1",
        "available": bool(ledger_rows),
        "state": "ready" if ledger_rows else "collecting",
        "period_hours": hours,
        "period_from": since_aware.isoformat(),
        "period_to": now.isoformat(),
        "created": sum(row["change_type"] == "created" for row in items),
        "changed": sum(row["change_type"] == "changed" for row in items),
        "items": items,
    }


def _cached_insights_payload(
    request: Request,
    *,
    lang: str,
) -> dict[str, Any]:
    """Share one short-lived analytics snapshot between HTML and JSON routes."""
    active_lang = _public_lang(lang)
    root_path = _root_path(request)
    public_base_url = _public_root_base(request, root_path)
    cache_key = (active_lang, public_base_url)
    now = datetime.now(UTC)
    with _public_items_cache_lock:
        cached = _insights_cache.get(cache_key)
        if cached is not None and now - cached[0] < _INSIGHTS_CACHE_TTL:
            return cached[1]

    rows = list(
        _cached_public_v1_index(
            content_lang=active_lang,
            include_irrelevant=False,
            public_base_url=public_base_url,
        ).values()
    )
    current_ids = {
        item.id for item in _cached_current_catalog_items(content_lang=active_lang)
    }
    catalog_rows = [item for item in rows if item.id in current_ids]
    payload = build_insights_payload(
        rows,
        lang=active_lang,
        history=_change_history_payload(
            request,
            hours=24,
            limit=20,
            lang=active_lang,
        ),
        catalog_items=catalog_rows,
    )
    with _public_items_cache_lock:
        _insights_cache[cache_key] = (now, payload)
    return payload


@app.get("/api/v1", include_in_schema=False)
async def api_v1_index(request: Request) -> JSONResponse:
    root_path = _root_path(request)
    base = _public_root_base(request, root_path).rstrip("/")
    payload = {
        "schema_version": DATASET_SCHEMA_VERSION,
        "opportunity_schema_version": SCHEMA_VERSION,
        "routes": {
            "opportunities": f"{base}/api/v1/opportunities",
            "opportunities_ndjson": f"{base}/api/v1/opportunities.ndjson",
            "opportunity": f"{base}/api/v1/opportunities/{{id}}",
            "insights": f"{base}/api/v1/insights",
            "changes": f"{base}/api/v1/changes",
            "schema": f"{base}/api/v1/schema",
            "media_feed_json": f"{base}/media/v1/feed.json",
            "media_feed_rss": f"{base}/media/v1/feed.rss",
            "daily_digest_json": f"{base}/media/v1/digest/daily.json",
            "daily_digest_text": f"{base}/media/v1/digest/daily.txt",
            "qpost_drafts": f"{base}/media/v1/qpost/drafts.json",
        },
    }
    return _versioned_json_response(payload)


@app.get("/api/v1/changes")
async def api_v1_changes(
    request: Request,
    hours: int = Query(24, ge=1, le=24 * 90),
    limit: int = Query(100, ge=1, le=1000),
    lang: str | None = Query(None),
) -> JSONResponse:
    active_lang = _public_lang(lang)
    payload = _change_history_payload(
        request,
        hours=hours,
        limit=limit,
        lang=active_lang,
    )
    return _versioned_json_response(payload)


@app.get("/api/v1/insights")
async def api_v1_insights(
    request: Request,
    lang: str | None = Query(None),
) -> JSONResponse:
    active_lang = _public_lang(lang)
    return _versioned_json_response(_cached_insights_payload(request, lang=active_lang))


@app.get("/api/v1/schema")
async def api_v1_schema() -> JSONResponse:
    return _versioned_json_response(
        {
            "schema_version": SCHEMA_VERSION,
            "dataset_schema_version": DATASET_SCHEMA_VERSION,
            "opportunity": OpportunityV1.model_json_schema(),
        }
    )


@app.get("/api/v1/opportunities")
async def list_opportunities_v1(
    request: Request,
    tag: str | None = Query(None),
    q: str | None = Query(None, max_length=200),
    source: str | None = Query(None, max_length=120),
    lifecycle: str | None = Query(
        None,
        pattern="^(open|closing_soon|rolling|forecast|closed|awarded)$",
    ),
    region: str | None = Query(
        None,
        pattern="^(kazakhstan|central_asia|global)$",
    ),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    deadline_before: date | None = None,
    deadline_after: date | None = None,
    include_irrelevant: bool = False,
    limit: int = Query(50, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    lang: str | None = Query(None),
) -> JSONResponse:
    rows, total_count, _ = _query_opportunities_v1(
        request,
        tag=tag,
        q=q,
        source=source,
        lifecycle=lifecycle,
        region=region,
        min_score=min_score,
        deadline_before=deadline_before,
        deadline_after=deadline_after,
        include_irrelevant=include_irrelevant,
        limit=limit,
        offset=offset,
        lang=lang,
    )
    payload = {
        "schema_version": DATASET_SCHEMA_VERSION,
        "opportunity_schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset_revision": dataset_revision(rows),
        "total_count": total_count,
        "result_count": len(rows),
        "items": rows,
    }
    response = _versioned_json_response(payload)
    response.headers["X-Total-Count"] = str(total_count)
    response.headers["X-Result-Count"] = str(len(rows))
    return response


@app.get("/api/v1/opportunities.ndjson")
async def export_opportunities_v1_ndjson(
    request: Request,
    tag: str | None = Query(None),
    q: str | None = Query(None, max_length=200),
    source: str | None = Query(None, max_length=120),
    lifecycle: str | None = Query(
        None,
        pattern="^(open|closing_soon|rolling|forecast|closed|awarded)$",
    ),
    region: str | None = Query(
        None,
        pattern="^(kazakhstan|central_asia|global)$",
    ),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    deadline_before: date | None = None,
    deadline_after: date | None = None,
    include_irrelevant: bool = False,
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    lang: str | None = Query(None),
) -> Response:
    cached = _cached_ndjson_export(
        request,
        filename="qazfund-opportunities-v1.ndjson",
        prefix="qazfund-opportunities-v1",
    )
    if cached is not None:
        return cached
    rows, _, _ = _query_opportunities_v1(
        request,
        tag=tag,
        q=q,
        source=source,
        lifecycle=lifecycle,
        region=region,
        min_score=min_score,
        deadline_before=deadline_before,
        deadline_after=deadline_after,
        include_irrelevant=include_irrelevant,
        limit=limit,
        offset=offset,
        lang=lang,
    )
    last_modified = max(
        (item.timestamps.discovered_at for item in rows),
        default=None,
    )
    return _store_ndjson_export(
        request,
        rows=(item.model_dump(mode="json") for item in rows),
        filename="qazfund-opportunities-v1.ndjson",
        last_modified=last_modified,
        prefix="qazfund-opportunities-v1",
    )


@app.get("/api/v1/opportunities/{opportunity_id}", response_model=OpportunityV1)
async def get_opportunity_v1(
    request: Request,
    opportunity_id: UUID,
    lang: str | None = Query(None),
) -> OpportunityV1:
    return _find_opportunity_v1(request, opportunity_id, lang=lang)


@app.get("/media/v1/opportunities/{opportunity_id}/content.json")
async def opportunity_media_content(
    request: Request,
    opportunity_id: UUID,
    lang: str | None = Query(None),
) -> JSONResponse:
    item = _find_opportunity_v1(request, opportunity_id, lang=lang)
    return JSONResponse(
        jsonable_encoder(content_payload(item, lang=_public_lang(lang)))
    )


@app.get("/media/v1/opportunities/{opportunity_id}/citation.txt")
async def opportunity_media_citation(
    request: Request,
    opportunity_id: UUID,
    style: str = Query("citation", pattern="^(plain|markdown|citation|press)$"),
    lang: str | None = Query(None),
) -> Response:
    item = _find_opportunity_v1(request, opportunity_id, lang=lang)
    text = citation_text(item, style=cast(Any, style), lang=_public_lang(lang))
    return Response(text, media_type="text/plain; charset=utf-8")


@app.get("/media/v1/opportunities/{opportunity_id}/card.svg")
async def opportunity_media_card(
    request: Request,
    opportunity_id: UUID,
    card_format: str = Query("og", alias="format"),
    lang: str | None = Query(None),
) -> Response:
    if card_format not in CARD_FORMATS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    item = _find_opportunity_v1(request, opportunity_id, lang=lang)
    return Response(
        render_opportunity_card_svg(
            item,
            card_format=card_format,
            lang=_public_lang(lang),
        ),
        media_type="image/svg+xml",
    )


@app.get("/media/v1/charts/{chart_type}.json")
async def media_chart_json(
    request: Request,
    chart_type: str,
    lang: str | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
) -> JSONResponse:
    if chart_type not in CHART_TYPES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    active_lang = _public_lang(lang)
    rows = _localized_chart_rows(
        chart_rows(
            _media_opportunity_rows(request, lang=active_lang, limit=limit), chart_type
        ),
        lang=active_lang,
    )
    return JSONResponse(
        jsonable_encoder(
            {
                "schema_version": "qazfund-media-chart.v1",
                "chart_type": chart_type,
                "title": chart_title(chart_type, active_lang),
                "generated_at": datetime.now(UTC).isoformat(),
                "rows": rows,
            }
        )
    )


@app.get("/media/v1/charts/{chart_type}.csv")
async def media_chart_csv(
    request: Request,
    chart_type: str,
    lang: str | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
) -> Response:
    if chart_type not in CHART_TYPES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    active_lang = _public_lang(lang)
    rows = _localized_chart_rows(
        chart_rows(
            _media_opportunity_rows(request, lang=active_lang, limit=limit), chart_type
        ),
        lang=active_lang,
    )
    return Response(chart_csv(rows), media_type="text/csv; charset=utf-8")


@app.get("/media/v1/charts/{chart_type}.svg")
async def media_chart_svg(
    request: Request,
    chart_type: str,
    lang: str | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
) -> Response:
    if chart_type not in CHART_TYPES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    active_lang = _public_lang(lang)
    generated_at = datetime.now(UTC)
    rows = _localized_chart_rows(
        chart_rows(
            _media_opportunity_rows(request, lang=active_lang, limit=limit), chart_type
        ),
        lang=active_lang,
    )
    return Response(
        render_chart_svg(
            rows,
            title=chart_title(chart_type, active_lang),
            generated_at=generated_at,
        ),
        media_type="image/svg+xml",
    )


@app.get("/media/v1/feed.json")
async def media_feed_json(
    request: Request,
    lang: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> Response:
    active_lang = _public_lang(lang)
    root_path = _root_path(request)
    base = _public_root_base(request, root_path)
    payload = json_feed(
        _media_opportunity_rows(request, lang=active_lang, limit=limit),
        base_url=base,
        lang=active_lang,
    )
    return Response(
        json_dumps(payload),
        media_type="application/feed+json; charset=utf-8",
    )


@app.get("/media/v1/feed.rss")
async def media_feed_rss(
    request: Request,
    lang: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> Response:
    active_lang = _public_lang(lang)
    root_path = _root_path(request)
    base = _public_root_base(request, root_path)
    return Response(
        rss_feed(
            _media_opportunity_rows(request, lang=active_lang, limit=limit),
            base_url=base,
            generated_at=datetime.now(UTC),
            lang=active_lang,
        ),
        media_type="application/rss+xml; charset=utf-8",
    )


@app.get("/media/v1/digest/daily.json")
async def media_daily_digest_json(
    request: Request,
    lang: str | None = Query(None),
    limit: int = Query(12, ge=1, le=30),
) -> JSONResponse:
    active_lang = _public_lang(lang)
    history = _change_history_payload(
        request,
        hours=24,
        limit=limit,
        lang=active_lang,
    )
    payload = daily_digest_payload(history, lang=active_lang, limit=limit)
    payload["text"] = daily_digest_text(payload)
    return _versioned_json_response(payload)


@app.get("/media/v1/digest/daily.txt")
async def media_daily_digest_text(
    request: Request,
    lang: str | None = Query(None),
    limit: int = Query(12, ge=1, le=30),
) -> Response:
    active_lang = _public_lang(lang)
    history = _change_history_payload(
        request,
        hours=24,
        limit=limit,
        lang=active_lang,
    )
    payload = daily_digest_payload(history, lang=active_lang, limit=limit)
    return Response(
        daily_digest_text(payload) + "\n",
        media_type="text/plain; charset=utf-8",
    )


@app.get("/media/v1/qpost/drafts.json")
async def media_qpost_drafts(
    request: Request,
    lang: str | None = Query(None),
    template: str = Query("grant_day", pattern=f"^({'|'.join(QPOST_TEMPLATES)})$"),
    limit: int = Query(5, ge=1, le=12),
) -> JSONResponse:
    """Return source-grounded candidates that require manual review in QPost."""
    active_lang = _public_lang(lang)
    today = public_today()
    opportunities, _ = _query_opportunities(
        tag=None,
        q=None,
        source=None,
        lifecycle=None,
        region=None,
        min_score=0.3,
        deadline_before=None,
        deadline_after=today,
        include_irrelevant=False,
        limit=200,
        offset=0,
        lang=active_lang,
        compact=False,
    )
    payload = build_qpost_draft_feed(
        opportunities,
        base_url=_public_root_base(request, _root_path(request)),
        lang=active_lang,
        template=template,
        today=today,
        limit=limit,
    )
    response = _versioned_json_response(payload)
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response


@app.get("/opportunities", response_model=list[Opportunity])
async def list_opportunities(
    tag: str | None = Query(None),
    q: str | None = Query(None, max_length=200),
    source: str | None = Query(None, max_length=120),
    lifecycle: str | None = Query(
        None,
        pattern="^(open|closing_soon|rolling|forecast|closed|awarded)$",
    ),
    region: str | None = Query(
        None,
        pattern="^(kazakhstan|central_asia|global)$",
    ),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    deadline_before: date | None = None,
    deadline_after: date | None = None,
    include_irrelevant: bool = False,
    limit: int = Query(50, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    lang: str | None = Query(None),
    compact: bool = Query(False),
) -> Response:
    results, total_count = _query_opportunities(
        tag=tag,
        q=q,
        source=source,
        lifecycle=lifecycle,
        region=region,
        min_score=min_score,
        deadline_before=deadline_before,
        deadline_after=deadline_after,
        include_irrelevant=include_irrelevant,
        limit=limit,
        offset=offset,
        lang=lang,
        compact=compact,
    )
    return _opportunities_json_response(results, total_count=total_count)


@app.get("/opportunities/duplicate-candidates")
async def duplicate_candidates(
    min_score: float = Query(0.3, ge=0.0, le=1.0),
    limit: int = Query(200, ge=2, le=500),
    max_pairs: int = Query(100, ge=1, le=500),
    content_lang: str = Query("en", pattern="^(en|ru)$"),
) -> dict[str, Any]:
    """Return review-only duplicate candidates for public opportunity records."""

    items = [
        item
        for item in _cached_public_scope_items(content_lang)
        if float(item.score or 0.0) >= min_score
    ][:limit]
    if len(items) < 2:
        return {
            "schema_version": "duplicate_cluster.v1",
            "provider": "qazfund-local-fallback",
            "model": "duplicate-cluster-deterministic-v1",
            "quality_tier": "deterministic",
            "decision_ready": False,
            "item_count": len(items),
            "pair_count": 0,
            "cluster_count": 0,
            "pairs": [],
            "clusters": [],
        }
    return duplicate_cluster_envelope(items, max_pairs=max_pairs)


@app.get("/opportunities.ndjson", include_in_schema=True)
async def export_opportunities_ndjson(
    request: Request,
    tag: str | None = Query(None),
    q: str | None = Query(None, max_length=200),
    source: str | None = Query(None, max_length=120),
    lifecycle: str | None = Query(
        None,
        pattern="^(open|closing_soon|rolling|forecast|closed|awarded)$",
    ),
    region: str | None = Query(
        None,
        pattern="^(kazakhstan|central_asia|global)$",
    ),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    deadline_before: date | None = None,
    deadline_after: date | None = None,
    include_irrelevant: bool = False,
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    lang: str | None = Query(None),
    compact: bool = Query(False),
) -> Response:
    """Export the filtered public catalog as cache-aware newline-delimited JSON."""

    cached = _cached_ndjson_export(
        request,
        filename="qazfund-opportunities.ndjson",
        prefix="qazfund-opportunities",
    )
    if cached is not None:
        return cached
    items, _ = _query_opportunities(
        tag=tag,
        q=q,
        source=source,
        lifecycle=lifecycle,
        region=region,
        min_score=min_score,
        deadline_before=deadline_before,
        deadline_after=deadline_after,
        include_irrelevant=include_irrelevant,
        limit=limit,
        offset=offset,
        lang=lang,
        compact=compact,
    )
    rows: list[dict[str, Any]] = []
    for item in items:
        row = item.model_dump(mode="json")
        row["evidence_state"] = resolve_public_evidence_state(
            direct_source_url=item.source_url
        ).value
        rows.append(row)
    last_modified = max(
        (item.discovered_at for item in items),
        default=None,
    )
    return _store_ndjson_export(
        request,
        rows=rows,
        filename="qazfund-opportunities.ndjson",
        last_modified=last_modified,
        prefix="qazfund-opportunities",
    )


@app.head("/opportunities.ndjson", include_in_schema=False)
async def export_opportunities_ndjson_head() -> Response:
    return Response(
        status_code=200,
        media_type="application/x-ndjson; charset=utf-8",
        headers={"Cache-Control": _PUBLIC_DISCOVERY_CACHE},
    )


@app.head("/opportunities", include_in_schema=False)
async def list_opportunities_head(
    tag: str | None = Query(None),
    q: str | None = Query(None, max_length=200),
    source: str | None = Query(None, max_length=120),
    lifecycle: str | None = Query(
        None,
        pattern="^(open|closing_soon|rolling|forecast|closed|awarded)$",
    ),
    region: str | None = Query(
        None,
        pattern="^(kazakhstan|central_asia|global)$",
    ),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    deadline_before: date | None = None,
    deadline_after: date | None = None,
    include_irrelevant: bool = False,
    limit: int = Query(50, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    lang: str | None = Query(None),
    compact: bool = Query(False),
) -> Response:
    items, total_count = _query_opportunities(
        tag=tag,
        q=q,
        source=source,
        lifecycle=lifecycle,
        region=region,
        min_score=min_score,
        deadline_before=deadline_before,
        deadline_after=deadline_after,
        include_irrelevant=include_irrelevant,
        limit=limit,
        offset=offset,
        lang=lang,
        compact=compact,
    )
    return Response(
        status_code=200,
        media_type="application/json",
        headers={
            "X-Total-Count": str(total_count),
            "X-Result-Count": str(len(items)),
        },
    )


@app.get("/opportunities/{opportunity_id}", response_model=OpportunityDetail)
async def get_opportunity_detail(
    opportunity_id: UUID,
    lang: str | None = Query(None),
) -> OpportunityDetail:
    content_lang = _public_lang(lang)
    item = _find_opportunity(opportunity_id, content_lang=content_lang)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return await build_opportunity_detail(
        localize_opportunity(item, content_lang),
        lang=content_lang,
        allow_remote_fetch=False,
    )


@app.api_route(
    "/opportunities/{opportunity_id}/history.json",
    methods=["GET", "HEAD"],
    include_in_schema=False,
)
async def get_opportunity_history(
    request: Request,
    opportunity_id: UUID,
    lang: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> JSONResponse:
    """Return source-grounded public field changes for one opportunity."""

    content_lang = _public_lang(lang)
    item = _find_opportunity(opportunity_id, content_lang=content_lang)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    repository = _configured_repository()
    backend_available = repository is not None
    entries = (
        repository.history_for(item.fingerprint(), limit=limit)
        if repository is not None
        else []
    )
    root_path = _root_path(request)
    item_id = str(item.id)
    payload = build_history_snapshot(
        item=item,
        entries=entries,
        lang=content_lang,
        links={
            "current": _public_url(
                request,
                root_path,
                f"/opportunities/{item_id}?lang={content_lang}",
            ),
            "human": _public_url(
                request,
                root_path,
                f"/opportunity/{item_id}?lang={content_lang}",
            ),
        },
        backend_available=backend_available,
    )
    response = JSONResponse(payload)
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response


@app.head("/opportunities/{opportunity_id}", include_in_schema=False)
async def get_opportunity_detail_head(
    opportunity_id: UUID,
    lang: str | None = Query(None),
) -> Response:
    if _find_opportunity(opportunity_id, content_lang=_public_lang(lang)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return Response(status_code=200, media_type="application/json")


@app.get("/digest", response_model=Digest)
async def digest(
    tag: str | None = Query(None),
    min_score: float = Query(0.3, ge=0.0, le=1.0),
    limit: int = Query(10, ge=1, le=50),
    include_irrelevant: bool = False,
    lang: str | None = Query(None),
) -> Digest:
    content_lang = _public_lang(lang)
    today = public_today()
    items = _cached_public_scope_items(
        content_lang=content_lang, include_irrelevant=include_irrelevant
    )
    items = [item for item in items if _is_open(item, today)]
    if tag:
        items = [
            item for item in items if tag.lower() in (t.lower() for t in item.tags)
        ]
    items = [item for item in items if item.score >= min_score]
    items.sort(
        key=lambda item: (
            priority_score(item, today=today),
            item.score,
            item.discovered_at,
        ),
        reverse=True,
    )

    diversified = diversify_ranked_items(
        items,
        key=lambda item: item.source,
        max_per_key=2,
        limit=limit,
    )
    if len(diversified) < limit:
        selected = {item.id for item in diversified}
        diversified.extend(item for item in items if item.id not in selected)

    generated_at = datetime.now(UTC)
    return Digest(
        generated_at=generated_at,
        period_from=generated_at - timedelta(days=1),
        period_to=generated_at,
        items=[
            localize_opportunity(item, content_lang) for item in diversified[:limit]
        ],
        channel="api",
    )


@app.head("/digest", include_in_schema=False)
async def digest_head(
    tag: str | None = Query(None),
    min_score: float = Query(0.3, ge=0.0, le=1.0),
    limit: int = Query(10, ge=1, le=50),
    include_irrelevant: bool = False,
    lang: str | None = Query(None),
) -> Response:
    return Response(status_code=200, media_type="application/json")


@app.head("/sources", include_in_schema=False)
@app.head("/funders", include_in_schema=False)
@app.head("/api/v1", include_in_schema=False)
@app.head("/api/v1/schema", include_in_schema=False)
@app.head("/api/v1/opportunities", include_in_schema=False)
@app.head("/api/v1/opportunities.ndjson", include_in_schema=False)
@app.head("/api/v1/insights", include_in_schema=False)
@app.head("/api/v1/changes", include_in_schema=False)
async def public_machine_head(request: Request) -> Response:
    """Answer discovery probes without running catalog projections."""
    is_ndjson = request.url.path.endswith(".ndjson")
    headers = {
        "Cache-Control": (_PUBLIC_DISCOVERY_CACHE if is_ndjson else _PUBLIC_FAST_CACHE)
    }
    if request.url.path.startswith("/api/v1"):
        headers.update(
            {
                "X-Dataset-Schema-Version": DATASET_SCHEMA_VERSION,
                "X-Opportunity-Schema-Version": SCHEMA_VERSION,
            }
        )
    return Response(
        status_code=200,
        media_type=(
            "application/x-ndjson; charset=utf-8" if is_ndjson else "application/json"
        ),
        headers=headers,
    )
