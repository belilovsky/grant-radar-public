"""Server-rendered public funder pages for QAZ.FUND."""

from __future__ import annotations

import json
import re
from datetime import date
from enum import Enum
from html import escape
from typing import Any, cast
from urllib.parse import urlparse

from api.avds import AVDS_CSS, AVDS_FONT_HEAD
from api.dashboard import dashboard_copy
from api.public_meta import analytics_head_html, og_image_url
from core.models import Opportunity
from core.nlp import clean_source_summary
from core.opportunity_intelligence import public_lifecycle

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


def _absolute_href(origin: str, path: str) -> str:
    clean_origin = origin.rstrip("/")
    if path.startswith(("http://", "https://")):
        return path
    if not clean_origin:
        return path or "/"
    return f"{clean_origin}{path}"


def _catalog_path(root_path: str, lang: str) -> str:
    base = root_path.rstrip("/")
    if base:
        return f"{base}/?lang={lang}#opportunities"
    return f"/?lang={lang}#opportunities"


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
    labels = [
        _label_value(str(tag), copy)
        for tag in _object_list(funder.get("top_tags"))[:3]
        if str(tag).strip()
    ]
    return ", ".join(labels)


def _type_summary(funder: dict[str, object], copy: dict[str, object]) -> str:
    labels = [
        _label_value(kind, copy)
        for kind in _object_list(funder.get("top_types"))[:2]
        if str(kind).strip()
    ]
    return ", ".join(labels)


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


def _format_deadline(value: date | None, lang: str, rolling_label: str) -> str:
    if value is None:
        return rolling_label
    if lang == "en":
        return value.strftime("%b %d, %Y")
    return value.strftime("%d.%m.%Y")


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
    deadline_text = escape(
        _format_deadline(item.deadline, lang, str(copy["open_rolling"]))
    )
    return f"""
    <article class="opportunity-card">
      <div class="opportunity-head">
        <div>
          <h3><a href="{href}">{escape(item.title)}</a></h3>
          <div class="meta-row">
            <span class="meta-chip strong">{escape(primary_format)}</span>
            <span class="meta-chip lifecycle">{escape(_lifecycle_label(lifecycle, copy))}</span>
            <span class="meta-chip deadline">{deadline_text}</span>
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
    html_lang = escape(active_lang, quote=True)
    canonical_path = _funder_path(
        root_path.rstrip("/"), str(funder["slug"]), active_lang
    )
    canonical_href = escape(_absolute_href(site_origin, canonical_path), quote=True)
    catalog_href = escape(_catalog_path(root_path, active_lang), quote=True)
    back_label = escape(str(copy["funder_back_to_catalog"]))
    funder_name = escape(_label_value(str(funder["name"]), copy))
    overview = escape(_overview_sentence(funder, copy))
    og_locale = escape(active_lang.replace("-", "_") + "_KZ", quote=True)
    tag_chips = "".join(
        f'<span class="topic-chip">{escape(_label_value(str(tag), copy))}</span>'
        for tag in _object_list(funder.get("top_tags"))[:5]
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
    <section class="section">
      <h2>{escape(str(copy["funder_archive_title"]))}</h2>
      <p class="section-note">{escape(str(copy["funder_archive_note"]))}</p>
      <div class="opportunity-list">{archive_markup}</div>
    </section>
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
    ru_lang_class = "active" if active_lang == "ru" else ""
    en_lang_class = "active" if active_lang == "en" else ""

    return f"""<!doctype html>
<html lang="{html_lang}" {html_theme_attrs}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{funder_name} - QAZ.FUND</title>
  <meta name="description" content="{overview}">
  <link rel="canonical" href="{canonical_href}">
  <link rel="alternate" hreflang="ru" href="{ru_href}">
  <link rel="alternate" hreflang="en" href="{en_href}">
  <link rel="alternate" hreflang="x-default" href="{ru_href}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{funder_name} - QAZ.FUND">
  <meta property="og:description" content="{overview}">
  <meta property="og:url" content="{canonical_href}">
  <meta property="og:image" content="{social_image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:locale" content="{og_locale}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{funder_name} - QAZ.FUND">
  <meta name="twitter:description" content="{overview}">
  <meta name="twitter:image" content="{social_image}">
  <script type="application/ld+json">{schema_json}</script>
  {analytics_head}
  {AVDS_FONT_HEAD}
  <style>
    {AVDS_CSS}
    :root {{
      --bg: var(--av-color-background);
      --panel: var(--av-color-surface-raised);
      --panel-subtle: color-mix(in oklab, var(--panel), var(--av-color-background) 18%);
      --line: color-mix(in oklab, var(--av-color-border-default), transparent 28%);
      --muted: var(--av-color-text-secondary);
      --ink: var(--av-color-text-primary);
      --brand: var(--color-accent);
      --brand-soft: var(--color-accent-subtle);
      --radius: var(--av-radius-lg);
      --shadow: 0 12px 32px rgb(15 23 42 / 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: var(--av-font-sans, Arial, sans-serif);
      background: var(--bg);
      color: var(--ink);
    }}
    a {{ color: inherit; }}
    .shell {{
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 20px 0 40px;
    }}
    .back-link {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      text-decoration: none;
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 14px;
    }}
    .back-link:hover {{ color: var(--brand); }}
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
      gap: 14px;
      padding: 20px;
      border: 0;
      border-radius: 0;
      background: color-mix(in oklab, var(--panel), var(--brand-soft) 18%);
      box-shadow: none;
    }}
    .eyebrow {{
      color: var(--muted);
      font-family: var(--av-font-sans, Arial, sans-serif);
      font-size: 12px;
      font-weight: 700;
      text-transform: none;
      letter-spacing: 0;
    }}
    h1 {{
      margin: 0;
      font-family: var(--av-font-sans, Arial, sans-serif);
      max-width: 20ch;
      font-size: clamp(26px, 3vw, 38px);
      line-height: 1.08;
      text-wrap: balance;
    }}
    .hero p {{
      margin: 0;
      max-width: 72ch;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.55;
    }}
    .stat-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 0;
    }}
    .stat {{
      border: 0;
      border-left: 1px solid var(--line);
      border-radius: 0;
      background: transparent;
      padding: 8px 10px;
    }}
    .stat:first-child {{ border-left: 0; }}
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
      font-size: 16px;
      line-height: 1.05;
      font-family: var(--av-font-sans, Arial, sans-serif);
    }}
    .section {{
      padding-top: 22px;
      margin-top: 22px;
      border-top: 1px solid var(--line);
    }}
    .section h2 {{
      margin: 0 0 8px;
      font-family: var(--av-font-sans, Arial, sans-serif);
      font-size: 17px;
      line-height: 1.2;
    }}
    .section p.section-note {{
      margin: 0 0 10px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.45;
    }}
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
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}
    .opportunity-card {{
      display: grid;
      align-content: start;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-md);
      background: var(--panel);
      padding: 14px;
    }}
    .opportunity-head {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 8px;
      align-items: start;
      margin-bottom: 8px;
    }}
    .opportunity-card h3 {{
      margin: 0 0 8px;
      font-size: 16px;
      line-height: 1.25;
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
      font-size: 13px;
      line-height: 1.45;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .card-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
      align-self: end;
    }}
    .button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 34px;
      padding: 0 12px;
      border: 1px solid transparent;
      border-radius: var(--av-radius-md);
      background: var(--brand);
      color: white;
      text-decoration: none;
      font-size: 14px;
      font-weight: 650;
    }}
    .button.soft {{
      background: var(--brand-soft);
      color: var(--brand);
      border-color: transparent;
    }}
    .source-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 0;
    }}
    .source-link {{
      display: grid;
      gap: 4px;
      padding: 12px 4px;
      border: 0;
      border-bottom: 1px solid var(--line);
      border-radius: 0;
      background: transparent;
      text-decoration: none;
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
      gap: 4px;
      margin-top: 28px;
      padding-top: 16px;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }}
    .site-footer p {{ margin: 0; }}
    .site-footer a {{ color: var(--ink); font-weight: 700; }}
    @media (max-width: 900px) {{
      .opportunity-list {{
        grid-template-columns: 1fr;
      }}
      .source-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
    }}
    @media (max-width: 640px) {{
      .shell {{
        width: min(100%, calc(100% - 24px));
        padding-top: 16px;
      }}
      .hero {{
        padding: 12px;
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
    }}
  </style>
</head>
<body>
  <main class="shell">
    <div class="topbar">
      <a class="back-link" href="{catalog_href}">{back_label}</a>
      <nav class="lang-switch" aria-label="{escape(str(copy['language_switch']), quote=True)}">
        <a class="{ru_lang_class}" href="{ru_href}" lang="ru">RU</a>
        <a class="{en_lang_class}" href="{en_href}" lang="en">EN</a>
      </nav>
    </div>
    <section class="hero">
      <span class="eyebrow">{escape(str(copy["funder_page_eyebrow"]))}</span>
      <div>
        <h1>{funder_name}</h1>
        <p>{overview}</p>
      </div>
      <div class="topic-row">{tag_chips}</div>
      <div class="stat-grid">{stat_markup}</div>
    </section>

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
      <p>
        {escape(str(copy["footer_owner"]))}
        <a href="https://qdev.run">{escape(str(copy["footer_qdev"]))}</a>
      </p>
      <p>{escape(str(copy["footer_disclaimer"]))}</p>
    </footer>
  </main>
</body>
</html>"""
