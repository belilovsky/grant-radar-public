"""Server-rendered public funder pages for QAZ.FUND."""

from __future__ import annotations

import json
import re
from datetime import date
from enum import Enum
from html import escape
from typing import Any, cast
from urllib.parse import urlparse

from qazstack.opportunities import public_lifecycle

from api.avds import AVDS_CSS, AVDS_FONT_HEAD
from api.dashboard import dashboard_copy
from api.page_primitives import absolute_href as _absolute_href
from api.page_primitives import catalog_path as _catalog_path
from api.page_primitives import format_deadline as _format_deadline
from api.public_meta import analytics_head_html, og_image_url
from core.models import Opportunity
from core.nlp import clean_source_summary

_ACRONYM_MAP = {
    "ai": "AI",
    "api": "API",
    "db": "DB",
    "ebrd": "EBRD",
    "ecepp": "ECEPP",
    "eu": "EU",
    "iite": "IITE",
    "isdb": "IsDB",
    "ngo": "NGO",
    "qic": "QIC",
    "qa": "QA",
    "rk": "RK",
    "uk": "UK",
    "undp": "UNDP",
    "unesco": "UNESCO",
    "unicef": "UNICEF",
    "us": "US",
}


def _funder_path(root_path: str, slug: str, lang: str) -> str:
    base = root_path.rstrip("/")
    if base:
        return f"{base}/funder/{slug}?lang={lang}"
    return f"/funder/{slug}?lang={lang}"


def _opportunity_path(root_path: str, opportunity_id: str, lang: str) -> str:
    base = root_path.rstrip("/")
    if base:
        return f"{base}/opportunity/{opportunity_id}?lang={lang}"
    return f"/opportunity/{opportunity_id}?lang={lang}"


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
    return " ".join(
        _ACRONYM_MAP.get(part.lower(), part.lower().capitalize())
        for part in raw.replace("-", "_").split("_")
        if part
    )


def _object_list(value: object) -> list[object]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _dict_list(value: object) -> list[dict[str, Any]]:
    rows = _object_list(value)
    return [cast(dict[str, Any], row) for row in rows if isinstance(row, dict)]


def _lifecycle_label(lifecycle: str, copy: dict[str, object]) -> str:
    return str(copy.get(f"lifecycle_{lifecycle}") or lifecycle.replace("_", " "))


def _region_summary(funder: dict[str, object], copy: dict[str, object]) -> str:
    labels = [
        _label_value(str(region), copy)
        for region in _object_list(funder.get("top_regions"))[:2]
        if str(region).strip()
    ]
    return ", ".join(labels)


def _tag_summary(funder: dict[str, object], copy: dict[str, object]) -> str:
    return ", ".join(_public_topic_labels(funder, copy)[:3])


def _type_summary(funder: dict[str, object], copy: dict[str, object]) -> str:
    labels = [
        _label_value(kind, copy)
        for kind in _object_list(funder.get("top_types"))[:2]
        if str(kind).strip()
    ]
    return ", ".join(labels)


def _public_topic_labels(
    funder: dict[str, object], copy: dict[str, object]
) -> list[str]:
    """Keep funder themes distinct from already displayed opportunity formats."""

    type_labels = {
        _label_value(kind, copy).casefold()
        for kind in _object_list(funder.get("top_types"))
        if str(kind).strip()
    }
    labels: list[str] = []
    seen: set[str] = set()
    for tag in _object_list(funder.get("top_tags")):
        if not str(tag).strip():
            continue
        label = _label_value(str(tag), copy)
        normalized = label.casefold()
        if not label or normalized in type_labels or normalized in seen:
            continue
        seen.add(normalized)
        labels.append(label)
    return labels


def _overview_sentence(funder: dict[str, object], copy: dict[str, object]) -> str:
    types = _type_summary(funder, copy)
    tags = _tag_summary(funder, copy)
    regions = _region_summary(funder, copy)
    bits = [str(copy["funder_overview_intro"])]
    if types:
        bits.append(str(copy["funder_overview_types"]).format(types=types))
    if tags:
        bits.append(str(copy["funder_overview_topics"]).format(topics=tags))
    if regions:
        bits.append(str(copy["funder_overview_regions"]).format(regions=regions))
    return " ".join(bits).strip()


def _tag_is_supported(item: Opportunity, raw_tag: object) -> bool:
    normalized = str(raw_tag or "").strip().casefold().replace("_", " ")
    if normalized not in {"ai", "artificial intelligence", "ии"}:
        return True
    public_copy = f"{item.title} {item.summary}".casefold()
    return bool(
        re.search(
            r"(?<![a-z0-9])ai(?![a-z0-9])|artificial intelligence|"
            r"искусственн\w* интеллект\w*|жасанды интеллект",
            public_copy,
            re.IGNORECASE,
        )
    )


def _unique_public_tags(item: Opportunity, copy: dict[str, object]) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    for raw_tag in [item.type, *list(item.tags)]:
        if not _tag_is_supported(item, raw_tag):
            continue
        label = _label_value(raw_tag, copy)
        normalized = label.casefold()
        if not label or normalized in seen:
            continue
        seen.add(normalized)
        labels.append(label)
    return labels[:4]


def _source_meta_label(source: dict[str, Any], copy: dict[str, object]) -> str:
    base_url = str(source.get("base_url") or "").strip()
    host = urlparse(base_url).netloc.strip()
    if host:
        return host
    return str(copy.get("detail_open_source") or "Official source")


def _clean_summary_text(text: str, *, title: str = "") -> str:
    return clean_source_summary(text, title=title)


def _int_stat(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip() or "0")
        except ValueError:
            return 0
    return 0


def _json_ld(payload: dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")


def _funder_schema(
    *,
    funder: dict[str, object],
    display_name: str,
    overview: str,
    canonical_href: str,
    catalog_href: str,
    lang: str,
) -> str:
    breadcrumb_id = f"{canonical_href}#breadcrumb"
    organization_id = f"{canonical_href}#organization"
    page_id = f"{canonical_href}#page"
    same_as = [
        str(source.get("base_url") or "").strip()
        for source in _dict_list(funder.get("sources"))
        if str(source.get("base_url") or "").strip()
    ]
    graph = [
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
                    "name": display_name,
                    "item": canonical_href,
                },
            ],
        },
        {
            "@type": "Organization",
            "@id": organization_id,
            "name": display_name,
            "description": overview,
            "url": canonical_href,
            "sameAs": same_as,
        },
        {
            "@type": "CollectionPage",
            "@id": page_id,
            "url": canonical_href,
            "name": display_name,
            "description": overview,
            "inLanguage": lang,
            "about": {"@id": organization_id},
            "breadcrumb": {"@id": breadcrumb_id},
            "mainEntity": {
                "@type": "ItemList",
                "name": display_name,
                "numberOfItems": _int_stat(funder.get("total_items")),
            },
        },
    ]
    return _json_ld({"@context": "https://schema.org", "@graph": graph})


def _opportunity_card(
    item: Opportunity,
    *,
    copy: dict[str, object],
    root_path: str,
    lang: str,
) -> str:
    lifecycle = public_lifecycle(item)
    public_tags = _unique_public_tags(item, copy)
    primary_format = public_tags[0] if public_tags else _label_value(item.type, copy)
    tag_markup = "".join(
        f'<span class="meta-chip">{escape(label)}</span>' for label in public_tags[1:]
    )
    href = escape(_opportunity_path(root_path, str(item.id), lang), quote=True)
    summary_text = escape(
        _clean_summary_text(item.summary, title=item.title) or str(copy["no_summary"])
    )
    deadline_markup = (
        f'<span class="meta-chip deadline">'
        f"{escape(_format_deadline(item.deadline, lang, str(copy['open_rolling'])))}"
        "</span>"
        if item.deadline is not None
        else ""
    )
    search_blob = " ".join(
        [item.title, item.summary, primary_format, *public_tags]
    ).lower()
    return f"""
    <article class="opportunity-card" data-card-search="{escape(search_blob, quote=True)}">
      <div class="opportunity-head">
        <div>
          <h3><a href="{href}">{escape(item.title)}</a></h3>
          <div class="meta-row">
            <span class="meta-chip strong">{escape(primary_format)}</span>
            <span class="meta-chip lifecycle">{escape(_lifecycle_label(lifecycle, copy))}</span>
            {deadline_markup}
            {tag_markup}
          </div>
        </div>
      </div>
      <p>{summary_text}</p>
      <div class="card-actions">
        <a
          class="button soft"
          href="{href}"
        >{escape(str(copy["funder_open_card"]))}</a>
        <a
          class="button"
          href="{escape(str(item.source_url), quote=True)}"
          target="_blank"
          rel="noopener"
        >{escape(str(copy["detail_open_source"]))}</a>
      </div>
    </article>
    """


def render_funder_page(
    *,
    funder: dict[str, object],
    live_items: list[Opportunity],
    archive_items: list[Opportunity],
    lang: str,
    root_path: str,
    site_origin: str,
) -> str:
    copy = dashboard_copy(lang)
    active_lang = str(copy["lang"])
    ru_href = escape(
        _absolute_href(
            site_origin, _funder_path(root_path.rstrip("/"), str(funder["slug"]), "ru")
        ),
        quote=True,
    )
    en_href = escape(
        _absolute_href(
            site_origin, _funder_path(root_path.rstrip("/"), str(funder["slug"]), "en")
        ),
        quote=True,
    )
    kk_href = escape(
        _absolute_href(
            site_origin, _funder_path(root_path.rstrip("/"), str(funder["slug"]), "kk")
        ),
        quote=True,
    )
    html_lang = escape(active_lang, quote=True)
    canonical_path = _funder_path(
        root_path.rstrip("/"), str(funder["slug"]), active_lang
    )
    canonical_href = escape(_absolute_href(site_origin, canonical_path), quote=True)
    catalog_href = escape(_catalog_path(root_path, active_lang), quote=True)
    base_path = root_path.rstrip("/")
    sources_href = escape(
        (
            f"{base_path}/?lang={active_lang}#sources"
            if base_path
            else f"/?lang={active_lang}#sources"
        ),
        quote=True,
    )
    status_href = escape(
        (
            f"{base_path}/status?lang={active_lang}"
            if base_path
            else f"/status?lang={active_lang}"
        ),
        quote=True,
    )
    docs_href = escape(
        (
            f"{base_path}/docs?lang={active_lang}"
            if base_path
            else f"/docs?lang={active_lang}"
        ),
        quote=True,
    )
    insights_href = escape(
        (
            f"{base_path}/insights?lang={active_lang}"
            if base_path
            else f"/insights?lang={active_lang}"
        ),
        quote=True,
    )
    terms_href = escape(
        (
            f"{base_path}/terms?lang={active_lang}"
            if base_path
            else f"/terms?lang={active_lang}"
        ),
        quote=True,
    )
    data_policy_href = escape(
        (
            f"{base_path}/data-policy?lang={active_lang}"
            if base_path
            else f"/data-policy?lang={active_lang}"
        ),
        quote=True,
    )
    attribution_href = escape(
        (
            f"{base_path}/attribution?lang={active_lang}"
            if base_path
            else f"/attribution?lang={active_lang}"
        ),
        quote=True,
    )
    back_label = escape(str(copy["funder_back_to_catalog"]))
    funder_name = escape(_label_value(str(funder["name"]), copy))
    overview = escape(_overview_sentence(funder, copy))
    og_locale = escape(active_lang.replace("-", "_") + "_KZ", quote=True)
    tag_chips = "".join(
        f'<span class="topic-chip">{escape(label)}</span>'
        for label in _public_topic_labels(funder, copy)[:5]
    )
    source_cards = "".join(f"""
        <a
          class="source-link"
          href="{escape(str(source.get("base_url") or "#"), quote=True)}"
          target="_blank"
          rel="noopener"
        >
          <strong>{escape(_label_value(str(source.get("name") or ""), copy))}</strong>
          <span>{escape(_source_meta_label(source, copy))}</span>
        </a>
        """ for source in _dict_list(funder.get("sources"))[:8])
    live_markup = "".join(
        _opportunity_card(item, copy=copy, root_path=root_path, lang=active_lang)
        for item in live_items
    )
    archive_markup = "".join(
        _opportunity_card(item, copy=copy, root_path=root_path, lang=active_lang)
        for item in archive_items
    )
    stat_entries: list[tuple[str, str]] = []
    current_items = _int_stat(funder.get("current_items"))
    rolling_items = _int_stat(funder.get("rolling_items"))
    forecast_items = _int_stat(funder.get("forecast_items"))
    total_items = _int_stat(funder.get("total_items"))
    if current_items:
        stat_entries.append((str(copy["funder_live_now"]), str(current_items)))
    if rolling_items:
        stat_entries.append((str(copy["lifecycle_rolling"]), str(rolling_items)))
    if forecast_items:
        stat_entries.append((str(copy["lifecycle_forecast"]), str(forecast_items)))
    next_deadline = funder.get("next_deadline")
    if isinstance(next_deadline, date):
        stat_entries.append(
            (
                str(copy["funder_next_deadline"]),
                _format_deadline(next_deadline, active_lang, str(copy["open_rolling"])),
            )
        )
    if total_items and total_items != current_items:
        stat_entries.append((str(copy["funder_total_items"]), str(total_items)))
    stat_markup = "".join(
        f'<div class="stat"><span>{escape(label)}</span><strong>{escape(value)}</strong></div>'
        for label, value in stat_entries
    )
    archive_section = (
        f"""
    <details class="section archive-disclosure">
      <summary><span>{escape(str(copy["funder_archive_title"]))}</span>
        <strong>{len(archive_items)}</strong></summary>
      <div class="archive-body">
        <p class="section-note">{escape(str(copy["funder_archive_note"]))}</p>
        <div class="opportunity-list">{archive_markup}</div>
      </div>
    </details>
        """
        if archive_markup
        else ""
    )
    schema_json = _funder_schema(
        funder=funder,
        display_name=_label_value(str(funder["name"]), copy),
        overview=_overview_sentence(funder, copy),
        canonical_href=_absolute_href(site_origin, canonical_path),
        catalog_href=_absolute_href(site_origin, _catalog_path(root_path, active_lang)),
        lang=active_lang,
    )
    html_theme_attrs = (
        'data-avds="grant-radar" data-av-theme="light" data-theme="light"'
    )
    social_image = escape(og_image_url(site_origin, root_path), quote=True)
    analytics_head = analytics_head_html()
    search_label = {
        "ru": "Поиск по программам фонда",
        "kk": "Қор бағдарламаларын іздеу",
        "en": "Search this funder's programmes",
    }[active_lang]
    no_search_results = {
        "ru": "По этому запросу программ не найдено.",
        "kk": "Бұл сұрау бойынша бағдарлама табылмады.",
        "en": "No programmes match this search.",
    }[active_lang]
    ru_lang_class = "active" if active_lang == "ru" else ""
    kk_lang_class = "active" if active_lang == "kk" else ""
    en_lang_class = "active" if active_lang == "en" else ""
    ru_lang_current = ' aria-current="page"' if active_lang == "ru" else ""
    kk_lang_current = ' aria-current="page"' if active_lang == "kk" else ""
    en_lang_current = ' aria-current="page"' if active_lang == "en" else ""
    fallback_note = str(copy.get("language_fallback_note") or "").strip()
    fallback_note_markup = (
        f'<p class="language-fallback-note" lang="kk" '
        f'data-language-fallback="source">{escape(fallback_note)}</p>'
        if fallback_note
        else ""
    )

    return f"""<!doctype html>
<html lang="{html_lang}" {html_theme_attrs}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{funder_name} – QAZ.FUND</title>
  <meta name="description" content="{overview}">
  <link rel="canonical" href="{canonical_href}">
  <link rel="alternate" hreflang="kk" href="{kk_href}">
  <link rel="alternate" hreflang="ru" href="{ru_href}">
  <link rel="alternate" hreflang="en" href="{en_href}">
  <link rel="alternate" hreflang="x-default" href="{ru_href}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{funder_name} – QAZ.FUND">
  <meta property="og:description" content="{overview}">
  <meta property="og:url" content="{canonical_href}">
  <meta property="og:image" content="{social_image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:locale" content="{og_locale}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{funder_name} – QAZ.FUND">
  <meta name="twitter:description" content="{overview}">
  <meta name="twitter:image" content="{social_image}">
  <script type="application/ld+json">{schema_json}</script>
  {analytics_head}
  {AVDS_FONT_HEAD}
  <style>
    {AVDS_CSS}
    :root {{
      --bg: var(--color-bg);
      --panel: var(--color-surface);
      --panel-subtle: color-mix(in oklab, var(--panel), var(--av-color-background) 28%);
      --panel-wash: color-mix(in oklab, var(--panel), var(--av-color-background) 42%);
      --panel-wash-section: color-mix(in oklab, var(--panel), var(--av-color-background) 20%);
      --panel-wash-card: color-mix(in oklab, var(--panel), var(--av-color-background) 32%);
      --line: var(--color-border);
      --muted: var(--color-text-muted);
      --ink: var(--color-text);
      --brand: var(--color-accent);
      --brand-soft: var(--color-accent-subtle);
      --radius: var(--av-radius-lg);
      --shadow: var(--av-shadow-md);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: var(--av-font-sans, Arial, sans-serif);
      background:
        radial-gradient(circle at 12% 0%, var(--brand-soft), transparent 28rem),
        var(--bg);
      color: var(--ink);
    }}
    a {{ color: inherit; }}
    .shell {{
      width: min(var(--av-container-dashboard), calc(100% - 64px));
      margin: 0 auto;
      padding: 18px 0 44px;
    }}
    .back-link {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      text-decoration: none;
      font-size: 14px;
      font-weight: 600;
      position: sticky;
      top: 12px;
      z-index: 20;
      margin-bottom: 18px;
      padding: 10px 14px;
      border: 1px solid color-mix(in oklab, var(--line), transparent 18%);
      border-radius: var(--av-radius-lg);
      background: color-mix(in oklab, var(--panel), transparent 7%);
      box-shadow: var(--av-shadow-sm);
      backdrop-filter: blur(16px);
    }}
    .back-link:hover {{ color: var(--brand); }}
    .language-fallback-note {{ margin:0 0 14px; padding:9px 12px; border-left:3px solid var(--brand);
      color:var(--muted); background:var(--panel-wash); font-size:12px; line-height:1.45; }}
    .topbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 14px;
    }}
    .topbar .back-link {{ margin-bottom: 0; }}
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
      text-decoration: none;
      font-size: 12px;
      font-weight: 700;
    }}
    .lang-switch a.active {{
      border-bottom-color: var(--brand);
      color: var(--ink);
    }}
    .hero {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(250px, 0.44fr);
      gap: 14px 36px;
      padding: 24px 26px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: color-mix(in oklab, var(--panel), var(--brand-soft) 22%);
      box-shadow: var(--shadow);
    }}
    .hero > .eyebrow {{ grid-column: 1 / -1; }}
    .eyebrow {{
      color: var(--brand);
      font-family: var(--av-font-sans, Arial, sans-serif);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    h1 {{
      margin: 0;
      font-family: var(--av-font-sans, Arial, sans-serif);
      max-width: 18ch;
      font-size: clamp(36px, 4.2vw, 58px);
      line-height: 1.02;
      letter-spacing: -0.035em;
      text-wrap: balance;
    }}
    .hero p {{
      margin: 0;
      max-width: 72ch;
      color: var(--muted);
      font-size: clamp(16px, 1.4vw, 19px);
      line-height: 1.55;
    }}
    .hero-copy {{ display: grid; gap: 12px; align-content: start; }}
    .stat-grid {{
      display: grid;
      grid-column: 2;
      grid-row: 2;
      grid-template-columns: repeat(2, minmax(120px, 1fr));
      gap: 10px;
      align-self: start;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: color-mix(in oklab, var(--panel), transparent 12%);
    }}
    .stat {{
      border: 1px solid var(--line);
      border-radius: var(--av-radius-md);
      background: var(--panel);
      padding: 12px;
    }}
    .stat span {{
      display: block;
      margin-bottom: 6px;
      color: var(--muted);
      font-family: var(--av-font-sans, Arial, sans-serif);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0;
      text-transform: none;
    }}
    .stat strong {{
      font-size: 22px;
      line-height: 1.05;
      font-family: var(--av-font-sans, Arial, sans-serif);
    }}
    .section {{
      padding: 16px;
      margin-top: 14px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--panel-wash-section);
      box-shadow: var(--av-shadow-2xs);
    }}
    .section h2 {{
      margin: 0 0 10px;
      font-family: var(--av-font-sans, Arial, sans-serif);
      font-size: 22px;
      line-height: 1.2;
    }}
    .section p.section-note {{
      margin: 0 0 10px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.45;
    }}
    .funder-search {{
      display:grid; gap:6px; margin-top:14px; color:var(--muted);
      font-size:12px; font-weight:700;
    }}
    .funder-search input {{
      width:100%; min-height:44px; padding:10px 12px; border:1px solid var(--line);
      border-radius:var(--av-radius-md); background:var(--panel); color:var(--ink);
    }}
    .funder-search-empty {{ display:none; margin:12px 0 0; color:var(--muted); font-size:13px; }}
    .opportunity-card[hidden],.archive-disclosure[hidden] {{ display:none !important; }}
    .archive-disclosure {{ padding:0; overflow:clip; }}
    .archive-disclosure > summary {{
      min-height:64px; padding:16px; display:flex; align-items:center;
      justify-content:space-between; gap:14px; list-style:none; cursor:pointer;
      font-size:20px; font-weight:800;
    }}
    .archive-disclosure > summary::-webkit-details-marker {{ display:none; }}
    .archive-disclosure > summary strong {{
      display:grid; place-items:center; min-width:34px; height:34px; border-radius:999px;
      background:var(--brand-soft); color:var(--brand); font-size:12px;
    }}
    .archive-disclosure[open] > summary {{ border-bottom:1px solid var(--line); }}
    .archive-body {{ padding:16px; }}
    .topic-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .topic-chip, .meta-chip {{
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      border: 0;
      border-radius: 999px;
      padding: 0 10px;
      background: var(--panel-subtle);
      color: var(--muted);
      font-size: 13px;
      font-weight: 600;
    }}
    .meta-chip.strong {{
      background: var(--brand-soft);
      color: var(--brand);
    }}
    .meta-chip.lifecycle {{
      background: color-mix(in oklab, var(--panel-subtle), white 4%);
      color: var(--ink);
    }}
    .opportunity-list {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 8px;
    }}
    .opportunity-card {{
      display: grid;
      grid-template-columns: 1fr;
      grid-template-rows: auto 1fr auto;
      gap: 14px;
      align-items: start;
      align-content: start;
      border: 1px solid var(--line-subtle);
      border-left: 3px solid color-mix(in oklab, var(--brand), white 38%);
      border-radius: var(--av-radius-md);
      background: var(--panel-wash-card);
      padding: 16px 14px;
      box-shadow: var(--av-shadow-2xs);
    }}
    .opportunity-card:first-child {{ border-left-color: var(--brand); }}
    .opportunity-head {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 8px;
      align-items: start;
      margin-bottom: 0;
    }}
    .opportunity-card h3 {{
      margin: 0 0 6px;
      font-size: 19px;
      line-height: 1.3;
    }}
    .opportunity-card h3 a {{
      text-decoration: none;
    }}
    .opportunity-card h3 a:hover {{
      color: var(--brand);
    }}
    .meta-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .opportunity-card p {{
      margin: 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.55;
      display: -webkit-box;
      -webkit-line-clamp: 4;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .card-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 0;
      align-self: end;
      justify-content: flex-start;
    }}
    .button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 40px;
      padding: 0 14px;
      border: 1px solid transparent;
      border-radius: var(--av-radius-md);
      background: var(--brand);
      color: white;
      text-decoration: none;
      font-size: 14px;
      font-weight: 650;
      white-space: nowrap;
    }}
    .button.soft {{
      background: var(--brand-soft);
      color: var(--brand);
      border-color: color-mix(in oklab, var(--brand), transparent 76%);
    }}
    .button:not(.soft):hover {{
      background: color-mix(in oklab, var(--brand), black 10%);
    }}
    .button.soft:hover {{
      border-color: var(--color-border-subtle);
      background: var(--panel-subtle);
      color: var(--brand);
    }}
    .source-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 8px;
    }}
    .source-link {{
      display: grid;
      gap: 4px;
      padding: 12px;
      border: 1px solid var(--line-subtle);
      border-radius: var(--av-radius-md);
      background: var(--panel-wash-card);
      text-decoration: none;
      box-shadow: var(--av-shadow-2xs);
    }}
    .source-link strong {{
      font-size: 15px;
    }}
    .source-link span {{
      color: var(--muted);
      font-size: 13px;
      overflow-wrap: anywhere;
    }}
    .empty {{
      padding: 14px;
      border: 1px dashed var(--line);
      border-radius: 16px;
      color: var(--muted);
      background: var(--panel-subtle);
    }}
    .site-footer {{
      display: grid;
      gap: 8px;
      margin-top: 18px;
      padding: 22px 24px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: var(--panel);
      color: var(--muted);
      font-size: 14px;
      line-height: 1.5;
    }}
    .site-footer-nav {{
      display:flex;
      flex-wrap:wrap;
      gap:6px 16px;
      align-items:center;
      font-size:12px;
      font-weight:650;
    }}
    .site-footer p {{ margin: 0; }}
    .site-footer a {{ color: var(--ink); font-weight: 700; }}
    a:focus-visible, button:focus-visible {{
      outline:2px solid var(--brand);
      outline-offset:2px;
      border-radius:var(--av-radius-sm);
    }}
    @media (min-width:1440px) {{
      .hero {{
        grid-template-columns:minmax(0,1.25fr) minmax(420px,.55fr);
        gap:56px;
        padding:32px 36px;
      }}
      .opportunity-card {{
        grid-template-columns:minmax(380px,1.08fr) minmax(360px,.92fr) minmax(250px,.44fr);
        gap:40px;
      }}
      .source-grid {{
        grid-template-columns:repeat(2,minmax(0,1fr));
        column-gap:40px;
      }}
    }}
    @media (min-width:2200px) {{
      .shell {{
        width: min(1920px, calc(100% - 160px));
      }}
      .hero {{
        grid-template-columns:minmax(0,1.45fr) minmax(520px,.65fr);
        gap:72px;
        padding-block:40px;
      }}
      .hero-copy {{ max-width:1080px; }}
      .opportunity-card {{
        grid-template-columns:minmax(420px,1.18fr) minmax(420px,.92fr) minmax(280px,.42fr);
        gap:48px;
      }}
      .source-grid {{
        grid-template-columns:repeat(4,minmax(0,1fr));
        column-gap:48px;
      }}
    }}
    @media (max-width: 900px) {{
      .button,
      .lang-switch a,
      .back-link,
      .opportunity-card h3 a,
      .site-footer-nav a,
      .site-footer > p a {{
        display: inline-flex;
        align-items: center;
        min-height: var(--av-control-height-lg);
      }}
      .lang-switch a,
      .site-footer-nav a {{ min-width: var(--av-control-height-lg); }}
      .site-footer-nav a {{ justify-content: center; }}
      .hero {{ grid-template-columns: 1fr; }}
      .stat-grid {{
        grid-column: auto;
        grid-row: auto;
        padding: 16px;
        border: 1px solid var(--line);
      }}
      .opportunity-list {{
        grid-template-columns: 1fr;
      }}
      .opportunity-card {{
        grid-template-columns: 1fr;
      }}
      .card-actions {{ justify-content: flex-start; }}
      .source-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
    }}
    @media (max-width: 640px) {{
      .button,
      .lang-switch a,
      .back-link {{ min-height: var(--av-control-height-lg); }}
      .lang-switch a {{ min-width: var(--av-control-height-lg); }}
      .shell {{
        width: min(100%, calc(100% - 24px));
        padding-top: 16px;
      }}
      .topbar {{
        top: 8px;
        padding: 8px 10px;
      }}
      .hero {{
        padding: 16px;
      }}
      .stat-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .source-grid {{
        grid-template-columns: 1fr;
      }}
      .opportunity-head {{
        grid-template-columns: 1fr;
      }}
      .section {{ padding: 14px; }}
      .opportunity-card {{ padding: 14px 12px; }}
      .card-actions {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .card-actions .button {{ width: 100%; }}
    }}
  </style>
</head>
<body>
  <main class="shell" data-avds-component="funder-page">
    <div class="topbar">
      <a class="back-link" href="{catalog_href}">{back_label}</a>
      <nav class="lang-switch" aria-label="{escape(str(copy['language_switch']), quote=True)}">
        <a class="{kk_lang_class}" href="{kk_href}" lang="kk"{kk_lang_current}>KAZ</a>
        <a class="{ru_lang_class}" href="{ru_href}" lang="ru"{ru_lang_current}>RU</a>
        <a class="{en_lang_class}" href="{en_href}" lang="en"{en_lang_current}>EN</a>
      </nav>
    </div>
    {fallback_note_markup}
    <section class="hero" data-avds-component="hero-band">
      <span class="eyebrow">{escape(str(copy["funder_page_eyebrow"]))}</span>
      <div class="hero-copy">
        <h1>{funder_name}</h1>
        <p>{overview}</p>
        <div class="topic-row">{tag_chips}</div>
      </div>
      <div class="stat-grid">{stat_markup}</div>
    </section>

    <label class="funder-search" for="funder-program-search">
      {escape(search_label)}
      <input id="funder-program-search" type="search" autocomplete="off"
        placeholder="{escape(search_label, quote=True)}">
    </label>
    <p class="funder-search-empty" id="funder-search-empty">{escape(no_search_results)}</p>

    <section class="section">
      <h2>{escape(str(copy["funder_live_title"]))}</h2>
      <p class="section-note">{escape(str(copy["funder_live_note"]))}</p>
      <div class="opportunity-list">
        {live_markup or f'<div class="empty">{escape(str(copy["funder_live_empty"]))}</div>'}
      </div>
    </section>

    {archive_section}

    <section class="section">
      <h2>{escape(str(copy["funder_sources_title"]))}</h2>
      <p class="section-note">{escape(str(copy["funder_sources_note"]))}</p>
      <div class="source-grid">
        {source_cards or (
            f'<div class="empty">{escape(str(copy["source_catalog_unavailable"]))}</div>'
        )}
      </div>
    </section>
    <footer class="site-footer">
      <a class="footer-contact" href="mailto:contact@qaz.fund">contact@qaz.fund</a>
      <nav class="site-footer-nav" aria-label="{escape(str(copy["views_aria"]), quote=True)}">
        <a href="{catalog_href}">{escape(str(copy["tab_opportunities"]))}</a>
        <a href="{sources_href}">{escape(str(copy["tab_sources"]))}</a>
        <a href="{insights_href}">{escape(str(copy["insights_link"]))}</a>
        <a href="{status_href}">{escape(str(copy["status_link"]))}</a>
        <a href="{docs_href}">{escape(str(copy["api_docs"]))}</a>
        <a href="{terms_href}">{escape(str(copy["footer_terms"]))}</a>
        <a href="{data_policy_href}">{escape(str(copy["footer_data_policy"]))}</a>
        <a href="{attribution_href}">{escape(str(copy["footer_attribution"]))}</a>
      </nav>
      <p>
        {escape(str(copy["footer_owner"]))}
        <a href="https://qdev.run">{escape(str(copy["footer_qdev"]))}</a>
      </p>
      <p>{escape(str(copy["footer_disclaimer"]))}</p>
    </footer>
  </main>
  <script>
    (() => {{
      const input = document.getElementById("funder-program-search");
      const cards = [...document.querySelectorAll(".opportunity-card")];
      const empty = document.getElementById("funder-search-empty");
      const archive = document.querySelector(".archive-disclosure");
      input.addEventListener("input", () => {{
        const query = String(input.value || "").trim().toLowerCase();
        let visible = 0;
        cards.forEach((card) => {{
          card.hidden = Boolean(query) && !(card.dataset.cardSearch || "").includes(query);
          if (!card.hidden) visible += 1;
        }});
        if (archive) {{
          const archiveVisible = [...archive.querySelectorAll(".opportunity-card")]
            .some((card) => !card.hidden);
          archive.hidden = Boolean(query) && !archiveVisible;
          if (query && archiveVisible) archive.open = true;
          if (!query) archive.hidden = false;
        }}
        empty.style.display = visible ? "none" : "block";
      }});
    }})();
  </script>
</body>
</html>"""
