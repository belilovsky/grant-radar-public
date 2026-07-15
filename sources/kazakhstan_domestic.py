"""Curated Kazakhstan domestic support programs.

This source tracks official Kazakhstan grant, subsidy, tax-benefit and
state-support entry points. Most of these pages are evergreen services rather
than item-level grant feeds, so the parser keeps one normalized rolling record
per official program page.
"""

from __future__ import annotations

import hashlib
import re
import ssl
import tempfile
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import structlog
from bs4 import BeautifulSoup

from core.models import Opportunity, OpportunityType
from core.source_text import clean_plain_source_text as _clean_text
from sources.base import BaseSource

log = structlog.get_logger()

MAX_DETAIL_TEXT_CHARS = 12_000
MAX_DETAIL_SECTION_CHARS = 1_800
MAX_DETAIL_SECTIONS = 8
DETAIL_BLOCK_TAGS = {
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
_CYRILLIC_RE = re.compile(r"[А-Яа-яӘәҒғҚқҢңӨөҰұҮүҺһІіЁё]")
GOVKZ_SEO_HEADERS = {
    "User-Agent": "python-httpx/0.27.2",
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
}
QAZINDUSTRY_INTERMEDIATE_CA_URL = "http://crt.usertrust.com/GoGetSSLRSADVCA.crt"
_QAZINDUSTRY_CA_BUNDLE_PATH: str | None = None
DETAIL_NOISE_HEADINGS = {
    "другие новости по теме",
    "получите консультацию!",
    "получите консультацию",
    "other related news",
    "get a consultation!",
    "get a consultation",
}
SKIP_DETAIL_HEADING = "__skip_detail_section__"
DETAIL_NOISE_PHRASES = (
    "call center",
    "about the company",
    "corporate structure",
    "board of directors",
    "organizational structure",
    "corporate governance",
    "corporate documents",
    "policy in the field of quality",
    "external audit",
    "the ombudsman",
    "corporate reporting",
    "financial and annual reports",
    "financial and annual report",
    "sustainable development",
    "un sustainable development",
    "loan program",
    "our activities",
    "open an account online",
    "opening an online account",
    "settlement of problem debt",
    "corporate branches",
    "press center",
    "purchase",
    "jobs",
    "investor",
    "information for investors",
    "media about us",
    "other related news",
    "get a consultation",
)


@dataclass(frozen=True)
class DomesticProgram:
    url: str
    title: str
    summary: str
    tags: tuple[str, ...]
    type: OpportunityType = OpportunityType.GRANT
    rolling: bool = True
    retain_on_fetch_error: bool = True
    eligibility: tuple[str, ...] = ()
    amount_raw: str | None = None
    amount_min: Decimal | None = None
    amount_max: Decimal | None = None
    currency: str = "USD"
    application_url: str | None = None


DOMESTIC_PROGRAMS = (
    DomesticProgram(
        url="https://qazinn.kz/en/granty-qazinnovations",
        title="QazInnovations grants",
        summary=(
            "Official Kazakhstan innovation grant routes for commercialization "
            "of technologies, technology development and consortium projects."
        ),
        tags=(
            "grant",
            "innovation",
            "commercialization",
            "startup",
            "business_support",
            "qazinnovations",
        ),
    ),
    DomesticProgram(
        url="https://egov.kz/cms/ru/mobile-services/pass455_mir",
        title="Innovation grants for commercialization of technologies",
        summary=(
            "Official eGov service page for Kazakhstan innovation grants handled "
            "through QazInnovations and the digital development ministry."
        ),
        tags=(
            "grant",
            "innovation",
            "commercialization",
            "research",
            "qazinnovations",
            "egov",
        ),
    ),
    DomesticProgram(
        url="https://damu.kz/en/programmi/subsidy/sme_subsidy/",
        title="Damu subsidies for small businesses",
        summary=(
            "Damu SME support route with interest-rate subsidies and financing "
            "support for eligible small businesses."
        ),
        tags=("subsidy", "sme", "startup", "business_support", "damu"),
    ),
    DomesticProgram(
        url="https://damu.kz/en/programmi/subsidy/enterprise_development/",
        title="Damu Unified Integrated Programme subsidies",
        summary=(
            "Damu subsidy route under the unified entrepreneurship support "
            "programme for eligible Kazakhstan businesses."
        ),
        tags=("subsidy", "sme", "business_support", "damu"),
    ),
    DomesticProgram(
        url="https://damu.kz/en/programmi/guarantee/",
        title="Damu Fund guarantee programmes",
        summary=(
            "Official Damu guarantee-programmes entry point for business loans "
            "and access-to-finance support."
        ),
        tags=("loan_guarantee", "sme", "business_support", "damu"),
    ),
    DomesticProgram(
        url="https://damu.kz/en/programmi/guarantee/invest_projects/",
        title="Damu guarantees for investment projects",
        summary=(
            "Guarantee route for eligible Kazakhstan investment projects, "
            "including priority investment-project financing support."
        ),
        tags=("loan_guarantee", "investment", "sme", "business_support", "damu"),
    ),
    DomesticProgram(
        url="https://damu.kz/en/programmi/subsidy/inner_support/",
        title="Damu support for domestic trade entities",
        summary=(
            "Damu subsidy and guarantee support for eligible domestic trade "
            "entities in Kazakhstan."
        ),
        tags=("subsidy", "loan_guarantee", "trade", "business_support", "damu"),
    ),
    DomesticProgram(
        url="https://egov.kz/cms/ru/mobile-services/pass258_mne",
        title="Interest-rate subsidy service for entrepreneurs",
        summary=(
            "Official eGov service for subsidizing part of the interest rate on "
            "business loans and financial leasing under Kazakhstan entrepreneurship "
            "support programs."
        ),
        tags=(
            "subsidy",
            "preferential_financing",
            "leasing",
            "sme",
            "business_support",
            "egov",
        ),
        eligibility=(
            "Kazakhstan entrepreneurs applying for loan or financial-leasing interest-rate support",
        ),
        application_url="https://egov.kz/cms/ru/mobile-services/pass258_mne",
    ),
    DomesticProgram(
        url="https://egov.kz/cms/ru/articles/road_business_map",
        title="Road Map of Business support programme",
        summary=(
            "Official eGov overview of Kazakhstan business-support instruments, "
            "including loan and leasing subsidies, guarantees, grants and "
            "non-financial support routes."
        ),
        tags=(
            "subsidy",
            "loan_guarantee",
            "grant",
            "sme",
            "business_support",
            "egov",
        ),
        eligibility=("Kazakhstan SMEs and entrepreneurs under programme conditions",),
    ),
    DomesticProgram(
        url="https://egov.kz/cms/ru/services/state_support_measures/260_pass",
        title="State grants for social entrepreneurship",
        summary=(
            "Official eGov service for Kazakhstan state grants for social "
            "entrepreneurship entities, including online application steps and "
            "required documents."
        ),
        tags=(
            "grant",
            "social_entrepreneurship",
            "sme",
            "business_support",
            "egov",
        ),
        eligibility=(
            "Kazakhstan individual entrepreneurs and legal entities that are "
            "social-entrepreneurship SMEs",
        ),
        amount_raw="up to 5,000,000 KZT according to current service conditions",
        amount_max=Decimal("5000000"),
        currency="KZT",
        application_url="https://egov.kz/cms/ru/services/state_support_measures/260_pass",
    ),
    DomesticProgram(
        url="https://www.enbek.kz/ru/node/3481",
        title="State grant for startup business development",
        summary=(
            "Official Enbek page for grants issued free of charge for new "
            "business ideas and startup-business development through Business Enbek."
        ),
        tags=("grant", "startup", "employment", "business_support", "enbek"),
        eligibility=(
            "Eligible Kazakhstan individuals with a business project and "
            "programme certificate",
        ),
        amount_raw="up to 400 MRP",
    ),
    DomesticProgram(
        url="https://www.gov.kz/situations/501/1169?lang=ru",
        title="How to get a state grant to start a business",
        summary=(
            "Official gov.kz guidance on the conditions, categories and application "
            "process for Kazakhstan state grants for opening or developing a "
            "business."
        ),
        tags=("grant", "startup", "employment", "business_support", "govkz"),
        eligibility=(
            "Eligible socially vulnerable Kazakhstan citizens after training "
            "certificate and project defense",
        ),
        amount_raw="up to 400 MRP",
    ),
    DomesticProgram(
        url="https://baiterek.gov.kz/en/entrepreneurship-support/sme-support-and-development/",
        title="Baiterek SME support and development",
        summary=(
            "Official Baiterek overview of SME support routes through Damu, "
            "KazakhExport, Industrial Development Fund, QIC and related subsidiaries."
        ),
        tags=("sme", "preferential_financing", "business_support", "baiterek"),
    ),
    DomesticProgram(
        url=(
            "https://baiterek.gov.kz/en/pr/news/"
            "bgov-kz-the-unified-platform-for-financial-support-to-businesses"
        ),
        title="Bgov.kz unified financial support platform",
        summary=(
            "Official Baiterek launch page for the unified platform covering Damu, "
            "DBK, KazAgroFinance, Agrarian Credit Corporation, IDF, QIC and KazakhExport."
        ),
        tags=("sme", "preferential_financing", "business_support", "baiterek", "bgov"),
    ),
    DomesticProgram(
        url="https://egov.kz/cms/ru/articles/agriculture/subsidies_for_agriculture",
        title="Subsidies for crop production",
        summary=(
            "Official eGov guide to crop-production subsidies including seed, "
            "fertilizer, water and priority-crop support routes."
        ),
        tags=("subsidy", "agrotech", "agriculture", "crop_production", "egov"),
    ),
    DomesticProgram(
        url="https://egov.kz/cms/ru/articles/livestock/subsidies_for_animals",
        title="Subsidies for animal breeding",
        summary=(
            "Official eGov guide to livestock and animal-breeding subsidies for "
            "eligible Kazakhstan producers."
        ),
        tags=("subsidy", "vettech", "livestock", "animal_health", "egov"),
    ),
    DomesticProgram(
        url="https://egov.kz/cms/ru/articles/livestock/demands_for_subsidies",
        title="Criteria for producers applying for subsidies",
        summary=(
            "Official eGov guide to eligibility criteria and verification methods "
            "for agricultural subsidy applicants."
        ),
        tags=("subsidy", "agrotech", "vettech", "agriculture", "egov"),
    ),
    DomesticProgram(
        url="https://www.gov.kz/services/3794",
        title="APK loan guarantee and insurance subsidies",
        summary=(
            "Official Kazakhstan government service for subsidizing guarantees "
            "and insurance of loans for agro-industrial complex entities."
        ),
        tags=("subsidy", "loan_guarantee", "agrotech", "agriculture", "govkz"),
    ),
    DomesticProgram(
        url="https://www.gov.kz/services/3377",
        title="Priority crop production subsidies",
        summary=(
            "Official government service for subsidies supporting priority crop "
            "production, including perennial plantations."
        ),
        tags=("subsidy", "agrotech", "agriculture", "crop_production", "govkz"),
    ),
    DomesticProgram(
        url="https://www.gov.kz/services/3388",
        title="Breeding livestock productivity subsidies",
        summary=(
            "Official government service for subsidies supporting breeding "
            "livestock, productivity and livestock-product quality."
        ),
        tags=("subsidy", "vettech", "livestock", "animal_health", "govkz"),
    ),
    DomesticProgram(
        url="https://www.kaf.kz/en/media/news/85249/",
        title="KazAgroFinance Own Feed and Preferential Leasing",
        summary=(
            "Official KazAgroFinance application announcement for preferential "
            "agricultural machinery leasing and the Own Feed program."
        ),
        tags=(
            "preferential_financing",
            "leasing",
            "agrotech",
            "agriculture",
            "kazagrofinance",
        ),
    ),
    DomesticProgram(
        url="https://www.kaf.kz/en/media/news/82782/",
        title="KazAgroFinance preferential agricultural leasing",
        summary=(
            "Official KazAgroFinance page for concessional agricultural machinery "
            "leasing at preferential rates for Kazakhstan farmers."
        ),
        tags=(
            "preferential_financing",
            "leasing",
            "agrotech",
            "agriculture",
            "kazagrofinance",
        ),
    ),
    DomesticProgram(
        url=(
            "https://agrocredit.kz/en/main/press-center/news/"
            "agrarnaya-kreditnaya-korporatsiya-zapustila-novoe-napravlenie-"
            "kreditovaniya/"
        ),
        title="Agrarian Credit Corporation livestock lending",
        summary=(
            "Official Agrarian Credit Corporation program for preferential "
            "short-term lending to livestock and feedlot producers."
        ),
        tags=(
            "preferential_financing",
            "agrotech",
            "vettech",
            "livestock",
            "agrocredit",
        ),
    ),
    DomesticProgram(
        url=(
            "https://agrocredit.kz/en/main/press-center/news/"
            "agrarnaya-kreditnaya-korporatsiya-prodolzhaet-finansirovanie-"
            "vesenne-polevykh-rabot/"
        ),
        title="Agrarian Credit Corporation Ken Dala financing",
        summary=(
            "Official Agrarian Credit Corporation page for preferential lending "
            "for spring field and harvesting work under the Ken Dala program."
        ),
        tags=(
            "preferential_financing",
            "agrotech",
            "agriculture",
            "crop_production",
            "agrocredit",
        ),
    ),
    DomesticProgram(
        url="https://www.ncste.kz/en/competition",
        title="NCSTE science grant competitions",
        summary=(
            "Official NCSTE competition list for Kazakhstan science grants, "
            "young-scientist calls and commercialization financing."
        ),
        tags=("grant", "research", "science", "commercialization", "ncste"),
    ),
    DomesticProgram(
        url="https://cisc.kz/ru/category/malye-granty/",
        title="CISC small grants",
        summary=(
            "Official Center for Support of Civil Initiatives category for small "
            "grants supporting NGOs, volunteers and civic initiatives."
        ),
        tags=("grant", "ngo", "civic", "civil_society", "cisc"),
    ),
    DomesticProgram(
        url="https://qazindustry.gov.kz/ru/business_reimbursement",
        title="QazIndustry productivity reimbursement measures",
        summary=(
            "Official QazIndustry state-stimulation measures for partial cost "
            "reimbursement to improve industrial productivity."
        ),
        tags=("reimbursement", "industry", "digitalization", "business_support"),
    ),
    DomesticProgram(
        url="https://qazindustry.gov.kz/o-nas/business_support",
        title="QazIndustry business support measures",
        summary=(
            "Official QazIndustry overview of industrial state-stimulation and "
            "business-support measures."
        ),
        tags=("reimbursement", "industry", "business_support", "qazindustry"),
    ),
    DomesticProgram(
        url="https://export.gov.kz/export/support?lang=en",
        title="Kazakhstan export cost recovery",
        summary=(
            "Official export.gov.kz support page for partial cost recovery and "
            "export-promotion support for Kazakhstan producers."
        ),
        tags=("reimbursement", "export", "trade", "business_support", "qaztrade"),
    ),
    DomesticProgram(
        url=("https://egov.kz/cms/ru/services/state_support_measures/" "reimbursement"),
        title="Reimbursement of export-promotion costs",
        summary=(
            "Official eGov service for partial reimbursement of costs to promote "
            "domestic processed goods, works and services abroad."
        ),
        tags=("reimbursement", "export", "trade", "business_support", "egov"),
    ),
    DomesticProgram(
        url="https://kazakhexport.kz/en/services/",
        title="KazakhExport services",
        summary=(
            "Official KazakhExport service entry point for export-credit agency "
            "support, insurance and trade-finance instruments."
        ),
        tags=(
            "preferential_financing",
            "export",
            "trade",
            "business_support",
            "kazakhexport",
        ),
    ),
    DomesticProgram(
        url=(
            "https://egov.kz/cms/ru/services/state_support_measures/" "pass003mgp_miid"
        ),
        title="Reimbursement for technological-process improvement",
        summary=(
            "Official eGov service for reimbursement of costs for improving "
            "technological processes at eligible enterprises."
        ),
        tags=("reimbursement", "industry", "technology", "digitalization", "egov"),
    ),
    DomesticProgram(
        url="https://egov.kz/cms/ru/government-services/for_busunesses/pass1404004_mps",
        title="Reimbursement for adoption of digital technologies",
        summary=(
            "Official eGov service for reimbursement of expenses related to "
            "adoption of digital technologies."
        ),
        tags=("reimbursement", "industry", "digitalization", "technology", "egov"),
    ),
    DomesticProgram(
        url="https://www.kdb.kz/en/services/investment-projects/",
        title="Development Bank of Kazakhstan investment-project financing",
        summary=(
            "Official DBK financing route for large investment projects, export "
            "operations, project finance and long-term industrial development."
        ),
        tags=(
            "preferential_financing",
            "investment",
            "industry",
            "business_support",
            "kdb",
        ),
    ),
    DomesticProgram(
        url="https://www.kdb.kz/en/services/guarantee/",
        title="Development Bank of Kazakhstan guarantees",
        summary=(
            "Official DBK guarantee instrument for medium-sized businesses and "
            "priority investment projects financed through banks and financial institutions."
        ),
        tags=(
            "loan_guarantee",
            "investment",
            "industry",
            "business_support",
            "kdb",
        ),
    ),
    DomesticProgram(
        url=(
            "https://idfrk.kz/en/pr/news/"
            "industrial-development-fund-jsc-expands-leasing-program-for-the-"
            "construction-of-small-industrial-zon"
        ),
        title="Industrial Development Fund small industrial zones leasing",
        summary=(
            "Official IDF program page for leasing support for construction of "
            "small industrial zones across Kazakhstan."
        ),
        tags=(
            "leasing",
            "industry",
            "preferential_financing",
            "business_support",
            "idf",
        ),
    ),
    DomesticProgram(
        url="https://invest.gov.kz/invest-guide/support/investment-activity1/tax-incentives1/",
        title="Kazakhstan investment tax incentives",
        summary=(
            "Official KAZAKH INVEST guide to tax preferences available under "
            "Kazakhstan investment contracts and special investment projects."
        ),
        tags=("tax_benefit", "investment", "business_support", "invest_gov"),
    ),
    DomesticProgram(
        url="https://invest.gov.kz/doing-business-here/fez-and/the-list-of-sez-and/",
        title="Kazakhstan special economic zones",
        summary=(
            "Official KAZAKH INVEST guide to special economic zones and related "
            "investment benefits in Kazakhstan."
        ),
        tags=("tax_benefit", "investment", "sez", "business_support", "invest_gov"),
    ),
    DomesticProgram(
        url="https://astanahub.com/en/registration/",
        title="Astana Hub participant tax benefits",
        summary=(
            "Official Astana Hub participant-registration page for tax "
            "preferences, visa benefits and startup-development support."
        ),
        tags=("tax_benefit", "startup", "it", "business_support", "astana_hub"),
    ),
    DomesticProgram(
        url=(
            "https://qic.kz/en/novosti-i-insayty/"
            "qazaqstan-investment-corporation-signed-an-agreement-to-join-the-"
            "alem-ventures-fund-venture-fund/"
        ),
        title="QIC Alem Ventures Fund participation",
        summary=(
            "Official QIC page on participation in the Alem Ventures fund of funds "
            "supporting IT projects in Kazakhstan, Central Asia and adjacent markets."
        ),
        tags=("investment", "private_equity", "venture", "startup", "qic"),
    ),
    DomesticProgram(
        url="https://astanahub.com/en/faq/information",
        title="Astana Hub participant registration FAQ",
        summary=(
            "Official Astana Hub FAQ describing participant eligibility, tax "
            "preferences, application timing and required registration conditions."
        ),
        tags=("tax_benefit", "startup", "it", "business_support", "astana_hub"),
    ),
)

ACTIVE_DOMESTIC_URLS = frozenset(program.url for program in DOMESTIC_PROGRAMS)


def _detect_detail_language(text: str, html: str = "") -> str:
    soup_lang = ""
    try:
        soup = BeautifulSoup(html, "lxml")
        soup_lang = str((soup.html or {}).get("lang") or "").strip().lower()
    except Exception:  # noqa: BLE001
        soup_lang = ""
    if soup_lang.startswith("en"):
        return "en"
    if soup_lang.startswith(("ru", "kk")):
        return "ru"
    return "ru" if _CYRILLIC_RE.search(text) else "en"


def _candidate_container(soup: BeautifulSoup) -> Any:
    body = soup.body or soup
    candidates = [body]
    for selector in DETAIL_CONTAINER_SELECTORS:
        candidates.extend(soup.select(selector))
    return max(
        candidates,
        key=lambda node: len(_clean_text(node.get_text(" ", strip=True))),
        default=body,
    )


def _append_detail_section(
    sections: list[dict[str, str]],
    heading: str,
    chunks: list[str],
) -> bool:
    filtered_chunks = [
        chunk
        for chunk in chunks
        if chunk and not _is_noise_heading(chunk) and not _is_noise_chunk(chunk)
    ]
    text = "\n".join(filtered_chunks)
    text = text[:MAX_DETAIL_SECTION_CHARS].strip()
    if not text:
        return False
    if not heading.strip() and _is_noise_chunk(text):
        return False
    sections.append({"heading": heading.strip(), "text": text})
    return True


def _is_noise_heading(value: str) -> bool:
    normalized = _clean_text(value).lower()
    return normalized in DETAIL_NOISE_HEADINGS


def _is_noise_chunk(text: str) -> bool:
    normalized = _clean_text(text).lower()
    if not normalized:
        return True
    if len(normalized) <= 160 and any(
        phrase in normalized for phrase in DETAIL_NOISE_PHRASES
    ):
        return True
    hits = sum(1 for phrase in DETAIL_NOISE_PHRASES if phrase in normalized)
    if hits >= 3:
        return True
    return (
        len(normalized) > 400
        and hits >= 2
        and normalized.count(".") <= 2
        and normalized.count(":") <= 1
    )


def _extract_detail_sections(html: str) -> tuple[list[dict[str, str]], bool]:
    soup = BeautifulSoup(html, "lxml")
    for tag_name in DETAIL_BLOCK_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    container = _candidate_container(soup)
    sections: list[dict[str, str]] = []
    current_heading = ""
    current_chunks: list[str] = []
    excerpt_only = False
    seen_chunks: set[str] = set()

    for node in container.find_all(["h1", "h2", "h3", "p", "li", "tr"], limit=260):
        if len(sections) >= MAX_DETAIL_SECTIONS:
            excerpt_only = True
            break
        if node.name == "tr":
            text = _clean_text(
                " | ".join(
                    _clean_text(cell.get_text(" ", strip=True))
                    for cell in node.find_all(["th", "td"])
                )
            )
        else:
            text = _clean_text(node.get_text(" ", strip=True))
        if not text or len(text) < 3:
            continue
        normalized = text.lower()
        if normalized in seen_chunks:
            continue
        seen_chunks.add(normalized)
        if node.name in {"h1", "h2", "h3"}:
            if _is_noise_heading(text):
                if _append_detail_section(sections, current_heading, current_chunks):
                    current_chunks = []
                current_heading = SKIP_DETAIL_HEADING
                current_chunks = []
                continue
            if _append_detail_section(sections, current_heading, current_chunks):
                current_chunks = []
            current_heading = text
            continue
        if current_heading == SKIP_DETAIL_HEADING:
            continue
        if _is_noise_heading(current_heading) or _is_noise_chunk(text):
            continue
        current_chunks.append(text)

    if len(sections) < MAX_DETAIL_SECTIONS:
        _append_detail_section(sections, current_heading, current_chunks)

    if not sections:
        fallback = _clean_text(container.get_text(" ", strip=True))
        if fallback:
            sections.append(
                {"heading": "", "text": fallback[:MAX_DETAIL_SECTION_CHARS]}
            )
            excerpt_only = len(fallback) > MAX_DETAIL_SECTION_CHARS
    return sections, excerpt_only


def _detail_text_from_sections(sections: list[dict[str, str]]) -> str:
    blocks: list[str] = []
    for section in sections:
        text = _clean_text(str(section.get("text") or ""))
        if not text:
            continue
        heading = _clean_text(str(section.get("heading") or ""))
        blocks.append(f"{heading}\n{text}".strip() if heading else text)
    return "\n\n".join(blocks)[:MAX_DETAIL_TEXT_CHARS].strip()


def _drop_leading_navigation_section(
    sections: list[dict[str, str]],
) -> list[dict[str, str]]:
    if len(sections) < 2:
        return sections
    first = sections[0]
    if _clean_text(str(first.get("heading") or "")):
        return sections
    text = str(first.get("text") or "")
    has_following_heading = any(
        _clean_text(str(section.get("heading") or "")) for section in sections[1:]
    )
    if has_following_heading:
        return sections[1:]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 8:
        return sections
    short_lines = sum(1 for line in lines if len(line.split()) <= 6)
    punctuation_hits = text.count(".") + text.count("!") + text.count("?")
    if has_following_heading and short_lines >= 6 and punctuation_hits <= 3:
        return sections[1:]
    return sections


def _curated_detail_payload(program: DomesticProgram, status: str) -> dict[str, Any]:
    sections = [{"heading": "Overview", "text": program.summary}]
    if program.eligibility:
        sections.append(
            {
                "heading": "Eligibility",
                "text": "\n".join(program.eligibility),
            }
        )
    if program.amount_raw:
        sections.append({"heading": "Support amount", "text": program.amount_raw})
    return {
        "detail_fetch_status": status,
        "detail_excerpt_only": True,
        "detail_language": "en",
        "detail_sections": sections,
        "detail_text": _detail_text_from_sections(sections),
    }


def _amount_raw_payload(program: DomesticProgram) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if program.amount_raw:
        payload["amount_raw"] = program.amount_raw
    if program.amount_min is not None:
        payload["amount_min"] = str(program.amount_min)
    if program.amount_max is not None:
        payload["amount_max"] = str(program.amount_max)
    if program.amount_min is not None or program.amount_max is not None:
        payload["currency"] = program.currency
    return payload


def _detail_snapshot(html: str) -> dict[str, Any] | None:
    sections, excerpt_only = _extract_detail_sections(html)
    sections = _drop_leading_navigation_section(sections)
    detail_text = _detail_text_from_sections(sections)
    if not detail_text:
        return None
    encoded = html.encode("utf-8", errors="ignore")
    return {
        "detail_fetch_status": "ok",
        "detail_excerpt_only": excerpt_only
        or len(detail_text) >= MAX_DETAIL_TEXT_CHARS,
        "detail_fetched_at": datetime.now(timezone.utc).isoformat(),
        "detail_language": _detect_detail_language(detail_text, html),
        "detail_html_sha256": hashlib.sha256(encoded).hexdigest(),
        "detail_sections": sections[:MAX_DETAIL_SECTIONS],
        "detail_text": detail_text,
    }


def _html_title(html: str) -> str | None:
    match = re.search(
        r"<title[^>]*>(?P<title>.*?)</title>", html, re.IGNORECASE | re.DOTALL
    )
    if match is None:
        return None
    return _clean_text(re.sub(r"<[^>]+>", " ", match.group("title")))


def _is_unavailable_page(html: str) -> bool:
    title = (_html_title(html) or "").lower()
    text = _clean_text(re.sub(r"<[^>]+>", " ", html)).lower()
    return "technical difficulties" in title or (
        "experiencing technical difficulties" in text and "please try again" in text
    )


def _is_blocked_fetch(status_code: int, page_title: str | None) -> bool:
    title = (page_title or "").strip().lower()
    return status_code in {401, 403, 429} or title in {
        "access denied",
        "403 forbidden",
        "too many requests",
    }


def _needs_qazindustry_ca_fallback(url: str, exc: Exception) -> bool:
    hostname = (urlparse(url).hostname or "").lower()
    return (
        hostname == "qazindustry.gov.kz"
        and isinstance(exc, httpx.ConnectError)
        and "CERTIFICATE_VERIFY_FAILED" in repr(exc)
        and "unable to get local issuer certificate" in repr(exc)
    )


async def _qazindustry_ca_bundle_path() -> str:
    global _QAZINDUSTRY_CA_BUNDLE_PATH
    if _QAZINDUSTRY_CA_BUNDLE_PATH and Path(_QAZINDUSTRY_CA_BUNDLE_PATH).exists():
        return _QAZINDUSTRY_CA_BUNDLE_PATH

    import certifi

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        response = await client.get(QAZINDUSTRY_INTERMEDIATE_CA_URL)
        response.raise_for_status()
        cert_bytes = response.content

    if b"BEGIN CERTIFICATE" in cert_bytes:
        intermediate_pem = cert_bytes.decode("ascii", errors="ignore")
    else:
        intermediate_pem = ssl.DER_cert_to_PEM_cert(cert_bytes)

    base_bundle = Path(certifi.where()).read_text(encoding="utf-8")
    bundle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="grant-radar-qazindustry-ca-",
        suffix=".pem",
        delete=False,
    )
    with bundle:
        bundle.write(base_bundle)
        bundle.write("\n")
        bundle.write(intermediate_pem)
        bundle.write("\n")
    _QAZINDUSTRY_CA_BUNDLE_PATH = bundle.name
    return bundle.name


def _looks_like_unhydrated_govkz_shell(url: str, html: str) -> bool:
    if "gov.kz/" not in url:
        return False
    title = (_html_title(html) or "").lower()
    if not title.startswith("gov.kz - "):
        return False
    return not re.search(r"<(?:h1|h2|h3|p|li|tr)\b", html, re.IGNORECASE)


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        normalized = value.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def _program_tags(program: DomesticProgram, default_tags: Iterable[str]) -> list[str]:
    tags = [*default_tags, *program.tags]
    if program.rolling:
        tags.append("rolling")
    return _unique(tags)


class KazakhstanDomesticSupportSource(BaseSource):
    slug = "kazakhstan_domestic_support"
    name = "Kazakhstan domestic support"
    base_url = "https://egov.kz/"
    default_tags = ["kazakhstan", "domestic_support", "state_program"]
    programs = DOMESTIC_PROGRAMS

    def _opportunity(
        self,
        program: DomesticProgram,
        *,
        raw: dict[str, Any],
    ) -> Opportunity:
        return Opportunity(
            source=self.slug,
            source_url=program.url,  # type: ignore[arg-type]
            type=program.type,
            title=program.title,
            summary=program.summary,
            amount_min=program.amount_min,
            amount_max=program.amount_max,
            currency=program.currency,
            eligibility=list(program.eligibility),
            tags=_program_tags(program, self.default_tags),
            raw=raw,
        )

    async def _get_program_response(self, url: str) -> httpx.Response:
        try:
            response = await self.client.get(url)
        except httpx.ConnectError as exc:
            if not _needs_qazindustry_ca_fallback(url, exc):
                raise
            ca_bundle_path = await _qazindustry_ca_bundle_path()
            async with httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "User-Agent": (
                        "grant-radar/0.1 "
                        "(+https://github.com/belilovsky/grant-radar)"
                    )
                },
                follow_redirects=True,
                verify=ca_bundle_path,
            ) as client:
                response = await client.get(url)
        except (httpx.ReadTimeout, httpx.RemoteProtocolError):
            response = await self.client.get(url)
        if _looks_like_unhydrated_govkz_shell(url, response.text):
            return await self.client.get(url, headers=GOVKZ_SEO_HEADERS)
        return response

    async def fetch(self) -> AsyncIterator[Opportunity]:
        count = 0
        for program in self.programs:
            try:
                response = await self._get_program_response(program.url)
                if response.status_code == 404 or response.status_code >= 500:
                    response.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                if program.retain_on_fetch_error and not isinstance(
                    exc, httpx.HTTPStatusError
                ):
                    log.info(
                        "kazakhstan_domestic_support.fetch_retained",
                        url=program.url,
                        reason=type(exc).__name__,
                    )
                    count += 1
                    yield self._opportunity(
                        program,
                        raw={
                            "external_id": program.url,
                            "page_title": program.title,
                            "status_code": None,
                            "deadline_policy": ("rolling" if program.rolling else None),
                            **_amount_raw_payload(program),
                            "application_url": program.application_url,
                            "eligibility_raw": list(program.eligibility),
                            **_curated_detail_payload(program, "parse_error"),
                            "status_note": (
                                "official curated domestic-support page "
                                "retained; automated fetch failed with "
                                f"{type(exc).__name__}"
                            ),
                        },
                    )
                    continue
                log.warning(
                    "kazakhstan_domestic_support.fetch_failed",
                    url=program.url,
                    error=repr(exc),
                )
                continue
            if _is_unavailable_page(response.text):
                log.info(
                    "kazakhstan_domestic_support.unavailable_page",
                    url=program.url,
                )
                continue

            page_title = _html_title(response.text)
            raw = {
                "external_id": program.url,
                "page_title": page_title,
                "status_code": response.status_code,
                "deadline_policy": "rolling" if program.rolling else None,
                **_amount_raw_payload(program),
                "application_url": program.application_url,
                "eligibility_raw": list(program.eligibility),
            }
            if _is_blocked_fetch(response.status_code, page_title):
                raw.update(
                    {
                        "page_title": program.title,
                        **_curated_detail_payload(program, "blocked"),
                        "status_note": (
                            "official curated domestic-support page retained; "
                            "automated fetch was blocked or rate limited"
                        ),
                    }
                )
            else:
                snapshot = _detail_snapshot(response.text)
                if snapshot is not None:
                    raw.update(snapshot)
                else:
                    raw.update(_curated_detail_payload(program, "parse_error"))

            count += 1
            yield self._opportunity(program, raw=raw)

        log.info("kazakhstan_domestic_support.batch", count=count)


KazakhstanDomesticSupportParser = KazakhstanDomesticSupportSource
DOMESTIC_PROGRAM_BY_URL = {program.url: program for program in DOMESTIC_PROGRAMS}
DOMESTIC_PROGRAM_TAGS = {
    program.url: _program_tags(program, KazakhstanDomesticSupportSource.default_tags)
    for program in DOMESTIC_PROGRAMS
}
