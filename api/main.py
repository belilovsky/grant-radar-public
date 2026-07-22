"""FastAPI app for grant-radar."""

from __future__ import annotations

import os
import re
import threading
import unicodedata
from collections import Counter
from collections.abc import Awaitable, Callable, Iterable, Mapping
from contextlib import asynccontextmanager, suppress
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from hmac import compare_digest
from html import escape, unescape
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from pydantic import TypeAdapter
from qazstack.content import diversify_ranked_items
from qazstack.evidence import count_evidence_states, resolve_public_evidence_state
from qazstack.export import ndjson_response
from qazstack.opportunities import normalized_opportunity_status, public_lifecycle
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from api.avds import AVDS_CSS
from api.dashboard import (
    GOOGLE_SITE_VERIFICATION_CONTENT,
    GOOGLE_SITE_VERIFICATION_FILENAME,
    render_dashboard,
)
from api.ecosystem import (
    avds_ui_contract,
    ecosystem_manifest,
    qazstack_consumer_contract,
)
from api.error_page import render_not_found_page
from api.funder_page import render_funder_page
from api.operator_page import render_operator_page
from api.opportunity_detail import build_opportunity_detail
from api.opportunity_page import render_opportunity_page
from api.public_meta import OG_IMAGE_SVG
from api.status_page import render_status_page
from core.geofit import (
    is_excluded_for_kazakhstan_focus,
    is_relevant_for_kazakhstan_focus,
)
from core.localization import (
    _localized_value,
    localize_opportunity,
    normalize_content_lang,
)
from core.models import Digest, Opportunity, OpportunityDetail, OpportunityType
from core.nlp import clean_source_summary
from core.persistence import Repository
from core.pipeline import run_all
from core.repository_factory import make_repository
from core.scoring import priority_score, ranking_payload
from core.scoring import score as score_opportunity
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


@asynccontextmanager
async def _lifespan(app: FastAPI):
    _warm_public_sitemap_cache()
    _warm_public_items_cache()
    yield


app = FastAPI(
    title="QAZ.FUND",
    description=(
        "Public funding navigator for grants, subsidies, accelerators, and "
        "support programs in Kazakhstan"
    ),
    version="0.1.0",
    root_path=os.environ.get("ROOT_PATH", ""),
    lifespan=_lifespan,
    docs_url=None,
    redoc_url=None,
)

_MACHINE_ROUTE_PREFIXES = (
    "/.well-known",
    "/coverage",
    "/digest",
    "/funders",
    "/health",
    "/openapi.json",
    "/opportunities",
    "/operator/health",
    "/ready",
    "/refresh",
    "/site-discovery.json",
    "/sources",
)
_PUBLIC_FAST_CACHE = "public, max-age=60, stale-while-revalidate=300"
_PUBLIC_DISCOVERY_CACHE = "public, max-age=300, stale-while-revalidate=1800"
_PUBLIC_LONG_CACHE = "public, max-age=3600, stale-while-revalidate=86400"
_PUBLIC_FAST_CACHE_PATHS = {
    "/",
    "/.well-known/avds-ui-contract.json",
    "/.well-known/qazstack-consumer.json",
    "/.well-known/qdev-ecosystem.json",
    "/coverage",
    "/funders",
    "/opportunities",
}
_PUBLIC_DISCOVERY_CACHE_PATHS = {
    "/llms.txt",
    "/robots.txt",
    "/site-discovery.json",
    "/sitemap.xml",
    "/sources",
}
_PUBLIC_LONG_CACHE_PATHS = {
    "/favicon.ico",
    "/og-image.svg",
    f"/{GOOGLE_SITE_VERIFICATION_FILENAME}",
}
_OPPORTUNITY_LIST_ADAPTER = TypeAdapter(list[Opportunity])


@app.exception_handler(StarletteHTTPException)
async def public_http_exception_page(
    request: Request,
    exc: StarletteHTTPException,
) -> Response:
    """Keep API errors structured while giving browser 404s a useful exit."""

    accepts_html = "text/html" in request.headers.get("accept", "").lower()
    is_machine_route = request.url.path.startswith(_MACHINE_ROUTE_PREFIXES)
    if (
        exc.status_code != status.HTTP_404_NOT_FOUND
        or not accepts_html
        or is_machine_route
    ):
        return JSONResponse(
            {"detail": exc.detail},
            status_code=exc.status_code,
            headers=exc.headers,
        )
    active_lang = _public_lang(str(request.query_params.get("lang") or ""))
    response = HTMLResponse(
        render_not_found_page(lang=active_lang, root_path=_root_path(request)),
        status_code=exc.status_code,
        headers=exc.headers,
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
_public_items_cache_lock = threading.Lock()
_public_items_cache: dict[str, tuple[datetime, list[Opportunity]]] = {}
_public_scope_cache: dict[tuple[str, bool], tuple[datetime, list[Opportunity]]] = {}
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
        "project_status",
        "projectstatusdisplay",
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
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=(), payment=()",
    )
    if request.method in {"GET", "HEAD"}:
        if request.url.path in _PUBLIC_FAST_CACHE_PATHS:
            response.headers.setdefault("Cache-Control", _PUBLIC_FAST_CACHE)
        elif request.url.path in _PUBLIC_DISCOVERY_CACHE_PATHS:
            response.headers.setdefault("Cache-Control", _PUBLIC_DISCOVERY_CACHE)
        elif request.url.path in _PUBLIC_LONG_CACHE_PATHS:
            response.headers.setdefault("Cache-Control", _PUBLIC_LONG_CACHE)
    return response


def _database_url() -> str:
    return (
        os.environ.get("GRANT_RADAR_DB_URL") or os.environ.get("DATABASE_URL") or ""
    ).strip()


def _public_base_url() -> str:
    return os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")


def _allowed_hosts() -> list[str]:
    from urllib.parse import urlparse

    hosts = {
        "localhost",
        "127.0.0.1",
        "::1",
        "testserver",
        "qaz.fund",
    }
    configured = os.environ.get("GRANT_RADAR_ALLOWED_HOSTS", "")
    for raw in configured.split(","):
        host = raw.strip().lower()
        if host:
            hosts.add(host)
    public_base = _public_base_url()
    if public_base:
        host = (urlparse(public_base).hostname or "").strip().lower()
        if host:
            hosts.add(host)
    return sorted(hosts)


app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts())
app.add_middleware(GZipMiddleware, minimum_size=1_000, compresslevel=5)


def _admin_token() -> str:
    return os.environ.get("GRANT_RADAR_ADMIN_TOKEN", "").strip()


def _bearer_token(authorization: str | None) -> str:
    if not authorization:
        return ""
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        return ""
    return token.strip()


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


def _list_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        return [str(item) for item in value]
    return [str(value)]


def _display_text(value: Any) -> str:
    return re.sub(r"\s+", " ", unescape(str(value or ""))).strip()


def _display_summary(value: Any) -> str:
    return clean_source_summary(_display_text(value))


def _opportunity_type(raw: dict[str, Any]) -> OpportunityType:
    try:
        return OpportunityType(str(raw.get("type") or OpportunityType.GRANT))
    except ValueError:
        return OpportunityType.GRANT


def _fallback_summary(raw: dict[str, Any], content_lang: str = "en") -> str:
    raw_payload = raw.get("raw")
    source_raw = raw_payload if isinstance(raw_payload, dict) else raw
    agency = (
        source_raw.get("agencyName")
        or source_raw.get("agency")
        or source_raw.get("agencyCode")
    )
    close_date = source_raw.get("closeDate") or source_raw.get("deadline")
    language_candidates = _list_value(
        source_raw.get("language") or source_raw.get("languages")
    )
    normalized_lang = (
        normalize_content_lang(language_candidates[0])
        if language_candidates
        else normalize_content_lang(content_lang)
    )
    if agency or close_date:
        if normalized_lang == "en":
            parts = ["Opportunity notice"]
            if agency:
                parts.append(f"from {agency}")
            if close_date:
                parts.append(f"closing {close_date}")
        else:
            parts = ["Уведомление о возможности"]
            if agency:
                parts.append(f"от {agency}")
            if close_date:
                parts.append(f"сроком до {close_date}")
        return " ".join(parts) + "."
    return ""


def _public_raw(raw: dict[str, Any]) -> dict[str, Any]:
    nested_raw = raw.get("raw")
    if isinstance(nested_raw, dict) and "source_url" in raw and "discovered_at" in raw:
        return nested_raw
    if isinstance(nested_raw, dict) and {"type", "tags", "languages"}.issubset(
        raw.keys()
    ):
        return nested_raw
    return raw


def _stored_opportunity(row: Any, *, content_lang: str = "en") -> Opportunity:
    raw = getattr(row, "raw", None)
    if not isinstance(raw, dict):
        raw = {}

    dedup_key = str(getattr(row, "dedup_key", None) or getattr(row, "id", ""))
    source_url: Any = str(getattr(row, "source_url", None) or raw.get("url") or "")
    discovered_at = getattr(row, "discovered_at", None)
    if not isinstance(discovered_at, datetime):
        discovered_at = datetime.now(UTC)
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
        opportunity_status=getattr(row, "opportunity_status", None),
        lifecycle=getattr(row, "lifecycle", None),
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
    normalized_status = normalized_opportunity_status(opportunity)
    opportunity.funder_slug = opportunity.funder_slug or _slugify_funder(
        _funder_name(opportunity)
    )
    opportunity.opportunity_status = opportunity.opportunity_status or normalized_status
    opportunity.lifecycle = opportunity.lifecycle or public_lifecycle(opportunity)
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
    external_id = str(raw.get("external_id") or raw.get("reference") or "").strip()
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
                if _is_active_item(item)
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
            if _is_active_item(item)
        ],
        content_lang=content_lang,
    )


def _cached_public_items(content_lang: str = "en") -> list[Opportunity]:
    """Return a bounded-lifetime public read model for repeated web requests."""
    normalized_lang = _public_lang(content_lang)
    now = datetime.now(UTC)
    with _public_items_cache_lock:
        cached = _public_items_cache.get(normalized_lang)
        if cached is not None and now - cached[0] < _PUBLIC_ITEMS_CACHE_TTL:
            return list(cached[1])

    items = _stored_items(content_lang=normalized_lang)
    with _public_items_cache_lock:
        _public_items_cache[normalized_lang] = (now, items)
    return list(items)


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
        _coverage_cache = None


def _warm_public_items_cache() -> None:
    """Warm both dashboard languages before the first public visitor arrives."""
    for content_lang in ("en", "ru"):
        with suppress(Exception):
            _cached_public_items(content_lang)
            _cached_public_scope_items(content_lang)
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
    return item.model_copy(
        update={
            "raw": {
                **raw,
                "decision_readiness": readiness,
                "ranking": ranking_payload(ranking_subject or item),
            }
        }
    )


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
    return item.deadline is None or item.deadline >= today


def _normalized_token(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _source_name(source_slug: str) -> str:
    source_cls = PARSERS.get(source_slug)
    if source_cls is not None:
        return str(source_cls.name)
    return source_slug.replace("_", " ").strip() or "Unknown source"


def _funder_name(item: Opportunity) -> str:
    name = str(item.funder or "").strip()
    return name or _source_name(item.source)


def _slugify_funder(value: str) -> str:
    normalized = _normalized_token(value)
    ascii_value = (
        unicodedata.normalize("NFKD", normalized).encode("ascii", "ignore").decode()
    )
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    if slug:
        return slug
    return f"funder-{uuid5(NAMESPACE_URL, normalized or value).hex[:10]}"


def _funder_region_tokens(item: Opportunity) -> set[str]:
    tags = {_normalized_token(tag) for tag in item.tags if _normalized_token(tag)}
    raw = item.raw if isinstance(item.raw, dict) else {}
    blob = " ".join(
        [
            str(raw.get("country") or ""),
            str(raw.get("region") or ""),
            str(raw.get("borrower") or ""),
            str(item.summary or ""),
            str(item.title or ""),
        ]
    ).lower()
    regions: set[str] = set()
    if (
        "kazakhstan" in tags
        or "kazakhstan" in blob
        or "казахстан" in blob
        or "қазақстан" in blob
    ):
        regions.add("kazakhstan")
    if (
        "central_asia" in tags
        or "central_asia_eligible" in tags
        or "central asia" in blob
        or "центральн" in blob
    ):
        regions.add("central_asia")
    if "global" in tags and not regions:
        regions.add("global")
    if not regions:
        regions.add("global")
    return regions


def _opportunity_search_blob(item: Opportunity) -> str:
    """Build a deterministic text index from public opportunity fields."""
    raw = item.raw if isinstance(item.raw, dict) else {}
    values: list[Any] = [
        item.title,
        item.summary,
        item.funder,
        item.source,
        *item.tags,
        *item.eligibility,
        *(
            raw.get(key)
            for key in ("page_title", "listing_title", "reference", "agency", "country")
        ),
    ]
    return _normalized_token(" ".join(str(value or "") for value in values))


def _matches_opportunity_query(item: Opportunity, query: str) -> bool:
    tokens = [token for token in _normalized_token(query).split(" ") if token]
    if not tokens:
        return True
    blob = _opportunity_search_blob(item)
    return all(token in blob for token in tokens)


def _funder_tag_tokens(item: Opportunity) -> list[str]:
    ignored = {
        "rolling",
        "closed",
        "watchlist",
        "global",
        "kazakhstan",
        "central_asia",
        "central_asia_eligible",
    }
    return [
        _normalized_token(tag)
        for tag in item.tags
        if _normalized_token(tag) and _normalized_token(tag) not in ignored
    ]


def _build_funder_index(items: Iterable[Opportunity]) -> dict[str, dict[str, Any]]:
    today = date.today()
    groups: dict[str, dict[str, Any]] = {}
    for item in items:
        name = _funder_name(item)
        slug = _slugify_funder(name)
        group = groups.setdefault(
            slug,
            {
                "slug": slug,
                "name": name,
                "items": [],
                "types": Counter(),
                "tags": Counter(),
                "regions": Counter(),
                "sources": {},
                "open_items": 0,
                "closing_soon_items": 0,
                "rolling_items": 0,
                "forecast_items": 0,
                "closed_items": 0,
                "awarded_items": 0,
                "current_items": 0,
                "score_sum": 0.0,
                "next_deadline": None,
            },
        )
        group["items"].append(item)
        group["score_sum"] += float(item.score or 0.0)
        group["types"].update([item.type.value])
        group["tags"].update(_funder_tag_tokens(item))
        group["regions"].update(_funder_region_tokens(item))
        source_slug = str(item.source)
        if source_slug not in group["sources"]:
            group["sources"][source_slug] = {
                "slug": source_slug,
                "name": _source_name(source_slug),
                "base_url": getattr(PARSERS.get(source_slug), "base_url", ""),
            }
        lifecycle = public_lifecycle(item, today=today)
        count_key = f"{lifecycle}_items"
        group[count_key] = int(group.get(count_key, 0)) + 1
        if lifecycle in {"open", "closing_soon", "rolling"}:
            group["current_items"] += 1
        if item.deadline and item.deadline >= today:
            current_next_deadline = group["next_deadline"]
            if current_next_deadline is None or item.deadline < current_next_deadline:
                group["next_deadline"] = item.deadline

    for group in groups.values():
        items = cast(list[Opportunity], group["items"])
        items.sort(
            key=lambda row: (
                priority_score(row, today=today),
                row.score,
                row.discovered_at,
            ),
            reverse=True,
        )
        total_items = len(items)
        group["total_items"] = total_items
        group["avg_score"] = (
            round(group["score_sum"] / total_items, 3) if total_items else 0
        )
        group["top_tags"] = [
            tag for tag, _ in cast(Counter[str], group["tags"]).most_common(4)
        ]
        group["top_regions"] = [
            region for region, _ in cast(Counter[str], group["regions"]).most_common(3)
        ]
        group["top_types"] = [
            kind for kind, _ in cast(Counter[str], group["types"]).most_common(3)
        ]
        group["sources"] = sorted(
            cast(dict[str, dict[str, str]], group["sources"]).values(),
            key=lambda row: (row["name"], row["slug"]),
        )
    return groups


def _funder_index(content_lang: str = "en") -> dict[str, dict[str, Any]]:
    return _build_funder_index(
        _cached_public_scope_items(content_lang=content_lang, include_irrelevant=False)
    )


def _funder_payload(group: dict[str, Any]) -> dict[str, Any]:
    return {
        "slug": group["slug"],
        "name": group["name"],
        "total_items": group["total_items"],
        "current_items": group["current_items"],
        "open_items": group["open_items"],
        "closing_soon_items": group["closing_soon_items"],
        "rolling_items": group["rolling_items"],
        "forecast_items": group["forecast_items"],
        "closed_items": group["closed_items"],
        "awarded_items": group["awarded_items"],
        "avg_score": group["avg_score"],
        "next_deadline": group["next_deadline"],
        "top_tags": group["top_tags"],
        "top_regions": group["top_regions"],
        "top_types": group["top_types"],
        "sources": group["sources"],
    }


def _similarity_tokens(item: Opportunity) -> set[str]:
    raw = item.raw if isinstance(item.raw, dict) else {}
    tokens = {
        f"tag:{_normalized_token(tag)}" for tag in item.tags if _normalized_token(tag)
    }
    for key in ("country", "region", "borrower", "notice_type", "deadline_policy"):
        normalized = _normalized_token(raw.get(key))
        if normalized:
            tokens.add(f"{key}:{normalized}")
    return tokens


def _related_reason_key(target: Opportunity, candidate: Opportunity) -> str:
    if candidate.source == target.source:
        return "related_reason_source"
    if _normalized_token(candidate.funder) and _normalized_token(
        candidate.funder
    ) == _normalized_token(target.funder):
        return "related_reason_funder"
    if _similarity_tokens(target) & _similarity_tokens(candidate):
        return "related_reason_theme"
    return "related_reason_format"


def _related_relevance(target: Opportunity, candidate: Opportunity) -> float:
    """Return normalized item similarity without pretending personalization."""

    target_tokens = _similarity_tokens(target)
    candidate_tokens = _similarity_tokens(candidate)
    union = target_tokens | candidate_tokens
    jaccard = len(target_tokens & candidate_tokens) / len(union) if union else 0.0
    same_funder = bool(
        _normalized_token(target.funder)
        and _normalized_token(target.funder) == _normalized_token(candidate.funder)
    )
    same_type = target.type == candidate.type
    same_source = target.source == candidate.source
    value = (
        jaccard * 0.40
        + float(same_funder) * 0.30
        + float(same_type) * 0.15
        + float(same_source) * 0.10
        + float(candidate.score or 0.0) * 0.05
    )
    return round(min(1.0, value), 4)


def _related_opportunities(
    target: Opportunity,
    *,
    lang: str,
    limit: int = 3,
) -> list[tuple[Opportunity, str]]:
    today = date.today()
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
    today = date.today()
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
            if is_relevant_for_kazakhstan_focus(item) and item.score >= 0.3
        ]
        last_seen = max(
            (item.discovered_at for item in source_items),
            default=None,
        )
        last_checked = source_checks.get(slug)
        freshness_at = _newest_timestamp(last_seen, last_checked)
        freshness = _source_freshness(freshness_at)
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
            if is_relevant_for_kazakhstan_focus(item) and item.score >= 0.3
        ]
        last_seen = max((item.discovered_at for item in source_items), default=None)
        freshness = _source_freshness(last_seen)
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


def _source_freshness(last_seen: datetime | None) -> dict[str, Any]:
    """Return stable public freshness signals without exposing run errors."""
    if last_seen is None:
        return {"freshness_status": "unknown", "age_hours": None}
    normalized = _normalized_utc(last_seen)
    assert normalized is not None
    age_hours = max(0.0, (datetime.now(UTC) - normalized).total_seconds() / 3600)
    return {
        "freshness_status": "stale" if age_hours > 72 else "fresh",
        "age_hours": round(age_hours, 1),
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
            1 for row in source_rows if row.get("freshness_status") == "fresh"
        ),
        "stale_sources": sum(
            1 for row in source_rows if row.get("freshness_status") == "stale"
        ),
        "unknown_freshness_sources": sum(
            1 for row in source_rows if row.get("freshness_status") == "unknown"
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
    root_ru = _public_url_from_base(base_url, "/?lang=ru")
    root_en = _public_url_from_base(base_url, "/?lang=en")
    opportunities = sorted(
        [
            item
            for item in _cached_public_scope_items(content_lang="en")
            if _is_open(item, date.today())
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
                "ru": root_ru,
                "en": root_en,
                "x-default": root_ru,
            },
        ),
    ]

    for item in opportunities[:500]:
        ru_url = _public_url_from_base(base_url, f"/opportunity/{item.id}?lang=ru")
        en_url = _public_url_from_base(base_url, f"/opportunity/{item.id}?lang=en")
        rows.append(
            _sitemap_entry(
                ru_url,
                lastmod=_lastmod_for(item.discovered_at),
                changefreq="weekly",
                priority="0.8",
                alternates={
                    "ru": ru_url,
                    "en": en_url,
                    "x-default": ru_url,
                },
            )
        )

    for slug in sorted(funders.keys())[:200]:
        ru_url = _public_url_from_base(base_url, f"/funder/{slug}?lang=ru")
        en_url = _public_url_from_base(base_url, f"/funder/{slug}?lang=en")
        rows.append(
            _sitemap_entry(
                ru_url,
                changefreq="monthly",
                priority="0.5",
                alternates={
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
    public_items = _cached_public_items(content_lang="en")
    relevant_items = len(_cached_public_scope_items(content_lang="en"))
    source_count = len(
        {item.source for item in public_items if str(item.source).strip()}
    )
    lang = str(request.query_params.get("lang") or "").strip().lower()
    dashboard_lang = "en" if lang == "en" else "ru"
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


@app.api_route("/docs", methods=["GET", "HEAD"], include_in_schema=False)
async def swagger_docs(request: Request) -> HTMLResponse:
    root_path = _root_path(request).rstrip("/")
    docs_lang = _public_lang(str(request.query_params.get("lang") or "").strip())
    home_href = f"{root_path}/?lang={docs_lang}" if root_path else f"/?lang={docs_lang}"
    openapi_href = f"{root_path}/openapi.json" if root_path else "/openapi.json"
    docs_copy = {
        "ru": {
            "back": "Вернуться на сайт",
            "heading": "Документация API",
            "description": (
                "Интерактивное описание публичного API QAZ.FUND для каталогов, "
                "источников, возможностей и статуса данных."
            ),
        },
        "en": {
            "back": "Back to site",
            "heading": "API documentation",
            "description": (
                "Interactive reference for the public QAZ.FUND API covering the "
                "catalog, sources, opportunities, and data status."
            ),
        },
    }[docs_lang]
    canonical_href = _public_url(request, root_path, f"/docs?lang={docs_lang}")
    swagger = get_swagger_ui_html(
        openapi_url=openapi_href,
        title="QAZ.FUND API",
        swagger_favicon_url=f"{root_path}/favicon.ico" if root_path else "/favicon.ico",
        swagger_ui_parameters={"deepLinking": False},
    )
    page_header = (
        '<header class="qazfund-docs-header">'
        f'<a href="{escape(home_href, quote=True)}" '
        f'aria-label="{escape(str(docs_copy["back"]), quote=True)}">'
        f'← {escape(str(docs_copy["back"]))}</a>'
        f'<span class="qazfund-docs-title">{escape(str(docs_copy["heading"]))}</span>'
        "</header>"
    )
    head_markup = f"""
  <meta name="description" content="{escape(str(docs_copy["description"]), quote=True)}">
  <link rel="canonical" href="{escape(canonical_href, quote=True)}">
  <style>
    {AVDS_CSS}
    html, body {{
      margin: 0;
      background: var(--color-bg);
      color: var(--color-text);
      font-family: var(--av-font-sans);
    }}
    .qazfund-docs-header {{
      max-width: var(--av-container-dashboard);
      margin: 0 auto;
      padding: 14px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      border-bottom: 1px solid var(--color-border);
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
    .qazfund-docs-header a:focus-visible {{
      outline: 2px solid currentColor;
      outline-offset: 4px;
    }}
    .swagger-ui {{
      max-width: var(--av-container-dashboard);
      margin: 0 auto;
      font-family: var(--av-font-sans);
      color: var(--color-text);
    }}
    .swagger-ui .info {{ margin: 24px 0; }}
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
    @media (max-width: 520px) {{
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
      .qazfund-docs-header {{ align-items: flex-start; padding-inline: 16px; }}
      .qazfund-docs-title {{ max-width: 15ch; text-align: right; }}
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
        '<main id="swagger-ui"></main>',
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
    root_path = _root_path(request)
    site_origin = _site_origin(request, root_path)
    related_items = _related_opportunities(item, lang=content_lang)
    detail = await build_opportunity_detail(
        localize_opportunity(item, content_lang),
        lang=content_lang,
        allow_remote_fetch=False,
    )
    return HTMLResponse(
        render_opportunity_page(
            detail=detail,
            lang=content_lang,
            root_path=root_path,
            site_origin=site_origin,
            related_items=related_items,
        )
    )


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
    status_page = _public_url(request, root_path, "/status")
    coverage = _public_url(request, root_path, "/coverage")
    opportunities = _public_url(request, root_path, "/opportunities")
    opportunities_ndjson = _public_url(request, root_path, "/opportunities.ndjson")
    digest = _public_url(request, root_path, "/digest")
    return Response(
        "\n".join(
            [
                "# QAZ.FUND",
                (
                    "> Public funding navigator for grants, subsidies, accelerators, "
                    "and support programs relevant to Kazakhstan-focused teams "
                    "and institutions."
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
                f"- Source status page: {status_page}",
                "",
                "## Public data endpoints",
                f"- Coverage JSON: {coverage}",
                f"- Opportunities JSON: {opportunities}",
                f"- Opportunities NDJSON: {opportunities_ndjson}",
                "- Opportunity detail JSON: /opportunities/{id}?lang=ru|en",
                f"- Digest JSON: {digest}",
                "",
                "## AI consumption guidance",
                (
                    "- Prefer Opportunities NDJSON for bulk reads; it supports "
                    "cache validation and stable newline-delimited records."
                ),
                (
                    "- Use Site discovery JSON for route templates, query templates, "
                    "cache expectations, and contract URLs."
                ),
                (
                    "- Cache public discovery documents for at least 300 seconds "
                    "unless HTTP headers say otherwise."
                ),
                "",
                "## Public route templates",
                "- Opportunity page: /opportunity/{id}?lang=ru|en",
                "- Funder page: /funder/{slug}?lang=ru|en",
                "",
                "## Query hints",
                (
                    "- Opportunities filters: q, source, lifecycle, region, tag, "
                    "min_score, deadline_before, deadline_after, limit, offset, lang"
                ),
                "- Digest filters: limit, min_score, tag, lang",
                "",
                "## What this site is for",
                (
                    "- Track public grant, subsidy, accelerator, and "
                    "support-program opportunities."
                ),
                "- Help Kazakhstan-focused teams discover relevant funding routes.",
                "- Provide public summaries, funder pages, and opportunity pages.",
                "",
                "## Operator notes for AI systems",
                (
                    "- Treat QAZ.FUND as a public opportunity discovery surface, "
                    "not as an application processor."
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
    status_page = _public_url(request, root_path, "/status")
    coverage = _public_url(request, root_path, "/coverage")
    opportunities = _public_url(request, root_path, "/opportunities")
    opportunities_ndjson = _public_url(request, root_path, "/opportunities.ndjson")
    digest = _public_url(request, root_path, "/digest")
    ecosystem = _public_url(request, root_path, "/.well-known/qdev-ecosystem.json")
    release = _public_url(request, root_path, "/.well-known/release.json")
    qazstack_contract = _public_url(
        request, root_path, "/.well-known/qazstack-consumer.json"
    )
    avds_contract = _public_url(
        request, root_path, "/.well-known/avds-ui-contract.json"
    )
    payload = {
        "site": "QAZ.FUND",
        "type": "public-funding-navigator",
        "home": home,
        "sitemap": sitemap,
        "llms": llms,
        "api_docs": docs,
        "openapi": openapi_url,
        "source_status": status_page,
        "ecosystem": ecosystem,
        "release": release,
        "contracts": {
            "qazstack": qazstack_contract,
            "avds4": avds_contract,
        },
        "languages": ["ru", "en"],
        "routes": {
            "home": "/?lang={lang}",
            "coverage": "/coverage",
            "source_status": "/status?lang={lang}",
            "opportunities": "/opportunities?lang={lang}",
            "opportunities_ndjson": "/opportunities.ndjson?lang={lang}",
            "opportunity_api": "/opportunities/{id}?lang={lang}",
            "opportunity": "/opportunity/{id}?lang={lang}",
            "funder": "/funder/{slug}?lang={lang}",
            "digest": "/digest?lang={lang}",
        },
        "data_endpoints": {
            "coverage": coverage,
            "opportunities": opportunities,
            "opportunities_ndjson": opportunities_ndjson,
            "digest": digest,
        },
        "ai_consumption": {
            "preferred_bulk_export": opportunities_ndjson,
            "preferred_detail_template": "/opportunities/{id}?lang=ru|en",
            "preferred_human_template": "/opportunity/{id}?lang=ru|en",
            "recommended_language_order": ["ru", "en"],
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
                "raw.decision_readiness",
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
                "/opportunities.ndjson?lang=ru&limit=500&min_score=0.3"
            ),
            "digest_ai": "/digest?lang=ru&limit=5&tag=ai",
        },
        "capabilities": [
            "public opportunity pages",
            "public funder pages",
            "machine-readable opportunity api",
            "cache-aware ndjson export",
            "machine-readable source coverage",
            "public source freshness status",
            "official source links",
            "read-only public catalog",
            "qdev ecosystem contract",
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
    await coverage()
    return Response(status_code=200, media_type="application/json")


@app.api_route("/status", methods=["GET", "HEAD"], include_in_schema=False)
async def public_status_page(request: Request) -> HTMLResponse:
    """Render a public, cacheable source-freshness view."""
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
    active_lang = _public_lang(str(request.query_params.get("lang") or "").strip())
    response = HTMLResponse(
        render_operator_page(lang=active_lang, root_path=_root_path(request))
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
        if row.get("freshness_status") == "stale"
    ]
    failed_runs = [row for row in recent_runs if row.get("status") == "error"]
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
    return HTMLResponse(
        render_funder_page(
            funder=_funder_payload(group),
            live_items=live_items,
            archive_items=archive_items,
            lang=content_lang,
            root_path=root_path,
            site_origin=site_origin,
        )
    )


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
    items = _cached_public_scope_items(
        content_lang=content_lang, include_irrelevant=include_irrelevant
    )
    if tag:
        items = [o for o in items if tag.lower() in (t.lower() for t in o.tags)]
    if q:
        items = [item for item in items if _matches_opportunity_query(item, q)]
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
        items = [o for o in items if o.deadline is None or o.deadline >= deadline_after]
    total_count = len(items)
    today = date.today()
    items.sort(
        key=lambda item: (
            priority_score(item, today=today),
            item.score,
            item.discovered_at,
        ),
        reverse=True,
    )
    results = [
        _with_decision_readiness(
            localize_opportunity(item, content_lang),
            ranking_subject=item,
        )
        for item in items[offset : offset + limit]
    ]
    if compact:
        return [_compact_dashboard_item(item) for item in results], total_count
    return results, total_count


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
) -> Response:
    """Export the filtered public catalog as cache-aware newline-delimited JSON."""

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
        compact=False,
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
    return ndjson_response(
        request,
        rows,
        filename="qazfund-opportunities.ndjson",
        last_modified=last_modified,
        prefix="qazfund-opportunities",
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


@app.head("/opportunities/{opportunity_id}", include_in_schema=False)
async def get_opportunity_detail_head(
    opportunity_id: UUID,
    lang: str | None = Query(None),
) -> Response:
    await get_opportunity_detail(opportunity_id, lang=lang)
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
    today = date.today()
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
    await digest(
        tag=tag,
        min_score=min_score,
        limit=limit,
        include_irrelevant=include_irrelevant,
        lang=lang,
    )
    return Response(status_code=200, media_type="application/json")
