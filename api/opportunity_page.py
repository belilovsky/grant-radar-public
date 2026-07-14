"""Server-rendered public opportunity pages for QAZ.FUND."""

from __future__ import annotations

import json
import re
from datetime import date
from enum import Enum
from html import escape
from urllib.parse import urlparse

from api.avds import AVDS_CSS, AVDS_FONT_HEAD
from api.dashboard import dashboard_copy
from api.public_meta import analytics_head_html, og_image_url
from core.models import Opportunity, OpportunityDetail, OpportunityMetadataField
from core.nlp import clean_source_summary

PUBLIC_METADATA_KEYS = frozenset(
    {
        "source",
        "funder",
        "deadline",
        "amount",
        "amount_raw",
        "country",
        "region",
        "project_id",
        "reference",
        "status",
        "notice_type",
        "borrower",
        "board_approval",
        "closing_date",
    }
)
HERO_METADATA_KEYS = frozenset({"source", "funder", "deadline"})
SOURCE_COLLAPSE_PARAGRAPH_THRESHOLD = 4
SOURCE_COLLAPSE_CHAR_THRESHOLD = 1600


def _absolute_href(origin: str, path: str) -> str:
    clean_origin = origin.rstrip("/")
    if path.startswith(("http://", "https://")):
        return path
    if not clean_origin:
        return path or "/"
    return f"{clean_origin}{path}"


def _page_path(root_path: str, opportunity_id: str, lang: str) -> str:
    base = root_path.rstrip("/")
    path = f"/opportunity/{opportunity_id}"
    if base:
        path = f"{base}{path}"
    return f"{path}?lang={lang}"


def _catalog_path(root_path: str, lang: str) -> str:
    base = root_path.rstrip("/")
    if base:
        return f"{base}/?lang={lang}#opportunities"
    return f"/?lang={lang}#opportunities"


def _host_label(value: str) -> str:
    try:
        host = urlparse(value).hostname or ""
    except ValueError:
        host = ""
    if host.startswith("www."):
        host = host[4:]
    return host or value


def _label_value(value: object, copy: dict[str, object]) -> str:
    raw_value = value.value if isinstance(value, Enum) else value
    raw = str(raw_value or "").strip()
    if not raw:
        return ""
    label_map_raw = copy.get("label_map")
    label_map = label_map_raw if isinstance(label_map_raw, dict) else {}
    normalized = raw.lower().replace("-", "_").replace(" ", "_")
    mapped = label_map.get(normalized) or label_map.get(raw.lower())
    if isinstance(mapped, str) and mapped.strip():
        return mapped.strip()
    return raw.replace("_", " ")


def _localized_item_value(
    item: Opportunity,
    field: str,
    lang: str,
    fallback: str,
) -> str:
    raw = item.raw if isinstance(item.raw, dict) else {}
    i18n = raw.get("i18n")
    localized = i18n.get(lang) if isinstance(i18n, dict) else None
    value = localized.get(field) if isinstance(localized, dict) else None
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback.strip()


def _has_cyrillic(value: str) -> bool:
    return bool(re.search(r"[А-Яа-яЁё]", value))


def _needs_russian_title_fallback(title: str, summary: str, lang: str) -> bool:
    if lang != "ru" or not title or not _has_cyrillic(summary):
        return False
    latin_count = len(re.findall(r"[A-Za-z]", title))
    cyrillic_count = len(re.findall(r"[А-Яа-яЁё]", title))
    return latin_count > cyrillic_count


def _summary_title_fallback(summary: str) -> str:
    sentence_candidates = re.split(r"(?<=[.!?])\s+", summary.strip(), maxsplit=3)
    candidate = sentence_candidates[0] if sentence_candidates else summary.strip()
    skip_prefixes = (
        "крайний срок",
        "срок подачи",
        "дата закрытия",
        "заявки принимаются до",
    )
    for sentence in sentence_candidates:
        normalized = sentence.strip().lower()
        if normalized and not normalized.startswith(skip_prefixes):
            candidate = sentence
            break
    candidate = candidate.rstrip(".!?").strip()
    if len(candidate) <= 120:
        return candidate
    return candidate[:117].rstrip() + "..."


def _clean_summary_text(text: str, *, title: str = "") -> str:
    return clean_source_summary(text, title=title)


def _seo_excerpt(text: str, *, max_length: int = 280) -> str:
    normalized = _clean_summary_text(text)
    if not normalized:
        return ""
    if len(normalized) <= max_length:
        return normalized
    window = normalized[: max_length + 1]
    cut = window.rfind(" ")
    if cut >= max_length * 0.6:
        window = window[:cut]
    else:
        window = normalized[:max_length]
    return window.rstrip(" -:;,") + "..."


def _format_deadline(value: date | None, lang: str, rolling_label: str) -> str:
    if value is None:
        return rolling_label
    if lang == "en":
        return value.strftime("%b %d, %Y")
    return value.strftime("%d.%m.%Y")


def _metadata_markup(
    metadata: list[OpportunityMetadataField],
    labels: dict[str, str],
    copy: dict[str, object],
    *,
    lang: str,
) -> str:
    if not metadata:
        return ""
    items = []
    source_value = next(
        (
            entry.value
            for entry in metadata
            if entry.key == "source" and str(entry.value or "").strip()
        ),
        "",
    )
    for entry in metadata:
        if entry.key not in PUBLIC_METADATA_KEYS:
            continue
        if (
            entry.key == "funder"
            and source_value
            and str(entry.value or "").strip().casefold()
            == str(source_value).strip().casefold()
        ):
            continue
        label = labels.get(entry.key, entry.key.replace("_", " ").title())
        value = _label_value(entry.value, copy)
        if entry.key in {"deadline", "closing_date", "board_approval"}:
            try:
                parsed_date = date.fromisoformat(str(entry.value).strip())
            except ValueError:
                parsed_date = None
            if parsed_date is not None:
                value = _format_deadline(parsed_date, lang, str(copy["open_rolling"]))
        items.append(
            """
            <div class="meta-item">
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
            """.format(
                label=escape(label),
                value=escape(value),
            )
        )
    return "".join(items)


def _json_ld(payload: dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")


def _opportunity_schema(
    *,
    detail: OpportunityDetail,
    page_title: str,
    display_title: str,
    summary: str,
    canonical_href: str,
    catalog_href: str,
    site_root_href: str,
    lang: str,
    funder_name: str,
) -> str:
    breadcrumb_id = f"{canonical_href}#breadcrumb"
    page_id = f"{canonical_href}#page"
    graph: list[dict[str, object]] = [
        {
            "@type": "BreadcrumbList",
            "@id": breadcrumb_id,
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "QAZ.FUND",
                    "item": catalog_href,
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": display_title,
                    "item": canonical_href,
                },
            ],
        },
        {
            "@type": "WebPage",
            "@id": page_id,
            "url": canonical_href,
            "name": page_title,
            "description": summary,
            "inLanguage": lang,
            "breadcrumb": {"@id": breadcrumb_id},
            "isPartOf": {"@id": f"{site_root_href}#website"},
            "about": {
                "@type": "Thing",
                "name": detail.title,
                "description": summary,
                "identifier": str(detail.id),
                "keywords": ", ".join(detail.tags),
                "sameAs": str(detail.source_url),
            },
        },
    ]
    if funder_name:
        graph.append(
            {
                "@type": "Organization",
                "@id": f"{canonical_href}#funder",
                "name": funder_name,
            }
        )
        graph[1]["publisher"] = {"@id": f"{canonical_href}#funder"}
    return _json_ld({"@context": "https://schema.org", "@graph": graph})


def _sections_markup(
    detail: OpportunityDetail,
    fallback_heading: str,
    *,
    title: str,
    expand_label: str = "",
) -> str:
    sections = [section for section in detail.detail_sections if section.text.strip()]
    if not sections:
        return ""
    blocks = []
    seen_sections: list[tuple[str, str]] = []
    for section in sections:
        if detail.eligibility and len(section.text) < 96 and "_" in section.text:
            continue
        normalized_heading = re.sub(
            r"\W+", " ", (section.heading or fallback_heading).casefold()
        ).strip()
        normalized_text = re.sub(r"\W+", " ", section.text.casefold()).strip()
        if any(
            normalized_heading == seen_heading
            and (
                normalized_text.startswith(seen_text)
                or seen_text.startswith(normalized_text)
            )
            for seen_heading, seen_text in seen_sections
            if normalized_text and seen_text
        ):
            continue
        if normalized_text:
            seen_sections.append((normalized_heading, normalized_text))
        paragraphs = "".join(
            "<p>"
            + escape(
                (_clean_summary_text(chunk, title=title) or chunk.strip()).replace(
                    "_", " "
                )
            )
            + "</p>"
            for chunk in _paragraph_chunks(section.text)
            if chunk.strip()
        )
        heading = escape(section.heading or fallback_heading)
        paragraph_count = paragraphs.count("<p>")
        should_collapse = (
            not section.heading.strip()
            or len(section.text) >= SOURCE_COLLAPSE_CHAR_THRESHOLD
            or paragraph_count >= SOURCE_COLLAPSE_PARAGRAPH_THRESHOLD
        )
        if should_collapse:
            blocks.append(
                """
                <details class="section-card source-disclosure">
                  <summary>
                    <span class="source-disclosure-title">{heading}</span>
                    <span class="source-disclosure-action">{action}</span>
                  </summary>
                  <div class="richtext">{paragraphs}</div>
                </details>
                """.format(
                    heading=heading,
                    action=escape(expand_label or fallback_heading),
                    paragraphs=paragraphs,
                )
            )
            continue
        blocks.append(
            """
            <section class="section-card">
              <h2>{heading}</h2>
              <div class="richtext">{paragraphs}</div>
            </section>
            """.format(
                heading=heading,
                paragraphs=paragraphs,
            )
        )
    return "".join(blocks)


def _paragraph_chunks(text: str, *, target_length: int = 520) -> list[str]:
    """Turn source walls of text into stable, readable paragraphs."""

    blocks: list[str] = []
    for raw_block in text.splitlines():
        normalized = re.sub(r"\s+", " ", raw_block).strip()
        if not normalized:
            continue
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZА-ЯӘҒҚҢӨҰҮҺІ0-9«])", normalized)
        current: list[str] = []
        current_length = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            projected = current_length + len(sentence) + (1 if current else 0)
            if current and projected > target_length:
                blocks.append(" ".join(current))
                current = []
                current_length = 0
            current.append(sentence)
            current_length += len(sentence) + (1 if current_length else 0)
        if current:
            blocks.append(" ".join(current))
    return blocks


def _term_blob(detail: OpportunityDetail) -> str:
    raw = detail.raw if isinstance(detail.raw, dict) else {}
    raw_bits: list[str] = []
    for value in raw.values():
        if isinstance(value, str):
            raw_bits.append(value)
        elif isinstance(value, (list, tuple, set)):
            raw_bits.extend(str(item) for item in value if isinstance(item, str))
    return " ".join(
        [
            detail.title,
            detail.summary,
            detail.source,
            detail.funder or "",
            " ".join(detail.tags),
            " ".join(detail.eligibility),
            " ".join(raw_bits),
        ]
    ).lower()


def _prepare_focus_key(detail: OpportunityDetail) -> str:
    terms = _term_blob(detail)
    type_value = detail.type.value
    if any(token in terms for token in ("tender", "procurement", "rfp", "eoi")):
        return "tender"
    if type_value in {"tender"}:
        return "tender"
    if any(
        token in terms
        for token in (
            "subsidy",
            "субсид",
            "tax_benefit",
            "loan_guarantee",
            "preferential_financing",
            "domestic_support",
            "egov",
            "bgov",
            "damu",
        )
    ):
        return "subsidy"
    if any(
        token in terms
        for token in ("science", "research", "commercialization", "lab", "university")
    ):
        return "science"
    if any(
        token in terms
        for token in ("ngo", "nonprofit", "civil_society", "media", "journalism")
    ):
        return "ngo"
    if type_value in {"accelerator", "cloud_credit"} or any(
        token in terms
        for token in ("startup", "accelerator", "cloud", "pitch", "pilot")
    ):
        return "startup"
    return "grant"


def _prepare_markup(
    detail: OpportunityDetail,
    *,
    copy: dict[str, object],
) -> str:
    focus_key = _prepare_focus_key(detail)
    focus_map = {
        "grant": ("prepare_grant_title", "prepare_grant_text"),
        "tender": ("prepare_tender_title", "prepare_tender_text"),
        "startup": ("prepare_startup_title", "prepare_startup_text"),
        "subsidy": ("prepare_subsidy_title", "prepare_subsidy_text"),
        "science": ("prepare_science_title", "prepare_science_text"),
        "ngo": ("prepare_ngo_title", "prepare_ngo_text"),
    }
    deadline_pair = (
        ("prepare_deadline_title", "prepare_deadline_text")
        if detail.deadline is not None
        else ("prepare_rolling_title", "prepare_rolling_text")
    )
    cards = [
        ("prepare_eligibility_title", "prepare_eligibility_text"),
        deadline_pair,
        focus_map[focus_key],
        ("prepare_source_title", "prepare_source_text"),
    ]
    card_markup = []
    for index, (title_key, text_key) in enumerate(cards, start=1):
        card_markup.append(
            """
            <article class="prepare-card">
              <span class="prepare-index">{index:02d}</span>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
            """.format(
                index=index,
                title=escape(str(copy[title_key])),
                text=escape(str(copy[text_key])),
            )
        )
    return """
    <section class="prepare-section">
      <div class="prepare-head">
        <span class="eyebrow">{eyebrow}</span>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      <div class="prepare-grid">{cards}</div>
    </section>
    """.format(
        eyebrow=escape(str(copy["prepare_section_eyebrow"])),
        title=escape(str(copy["prepare_section_title"])),
        description=escape(str(copy["prepare_section_description"])),
        cards="".join(card_markup),
    )


def _apply_markup(
    *,
    has_application_url: bool,
    copy: dict[str, object],
) -> str:
    first_step = (
        ("apply_step_open_apply_title", "apply_step_open_apply_text")
        if has_application_url
        else ("apply_step_open_source_title", "apply_step_open_source_text")
    )
    steps = [
        first_step,
        ("apply_step_check_title", "apply_step_check_text"),
        ("apply_step_pack_title", "apply_step_pack_text"),
        ("apply_step_submit_title", "apply_step_submit_text"),
    ]
    step_markup = []
    for index, (title_key, text_key) in enumerate(steps, start=1):
        step_markup.append(
            """
            <li class="apply-step">
              <span class="apply-index">{index:02d}</span>
              <div>
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
            </li>
            """.format(
                index=index,
                title=escape(str(copy[title_key])),
                text=escape(str(copy[text_key])),
            )
        )
    return """
    <section class="apply-section">
      <div class="apply-head">
        <span class="eyebrow">{eyebrow}</span>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      <ol class="apply-list">{steps}</ol>
    </section>
    """.format(
        eyebrow=escape(str(copy["apply_section_eyebrow"])),
        title=escape(str(copy["apply_section_title"])),
        description=escape(str(copy["apply_section_description"])),
        steps="".join(step_markup),
    )


def _related_markup(
    related_items: list[tuple[Opportunity, str]],
    *,
    lang: str,
    root_path: str,
    copy: dict[str, object],
) -> str:
    if not related_items:
        return ""
    cards: list[str] = []
    for item, reason_key in related_items:
        title = _localized_item_value(
            item,
            "title",
            lang,
            item.title or str(copy["detail_title_fallback"]),
        ) or str(copy["detail_title_fallback"])
        summary = _clean_summary_text(
            _localized_item_value(
                item,
                "summary",
                lang,
                item.summary or str(copy["no_summary"]),
            ),
            title=title,
        ) or str(copy["no_summary"])
        if _needs_russian_title_fallback(title, summary, lang):
            title = _summary_title_fallback(summary)
        href = escape(_page_path(root_path, str(item.id), lang), quote=True)
        reason = escape(str(copy.get(reason_key, copy["related_reason_theme"])))
        source_label = escape(item.funder or _label_value(item.source, copy))
        deadline_label = escape(
            _format_deadline(item.deadline, lang, str(copy["open_rolling"]))
        )
        cards.append(
            """
            <article class="related-card">
              <div class="related-top">
                <span class="related-reason">{reason}</span>
                <span class="related-deadline">{deadline}</span>
              </div>
              <h3><a href="{href}">{title}</a></h3>
              <p class="related-summary">{summary}</p>
              <div class="related-meta">
                <span>{source}</span>
                <a class="related-link" href="{href}">{action}</a>
              </div>
            </article>
            """.format(
                reason=reason,
                deadline=deadline_label,
                href=href,
                title=escape(title),
                summary=escape(summary),
                source=source_label,
                action=escape(str(copy["related_open"])),
            )
        )
    return """
    <section class="related-section">
      <div class="related-head">
        <span class="eyebrow">{eyebrow}</span>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      <div class="related-grid">{cards}</div>
    </section>
    """.format(
        eyebrow=escape(str(copy["related_section_eyebrow"])),
        title=escape(str(copy["related_section_title"])),
        description=escape(str(copy["related_section_description"])),
        cards="".join(cards),
    )


def render_opportunity_page(
    *,
    detail: OpportunityDetail,
    lang: str,
    root_path: str,
    site_origin: str,
    related_items: list[tuple[Opportunity, str]] | None = None,
) -> str:
    copy = dashboard_copy(lang)
    active_lang = str(copy["lang"])
    title = detail.title or str(copy["detail_title_fallback"])
    summary = _clean_summary_text(detail.summary, title=title) or str(
        copy["detail_empty"]
    )
    seo_summary = _seo_excerpt(summary) or summary
    page_title = f"{title} – QAZ.FUND"
    canonical_path = _page_path(root_path, str(detail.id), active_lang)
    canonical_href = escape(_absolute_href(site_origin, canonical_path), quote=True)
    ru_href = escape(
        _absolute_href(site_origin, _page_path(root_path, str(detail.id), "ru")),
        quote=True,
    )
    en_href = escape(
        _absolute_href(site_origin, _page_path(root_path, str(detail.id), "en")),
        quote=True,
    )
    catalog_href = escape(_catalog_path(root_path, active_lang), quote=True)
    source_href = escape(str(detail.source_url), quote=True)
    application_href = (
        escape(detail.application_url, quote=True) if detail.application_url else ""
    )
    raw_metadata_labels = copy.get("detail_meta_labels")
    metadata_labels = (
        raw_metadata_labels if isinstance(raw_metadata_labels, dict) else {}
    )
    secondary_metadata = [
        entry for entry in detail.metadata if entry.key not in HERO_METADATA_KEYS
    ]
    metadata_markup = _metadata_markup(
        secondary_metadata,
        metadata_labels,
        copy,
        lang=active_lang,
    )
    content_grid_class = (
        "content-grid" if metadata_markup else "content-grid content-grid--single"
    )
    sidebar_markup = (
        f"""
      <aside class="sidebar-card">
        <h2>{escape(str(copy["detail_meta_title"]))}</h2>
        <div class="meta-grid">{metadata_markup}</div>
      </aside>
        """
        if metadata_markup
        else ""
    )
    sections_markup = _sections_markup(
        detail,
        str(copy["detail_source_excerpt"]),
        title=title,
        expand_label=str(copy["detail_expand_source"]),
    )
    prepare_markup = _prepare_markup(detail, copy=copy)
    apply_markup = _apply_markup(
        has_application_url=bool(application_href),
        copy=copy,
    )
    related_markup = _related_markup(
        related_items or [],
        lang=active_lang,
        root_path=root_path,
        copy=copy,
    )
    source_label = escape(detail.funder or _label_value(detail.source, copy))
    deadline_label = escape(
        _format_deadline(detail.deadline, active_lang, str(copy["open_rolling"]))
    )
    source_host = escape(_host_label(str(detail.source_url)))
    format_label = escape(_label_value(detail.type, copy))
    og_locale = escape(active_lang.replace("-", "_") + "_KZ", quote=True)
    canonical_url = _absolute_href(site_origin, canonical_path)
    catalog_url = _absolute_href(site_origin, _catalog_path(root_path, active_lang))
    site_root_url = _absolute_href(
        site_origin,
        (
            f"{root_path.rstrip('/')}/?lang={active_lang}"
            if root_path.rstrip("/")
            else f"/?lang={active_lang}"
        ),
    )
    social_image = escape(og_image_url(site_origin, root_path), quote=True)
    analytics_head = analytics_head_html()
    ru_lang_class = "active" if active_lang == "ru" else ""
    en_lang_class = "active" if active_lang == "en" else ""
    eligibility = [
        escape(_label_value(value, copy))
        for value in detail.eligibility
        if isinstance(value, str) and value.strip()
    ]
    eligibility_markup = "".join(
        f'<span class="pill">{value}</span>' for value in eligibility[:6]
    )
    application_button = (
        """
        <a class="button slim" href="{href}" target="_blank" rel="noopener">
          {label}
        </a>
        """.format(
            href=application_href,
            label=escape(str(copy["detail_open_application"])),
        )
        if application_href
        else ""
    )
    empty_markup = ""
    if not metadata_markup and not sections_markup:
        empty_markup = (
            f'<div class="empty-state">{escape(str(copy["detail_empty"]))}</div>'
        )
    html_attrs = (
        f'lang="{escape(active_lang, quote=True)}" '
        'data-avds="grant-radar" data-av-theme="light" data-theme="light"'
    )
    deadline_meta_label = escape(str(metadata_labels.get("deadline", "Deadline")))
    schema_json = _opportunity_schema(
        detail=detail,
        page_title=page_title,
        display_title=title,
        summary=seo_summary,
        canonical_href=canonical_url,
        catalog_href=catalog_url,
        site_root_href=site_root_url,
        lang=active_lang,
        funder_name=detail.funder or "",
    )

    return f"""<!doctype html>
<html {html_attrs}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(page_title)}</title>
  <meta name="description" content="{escape(seo_summary, quote=True)}">
  <link rel="canonical" href="{canonical_href}">
  <link rel="alternate" hreflang="ru" href="{ru_href}">
  <link rel="alternate" hreflang="en" href="{en_href}">
  <link rel="alternate" hreflang="x-default" href="{ru_href}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{escape(page_title, quote=True)}">
  <meta property="og:description" content="{escape(seo_summary, quote=True)}">
  <meta property="og:url" content="{canonical_href}">
  <meta property="og:image" content="{social_image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:locale" content="{og_locale}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{escape(page_title, quote=True)}">
  <meta name="twitter:description" content="{escape(seo_summary, quote=True)}">
  <meta name="twitter:image" content="{social_image}">
  <script type="application/ld+json">{schema_json}</script>
{analytics_head}
{AVDS_FONT_HEAD}
  <style>
{AVDS_CSS}
    :root {{
      color-scheme: light;
      --bg: var(--color-bg);
      --surface: var(--color-surface);
      --surface-subtle: var(--color-bg-subtle);
      --surface-raised: var(--color-surface-raised);
      --surface-wash: color-mix(in oklab, var(--surface), var(--surface-subtle) 42%);
      --accent-wash: color-mix(in oklab, var(--surface), var(--brand-soft) 24%);
      --text: var(--color-text);
      --muted: var(--color-text-muted);
      --line: var(--color-border);
      --line-strong: var(--color-border-strong);
      --brand: var(--color-accent);
      --brand-soft: var(--color-accent-subtle);
      --success: var(--color-success);
      --success-soft: var(--color-success-subtle);
      --radius: var(--av-radius-lg);
      --shadow: var(--shadow-md);
      --container-max: min(1180px, calc(100% - 32px));
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: var(--av-font-sans);
      font-size: var(--av-text-base);
      line-height: var(--av-leading-normal);
    }}
    a {{ color: inherit; text-decoration: none; }}
    .shell {{
      width: var(--container-max);
      margin: 0 auto;
      padding: 16px 0 36px;
    }}
    .topbar {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 16px;
    }}
    .breadcrumbs {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: var(--av-text-sm);
    }}
    .breadcrumbs a:hover {{
      color: var(--brand);
    }}
    .lang-switch {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }}
    .lang-switch a {{
      min-width: 34px;
      padding: 6px 8px;
      border-bottom: 2px solid transparent;
      color: var(--muted);
      text-align: center;
      font-size: var(--av-text-xs);
      font-weight: 700;
    }}
    .lang-switch a.active {{
      border-bottom-color: var(--brand);
      color: var(--text);
    }}
    .hero {{
      display: grid;
      gap: 12px;
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-md);
      background: var(--surface);
      box-shadow: var(--av-shadow-xs);
      margin-bottom: 12px;
    }}
    .eyebrow {{
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-family: var(--font-sans);
      font-weight: 650;
      text-transform: none;
      letter-spacing: 0;
    }}
    .hero h1 {{
      margin: 0;
      max-width: 30ch;
      font-size: clamp(27px, 2.8vw, 36px);
      line-height: 1.06;
      text-wrap: balance;
    }}
    .summary {{
      margin: 0;
      max-width: 64ch;
      color: color-mix(in oklab, var(--text), var(--muted) 35%);
      font-size: 15px;
      line-height: 1.55;
    }}
    .hero-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.7fr) minmax(230px, 0.62fr);
      gap: 18px;
      align-items: start;
    }}
    .hero-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: var(--av-control-height-md);
      padding: 0 14px;
      border-radius: var(--av-radius-md);
      border: 1px solid var(--line);
      background: var(--surface);
      font-weight: 600;
    }}
    .button.primary {{
      border-color: color-mix(in oklab, var(--brand), black 12%);
      background: var(--brand);
      color: white;
    }}
    .button.slim {{
      min-height: var(--av-control-height-sm);
      background: color-mix(in oklab, var(--surface), white 14%);
    }}
    .hero-stats {{
      display: grid;
      gap: 8px;
      padding: 2px 0 2px 16px;
      border: 0;
      border-left: 1px solid var(--line);
      border-radius: 0;
      background: transparent;
    }}
    .hero-stats > div {{
      display: grid;
      gap: 2px;
    }}
    .hero-stats strong {{
      font-size: var(--av-text-base);
      line-height: 1.15;
    }}
    .metric {{
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-left: 3px solid var(--brand);
      border-radius: var(--av-radius-md);
      background: rgb(255 255 255 / 0.56);
      box-shadow: var(--av-shadow-xs);
    }}
    .metric span {{
      display: block;
      margin-bottom: 6px;
      color: var(--muted);
      font-size: var(--av-text-xs);
      text-transform: none;
      letter-spacing: 0;
    }}
    .metric strong {{
      font-size: var(--av-text-base);
      line-height: 1.2;
    }}
    .pills {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 12px;
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      min-height: var(--av-control-height-sm);
      padding: 0 12px;
      border-radius: 999px;
      border: 1px solid var(--line-subtle);
      background: var(--success-soft);
      color: color-mix(in oklab, var(--success), black 20%);
      font-size: var(--av-text-sm);
      font-weight: 600;
    }}
    .content-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.4fr) minmax(260px, 0.8fr);
      gap: 18px;
      align-items: start;
      padding-top: 14px;
      border-top: 1px solid var(--line);
    }}
    .content-grid--single {{
      grid-template-columns: minmax(0, 1fr);
    }}
    .content-grid--single .section-stack {{
      grid-template-columns: repeat(2, minmax(0, 1fr));
      column-gap: 24px;
    }}
    .content-grid--single .source-disclosure {{ grid-column: 1 / -1; }}
    .section-stack {{
      display: grid;
      gap: 0;
    }}
    .section-card {{
      padding: 14px 0;
      border: 0;
      border-bottom: 1px solid var(--line);
      border-radius: 0;
      background: transparent;
      box-shadow: none;
    }}
    .source-disclosure summary {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      cursor: pointer;
      list-style: none;
    }}
    .source-disclosure summary::-webkit-details-marker {{
      display: none;
    }}
    .source-disclosure-title {{
      font-size: 20px;
      font-weight: 750;
      line-height: 1.2;
    }}
    .source-disclosure-action {{
      flex: 0 0 auto;
      padding: 5px 10px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--surface-wash);
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-weight: 700;
    }}
    .source-disclosure[open] summary {{
      margin-bottom: 12px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--line-subtle);
    }}
    .sidebar-card {{
      padding: 12px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: var(--surface);
      box-shadow: none;
    }}
    .section-card h2,
    .sidebar-card h2 {{
      margin: 0 0 8px;
      font-size: 20px;
      line-height: 1.2;
    }}
    .richtext {{
      display: grid;
      gap: 8px;
    }}
    .richtext p {{
      margin: 0;
      max-width: 72ch;
      color: color-mix(in oklab, var(--text), var(--muted) 28%);
      line-height: 1.68;
    }}
    .meta-grid {{
      display: grid;
      gap: 8px;
    }}
    .meta-item {{
      padding: 8px 0;
      border: 0;
      border-bottom: 1px solid var(--line-subtle);
      border-radius: 0;
      background: transparent;
    }}
    .meta-item:first-child {{
      padding-top: 0;
      border-top: 0;
    }}
    .meta-item span {{
      display: block;
      margin-bottom: 4px;
      color: var(--muted);
      font-size: var(--av-text-xs);
      text-transform: none;
      letter-spacing: 0;
    }}
    .meta-item strong {{
      font-size: var(--av-text-base);
      line-height: 1.4;
    }}
    .status-note {{
      color: var(--muted);
      font-size: var(--av-text-sm);
    }}
    .empty-state {{
      padding: 14px;
      border: 1px dashed var(--line-strong);
      border-radius: var(--av-radius-md);
      background: var(--surface-subtle);
      color: var(--muted);
    }}
    .prepare-section {{
      display: grid;
      gap: 10px;
      margin-bottom: 0;
      padding: 18px 0;
      border: 0;
      border-bottom: 1px solid var(--line);
      border-radius: 0;
      background: transparent;
      box-shadow: none;
    }}
    .prepare-head {{
      display: grid;
      gap: 6px;
      max-width: 760px;
    }}
    .prepare-head h2 {{
      margin: 0;
      font-family: var(--font-sans);
      font-size: clamp(17px, 2vw, 21px);
      font-weight: 700;
      line-height: 1.16;
    }}
    .prepare-head p {{
      margin: 0;
      color: color-mix(in oklab, var(--text), var(--muted) 28%);
      font-size: var(--av-text-sm);
      line-height: 1.46;
    }}
    .prepare-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 0;
    }}
    .prepare-card {{
      display: grid;
      gap: 6px;
      min-height: 0;
      padding: 6px 14px;
      border: 0;
      border-left: 1px solid var(--line-subtle);
      border-radius: 0;
      background: transparent;
      box-shadow: none;
    }}
    .prepare-card:first-child {{ border-left: 0; padding-left: 0; }}
    .prepare-index {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 24px;
      border-radius: 999px;
      background: var(--brand);
      color: white;
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
    }}
    .prepare-card h3 {{
      margin: 0;
      font-size: var(--av-text-base);
      line-height: 1.25;
    }}
    .prepare-card p {{
      margin: 0;
      color: color-mix(in oklab, var(--text), var(--muted) 28%);
      font-size: var(--av-text-sm);
      line-height: 1.55;
    }}
    .apply-section {{
      display: grid;
      gap: 10px;
      margin-bottom: 0;
      padding: 18px 0;
      border: 0;
      border-bottom: 1px solid var(--line);
      border-radius: 0;
      background: transparent;
      box-shadow: none;
    }}
    .apply-head {{
      display: grid;
      gap: 6px;
      max-width: 760px;
    }}
    .apply-head h2 {{
      margin: 0;
      font-family: var(--font-sans);
      font-size: clamp(17px, 2vw, 21px);
      font-weight: 700;
      line-height: 1.16;
    }}
    .apply-head p {{
      margin: 0;
      color: color-mix(in oklab, var(--text), var(--muted) 28%);
      font-size: var(--av-text-sm);
      line-height: 1.46;
    }}
    .apply-list {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 0;
      padding: 0;
      margin: 0;
      list-style: none;
    }}
    .apply-step {{
      display: grid;
      grid-template-columns: 28px minmax(0, 1fr);
      gap: 8px;
      align-items: start;
      padding: 6px 14px;
      border: 0;
      border-left: 1px solid var(--line-subtle);
      border-radius: 0;
      background: transparent;
    }}
    .apply-step:first-child {{ border-left: 0; padding-left: 0; }}
    .apply-index {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 24px;
      border-radius: 999px;
      background: color-mix(in oklab, var(--success), black 8%);
      color: white;
      font-family: var(--font-mono);
      font-size: var(--av-text-xs);
      font-weight: 700;
    }}
    .apply-step h3 {{
      margin: 0 0 6px;
      font-size: var(--av-text-base);
      line-height: 1.25;
    }}
    .apply-step p {{
      margin: 0;
      color: color-mix(in oklab, var(--text), var(--muted) 28%);
      font-size: var(--av-text-sm);
      line-height: 1.55;
    }}
    .related-section {{
      display: grid;
      gap: 12px;
      margin-top: 14px;
      padding-top: 12px;
      border-top: 1px solid var(--line);
    }}
    .related-head {{
      display: grid;
      gap: 6px;
      max-width: 760px;
    }}
    .related-head h2 {{
      margin: 0;
      font-family: var(--font-sans);
      font-size: clamp(17px, 2vw, 21px);
      font-weight: 700;
      line-height: 1.16;
    }}
    .related-head p {{
      margin: 0;
      color: color-mix(in oklab, var(--text), var(--muted) 28%);
      font-size: var(--av-text-sm);
      line-height: 1.46;
    }}
    .related-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }}
    .related-card {{
      display: grid;
      gap: 10px;
      min-height: 0;
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-md);
      background: var(--surface);
      box-shadow: none;
    }}
    .related-top,
    .related-meta {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .related-reason,
    .related-deadline {{
      display: inline-flex;
      align-items: center;
      min-height: var(--av-control-height-sm);
      padding: 0 10px;
      border-radius: 999px;
      font-size: var(--av-text-xs);
      font-weight: 700;
      box-shadow: none;
      background: var(--surface-subtle);
      color: var(--muted);
    }}
    .related-card h3 {{
      margin: 0;
      font-size: var(--av-text-base);
      line-height: 1.22;
    }}
    .related-card h3 a:hover {{
      color: var(--brand);
    }}
    .related-summary {{
      margin: 0;
      color: color-mix(in oklab, var(--text), var(--muted) 30%);
      font-size: var(--av-text-sm);
      line-height: 1.48;
    }}
    .related-meta {{
      margin-top: auto;
      color: var(--muted);
      font-size: var(--av-text-xs);
      font-weight: 600;
    }}
    .related-link {{
      color: var(--brand);
      font-weight: 700;
    }}
    .related-link:hover {{
      text-decoration: underline;
      text-underline-offset: 2px;
    }}
    .site-footer {{
      display: grid;
      gap: 4px;
      margin-top: 28px;
      padding-top: 16px;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: var(--av-text-xs);
      line-height: 1.5;
    }}
    .site-footer p {{ margin: 0; }}
    .site-footer a {{ color: var(--text); font-weight: 700; }}
    @media (max-width: 900px) {{
      .hero-grid,
      .content-grid,
      .prepare-grid,
      .apply-list,
      .related-grid {{
        grid-template-columns: 1fr;
      }}
      .content-grid--single .section-stack {{ grid-template-columns: 1fr; }}
      .hero-stats,
      .sidebar-card {{
        padding: 12px 0 0;
        border-left: 0;
        border-top: 1px solid var(--line);
      }}
      .prepare-card,
      .prepare-card:first-child,
      .apply-step,
      .apply-step:first-child {{
        padding: 10px 0;
        border-left: 0;
        border-top: 1px solid var(--line-subtle);
      }}
      .prepare-card:first-child,
      .apply-step:first-child {{ border-top: 0; }}
    }}
    @media (max-width: 640px) {{
      .shell {{
        width: min(100%, calc(100% - 24px));
        padding: 14px 0 32px;
      }}
      .hero,
      .related-card {{
        padding: 12px;
      }}
      .hero h1 {{
        font-size: 25px;
      }}
      .summary {{
        font-size: 13px;
      }}
      .prepare-head h2,
      .apply-head h2,
      .related-head h2 {{
        font-size: 18px;
      }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <div class="topbar">
      <nav class="breadcrumbs" aria-label="{escape(str(copy["breadcrumbs_aria"]), quote=True)}">
        <a href="{catalog_href}">QAZ.FUND</a>
        <span>/</span>
        <a href="{catalog_href}">{escape(str(copy["opportunities_title"]))}</a>
        <span>/</span>
        <span>{escape(title)}</span>
      </nav>
      <nav class="lang-switch" aria-label="{escape(str(copy['language_switch']), quote=True)}">
        <a class="{ru_lang_class}" href="{ru_href}" lang="ru">RU</a>
        <a class="{en_lang_class}" href="{en_href}" lang="en">EN</a>
      </nav>
    </div>

    <section class="hero">
      <div class="hero-grid">
        <div>
          <div class="eyebrow">QAZ.FUND</div>
          <h1>{escape(title)}</h1>
          <p class="summary">{escape(summary)}</p>
          <div class="hero-actions">
            <a class="button primary" href="{source_href}" target="_blank" rel="noopener">
              {escape(str(copy["detail_open_source"]))}
            </a>
            <a class="button slim" href="{catalog_href}">
              {escape(str(copy["detail_all_opportunities"]))}
            </a>
            {application_button}
          </div>
        </div>
        <aside class="hero-stats">
          <div>
            <span class="eyebrow">{escape(str(copy["detail_meta_title"]))}</span>
          </div>
          <div>
            <strong>{source_label}</strong>
            <div class="status-note">{source_host}</div>
          </div>
          <div>
            <strong>{deadline_label}</strong>
            <div class="status-note">{deadline_meta_label}</div>
          </div>
          <div>
            <strong>{format_label}</strong>
            <div class="status-note">{escape(str(copy["meta_format_label"]))}</div>
          </div>
        </aside>
      </div>
    </section>

    <div class="pills">{eligibility_markup}</div>

    <section class="{content_grid_class}">
      <div class="section-stack">
        {sections_markup}
        {empty_markup}
      </div>
      {sidebar_markup}
    </section>
    {prepare_markup}
    {apply_markup}
    {related_markup}
    <footer class="site-footer">
      <p>
        {escape(str(copy["footer_owner"]))}
        <a href="https://qdev.run">{escape(str(copy["footer_qdev"]))}</a>
      </p>
      <p>{escape(str(copy["footer_disclaimer"]))}</p>
    </footer>
  </main>
</body>
</html>"""
