"""Local detail payloads for Grant Radar opportunity views."""

from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
from datetime import datetime, timedelta, timezone
from html import unescape
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from core.localization import (
    has_localized_content,
    localized_section_list,
    localized_text,
    normalize_content_lang,
)
from core.models import (
    Opportunity,
    OpportunityDetail,
    OpportunityDetailSection,
    OpportunityMetadataField,
)
from sources import PARSERS

try:
    from datetime import UTC
except ImportError:  # pragma: no cover - Python < 3.11 compatibility
    UTC = timezone.utc

DETAIL_USER_AGENT = "grant-radar/0.1 (+https://github.com/belilovsky/grant-radar)"
DETAIL_CACHE_TTL = timedelta(hours=12)
MAX_DETAIL_HTML_BYTES = 750_000
MAX_DETAIL_TEXT_CHARS = 14_000
MAX_SECTION_TEXT_CHARS = 1_800
MAX_SECTION_COUNT = 8
MAX_DETAIL_REDIRECTS = 4
STRUCTURED_ONLY_SOURCES = frozenset(
    {
        "world_bank_kazakhstan",
        "adb_kazakhstan",
        "google_cloud_startup",
        "microsoft_founders_hub",
        "aws_activate",
        "nvidia_inception",
        "cloudflare_startups",
        "mongodb_startups",
        "google_org_ai_opportunity",
    }
)
SOURCE_BLOCK_TAGS = {
    "script",
    "style",
    "noscript",
    "svg",
    "form",
    "iframe",
    "button",
    "input",
    "select",
    "textarea",
    "footer",
}
DETAIL_CONTAINER_SELECTORS = (
    "main",
    "article",
    "[role='main']",
    ".content",
    ".entry-content",
    ".post-content",
    ".article-content",
    ".article-body",
    ".page-content",
    ".news-detail",
    ".news-item",
    ".detail",
)
REMOTE_DETAIL_NOISE_HEADINGS = {
    "другие новости по теме",
    "получите консультацию!",
    "получите консультацию",
    "other related news",
    "get a consultation!",
    "get a consultation",
}
REMOTE_DETAIL_NOISE_PHRASES = (
    "call center",
    "about the company",
    "strategy, mission, vision",
    "corporate structure",
    "the board of directors",
    "the board",
    "organizational structure",
    "subsidiaries",
    "corporate governance",
    "information on the activities of the board of directors",
    "corporate documents",
    "policy in the field of quality",
    "external audit",
    "the ombudsman",
    "corporate reporting",
    "financial and annual reports",
    "financial and annual report",
    "corporate events",
    "sustainable development",
    "un sustainable development",
    "sustainable development policy",
    "action plan",
    "compliance control",
    "anti-corruption compliance",
    "compliance and anti-corruption",
    "contacts and details",
    "press center",
    "open an account online",
    "fortebank",
    "получите консультацию",
)
_TAXONOMY_TOKEN_RE = re.compile(r"^[a-z0-9_][a-z0-9_\-]{1,31}$")
_LOWERCASE_TOKEN_RE = re.compile(r"^[a-z][a-z0-9_\-]{1,31}$")
_DETAIL_CACHE: dict[str, tuple[datetime, dict[str, Any]]] = {}
_SECTION_HEADINGS = {
    "en": {
        "overview": "Overview",
        "eligibility": "Eligibility",
        "source_status": "Source status",
    },
    "ru": {
        "overview": "Обзор",
        "eligibility": "Кто может подать заявку",
        "source_status": "Статус источника",
    },
}

_SECTION_HEADING_ALIASES = {
    "overview": "overview",
    "eligibility": "eligibility",
    "source status": "source_status",
}


def _clean_text(value: str) -> str:
    value = unescape(value or "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _localized_section_heading(heading: str, lang: str) -> str:
    cleaned = _clean_text(heading)
    if not cleaned:
        return ""
    normalized = cleaned.strip().lower().replace("_", " ")
    key = _SECTION_HEADING_ALIASES.get(normalized)
    if not key:
        return cleaned
    localized = _SECTION_HEADINGS.get(lang, {}).get(key)
    return str(localized or cleaned)


def _safe_url(value: Any) -> str | None:
    if value is None:
        return None
    parsed = urlparse(str(value).strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return parsed.geturl()


def _is_public_ip(address: ipaddress._BaseAddress) -> bool:
    return not (
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def _host_family(host: str) -> str:
    parts = [part for part in host.split(".") if part]
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host


def _allowed_host_families(item: Opportunity, source_url: str) -> set[str]:
    parsed = urlparse(source_url)
    host = (parsed.hostname or "").strip().lower()
    families = {_host_family(host)} if host else set()
    source_cls = PARSERS.get(item.source)
    if source_cls is not None:
        base_host = urlparse(str(getattr(source_cls, "base_url", ""))).hostname or ""
        base_host = base_host.strip().lower()
        if base_host:
            families.add(_host_family(base_host))
    return {family for family in families if family}


def _is_fetch_allowed(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").strip().lower()
    if parsed.scheme not in {"http", "https"} or not host:
        return False
    if host == "localhost" or host.endswith(".localhost"):
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return True
    return _is_public_ip(address)


def _is_allowed_host_family(url: str, allowed_families: set[str]) -> bool:
    if not allowed_families:
        return False
    host = (urlparse(url).hostname or "").strip().lower()
    if not host:
        return False
    return _host_family(host) in allowed_families


async def _resolves_to_public_ip(url: str) -> bool:
    host = (urlparse(url).hostname or "").strip().lower()
    if not host:
        return False
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        return _is_public_ip(ipaddress.ip_address(host))

    try:
        loop = asyncio.get_running_loop()
        addrinfo = await loop.getaddrinfo(
            host,
            None,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
        )
    except OSError:
        return False

    addresses: set[ipaddress._BaseAddress] = set()
    for entry in addrinfo:
        sockaddr = entry[4]
        if not sockaddr:
            continue
        try:
            addresses.add(ipaddress.ip_address(str(sockaddr[0])))
        except ValueError:
            return False
    return bool(addresses) and all(_is_public_ip(address) for address in addresses)


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _normalize_compare(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _unique_metadata(
    items: list[OpportunityMetadataField],
) -> list[OpportunityMetadataField]:
    out: list[OpportunityMetadataField] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        normalized = (item.key.strip().lower(), item.value.strip().lower())
        if not item.value.strip() or normalized in seen:
            continue
        seen.add(normalized)
        out.append(item)
    return out


def _metadata_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return ", ".join(_clean_text(str(item)) for item in value if str(item).strip())
    return _clean_text(str(value))


def _append_metadata(
    items: list[OpportunityMetadataField], key: str, value: Any
) -> None:
    normalized = _metadata_value(value)
    if not normalized:
        return
    items.append(OpportunityMetadataField(key=key, value=normalized))


def _amount_label(item: Opportunity) -> str:
    if item.amount_min is None and item.amount_max is None:
        return ""
    currency = _clean_text(item.currency or "")
    if item.amount_min is not None and item.amount_max is not None:
        if item.amount_min == item.amount_max:
            return f"{item.amount_min} {currency}".strip()
        return f"{item.amount_min} – {item.amount_max} {currency}".strip()
    if item.amount_min is not None:
        return f"from {item.amount_min} {currency}".strip()
    return f"up to {item.amount_max} {currency}".strip()


def _metadata_fields(item: Opportunity) -> list[OpportunityMetadataField]:
    raw = item.raw if isinstance(item.raw, dict) else {}
    fields: list[OpportunityMetadataField] = []
    _append_metadata(fields, "source", item.source)
    _append_metadata(fields, "funder", item.funder)
    _append_metadata(
        fields, "deadline", item.deadline.isoformat() if item.deadline else None
    )
    _append_metadata(fields, "deadline_raw", raw.get("deadline_raw"))
    _append_metadata(fields, "deadline_policy", raw.get("deadline_policy"))
    _append_metadata(fields, "amount", _amount_label(item))
    _append_metadata(fields, "amount_raw", raw.get("amount_raw"))
    _append_metadata(fields, "project_id", raw.get("project_id"))
    _append_metadata(fields, "reference", raw.get("reference"))
    _append_metadata(fields, "status", raw.get("status"))
    _append_metadata(fields, "notice_type", raw.get("notice_type"))
    _append_metadata(fields, "borrower", raw.get("borrower"))
    _append_metadata(fields, "country", raw.get("country"))
    _append_metadata(fields, "region", raw.get("region"))
    _append_metadata(fields, "board_approval", raw.get("boardapprovaldate"))
    _append_metadata(fields, "closing_date", raw.get("closingdate"))
    _append_metadata(fields, "page_title", raw.get("page_title"))
    _append_metadata(fields, "application_url", raw.get("application_url"))
    _append_metadata(fields, "status_note", raw.get("status_note"))
    return _unique_metadata(fields)


def _section_heading(key: str, lang: str) -> str:
    content_lang = normalize_content_lang(lang)
    return _SECTION_HEADINGS.get(content_lang, _SECTION_HEADINGS["ru"]).get(
        key,
        _SECTION_HEADINGS["ru"][key],
    )


def _structured_sections(
    item: Opportunity,
    *,
    lang: str = "en",
) -> list[OpportunityDetailSection]:
    raw = item.raw if isinstance(item.raw, dict) else {}
    sections: list[OpportunityDetailSection] = []
    if item.summary:
        sections.append(
            OpportunityDetailSection(
                heading=_section_heading("overview", lang),
                text=item.summary,
            )
        )
    if item.eligibility:
        eligibility_lines = [
            cleaned
            for entry in item.eligibility
            if (cleaned := _clean_text(str(entry)))
            and not _is_internal_eligibility_text(cleaned)
        ]
        if eligibility_lines:
            sections.append(
                OpportunityDetailSection(
                    heading=_section_heading("eligibility", lang),
                    text="\n".join(eligibility_lines),
                )
            )
    status_note = localized_text(
        raw,
        lang,
        "status_note",
        fallback=str(raw.get("status_note") or ""),
    )
    if _clean_text(status_note):
        sections.append(
            OpportunityDetailSection(
                heading=_section_heading("source_status", lang),
                text=_clean_text(status_note),
            )
        )
    return [section for section in sections if section.text.strip()]


def _candidate_container(soup: BeautifulSoup) -> BeautifulSoup:
    body = soup.body or soup
    candidates = [body]
    for selector in DETAIL_CONTAINER_SELECTORS:
        candidates.extend(soup.select(selector))
    return max(
        candidates,
        key=lambda node: len(_clean_text(node.get_text(" ", strip=True))),
        default=body,
    )


def _append_section(
    sections: list[OpportunityDetailSection],
    heading: str,
    chunks: list[str],
) -> bool:
    filtered_chunks = [
        chunk
        for chunk in chunks
        if chunk and not _is_noise_heading(chunk) and not _is_noise_chunk(chunk)
    ]
    text = "\n".join(filtered_chunks)
    text = text[:MAX_SECTION_TEXT_CHARS].strip()
    if not text:
        return False
    if _is_noise_heading(heading) or (not heading.strip() and _is_noise_chunk(text)):
        return False
    sections.append(OpportunityDetailSection(heading=heading.strip(), text=text))
    return True


def _is_noise_heading(value: str) -> bool:
    return _normalize_compare(value) in REMOTE_DETAIL_NOISE_HEADINGS


def _is_noise_chunk(text: str) -> bool:
    normalized = _normalize_compare(text)
    if not normalized:
        return False
    if any(phrase in normalized for phrase in REMOTE_DETAIL_NOISE_PHRASES):
        return True
    if _looks_like_taxonomy_chunk(normalized):
        return True
    hits = sum(1 for phrase in REMOTE_DETAIL_NOISE_PHRASES if phrase in normalized)
    return hits >= 2


def _looks_like_taxonomy_chunk(normalized: str) -> bool:
    if len(normalized) > 64 or any(mark in normalized for mark in ".!?,:;/()"):
        return False
    tokens = normalized.split()
    if not 1 <= len(tokens) <= 4:
        return False
    if not any("_" in token for token in tokens):
        return False
    return all(_TAXONOMY_TOKEN_RE.fullmatch(token) for token in tokens)


def _is_internal_eligibility_text(text: str) -> bool:
    normalized = text.strip().lower()
    if _looks_like_taxonomy_chunk(normalized):
        return True
    return " " not in normalized and bool(_LOWERCASE_TOKEN_RE.fullmatch(normalized))


def _extract_remote_sections(html: str) -> tuple[list[OpportunityDetailSection], bool]:
    soup = BeautifulSoup(html, "lxml")
    for tag_name in SOURCE_BLOCK_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    container = _candidate_container(soup)
    sections: list[OpportunityDetailSection] = []
    current_heading = ""
    current_chunks: list[str] = []
    excerpt_only = False
    seen_chunks: set[str] = set()

    for node in container.find_all(["h1", "h2", "h3", "p", "li", "tr"], limit=260):
        if len(sections) >= MAX_SECTION_COUNT:
            excerpt_only = True
            break
        if node.name == "tr":
            cell_text = " | ".join(
                _clean_text(cell.get_text(" ", strip=True))
                for cell in node.find_all(["th", "td"])
            )
            text = _clean_text(cell_text)
        else:
            text = _clean_text(node.get_text(" ", strip=True))
        if not text or len(text) < 3:
            continue
        normalized = _normalize_compare(text)
        if normalized in seen_chunks:
            continue
        seen_chunks.add(normalized)
        if node.name in {"h1", "h2", "h3"}:
            if _is_noise_heading(text):
                if _append_section(sections, current_heading, current_chunks):
                    current_chunks = []
                current_heading = ""
                current_chunks = []
                continue
            if _append_section(sections, current_heading, current_chunks):
                current_chunks = []
            current_heading = text
            continue
        if _is_noise_heading(current_heading) or _is_noise_chunk(text):
            continue
        current_chunks.append(text)
    if len(sections) < MAX_SECTION_COUNT and _append_section(
        sections, current_heading, current_chunks
    ):
        current_chunks = []

    if not sections:
        fallback = _clean_text(container.get_text(" ", strip=True))
        if fallback:
            sections.append(
                OpportunityDetailSection(
                    heading="",
                    text=fallback[:MAX_SECTION_TEXT_CHARS],
                )
            )
            excerpt_only = len(fallback) > MAX_SECTION_TEXT_CHARS
    return sections, excerpt_only


def _detail_text_from_sections(sections: list[OpportunityDetailSection]) -> str:
    blocks: list[str] = []
    for section in sections:
        block = section.text.strip()
        if section.heading.strip():
            block = f"{section.heading.strip()}\n{block}"
        if block:
            blocks.append(block)
    text = "\n\n".join(blocks).strip()
    return text[:MAX_DETAIL_TEXT_CHARS].strip()


def _drop_host_specific_navigation_section(
    sections: list[OpportunityDetailSection],
    source_url: str,
) -> list[OpportunityDetailSection]:
    if len(sections) < 2:
        return sections
    hostname = (urlparse(source_url).hostname or "").lower()
    if hostname not in {"agrocredit.kz", "www.agrocredit.kz"}:
        return sections
    first = sections[0]
    if first.heading.strip():
        return sections
    if any(section.heading.strip() for section in sections[1:]):
        return sections[1:]
    return sections


def _sanitize_detail_sections(
    sections: list[OpportunityDetailSection],
    *,
    source_url: str = "",
) -> list[OpportunityDetailSection]:
    cleaned: list[OpportunityDetailSection] = []
    for section in sections:
        heading = _clean_text(section.heading)
        text = _clean_text(section.text)
        if not text:
            continue
        if _is_noise_heading(heading):
            continue
        if not heading and _is_noise_chunk(text):
            continue
        cleaned.append(OpportunityDetailSection(heading=heading, text=text))
    return _drop_host_specific_navigation_section(cleaned, source_url)


def _detail_from_raw(
    raw: dict[str, Any],
    *,
    lang: str = "en",
    source_url: str = "",
) -> dict[str, Any] | None:
    detail_text = _clean_text(
        localized_text(
            raw, lang, "detail_text", fallback=str(raw.get("detail_text") or "")
        )
    )
    raw_sections = localized_section_list(raw, lang, "detail_sections")
    if not detail_text and not raw_sections:
        return None
    sections: list[OpportunityDetailSection] = []
    for section in raw_sections:
        text = _clean_text(str(section["text"]))
        if not text:
            continue
        sections.append(
            OpportunityDetailSection(
                heading=_localized_section_heading(str(section["heading"]), lang),
                text=text[:MAX_SECTION_TEXT_CHARS],
            )
        )
    original_sections = list(sections)
    sections = _sanitize_detail_sections(sections, source_url=source_url)
    sections_changed = [(section.heading, section.text) for section in sections] != [
        (section.heading, section.text) for section in original_sections
    ]
    if sections and (sections_changed or not detail_text):
        detail_text = _detail_text_from_sections(sections)
    elif not detail_text:
        return None
    return {
        "detail_fetch_status": _clean_text(str(raw.get("detail_fetch_status") or "ok"))
        or "ok",
        "detail_excerpt_only": bool(raw.get("detail_excerpt_only")),
        "detail_fetched_at": _parse_datetime(raw.get("detail_fetched_at")),
        "detail_sections": sections[:MAX_SECTION_COUNT],
        "detail_text": detail_text[:MAX_DETAIL_TEXT_CHARS],
    }


async def _fetch_remote_detail(
    item: Opportunity, *, lang: str = "en"
) -> dict[str, Any]:
    raw = item.raw if isinstance(item.raw, dict) else {}
    persisted = _detail_from_raw(raw, lang=lang, source_url=str(item.source_url))
    if persisted is not None:
        return persisted

    if item.source in STRUCTURED_ONLY_SOURCES:
        return {"detail_fetch_status": "structured_only"}

    source_url = _safe_url(item.source_url)
    allowed_families = _allowed_host_families(item, source_url or "")
    if (
        not source_url
        or not _is_fetch_allowed(source_url)
        or not _is_allowed_host_family(source_url, allowed_families)
        or not await _resolves_to_public_ip(source_url)
    ):
        return {"detail_fetch_status": "not_allowed"}

    cached = _DETAIL_CACHE.get(source_url)
    now = datetime.now(UTC)
    if cached is not None and cached[0] > now:
        return cached[1]

    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=False,
            headers={
                "User-Agent": DETAIL_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            },
        ) as client:
            current_url = source_url
            response: httpx.Response | None = None
            for _ in range(MAX_DETAIL_REDIRECTS + 1):
                if (
                    not _is_fetch_allowed(current_url)
                    or not _is_allowed_host_family(current_url, allowed_families)
                    or not await _resolves_to_public_ip(current_url)
                ):
                    return {"detail_fetch_status": "not_allowed"}

                response = await client.get(current_url)
                if response.status_code not in {301, 302, 303, 307, 308}:
                    break
                location = response.headers.get("location")
                if not location:
                    return {"detail_fetch_status": "parse_error"}
                current_url = _safe_url(urljoin(current_url, location)) or ""
            else:
                return {"detail_fetch_status": "blocked"}
    except httpx.HTTPError:
        return {"detail_fetch_status": "parse_error"}

    if response is None:
        return {"detail_fetch_status": "parse_error"}
    if response.status_code in {401, 403, 429}:
        return {"detail_fetch_status": "blocked"}
    if response.status_code >= 400:
        return {"detail_fetch_status": "parse_error"}
    if len(response.content) > MAX_DETAIL_HTML_BYTES:
        return {"detail_fetch_status": "too_large"}

    content_type = (response.headers.get("content-type") or "").lower()
    if "html" not in content_type and not content_type.startswith("text/"):
        return {"detail_fetch_status": "unsupported_media"}

    sections, excerpt_only = _extract_remote_sections(response.text)
    sections = _drop_host_specific_navigation_section(sections, source_url)
    detail_text = _detail_text_from_sections(sections)
    if not detail_text:
        return {"detail_fetch_status": "parse_error"}

    payload = {
        "detail_fetch_status": "ok",
        "detail_excerpt_only": excerpt_only
        or len(detail_text) >= MAX_DETAIL_TEXT_CHARS,
        "detail_fetched_at": now,
        "detail_sections": sections[:MAX_SECTION_COUNT],
        "detail_text": detail_text[:MAX_DETAIL_TEXT_CHARS],
    }
    _DETAIL_CACHE[source_url] = (now + DETAIL_CACHE_TTL, payload)
    return payload


def _merge_sections(
    structured: list[OpportunityDetailSection],
    remote: list[OpportunityDetailSection],
    *,
    summary: str,
) -> list[OpportunityDetailSection]:
    merged: list[OpportunityDetailSection] = []
    seen: set[tuple[str, str]] = set()
    normalized_summary = _normalize_compare(summary)

    for section in [*structured, *remote]:
        heading = _clean_text(section.heading)
        text = _clean_text(section.text)
        if not text:
            continue
        normalized = _normalize_compare(text)
        if normalized_summary and normalized == normalized_summary and merged:
            continue
        signature = (_normalize_compare(heading), normalized)
        if signature in seen:
            continue
        seen.add(signature)
        merged.append(
            OpportunityDetailSection(
                heading=heading,
                text=text[:MAX_SECTION_TEXT_CHARS],
            )
        )
        if len(merged) >= MAX_SECTION_COUNT:
            break
    return merged


async def build_opportunity_detail(
    item: Opportunity,
    *,
    lang: str = "en",
) -> OpportunityDetail:
    content_lang = normalize_content_lang(lang)
    raw = item.raw if isinstance(item.raw, dict) else {}
    application_url = _safe_url(raw.get("application_url"))
    structured_sections = _structured_sections(item, lang=content_lang)
    remote = await _fetch_remote_detail(item, lang=content_lang)
    has_localized_remote = has_localized_content(
        raw,
        content_lang,
        "detail_sections",
        "detail_text",
    )
    remote_sections = remote.get("detail_sections") or []
    if content_lang != "en" and not has_localized_remote:
        remote_sections = []
    merged_sections = _merge_sections(
        structured_sections,
        remote_sections,
        summary=item.summary,
    )
    detail_text = _clean_text(str(remote.get("detail_text") or ""))
    if content_lang != "en" and not has_localized_remote:
        detail_text = ""
    if not detail_text:
        detail_text = _detail_text_from_sections(merged_sections)

    detail_available = bool(detail_text or merged_sections)
    detail_fetch_status = str(remote.get("detail_fetch_status") or "structured_only")
    if content_lang != "en" and not has_localized_remote:
        detail_fetch_status = "structured_only"
    return OpportunityDetail(
        **item.model_dump(),
        application_url=application_url,
        detail_available=detail_available,
        detail_fetch_status=detail_fetch_status,
        detail_excerpt_only=bool(remote.get("detail_excerpt_only")),
        detail_fetched_at=remote.get("detail_fetched_at"),
        detail_text=detail_text,
        detail_sections=merged_sections,
        metadata=_metadata_fields(item),
    )
