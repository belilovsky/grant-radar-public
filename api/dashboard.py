"""Server-rendered public dashboard shell for Grant Radar."""

from __future__ import annotations

import json
from html import escape
from typing import Any, Mapping

from api.avds import AVDS_CSS, AVDS_FONT_HEAD
from api.dashboard_copy import dashboard_copy
from api.dashboard_style import DASHBOARD_CSS
from api.public_meta import analytics_head_html, og_image_url

GOOGLE_SITE_VERIFICATION_FILENAME = "google6ce0cb641d438c0c.html"
GOOGLE_SITE_VERIFICATION_CONTENT = (
    f"google-site-verification: {GOOGLE_SITE_VERIFICATION_FILENAME}"
)
YANDEX_SITE_VERIFICATION_TOKEN = "01df12ab51cd6b70"  # nosec B105


def _root_href(base: str, lang: str) -> str:
    if base:
        return f"{base}/?lang={lang}"
    return f"/?lang={lang}"


def _absolute_href(origin: str, path: str) -> str:
    clean_origin = origin.rstrip("/")
    if not path:
        return clean_origin or "/"
    if path.startswith(("http://", "https://")):
        return path
    return f"{clean_origin}{path}" if clean_origin else path


def _json_ld(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")


def _dashboard_schema(
    *,
    copy: dict[str, object],
    canonical_href: str,
    ru_href: str,
    en_href: str,
    items: int,
) -> str:
    organization_id = f"{canonical_href}#organization"
    website_id = f"{canonical_href}#website"
    page_id = f"{canonical_href}#page"
    catalog_id = f"{canonical_href}#catalog"
    faq_id = f"{canonical_href}#faq"
    payload = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": organization_id,
                "name": str(copy["title"]),
                "url": canonical_href,
                "description": str(copy["meta_description"]),
            },
            {
                "@type": "WebSite",
                "@id": website_id,
                "url": canonical_href,
                "name": str(copy["title"]),
                "description": str(copy["meta_description"]),
                "inLanguage": str(copy["lang"]),
                "publisher": {"@id": organization_id},
            },
            {
                "@type": "CollectionPage",
                "@id": page_id,
                "url": canonical_href,
                "name": str(copy["headline"]),
                "description": str(copy["meta_description"]),
                "inLanguage": str(copy["lang"]),
                "isPartOf": {"@id": website_id},
                "mainEntity": {"@id": catalog_id},
            },
            {
                "@type": "ItemList",
                "@id": catalog_id,
                "name": str(copy["opportunities_title"]),
                "description": str(copy["opportunities_description"]),
                "url": canonical_href,
                "numberOfItems": items,
            },
            {
                "@type": "FAQPage",
                "@id": faq_id,
                "url": f"{canonical_href}#methodology-panel",
                "inLanguage": str(copy["lang"]),
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": str(copy["faq_q1"]),
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": str(copy["faq_a1"]),
                        },
                    },
                    {
                        "@type": "Question",
                        "name": str(copy["faq_q2"]),
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": str(copy["faq_a2"]),
                        },
                    },
                    {
                        "@type": "Question",
                        "name": str(copy["faq_q3"]),
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": str(copy["faq_a3"]),
                        },
                    },
                    {
                        "@type": "Question",
                        "name": str(copy["faq_q4"]),
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": str(copy["faq_a4"]),
                        },
                    },
                ],
            },
        ],
    }
    # Keep explicit alternate URLs in the graph for crawlers that cross-check.
    payload["@graph"][1]["hasPart"] = [  # type: ignore[index]
        {"@type": "WebPage", "url": ru_href, "inLanguage": "ru"},
        {"@type": "WebPage", "url": en_href, "inLanguage": "en"},
    ]
    return _json_ld(payload)


def render_dashboard(
    *,
    root_path: str,
    items: int,
    relevant_items: int = 0,
    source_count: int = 0,
    lang: str = "ru",
    site_origin: str = "",
) -> str:
    copy = dashboard_copy(lang)
    base_raw = root_path.rstrip("/")
    base = escape(base_raw, quote=True)
    active_lang = str(copy["lang"])
    docs_path = (
        f"{base_raw}/docs?lang={active_lang}"
        if base_raw
        else f"/docs?lang={active_lang}"
    )
    docs_href = escape(docs_path, quote=True)
    status_path = (
        f"{base_raw}/status?lang={active_lang}"
        if base_raw
        else f"/status?lang={active_lang}"
    )
    status_href = escape(status_path, quote=True)
    ru_href = escape(_root_href(base_raw, "ru"), quote=True)
    en_href = escape(_root_href(base_raw, "en"), quote=True)
    canonical_path = _root_href(base_raw, active_lang)
    canonical_href = escape(_absolute_href(site_origin, canonical_path), quote=True)
    ru_canonical = escape(
        _absolute_href(site_origin, _root_href(base_raw, "ru")),
        quote=True,
    )
    en_canonical = escape(
        _absolute_href(site_origin, _root_href(base_raw, "en")),
        quote=True,
    )
    schema_json = _dashboard_schema(
        copy=copy,
        canonical_href=_absolute_href(site_origin, canonical_path),
        ru_href=_absolute_href(site_origin, _root_href(base_raw, "ru")),
        en_href=_absolute_href(site_origin, _root_href(base_raw, "en")),
        items=items,
    )
    copy_json = json.dumps(copy, ensure_ascii=False)
    html_lang = escape(active_lang, quote=True)
    og_locale = escape(active_lang.replace("-", "_") + "_KZ", quote=True)
    social_image = escape(og_image_url(site_origin, base_raw), quote=True)
    analytics_head = analytics_head_html()
    html_theme_attrs = (
        'data-avds="grant-radar" data-av-theme="light" data-theme="light"'
    )
    language_switch_label = escape(str(copy["language_switch"]), quote=True)
    loading_sources_label = escape(str(copy["loading_sources"]))
    initial_health_status = escape(str(copy["status_checking"]))
    initial_health_items = escape(str(items))
    initial_health_sources = escape(str(source_count))
    lang_ru_class = "lang-link active" if active_lang == "ru" else "lang-link"
    lang_en_class = "lang-link active" if active_lang == "en" else "lang-link"
    lang_ru_current = ' aria-current="true"' if active_lang == "ru" else ""
    lang_en_current = ' aria-current="true"' if active_lang == "en" else ""

    def initial_preset_buttons(
        kind: str,
        presets: tuple[tuple[str, str], ...],
    ) -> str:
        return "".join(
            (
                '<button class="preset-button" type="button" '
                f'data-preset-kind="{kind}" data-preset-id="{preset_id}" '
                f'aria-pressed="{str(preset_id == "all").lower()}" '
                'data-avds-component="preset-button">'
                f"{escape(str(copy[label_key]))}</button>"
            )
            for preset_id, label_key in presets
        )

    initial_audience_presets = initial_preset_buttons(
        "audience",
        (
            ("all", "audience_all"),
            ("startup", "audience_startup"),
            ("business", "audience_business"),
            ("farmer", "audience_farmer"),
            ("ngo", "audience_ngo"),
            ("science", "audience_science"),
        ),
    )
    initial_format_presets = initial_preset_buttons(
        "format",
        (
            ("all", "format_all"),
            ("grants", "format_grants"),
            ("support", "format_support"),
            ("accelerators", "format_accelerators"),
            ("tenders", "format_tenders"),
        ),
    )
    initial_topic_presets = initial_preset_buttons(
        "topic",
        (
            ("all", "topic_all"),
            ("ai", "topic_ai"),
            ("agro", "topic_agro"),
            ("science", "topic_science"),
            ("public", "topic_public"),
            ("ngo", "topic_ngo"),
            ("business", "topic_business"),
        ),
    )

    return f"""<!doctype html>
<html lang="{html_lang}" {html_theme_attrs}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <script>
    if (window.matchMedia("(max-width: 760px)").matches) {{
      document.documentElement.dataset.compactFilters = "true";
    }}
  </script>
  <title>{escape(str(copy["title"]))}</title>
  <meta name="description" content="{escape(str(copy["meta_description"]), quote=True)}">
  <meta name="yandex-verification" content="{YANDEX_SITE_VERIFICATION_TOKEN}">
  <link rel="canonical" href="{canonical_href}">
  <link rel="alternate" hreflang="ru" href="{ru_canonical}">
  <link rel="alternate" hreflang="en" href="{en_canonical}">
  <link rel="alternate" hreflang="x-default" href="{ru_canonical}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{escape(str(copy["title"]), quote=True)}">
  <meta property="og:description" content="{escape(str(copy["meta_description"]), quote=True)}">
  <meta property="og:url" content="{canonical_href}">
  <meta property="og:image" content="{social_image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:locale" content="{og_locale}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{escape(str(copy["title"]), quote=True)}">
  <meta name="twitter:description" content="{escape(str(copy["meta_description"]), quote=True)}">
  <meta name="twitter:image" content="{social_image}">
  <script type="application/ld+json">{schema_json}</script>
{analytics_head}
{AVDS_FONT_HEAD}
  <style>
{AVDS_CSS}
{DASHBOARD_CSS}  </style>
</head>
<body>
  <main
    class="shell"
    id="main-content"
    data-api-base="{base}"
    data-lang="{escape(active_lang, quote=True)}"
    data-avds-component="admin-shell"
  >
    <section class="hero-band" data-avds-component="hero-band">
      <header class="topbar" data-avds-component="topbar">
        <div class="brand">
          <span class="eyebrow">{escape(str(copy["eyebrow"]))}</span>
          <div class="brand-row">
            <h1>{escape(str(copy["headline"]))}</h1>
          </div>
          <p>{escape(str(copy["subtitle"]))}</p>
          <div class="focus-row" aria-label="{escape(str(copy["focus_aria"]), quote=True)}">
            <span class="focus-chip">{escape(str(copy["focus_primary"]))}</span>
            <span class="focus-chip">{escape(str(copy["focus_secondary"]))}</span>
          </div>
        </div>
      </header>
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="hero-intro">{escape(str(copy["hero_intro"]))}</p>
          <div class="hero-actions">
            <button
              class="button primary"
              type="button"
              data-hero-reset="true"
              data-hero-view="opportunities"
              data-avds-component="button"
            >{escape(str(copy["hero_primary_cta"]))}</button>
          </div>
          <div class="hero-points" aria-label="{escape(str(copy["hero_stage_title"]), quote=True)}">
            <div class="hero-point">
              <span class="hero-point-index">01</span>
              <span>{escape(str(copy["hero_stage_point_one"]))}</span>
            </div>
            <div class="hero-point">
              <span class="hero-point-index">02</span>
              <span>{escape(str(copy["hero_stage_point_two"]))}</span>
            </div>
            <div class="hero-point">
              <span class="hero-point-index">03</span>
              <span>{escape(str(copy["hero_stage_point_three"]))}</span>
            </div>
          </div>
        </div>
        <section
          class="hero-stage"
          aria-label="{escape(str(copy["hero_picks_label"]), quote=True)}"
        >
          <span class="hero-stage-eyebrow">{escape(str(copy["hero_stage_eyebrow"]))}</span>
          <h2 class="hero-stage-title">{escape(str(copy["hero_stage_title"]))}</h2>
          <div class="hero-picks">
            <div class="hero-pick-row">
              <button
                class="button hero-pick"
                type="button"
                data-hero-reset="true"
                data-hero-view="opportunities"
                data-avds-component="button"
              >{escape(str(copy["hero_pick_startup"]))}</button>
              <button
                class="button hero-pick"
                type="button"
                data-hero-reset="true"
                data-hero-view="opportunities"
                data-hero-focus="search"
                data-avds-component="button"
              >{escape(str(copy["hero_pick_business"]))}</button>
              <button
                class="button hero-pick"
                type="button"
                data-hero-reset="true"
                data-hero-view="opportunities"
                data-hero-deadline="month"
                data-hero-sort="deadline"
                data-avds-component="button"
              >{escape(str(copy["hero_pick_farmer"]))}</button>
              <button
                class="button hero-pick"
                type="button"
                data-hero-reset="true"
                data-hero-view="opportunities"
                data-hero-format="support"
                data-hero-region="kazakhstan"
                data-avds-component="button"
              >{escape(str(copy["hero_pick_science"]))}</button>
              <button
                class="button hero-pick"
                type="button"
                data-hero-reset="true"
                data-hero-view="opportunities"
                data-hero-format="tenders"
                data-hero-topic="public"
                data-hero-region="kazakhstan"
                data-avds-component="button"
              >{escape(str(copy["hero_pick_tenders"]))}</button>
            </div>
          </div>
        </section>
      </div>

      <section class="grid" aria-label="{escape(str(copy["metrics_aria"]), quote=True)}">
        <div class="metric avds-stat-kpi-card" data-avds-component="metric-card">
          <span>{escape(str(copy["metric_total"]))}</span>
          <strong id="metric-total">{items}</strong>
        </div>
        <div class="metric strong avds-stat-kpi-card" data-avds-component="metric-card">
          <span>{escape(str(copy["metric_relevant"]))}</span>
          <strong id="metric-strong" data-catalog-count="{relevant_items}">{relevant_items}</strong>
        </div>
        <div class="metric sources avds-stat-kpi-card" data-avds-component="metric-card">
          <span>{escape(str(copy["metric_sources"]))}</span>
          <strong id="metric-sources">{source_count}</strong>
        </div>
      </section>
    </section>

    <div class="sticky-shell" data-avds-component="sticky-shell">
      <div class="sticky-bar">
        <nav
          class="toolbar avds-tabs-list"
          aria-label="{escape(str(copy["views_aria"]), quote=True)}"
          data-avds-component="toolbar"
        >
          <button
            class="button tab avds-tabs-trigger"
            type="button"
            data-view="opportunities"
            data-avds-component="button"
            aria-pressed="true"
          >{escape(str(copy["tab_opportunities"]))}</button>
          <button
            class="button tab avds-tabs-trigger"
            type="button"
            data-view="sources"
            data-avds-component="button"
          >{escape(str(copy["tab_sources"]))}</button>
        </nav>
        <div class="sticky-actions">
          <div class="status-pill" id="status-pill" data-avds-component="status-pill">
            <span class="status-dot"></span>
            <span>{escape(str(copy["status_checking"]))}</span>
          </div>
          <div class="topbar-actions">
            <div class="utility-links">
              <a class="utility-link" href="{docs_href}">{escape(str(copy["api_docs"]))}</a>
              <a class="utility-link" href="#methodology-panel"
                >{escape(str(copy["methodology_link"]))}</a
              >
              <a class="utility-link" href="{status_href}">{escape(str(copy["status_link"]))}</a>
            </div>
            <div class="lang-switch" role="group" aria-label="{language_switch_label}">
              <a
                class="{lang_ru_class}"
                href="{ru_href}"
                hreflang="ru"
                lang="ru"
                {lang_ru_current}
              >RU</a>
              <a
                class="{lang_en_class}"
                href="{en_href}"
                hreflang="en"
                lang="en"
                {lang_en_current}
              >EN</a>
            </div>
          </div>
        </div>
      </div>
    </div>

    <section class="panel primary" id="opportunities-panel" data-avds-component="panel">
      <div class="panel-head">
        <div>
          <h2>{escape(str(copy["opportunities_title"]))}</h2>
          <p id="opportunities-description">{escape(str(copy["opportunities_description"]))}</p>
        </div>
      </div>
      <details class="filter-disclosure" id="filter-disclosure" open>
        <summary>{escape(str(copy["mobile_filters_summary"]))}</summary>
        <div class="filter-disclosure-body">
      <div class="preset-grid">
        <div class="preset-group" aria-label="{escape(str(copy["audience_aria"]), quote=True)}">
          <span class="filter-label">{escape(str(copy["audience_label"]))}</span>
          <div
            class="preset-row"
            id="audience-presets"
            data-avds-component="preset-row"
          >{initial_audience_presets}</div>
        </div>
        <div class="preset-group" aria-label="{escape(str(copy["format_aria"]), quote=True)}">
          <span class="filter-label">{escape(str(copy["format_label"]))}</span>
          <div
            class="preset-row"
            id="format-presets"
            data-avds-component="preset-row"
          >{initial_format_presets}</div>
        </div>
        <div class="preset-group" aria-label="{escape(str(copy["topic_aria"]), quote=True)}">
          <span class="filter-label">{escape(str(copy["topic_label"]))}</span>
          <div
            class="preset-row"
            id="topic-presets"
            data-avds-component="preset-row"
          >{initial_topic_presets}</div>
        </div>
      </div>
      <div
        class="filters-shell"
        aria-label="{escape(str(copy["opportunities_title"]), quote=True)}"
      >
        <div class="filters primary-filters">
          <label class="filter-block" for="search">
            <span class="filter-label">{escape(str(copy["search_label"]))}</span>
            <input
              class="field avds-field"
              id="search"
              type="search"
              placeholder="{escape(str(copy["search_placeholder"]), quote=True)}"
              data-avds-component="field"
            >
          </label>
          <label class="filter-block" for="region-filter">
            <span class="filter-label">{escape(str(copy["region_label"]))}</span>
            <select
              class="field avds-field"
              id="region-filter"
              aria-label="{escape(str(copy["region_aria"]), quote=True)}"
              data-avds-component="field"
            >
              <option value="all" selected>{escape(str(copy["region_all"]))}</option>
              <option value="kazakhstan">{escape(str(copy["region_kazakhstan"]))}</option>
              <option value="central_asia">{escape(str(copy["region_central_asia"]))}</option>
              <option value="global">{escape(str(copy["region_global"]))}</option>
            </select>
          </label>
          <label class="filter-block" for="scope-filter">
            <span class="filter-label">{escape(str(copy["scope_label"]))}</span>
            <select
              class="field avds-field"
              id="scope-filter"
              aria-label="{escape(str(copy["scope_aria"]), quote=True)}"
              data-avds-component="field"
            >
              <option value="open" selected>{escape(str(copy["scope_open"]))}</option>
              <option value="all">{escape(str(copy["scope_all"]))}</option>
            </select>
          </label>
        </div>
        <details class="advanced-filters">
          <summary>{escape(str(copy["advanced_filters"]))}</summary>
          <div class="filters">
            <label class="filter-block" for="lifecycle-filter">
              <span class="filter-label">{escape(str(copy["lifecycle_label"]))}</span>
              <select
                class="field avds-field"
                id="lifecycle-filter"
                aria-label="{escape(str(copy["lifecycle_aria"]), quote=True)}"
                data-avds-component="field"
              >
                <option value="all" selected>{escape(str(copy["lifecycle_all"]))}</option>
                <option value="open">{escape(str(copy["lifecycle_open"]))}</option>
                <option value="forecast">{escape(str(copy["lifecycle_forecast"]))}</option>
                <option value="closing_soon">{escape(str(copy["lifecycle_closing_soon"]))}</option>
                <option value="rolling">{escape(str(copy["lifecycle_rolling"]))}</option>
                <option value="closed">{escape(str(copy["lifecycle_closed"]))}</option>
                <option value="awarded">{escape(str(copy["lifecycle_awarded"]))}</option>
              </select>
            </label>
            <label class="filter-block" for="deadline-filter">
              <span class="filter-label">{escape(str(copy["deadline_filter_label"]))}</span>
              <select
                class="field avds-field"
                id="deadline-filter"
                aria-label="{escape(str(copy["deadline_filter_aria"]), quote=True)}"
                data-avds-component="field"
              >
                <option value="all" selected>{escape(str(copy["deadline_filter_all"]))}</option>
                <option value="soon">{escape(str(copy["deadline_filter_soon"]))}</option>
                <option value="month">{escape(str(copy["deadline_filter_month"]))}</option>
                <option value="rolling">{escape(str(copy["deadline_filter_rolling"]))}</option>
              </select>
            </label>
            <label class="filter-block" for="sort-filter">
              <span class="filter-label">{escape(str(copy["sort_label"]))}</span>
              <select
                class="field avds-field"
                id="sort-filter"
                aria-label="{escape(str(copy["sort_aria"]), quote=True)}"
                data-avds-component="field"
              >
                <option value="priority" selected>{escape(str(copy["sort_priority"]))}</option>
                <option value="deadline">{escape(str(copy["sort_deadline"]))}</option>
                <option value="updated">{escape(str(copy["sort_updated"]))}</option>
              </select>
            </label>
            <label class="filter-block" for="score-filter">
              <span class="filter-label">{escape(str(copy["min_score_label"]))}</span>
              <select
                class="field avds-field"
                id="score-filter"
                aria-label="{escape(str(copy["min_score_aria"]), quote=True)}"
                data-avds-component="field"
              >
                <option value="0">{escape(str(copy["all_scores"]))}</option>
                <option value="0.3" selected>{escape(str(copy["score_option_03"]))}</option>
                <option value="0.5">{escape(str(copy["score_option_05"]))}</option>
                <option value="0.7">{escape(str(copy["score_option_07"]))}</option>
              </select>
              <span class="filter-help">{escape(str(copy["score_help"]))}</span>
            </label>
            <label class="filter-block" for="source-filter">
              <span class="filter-label">{escape(str(copy["source_label"]))}</span>
              <select
                class="field avds-field"
                id="source-filter"
                aria-label="{escape(str(copy["source_aria"]), quote=True)}"
                data-avds-component="field"
              >
                <option value="all">{escape(str(copy["all_sources"]))}</option>
              </select>
            </label>
          </div>
        </details>
      </div>
        </div>
      </details>
      <div class="filters-meta">
        <div id="filter-summary" class="filter-summary" data-avds-component="filter-summary"></div>
        <button
          class="text-button"
          type="button"
          id="clear-filters"
          data-avds-component="button"
        >{escape(str(copy["clear_filters"]))}</button>
      </div>
      <div
        class="saved-views"
        aria-label="{escape(str(copy["collections_aria"]), quote=True)}"
        data-avds-component="saved-views"
      >
        <div class="saved-views-head">
          <span class="filter-label">{escape(str(copy["collections_label"]))}</span>
          <div class="saved-actions">
            <button
              class="text-button workspace-filter"
              type="button"
              id="workspace-filter"
              aria-pressed="false"
              data-avds-component="button"
            >{escape(str(copy["workspace_filter"]))}</button>
            <details class="workspace-backup" id="workspace-backup">
              <summary
                class="text-button"
                aria-label="{escape(str(copy["workspace_backup_aria"]), quote=True)}"
              >{escape(str(copy["workspace_backup"]))}</summary>
              <div
                class="workspace-backup-menu"
                role="group"
                aria-label="{escape(str(copy["workspace_backup_aria"]), quote=True)}"
              >
                <button class="text-button" type="button" id="export-csv">
                  {escape(str(copy["export_csv"]))}
                </button>
                <button class="text-button" type="button" id="export-deadlines">
                  {escape(str(copy["export_deadlines"]))}
                </button>
                <button class="text-button" type="button" id="export-workspace">
                  {escape(str(copy["workspace_export"]))}
                </button>
                <label class="text-button" for="import-workspace">
                  {escape(str(copy["workspace_import"]))}
                </label>
                <input
                  class="visually-hidden"
                  type="file"
                  id="import-workspace"
                  accept="application/json,.json"
                >
              </div>
            </details>
            <button
              class="text-button"
              type="button"
              id="save-view"
              data-avds-component="button"
            >{escape(str(copy["save_view"]))}</button>
            <button
              class="text-button"
              type="button"
              id="share-view"
              data-avds-component="button"
            >{escape(str(copy["share_view"]))}</button>
          </div>
        </div>
        <div id="saved-views" class="saved-view-row">
          <span class="saved-empty">{escape(str(copy["collections_empty"]))}</span>
        </div>
        <div
          id="saved-view-notice"
          class="saved-view-notice hidden"
          aria-live="polite"
          aria-label="{escape(str(copy["saved_view_status_label"]), quote=True)}"
        ></div>
      </div>
      <section
        class="workspace-queue"
        id="workspace-queue"
        aria-label="{escape(str(copy["workspace_queue_aria"]), quote=True)}"
        hidden
      >
        <div class="workspace-queue-head">
          <h2 class="workspace-queue-title">{escape(str(copy["workspace_queue_title"]))}</h2>
          <span class="workspace-queue-local">{escape(str(copy["workspace_queue_local"]))}</span>
        </div>
        <div class="workspace-queue-list" id="workspace-queue-list"></div>
        <span class="workspace-queue-more" id="workspace-queue-more"></span>
      </section>
      <div
        id="topic-brief"
        class="topic-brief hidden"
        data-avds-component="topic-brief"
      ></div>
      <div
        id="opportunities-message"
        class="message loading-state"
        data-avds-component="message"
        aria-label="{escape(str(copy["loading_opportunities"]), quote=True)}"
      ><span class="visually-hidden">{escape(str(copy["loading_opportunities"]))}</span></div>
      <div id="opportunities-list" class="list" aria-live="polite"></div>
      <div id="load-more-wrap" class="list-actions hidden">
        <button
          class="button slim"
          type="button"
          id="load-more"
          data-avds-component="button"
        >{escape(str(copy["load_more"]))}</button>
      </div>
    </section>

    <details class="discovery-library" data-avds-component="discovery-library">
      <summary>
        <span>{escape(str(copy["discovery_library_summary"]))}</span>
        <span class="discovery-library-description">
          {escape(str(copy["discovery_library_description"]))}
        </span>
      </summary>
      <div class="discovery-library-body">
        <section class="spotlight-section" aria-labelledby="spotlight-title">
          <div class="spotlight-copy">
            <span class="eyebrow">{escape(str(copy["spotlight_section_eyebrow"]))}</span>
            <h2 id="spotlight-title">{escape(str(copy["spotlight_section_title"]))}</h2>
            <p>{escape(str(copy["spotlight_section_description"]))}</p>
          </div>
          <div
            class="spotlight-grid async-grid"
            id="spotlight-grid"
            data-avds-component="spotlight-grid"
            aria-busy="true"
          ></div>
        </section>

        <div class="discovery-grid" data-avds-component="discovery-grid">
          <section class="pathways-section" aria-labelledby="pathways-title">
            <div class="spotlight-copy">
              <span class="eyebrow">{escape(str(copy["pathways_section_eyebrow"]))}</span>
              <h2 id="pathways-title">{escape(str(copy["pathways_section_title"]))}</h2>
              <p>{escape(str(copy["pathways_section_description"]))}</p>
            </div>
            <div
              class="pathways-grid async-grid"
              id="pathways-grid"
              data-avds-component="pathways-grid"
              aria-busy="true"
            ></div>
          </section>

          <section class="themes-section" aria-labelledby="themes-title">
            <div class="spotlight-copy">
              <span class="eyebrow">{escape(str(copy["themes_section_eyebrow"]))}</span>
              <h2 id="themes-title">{escape(str(copy["themes_section_title"]))}</h2>
              <p>{escape(str(copy["themes_section_description"]))}</p>
            </div>
            <div
              class="themes-grid async-grid"
              id="themes-grid"
              data-avds-component="themes-grid"
              aria-busy="true"
            ></div>
          </section>
        </div>
      </div>
    </details>

    <details
      class="trust-library"
      id="trust-library"
      data-avds-component="trust-library"
    >
      <summary>
        <span>{escape(str(copy["trust_library_summary"]))}</span>
        <span class="trust-library-description">
          {escape(str(copy["trust_library_description"]))}
        </span>
      </summary>
      <div class="trust-library-body">
    <section class="funder-section" aria-labelledby="funders-title">
      <div class="spotlight-copy">
        <span class="eyebrow">{escape(str(copy["funder_section_eyebrow"]))}</span>
        <h2 id="funders-title">{escape(str(copy["funder_section_title"]))}</h2>
        <p>{escape(str(copy["funder_section_description"]))}</p>
      </div>
      <div
        class="funder-grid async-grid"
        id="funder-grid"
        data-avds-component="funder-grid"
        aria-busy="true"
      ></div>
    </section>

    <section class="panel" id="sources-panel" data-avds-component="panel">
      <div class="panel-head">
        <div>
          <h2>{escape(str(copy["sources_title"]))}</h2>
          <p>{escape(str(copy["sources_description"]))}</p>
        </div>
        <div class="panel-actions">
          <span class="panel-summary" id="source-summary">{loading_sources_label}</span>
          <button
            class="button slim"
            type="button"
            id="toggle-sources"
            data-avds-component="button"
          >{escape(str(copy["show_all_sources"]))}</button>
        </div>
      </div>
      <div id="source-list" class="source-grid"></div>
    </section>

    <section class="panel" id="health-panel" data-avds-component="panel">
      <div class="panel-head">
        <div>
          <h2>{escape(str(copy["health_title"]))}</h2>
          <p>{escape(str(copy["health_description"]))}</p>
        </div>
        <div class="panel-actions">
          <button
            class="button slim"
            type="button"
            id="reload"
            data-avds-component="button"
          >{escape(str(copy["reload_live_data"]))}</button>
        </div>
      </div>
      <div class="health-grid">
        <div class="health-item avds-stat-kpi-card" data-avds-component="health-card">
          <span>{escape(str(copy["api_status"]))}</span>
          <strong id="health-status">{initial_health_status}</strong>
        </div>
        <div class="health-item avds-stat-kpi-card" data-avds-component="health-card">
          <span>{escape(str(copy["stored_items"]))}</span>
          <strong id="health-items">{initial_health_items}</strong>
        </div>
        <div class="health-item avds-stat-kpi-card" data-avds-component="health-card">
          <span>{escape(str(copy["health_sources"]))}</span>
          <strong id="health-sources">{initial_health_sources}</strong>
        </div>
        <div class="health-item avds-stat-kpi-card" data-avds-component="health-card">
          <span>{escape(str(copy["health_stale_sources"]))}</span>
          <strong id="health-stale-sources">0</strong>
        </div>
      </div>
      <p class="health-note" id="health-note">{escape(str(copy["health_note_loading"]))}</p>
    </section>

    <section class="panel" id="methodology-panel" data-avds-component="panel">
      <div class="panel-head">
        <div>
          <h2>{escape(str(copy["methodology_title"]))}</h2>
          <p>{escape(str(copy["methodology_description"]))}</p>
        </div>
      </div>
      <div class="method-grid" data-avds-component="method-grid">
        <article class="method-card" data-avds-component="method-card">
          <h3>{escape(str(copy["method_card_sources_title"]))}</h3>
          <p>{escape(str(copy["method_card_sources_text"]))}</p>
        </article>
        <article class="method-card" data-avds-component="method-card">
          <h3>{escape(str(copy["method_card_relevance_title"]))}</h3>
          <p>{escape(str(copy["method_card_relevance_text"]))}</p>
        </article>
        <article class="method-card" data-avds-component="method-card">
          <h3>{escape(str(copy["method_card_trust_title"]))}</h3>
          <p>{escape(str(copy["method_card_trust_text"]))}</p>
        </article>
      </div>
      <div class="method-disclaimer" data-avds-component="method-disclaimer">
        <strong>{escape(str(copy["method_disclaimer_title"]))}</strong>
        <p>{escape(str(copy["method_disclaimer_text"]))}</p>
      </div>
      <section class="role-guide" data-avds-component="role-guide">
        <div class="role-guide-head">
          <h3>{escape(str(copy["role_guide_title"]))}</h3>
          <p>{escape(str(copy["role_guide_description"]))}</p>
        </div>
        <div class="role-list">
          <article class="role-item">
            <h4>{escape(str(copy["role_analyst_title"]))}</h4>
            <p>{escape(str(copy["role_analyst_text"]))}</p>
          </article>
          <article class="role-item">
            <h4>{escape(str(copy["role_journalist_title"]))}</h4>
            <p>{escape(str(copy["role_journalist_text"]))}</p>
          </article>
          <article class="role-item">
            <h4>{escape(str(copy["role_editor_title"]))}</h4>
            <p>{escape(str(copy["role_editor_text"]))}</p>
          </article>
          <article class="role-item">
            <h4>{escape(str(copy["role_lawyer_title"]))}</h4>
            <p>{escape(str(copy["role_lawyer_text"]))}</p>
          </article>
          <article class="role-item">
            <h4>{escape(str(copy["role_official_title"]))}</h4>
            <p>{escape(str(copy["role_official_text"]))}</p>
          </article>
        </div>
      </section>
      <div class="faq-list" data-avds-component="faq-list">
        <article class="faq-item">
          <h3>{escape(str(copy["faq_q1"]))}</h3>
          <p>{escape(str(copy["faq_a1"]))}</p>
        </article>
        <article class="faq-item">
          <h3>{escape(str(copy["faq_q2"]))}</h3>
          <p>{escape(str(copy["faq_a2"]))}</p>
        </article>
        <article class="faq-item">
          <h3>{escape(str(copy["faq_q3"]))}</h3>
          <p>{escape(str(copy["faq_a3"]))}</p>
        </article>
        <article class="faq-item">
          <h3>{escape(str(copy["faq_q4"]))}</h3>
          <p>{escape(str(copy["faq_a4"]))}</p>
        </article>
      </div>
    </section>
      </div>
    </details>
    <footer class="site-footer" data-avds-component="site-footer">
      <p>
        {escape(str(copy["footer_owner"]))}
        <a href="https://qdev.run" target="_blank" rel="noopener">
          {escape(str(copy["footer_qdev"]))}
        </a>
      </p>
      <p>{escape(str(copy["footer_disclaimer"]))}</p>
      <p>
        <a
          href="https://github.com/belilovsky/grant-radar-public/issues"
          target="_blank"
          rel="noopener"
        >
          {escape(str(copy["footer_support"]))}
        </a>
      </p>
    </footer>
  </main>

  <div
    class="detail-backdrop"
    id="detail-backdrop"
    hidden
    aria-hidden="true"
  ></div>
  <aside
    class="detail-drawer"
    id="detail-drawer"
    role="dialog"
    aria-modal="true"
    hidden
    aria-hidden="true"
    aria-label="{escape(str(copy["detail_panel_label"]), quote=True)}"
  >
    <div class="detail-header">
      <div>
        <span class="eyebrow">{escape(str(copy["detail_shell_title"]))}</span>
        <h2 id="detail-title">{escape(str(copy["detail_title_fallback"]))}</h2>
        <p class="detail-status" id="detail-status">{escape(str(copy["detail_loading"]))}</p>
      </div>
      <button
        class="button slim detail-close"
        type="button"
        id="detail-close"
        data-avds-component="button"
      >{escape(str(copy["detail_close"]))}</button>
    </div>
    <div class="detail-body">
      <div class="detail-empty" id="detail-empty">{escape(str(copy["detail_loading"]))}</div>
      <div class="detail-fit hidden" id="detail-fit">
        <h3>{escape(str(copy["detail_fit_title"]))}</h3>
        <p id="detail-fit-summary">{escape(str(copy["detail_fit_review"]))}</p>
        <div class="fit-pills" id="detail-fit-pills"></div>
      </div>
      <div class="detail-readiness hidden" id="detail-readiness">
        <h3>{escape(str(copy["detail_readiness_title"]))}</h3>
        <p id="detail-readiness-text"></p>
      </div>
      <div class="detail-meta hidden" id="detail-meta">
        <h3>{escape(str(copy["detail_meta_title"]))}</h3>
        <div class="detail-meta-grid" id="detail-meta-grid"></div>
      </div>
      <div class="detail-sections hidden" id="detail-sections">
        <h3>{escape(str(copy["detail_sections_title"]))}</h3>
        <div class="detail-richtext" id="detail-sections-body"></div>
      </div>
    </div>
    <div class="detail-footer">
      <div class="detail-footer-actions">
        <a
          class="button slim soft"
          href="#"
          id="detail-open-page"
          data-avds-component="button"
        >{escape(str(copy["detail_open_page"]))}</a>
        <a
          class="button slim"
          href="#"
          id="detail-open-source"
          target="_blank"
          rel="noopener"
          data-avds-component="button"
        >{escape(str(copy["detail_open_source"]))}</a>
        <a
          class="button slim hidden"
          href="#"
          id="detail-open-application"
          target="_blank"
          rel="noopener"
          data-avds-component="button"
        >{escape(str(copy["detail_open_application"]))}</a>
      </div>
    </div>
  </aside>

  <script>
    const copy = {copy_json};
    const root = document.querySelector("[data-api-base]");
    const datasetApiBase = root.dataset.apiBase || "";
    const deriveApiBase = () => {{
      if (datasetApiBase) return datasetApiBase.replace(/\\/$/, "");
      const path = window.location.pathname || "/";
      if (!path || path === "/") return "";
      return path.endsWith("/") ? path.slice(0, -1) : path;
    }};
    const apiBase = deriveApiBase();
    const state = {{
      health: null,
      coverage: null,
      sources: [],
      sourcesLoaded: false,
      funders: [],
      items: [],
      sort: "priority",
      minScore: 0.3,
      query: "",
      source: "all",
      audience: "all",
      format: "all",
      topic: "all",
      lifecycle: "all",
      region: "all",
      deadlineMode: "all",
      includeArchived: false,
      savedOnly: false,
      showAllSources: false,
      visibleLimit: 15,
      lastCheckedAt: "",
      detailId: "",
      detailFallbackUrl: "",
      detailItem: null,
      detailTrigger: null
    }};
    const DEFAULT_SORT = "priority";
    const DEFAULT_SCORE = 0.3;
    const ALL_INDEX_SCORE = 0;
    const DEFAULT_AUDIENCE = "all";
    const DEFAULT_FORMAT = "all";
    const DEFAULT_TOPIC = "all";
    const DEFAULT_LIFECYCLE = "all";
    const DEFAULT_REGION = "all";
    const DEFAULT_DEADLINE = "all";
    const DEFAULT_VISIBLE_ITEMS = window.matchMedia("(max-width: 560px)").matches ? 6 : 8;
    const COLLAPSED_SOURCES = 5;
    const SAVED_VIEW_STORAGE_KEY = "grantRadarSavedViews.v1";
    const SAVED_OPPORTUNITY_STORAGE_KEY = "grantRadarSavedOpportunities.v1";
    const WORKFLOW_STORAGE_KEY = "grantRadarOpportunityWorkflow.v1";
    const WORKSPACE_QUEUE_LIMIT = 3;
    const WORKFLOW_STATUSES = [
      {{ id: "review", label: copy.workflow_review }},
      {{ id: "fit", label: copy.workflow_fit }},
      {{ id: "preparing", label: copy.workflow_preparing }},
      {{ id: "submitted", label: copy.workflow_submitted }},
      {{ id: "result", label: copy.workflow_result }}
    ];
    const SEARCH_STOP_WORDS = new Set([
      "для", "или", "и", "в", "на", "по", "из", "the", "for", "and", "or", "in"
    ]);
    const SEARCH_SYNONYM_GROUPS = [
      ["грант", "grant", "funding", "конкурс"],
      ["субсид", "subsid", "support", "мера"],
      ["тендер", "закуп", "procurement", "tender", "rfp"],
      ["ферм", "агро", "сельск", "farm", "agri", "agriculture"],
      ["нко", "ngo", "nonprofit", "civil_society"],
      ["исслед", "наук", "research", "science"],
      ["стартап", "startup", "accelerator", "акселератор"],
      ["ии", "ai", "artificial_intelligence", "machine_learning"],
      ["образован", "education", "edtech"],
      ["медиа", "журналист", "media", "journalism"]
    ];
    const formatNumber = new Intl.NumberFormat(copy.locale || "ru-KZ");
    const $ = (selector) => document.querySelector(selector);
    const labelMap = copy.label_map || copy.labelMap || {{}};
    const escapeHtml = (value) => String(value || "").replace(/[&<>"']/g, (char) => ({{
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    }}[char]));
    const interpolate = (template, values = {{}}) => Object.entries(values).reduce(
      (result, [key, value]) => result.split(`{{${{key}}}}`).join(String(value)),
      template || ""
    );
    const text = (key, values) => interpolate(copy[key] || "", values);
    const formatScore = (score) => {{
      const value = Number(score || 0);
      if (value >= 0.7) return copy.score_exact;
      if (value >= 0.5) return copy.score_high;
      return copy.score_base;
    }};
    const normalizeKey = (value) => String(value || "")
      .trim()
      .toLowerCase()
      .replace(/[\\s-]+/g, "_");
    const supportedLifecycleValues = new Set([
      "open",
      "forecast",
      "closing_soon",
      "rolling",
      "closed",
      "awarded"
    ]);
    const rawObject = (item) => (
      item && item.raw && typeof item.raw === "object" ? item.raw : {{}}
    );
    function fallbackFunderSlug(value) {{
      const normalized = String(value || "").trim().toLowerCase().replace(/\\s+/g, " ");
      const ascii = normalized
        .normalize("NFKD")
        .replace(/[\\u0300-\\u036f]/g, "")
        .replace(/[^\\x00-\\x7F]/g, "");
      const slug = ascii.replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
      if (slug) return slug;
      let hash = 0;
      for (const char of normalized) {{
        hash = ((hash * 31) + char.charCodeAt(0)) >>> 0;
      }}
      return `funder-${{hash.toString(16).padStart(8, "0").slice(0, 10)}}`;
    }}
    function funderSlug(item) {{
      const raw = rawObject(item);
      return item.funder_slug || raw.funder_slug
        || fallbackFunderSlug(item.funder || item.source || "funder");
    }}
    function funderPageHref(funderSlugValue) {{
      if (!funderSlugValue) return "#";
      return withLang(`${{apiBase}}/funder/${{encodeURIComponent(String(funderSlugValue))}}`);
    }}
    function lifecycleLabel(value) {{
      return copy[`lifecycle_${{value}}`] || humanizeLabel(value);
    }}
    function itemLifecycle(item) {{
      const raw = rawObject(item);
      const declared = normalizeKey(
        item.lifecycle || item.opportunity_status || raw.lifecycle || raw.opportunity_status || ""
      );
      if (supportedLifecycleValues.has(declared)) {{
        return declared;
      }}
      if (declared === "upcoming" || declared === "draft") {{
        return "forecast";
      }}
      if (declared === "archived") {{
        return "closed";
      }}
      const statusBlob = [
        raw.status,
        raw.status_raw,
        raw.project_status,
        raw.projectstatusdisplay,
        raw.notice_type
      ].join(" ").toLowerCase();
      const forecastSignal = new RegExp(
        "forecast|pipeline|planned|preparation|upcoming|concept|prequalification|pre-solicitation"
      );
      if (/(award|winner|selected|contract signed|completed|implemented)/.test(statusBlob)) {{
        return "awarded";
      }}
      if (
        raw.deadline_policy === "closed"
        || hasTag(item, "closed")
        || /(closed|expired|cancelled|canceled|archived)/.test(statusBlob)
      ) {{
        return "closed";
      }}
      if (
        hasTag(item, "project_pipeline")
        || forecastSignal.test(statusBlob)
      ) {{
        return "forecast";
      }}
      if (raw.deadline_policy === "rolling" || hasTag(item, "rolling")) {{
        return "rolling";
      }}
      const days = daysUntilDeadline(item);
      if (days !== null && days >= 0 && days <= 14) {{
        return "closing_soon";
      }}
      if (days !== null && days < 0) {{
        return "closed";
      }}
      return "open";
    }}
    function isStartupAudience(item) {{
      return matchesAnyTag(item, [
        "startup",
        "startup_support",
        "cloud_credits",
        "venture",
        "private_equity",
        "microsoft_founders_hub",
        "google_cloud_startup",
        "cloudflare_startups",
        "mongodb_startups",
        "nvidia_inception",
        "aws_activate"
      ]) || matchesType(item, ["accelerator", "cloud_credit"]);
    }}

    function isFarmerAudience(item) {{
      return matchesAnyTag(item, [
        "crop_production",
        "livestock",
        "gosagro",
        "kazagrofinance",
        "agrocredit",
        "animal_health"
      ]) || (
        hasTag(item, "agrotech")
        && presetById(FORMAT_PRESETS, "support").matches(item)
      );
    }}

    function isPublicSectorOpportunity(item) {{
      return matchesType(item, ["tender"]) && matchesAnyTag(item, [
        "public_sector",
        "project_pipeline",
        "development",
        "govtech",
        "infrastructure"
      ]);
    }}
    const detailStatusCopy = {{
      ok: copy.detail_status_ok,
      structured_only: copy.detail_status_structured_only,
      blocked: copy.detail_status_blocked,
      not_allowed: copy.detail_status_not_allowed,
      too_large: copy.detail_status_too_large,
      unsupported_media: copy.detail_status_unsupported_media,
      parse_error: copy.detail_status_parse_error
    }};
    const AUDIENCE_PRESETS = [
      {{
        id: "all",
        label: copy.audience_all,
        matches: () => true
      }},
      {{
        id: "startup",
        label: copy.audience_startup,
        matches: (item) => isStartupAudience(item)
      }},
      {{
        id: "business",
        label: copy.audience_business,
        matches: (item) => matchesAnyTag(item, [
          "business_support",
          "sme",
          "domestic_support",
          "state_program",
          "subsidy",
          "preferential_financing",
          "loan_guarantee",
          "tax_benefit",
          "reimbursement",
          "leasing",
          "employment",
          "industry",
          "export",
          "trade",
          "investment",
          "qazindustry",
          "qaztrade",
          "damu",
          "enbek",
          "baiterek",
          "bgov",
          "kdb",
          "idf"
        ])
      }},
      {{
        id: "farmer",
        label: copy.audience_farmer,
        matches: (item) => isFarmerAudience(item)
      }},
      {{
        id: "ngo",
        label: copy.audience_ngo,
        matches: (item) => matchesAnyTag(item, [
          "ngo",
          "civil_society",
          "media",
          "journalism",
          "nonprofit_required",
          "partnership",
          "internews",
          "fundsforngos"
        ]) || matchesAnyEligibility(item, [
          "некоммерческая организация",
          "nonprofit",
          "ngo"
        ])
      }},
      {{
        id: "science",
        label: copy.audience_science,
        matches: (item) => matchesAnyTag(item, [
          "science",
          "commercialization",
          "research",
          "education",
          "science_fund",
          "ncste"
        ]) || matchesAnyEligibility(item, [
          "образование_организация",
          "образовательный_партнер",
          "research",
          "university"
        ])
      }}
    ];
    const SUPPORT_FORMAT_TAGS = [
      "subsidy",
      "domestic_support",
      "state_program",
      "preferential_financing",
      "loan_guarantee",
      "tax_benefit",
      "reimbursement",
      "leasing",
      "employment",
      "business_support",
      "investment"
    ];
    const FORMAT_PRESETS = [
      {{
        id: "all",
        label: copy.format_all,
        matches: () => true
      }},
      {{
        id: "grants",
        label: copy.format_grants,
        matches: (item) => matchesAnyTag(item, ["grant"])
          || (
            matchesType(item, ["grant", "contest", "fellowship"])
            && !matchesAnyTag(item, SUPPORT_FORMAT_TAGS)
          )
      }},
      {{
        id: "support",
        label: copy.format_support,
        matches: (item) => matchesAnyTag(item, SUPPORT_FORMAT_TAGS)
          && !matchesAnyTag(item, ["grant"])
      }},
      {{
        id: "accelerators",
        label: copy.format_accelerators,
        matches: (item) => matchesType(item, ["accelerator", "cloud_credit"])
          || matchesAnyTag(item, [
            "startup_support",
            "cloud_credits",
            "microsoft_founders_hub",
            "google_cloud_startup",
            "cloudflare_startups",
            "mongodb_startups",
            "nvidia_inception"
          ])
      }},
      {{
        id: "tenders",
        label: copy.format_tenders,
        matches: (item) => matchesType(item, ["tender"])
          || matchesAnyTag(item, ["procurement", "tender", "consulting", "ecepp"])
      }}
    ];
    const TOPIC_PRESETS = [
      {{
        id: "all",
        label: copy.topic_all,
        matches: () => true
      }},
      {{
        id: "ai",
        label: copy.topic_ai,
        matches: (item) => matchesAnyTag(item, [
          "ai",
          "digital_skills",
          "digitalization",
          "digital",
          "cloud_credits"
        ])
      }},
      {{
        id: "agro",
        label: copy.topic_agro,
        matches: (item) => matchesAnyTag(item, [
          "agrotech",
          "vettech",
          "ecotech",
          "green_transition",
          "agriculture",
          "crop_production",
          "livestock",
          "animal_health",
          "water",
          "climate_change"
        ])
      }},
      {{
        id: "science",
        label: copy.topic_science,
        matches: (item) => matchesAnyTag(item, [
          "education",
          "edtech",
          "teacher_training",
          "higher_education",
          "science",
          "research",
          "commercialization"
        ]) || matchesAnyEligibility(item, [
          "образование_организация",
          "образовательный_партнер",
          "research",
          "university"
        ])
      }},
      {{
        id: "public",
        label: copy.topic_public,
        matches: (item) => matchesAnyTag(item, [
          "public_sector",
          "project_pipeline",
          "development",
          "govtech",
          "infrastructure",
          "procurement"
        ]) || matchesType(item, ["tender"])
      }},
      {{
        id: "ngo",
        label: copy.topic_ngo,
        matches: (item) => matchesAnyTag(item, [
          "ngo",
          "civil_society",
          "media",
          "journalism",
          "nonprofit_required",
          "partnership",
          "internews",
          "fundsforngos"
        ]) || matchesAnyEligibility(item, [
          "некоммерческая организация",
          "nonprofit",
          "ngo"
        ])
      }},
      {{
        id: "business",
        label: copy.topic_business,
        matches: (item) => matchesAnyTag(item, [
          "business_support",
          "state_program",
          "subsidy",
          "preferential_financing",
          "loan_guarantee",
          "tax_benefit",
          "reimbursement",
          "leasing",
          "industry",
          "investment",
          "sme",
          "export",
          "trade"
        ])
      }}
    ];
    const REGION_FILTERS = [
      {{
        id: "all",
        label: copy.region_all,
        matches: () => true
      }},
      {{
        id: "kazakhstan",
        label: copy.region_kazakhstan,
        matches: (item) => regionalPriority(item) >= 3
      }},
      {{
        id: "central_asia",
        label: copy.region_central_asia,
        matches: (item) => regionalPriority(item) === 2
      }},
      {{
        id: "global",
        label: copy.region_global,
        matches: (item) => regionalPriority(item) <= 1
      }}
    ];
    const LIFECYCLE_FILTERS = [
      {{
        id: "all",
        label: copy.lifecycle_all,
        matches: () => true
      }},
      {{
        id: "open",
        label: copy.lifecycle_open,
        matches: (item) => itemLifecycle(item) === "open"
      }},
      {{
        id: "forecast",
        label: copy.lifecycle_forecast,
        matches: (item) => itemLifecycle(item) === "forecast"
      }},
      {{
        id: "closing_soon",
        label: copy.lifecycle_closing_soon,
        matches: (item) => itemLifecycle(item) === "closing_soon"
      }},
      {{
        id: "rolling",
        label: copy.lifecycle_rolling,
        matches: (item) => itemLifecycle(item) === "rolling"
      }},
      {{
        id: "closed",
        label: copy.lifecycle_closed,
        matches: (item) => itemLifecycle(item) === "closed"
      }},
      {{
        id: "awarded",
        label: copy.lifecycle_awarded,
        matches: (item) => itemLifecycle(item) === "awarded"
      }}
    ];
    const DEADLINE_FILTERS = [
      {{
        id: "all",
        label: copy.deadline_filter_all,
        matches: () => true
      }},
      {{
        id: "soon",
        label: copy.deadline_filter_soon,
        matches: (item) => {{
          const days = daysUntilDeadline(item);
          return days !== null && days >= 0 && days <= 14;
        }}
      }},
      {{
        id: "month",
        label: copy.deadline_filter_month,
        matches: (item) => {{
          const days = daysUntilDeadline(item);
          return days !== null && days >= 0 && days <= 31;
        }}
      }},
      {{
        id: "rolling",
        label: copy.deadline_filter_rolling,
        matches: (item) => !item.deadline
      }}
    ];
    const SORT_OPTIONS = [
      {{
        id: "priority",
        label: copy.sort_priority
      }},
      {{
        id: "deadline",
        label: copy.sort_deadline
      }},
      {{
        id: "updated",
        label: copy.sort_updated
      }}
    ];
    const SCORE_OPTIONS = [
      {{
        id: "0",
        value: 0,
        label: copy.all_scores
      }},
      {{
        id: "0.3",
        value: 0.3,
        label: copy.score_option_03
      }},
      {{
        id: "0.5",
        value: 0.5,
        label: copy.score_option_05
      }},
      {{
        id: "0.7",
        value: 0.7,
        label: copy.score_option_07
      }}
    ];

    function metadataLabel(key) {{
      const map = copy.detail_meta_labels || {{}};
      return map[key] || humanizeLabel(key);
    }}

    function metadataValue(entry) {{
      const key = String(entry.key || "");
      const value = String(entry.value || "");
      const normalizedValue = normalizeKey(value);
      const hasMappedLabel = Boolean(labelMap[value] || labelMap[normalizedValue]);
      if (["deadline", "closing_date", "board_approval"].includes(key)) {{
        return formatDeadline(value) || value;
      }}
      if (["source", "funder", "notice_type"].includes(key)) {{
        return humanizeLabel(value);
      }}
      if (
        hasMappedLabel
        && ["funder", "country", "region", "deadline_policy", "status", "notice_type"].includes(key)
      ) {{
        return humanizeLabel(value);
      }}
      return value;
    }}

    function normalizedDetailMetadata(entries) {{
      const seenKeys = new Set();
      const sourceValue = entries.find((entry) => entry.key === "source")?.value || "";
      return entries.filter((entry) => {{
        const key = String(entry.key || "");
        const value = String(entry.value || "");
        if (!key || !value || seenKeys.has(key)) return false;
        if (key === "funder" && normalizeKey(value) === normalizeKey(sourceValue)) {{
          return false;
        }}
        seenKeys.add(key);
        return true;
      }});
    }}

    function detailStatusText(status) {{
      return detailStatusCopy[status] || copy.detail_status_structured_only;
    }}

    function withLang(path) {{
      const [pathname, query = ""] = String(path || "").split("?");
      const params = new URLSearchParams(query);
      params.set("lang", copy.lang || "ru");
      const serialized = params.toString();
      return serialized ? `${{pathname}}?${{serialized}}` : pathname;
    }}

    function opportunityPageHref(opportunityId) {{
      if (!opportunityId) return "#";
      return withLang(`${{apiBase}}/opportunity/${{encodeURIComponent(String(opportunityId))}}`);
    }}

    function renderTextBlocks(value) {{
      const paragraphs = String(value || "")
        .split(/\\n+/)
        .map((entry) => cleanSummaryText(entry) || entry.trim())
        .filter(Boolean);
      return paragraphs.map((entry) => `<p>${{escapeHtml(entry)}}</p>`).join("");
    }}

    function renderDetailFit(item) {{
      const root = $("#detail-fit");
      const summary = $("#detail-fit-summary");
      const pills = $("#detail-fit-pills");
      if (!item) {{
        root.classList.add("hidden");
        summary.textContent = copy.detail_fit_review;
        pills.innerHTML = "";
        return;
      }}
      summary.textContent = fitSummaryText(item);
      pills.innerHTML = fitPillsMarkup(item);
      root.classList.remove("hidden");
    }}

    function renderDetailReadiness(item) {{
      const root = $("#detail-readiness");
      const target = $("#detail-readiness-text");
      const readiness = item && item.raw && item.raw.decision_readiness;
      if (!readiness || !Number.isFinite(Number(readiness.total_fields))) {{
        root.classList.add("hidden");
        target.textContent = "";
        return;
      }}
      const known = Number(readiness.known_fields || 0);
      const total = Number(readiness.total_fields || 0);
      const missingLabels = copy.detail_missing_labels || {{}};
      const missing = (Array.isArray(readiness.missing_fields)
        ? readiness.missing_fields
        : []
      ).map((key) => missingLabels[key] || humanizeLabel(key));
      target.textContent = missing.length
        ? text("detail_readiness_partial", {{
            known: formatNumber.format(known),
            total: formatNumber.format(total),
            missing: missing.join(", ")
          }})
        : text("detail_readiness_complete", {{ total: formatNumber.format(total) }});
      root.classList.remove("hidden");
    }}

    function openDetailShell() {{
      state.detailTrigger = document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
      document.body.classList.add("modal-open");
      $("#main-content").inert = true;
      $("#detail-backdrop").hidden = false;
      $("#detail-drawer").hidden = false;
      window.requestAnimationFrame(() => {{
        $("#detail-backdrop").classList.add("open");
        $("#detail-drawer").classList.add("open");
        $("#detail-close").focus();
      }});
      $("#detail-drawer").setAttribute("aria-hidden", "false");
    }}

    function closeDetailShell() {{
      const trigger = state.detailTrigger;
      state.detailId = "";
      state.detailFallbackUrl = "";
      state.detailItem = null;
      state.detailTrigger = null;
      $("#detail-backdrop").classList.remove("open");
      $("#detail-drawer").classList.remove("open");
      $("#detail-drawer").setAttribute("aria-hidden", "true");
      document.body.classList.remove("modal-open");
      $("#main-content").inert = false;
      window.setTimeout(() => {{
        if ($("#detail-drawer").classList.contains("open")) return;
        $("#detail-backdrop").hidden = true;
        $("#detail-drawer").hidden = true;
        if (trigger && document.contains(trigger)) trigger.focus();
      }}, 180);
    }}

    function renderDetailLoading() {{
      $("#detail-title").textContent = copy.detail_title_fallback;
      $("#detail-status").textContent = copy.detail_loading;
      $("#detail-empty").textContent = copy.detail_loading;
      $("#detail-empty").classList.remove("hidden");
      renderDetailFit(state.detailItem);
      renderDetailReadiness(state.detailItem);
      $("#detail-meta").classList.add("hidden");
      $("#detail-sections").classList.add("hidden");
      $("#detail-meta-grid").innerHTML = "";
      $("#detail-sections-body").innerHTML = "";
      $("#detail-open-source").setAttribute("href", state.detailFallbackUrl || "#");
      $("#detail-open-page").setAttribute("href", opportunityPageHref(state.detailId));
      $("#detail-open-application").classList.add("hidden");
    }}

    function renderDetailFailure() {{
      $("#detail-title").textContent = copy.detail_title_fallback;
      $("#detail-status").textContent = copy.detail_error;
      $("#detail-empty").textContent = copy.detail_error;
      $("#detail-empty").classList.remove("hidden");
      renderDetailFit(state.detailItem);
      renderDetailReadiness(state.detailItem);
      $("#detail-meta").classList.add("hidden");
      $("#detail-sections").classList.add("hidden");
      $("#detail-open-source").setAttribute("href", state.detailFallbackUrl || "#");
      $("#detail-open-page").setAttribute("href", opportunityPageHref(state.detailId));
      $("#detail-open-application").classList.add("hidden");
    }}

    function renderDetail(detail) {{
      const title = detail && detail.title ? detail.title : copy.detail_title_fallback;
      const statusText = detailStatusText(detail.detail_fetch_status);
      const metadata = normalizedDetailMetadata(
        Array.isArray(detail.metadata)
          ? detail.metadata.filter((entry) => entry && entry.key && entry.value)
          : []
      );
      const sections = Array.isArray(detail.detail_sections) ? detail.detail_sections.filter(
        (section) => section && section.text
      ) : [];
      $("#detail-title").textContent = title;
      $("#detail-status").textContent = statusText;
      $("#detail-open-source").setAttribute(
        "href",
        detail.source_url || state.detailFallbackUrl || "#"
      );
      $("#detail-open-page").setAttribute("href", opportunityPageHref(detail.id));
      renderDetailFit(detail);
      renderDetailReadiness(state.detailItem || detail);

      const applicationButton = $("#detail-open-application");
      if (detail.application_url) {{
        applicationButton.setAttribute("href", detail.application_url);
        applicationButton.classList.remove("hidden");
      }} else {{
        applicationButton.classList.add("hidden");
      }}

      const metaGrid = $("#detail-meta-grid");
      metaGrid.innerHTML = metadata.map((entry) => `
        <div class="detail-meta-item">
          <span>${{escapeHtml(metadataLabel(entry.key))}}</span>
          <strong>${{escapeHtml(metadataValue(entry))}}</strong>
        </div>
      `).join("");
      $("#detail-meta").classList.toggle("hidden", !metadata.length);

      const sectionBody = $("#detail-sections-body");
      sectionBody.innerHTML = sections.map((section) => `
        <section class="detail-section-block">
          <h3>${{escapeHtml(section.heading || copy.detail_source_excerpt)}}</h3>
          ${{renderTextBlocks(section.text)}}
        </section>
      `).join("");
      $("#detail-sections").classList.toggle("hidden", !sections.length);

      const emptyMessage = $("#detail-empty");
      if (sections.length || metadata.length) {{
        emptyMessage.classList.add("hidden");
      }} else {{
        emptyMessage.textContent = copy.detail_empty;
        emptyMessage.classList.remove("hidden");
      }}
    }}

    async function openOpportunityDetail(opportunityId, fallbackUrl = "") {{
      if (!opportunityId) return;
      state.detailId = opportunityId;
      state.detailFallbackUrl = fallbackUrl;
      state.detailItem = state.items.find(
        (item) => String(item.id) === String(opportunityId)
      ) || null;
      openDetailShell();
      renderDetailLoading();
      try {{
        const detail = await fetchJson(withLang(`/opportunities/${{opportunityId}}`));
        if (state.detailId !== opportunityId) return;
        renderDetail(detail);
      }} catch (error) {{
        if (state.detailId !== opportunityId) return;
        renderDetailFailure();
      }}
    }}

    async function fetchJson(path) {{
      const response = await fetch(`${{apiBase}}${{path}}`, {{
        headers: {{ Accept: "application/json" }}
      }});
      if (!response.ok) {{
        throw new Error(`Request failed: ${{response.status}} ${{response.statusText}}`);
      }}
      return response.json();
    }}

    function scoreClass(score) {{
      if (score >= 0.8) return "good";
      if (score >= 0.5) return "warn";
      return "low";
    }}

    function hasTag(item, tagName) {{
      const tags = Array.isArray(item.tags) ? item.tags : [];
      return tags.some((tag) => String(tag).toLowerCase() === tagName);
    }}

    function sourceBadge(source) {{
      const isWatchlist = hasTag(source, "watchlist");
      const label = isWatchlist ? copy.watchlist_badge : copy.direct_badge;
      const cls = isWatchlist ? "badge watchlist" : "badge";
      return `<span class="${{cls}}" data-avds-component="badge">${{escapeHtml(label)}}</span>`;
    }}

    function sourceContextLabel(source) {{
      return hasTag(source, "watchlist")
        ? copy.source_watchlist_note
        : copy.source_direct_note;
    }}

    function sourceIconVariant(source) {{
      const variants = ["blue", "green", "amber", "violet", "slate", "red"];
      const key = String(source.slug || source.name || "");
      const hash = Array.from(key).reduce((sum, char) => sum + char.charCodeAt(0), 0);
      return variants[hash % variants.length];
    }}

    function sourceInitials(source) {{
      const label = String(source.name || humanizeLabel(source.slug) || "GR");
      const words = label
        .replace(/[^0-9A-Za-zА-Яа-яӘәҒғҚқҢңӨөҰұҮүҺһІіЁё]+/g, " ")
        .trim()
        .split(/\\s+/)
        .filter(Boolean);
      const initials = words.length > 1
        ? `${{words[0][0] || ""}}${{words[1][0] || ""}}`
        : label.slice(0, 2);
      return (initials || "GR").toUpperCase();
    }}

    function itemBadges(item) {{
      const badges = [];
      const lifecycle = itemLifecycle(item);
      if (lifecycle && lifecycle !== "open") {{
        badges.push(
          `<span class="badge lifecycle" data-avds-component="badge">`
          + `${{escapeHtml(lifecycleLabel(lifecycle))}}</span>`
        );
      }}
      const regionalBadge = regionalBadgeLabel(item);
      if (regionalBadge) {{
        badges.push(
          `<span class="badge regional" data-avds-component="badge">`
          + `${{escapeHtml(regionalBadge)}}</span>`
        );
      }}
      if (hasTag(item, "watchlist")) {{
        badges.push(
          `<span class="badge watchlist" data-avds-component="badge">`
          + `${{escapeHtml(copy.watchlist_badge)}}</span>`
        );
      }}
      return badges.join("");
    }}

    function shortUrl(value) {{
      try {{
        const url = new URL(value);
        const host = url.hostname.startsWith("www.")
          ? url.hostname.slice(4)
          : url.hostname;
        return host;
      }} catch {{
        return value || copy.unknown_url;
      }}
    }}

    function humanizeLabel(value) {{
      const key = String(value || "").trim();
      const normalizedKey = normalizeKey(key);
      if (!key) return "";
      if (labelMap[key]) return labelMap[key];
      if (labelMap[normalizedKey]) return labelMap[normalizedKey];
      const acronymMap = {{
        ai: "AI",
        adb: "ADB",
        eu: "EU",
        uk: "UK",
        us: "US",
        ngo: "NGO",
        saas: "SaaS",
        api: "API",
        db: "DB",
        qa: "QA",
        ebrd: "EBRD",
        ecepp: "ECEPP",
        isdb: "IsDB",
        qic: "QIC",
        rk: "RK",
        undp: "UNDP",
        unesco: "UNESCO",
        unicef: "UNICEF",
        aws: "AWS",
        eeas: "EEAS",
        iite: "IITE"
      }};
      return key
        .split(/[_-]+/)
        .filter(Boolean)
        .map((part) => {{
          const lower = part.toLowerCase();
          if (acronymMap[lower]) return acronymMap[lower];
          return lower.charAt(0).toUpperCase() + lower.slice(1);
        }})
        .join(" ");
    }}

    function sourceDisplayName(source) {{
      const slug = String(source && source.slug || "").trim();
      const mapped = labelMap[slug] || labelMap[normalizeKey(slug)];
      if (mapped) return String(mapped);
      return String(source && source.name || humanizeLabel(slug));
    }}

    function itemTags(item) {{
      return (Array.isArray(item.tags) ? item.tags : []).map(normalizeKey);
    }}

    function itemEligibility(item) {{
      return (Array.isArray(item.eligibility) ? item.eligibility : []).map(normalizeKey);
    }}

    function matchesAnyTag(item, keys) {{
      const tags = itemTags(item);
      return keys.some((key) => tags.includes(normalizeKey(key)));
    }}

    function matchesAnyEligibility(item, keys) {{
      const eligibility = itemEligibility(item);
      return keys.some((key) => eligibility.includes(normalizeKey(key)));
    }}

    function matchesType(item, types) {{
      const currentType = normalizeKey(item.type || "");
      return types.some((type) => currentType === normalizeKey(type));
    }}

    function presetById(presets, id) {{
      return presets.find((preset) => preset.id === id) || presets[0];
    }}

    function activeAudiencePreset() {{
      return presetById(AUDIENCE_PRESETS, state.audience);
    }}

    function activeFormatPreset() {{
      return presetById(FORMAT_PRESETS, state.format);
    }}

    function activeTopicPreset() {{
      return presetById(TOPIC_PRESETS, state.topic);
    }}

    function activeTopicBrief() {{
      const topicId = state.topic;
      if (!topicId || topicId === DEFAULT_TOPIC) return null;
      const briefs = {{
        ai: {{
          title: copy.theme_ai_title,
          note: copy.theme_ai_note,
          bestFor: copy.topic_ai_best,
          focuses: [
            copy.topic_ai_focus_1,
            copy.topic_ai_focus_2,
            copy.topic_ai_focus_3
          ]
        }},
        agro: {{
          title: copy.theme_agro_title,
          note: copy.theme_agro_note,
          bestFor: copy.topic_agro_best,
          focuses: [
            copy.topic_agro_focus_1,
            copy.topic_agro_focus_2,
            copy.topic_agro_focus_3
          ]
        }},
        science: {{
          title: copy.theme_science_title,
          note: copy.theme_science_note,
          bestFor: copy.topic_science_best,
          focuses: [
            copy.topic_science_focus_1,
            copy.topic_science_focus_2,
            copy.topic_science_focus_3
          ]
        }},
        public: {{
          title: copy.theme_public_title,
          note: copy.theme_public_note,
          bestFor: copy.topic_public_best,
          focuses: [
            copy.topic_public_focus_1,
            copy.topic_public_focus_2,
            copy.topic_public_focus_3
          ]
        }},
        business: {{
          title: copy.theme_business_title,
          note: copy.theme_business_note,
          bestFor: copy.topic_business_best,
          focuses: [
            copy.topic_business_focus_1,
            copy.topic_business_focus_2,
            copy.topic_business_focus_3
          ]
        }},
        ngo: {{
          title: copy.theme_ngo_title,
          note: copy.theme_ngo_note,
          bestFor: copy.topic_ngo_best,
          focuses: [
            copy.topic_ngo_focus_1,
            copy.topic_ngo_focus_2,
            copy.topic_ngo_focus_3
          ]
        }}
      }};
      return briefs[topicId] || null;
    }}

    function activeRegionFilter() {{
      return presetById(REGION_FILTERS, state.region);
    }}

    function activeLifecycleFilter() {{
      return presetById(LIFECYCLE_FILTERS, state.lifecycle);
    }}

    function activeDeadlineFilter() {{
      return presetById(DEADLINE_FILTERS, state.deadlineMode);
    }}

    function activeSortOption() {{
      return presetById(SORT_OPTIONS, state.sort);
    }}

    function activeScoreOption() {{
      return (
        SCORE_OPTIONS.find((option) => option.value === state.minScore)
        || SCORE_OPTIONS[0]
      );
    }}

    function matchingAudiencePresets(item) {{
      const priority = {{
        science: 0,
        farmer: 1,
        ngo: 2,
        business: 3,
        startup: 4
      }};
      return AUDIENCE_PRESETS
        .filter((preset) => preset.id !== DEFAULT_AUDIENCE && preset.matches(item))
        .sort((left, right) => {{
          const leftRank = priority[left.id] ?? 99;
          const rightRank = priority[right.id] ?? 99;
          return leftRank - rightRank || left.label.localeCompare(right.label);
        }});
    }}

    function daysUntilDeadline(item) {{
      if (!item || !item.deadline) return null;
      const parsed = Date.parse(`${{item.deadline}}T00:00:00`);
      if (Number.isNaN(parsed)) return null;
      const today = new Date();
      const todayStart = Date.UTC(
        today.getUTCFullYear(),
        today.getUTCMonth(),
        today.getUTCDate()
      );
      return Math.ceil((parsed - todayStart) / (1000 * 60 * 60 * 24));
    }}

    function fitPills(item) {{
      const pills = matchingAudiencePresets(item)
        .slice(0, 2)
        .map((preset) => ({{
          label: preset.label,
          tone: "good"
        }}));
      if (!pills.length) {{
        pills.push({{
          label: copy.fit_unknown,
          tone: "warn"
        }});
      }}
      if (hasTag(item, "global")) {{
        pills.push({{
          label: copy.fit_global,
          tone: "neutral"
        }});
      }}
      const days = daysUntilDeadline(item);
      if (days !== null && days >= 0 && days <= 14) {{
        pills.push({{
          label: copy.fit_deadline_soon,
          tone: "warn"
        }});
      }}
      return pills.slice(0, 3);
    }}

    function fitSummaryText(item) {{
      const audiences = matchingAudiencePresets(item).map((preset) => preset.label);
      if (audiences.length) {{
        return `${{copy.detail_fit_good}}: ${{audiences.join(", ")}}`;
      }}
      return copy.detail_fit_review;
    }}

    function fitPillsMarkup(item) {{
      return fitPills(item).map((pill) => {{
        const toneClass = pill.tone && pill.tone !== "neutral" ? ` ${{pill.tone}}` : "";
        return (
          `<span class="fit-pill${{toneClass}}" data-avds-component="fit-pill">`
          + `${{escapeHtml(pill.label)}}`
          + `</span>`
        );
      }}).join("");
    }}

    function opportunityFormatLabel(item) {{
      const tendersPreset = presetById(FORMAT_PRESETS, "tenders");
      if (tendersPreset.matches(item)) return tendersPreset.label;
      const acceleratorsPreset = presetById(FORMAT_PRESETS, "accelerators");
      if (acceleratorsPreset.matches(item)) return acceleratorsPreset.label;
      const grantsPreset = presetById(FORMAT_PRESETS, "grants");
      if (grantsPreset.matches(item)) return grantsPreset.label;
      const supportPreset = presetById(FORMAT_PRESETS, "support");
      if (supportPreset.matches(item)) return supportPreset.label;
      return humanizeLabel(item.type || "");
    }}

    function opportunityRegionLabel(item) {{
      const priority = regionalPriority(item);
      if (priority >= 3) return copy.meta_region_kazakhstan;
      if (priority >= 2) return copy.meta_region_central_asia;
      return copy.meta_region_global;
    }}

    function opportunityDeadlineLabel(item) {{
      const days = daysUntilDeadline(item);
      if (days === null) return copy.meta_deadline_rolling;
      if (days >= 0 && days <= 14) {{
        return text("meta_deadline_soon_days", {{ count: formatNumber.format(days) }});
      }}
      if (days >= 0 && days <= 31) return copy.meta_deadline_month;
      return copy.meta_deadline_later;
    }}

    function opportunitySignalText(item) {{
      const supportPreset = presetById(FORMAT_PRESETS, "support");
      if (supportPreset.matches(item) && regionalPriority(item) >= 3) {{
        return copy.signal_support_kz;
      }}
      if (isPublicSectorOpportunity(item)) {{
        return copy.signal_public_sector;
      }}
      if (matchesType(item, ["tender"])) {{
        return copy.signal_tender;
      }}
      if (presetById(AUDIENCE_PRESETS, "science").matches(item)) {{
        return copy.signal_science;
      }}
      if (presetById(AUDIENCE_PRESETS, "farmer").matches(item)) {{
        return copy.signal_farmer;
      }}
      if (presetById(AUDIENCE_PRESETS, "ngo").matches(item)) {{
        return copy.signal_ngo;
      }}
      if (presetById(AUDIENCE_PRESETS, "business").matches(item)) {{
        return copy.signal_business;
      }}
      if (presetById(AUDIENCE_PRESETS, "startup").matches(item)) {{
        return copy.signal_startup;
      }}
      if (regionalPriority(item) >= 3) {{
        return copy.signal_kazakhstan;
      }}
      if (regionalPriority(item) >= 2) {{
        return copy.signal_central_asia;
      }}
      return copy.signal_global;
    }}

    function opportunitySignalPillsMarkup(item) {{
      const entries = [
        {{
          label: copy.meta_format_label,
          value: opportunityFormatLabel(item)
        }},
        {{
          label: copy.meta_region_label,
          value: opportunityRegionLabel(item)
        }},
        {{
          label: copy.meta_deadline_label,
          value: opportunityDeadlineLabel(item)
        }}
      ];
      return entries.map((entry) => (
        `<span class="signal-pill" data-avds-component="signal-pill">`
        + `<span>${{escapeHtml(entry.label)}}</span>`
        + `${{escapeHtml(entry.value)}}`
        + `</span>`
      )).join("");
    }}

    function externalActionUrl(item) {{
      const raw = item && item.raw && typeof item.raw === "object" ? item.raw : {{}};
      const applicationUrl = typeof raw.application_url === "string"
        ? raw.application_url.trim()
        : "";
      return applicationUrl || item.source_url || opportunityPageHref(item && item.id) || "#";
    }}

    function primaryActionUrl(item) {{
      return opportunityPageHref(item && item.id) || externalActionUrl(item);
    }}

    function spotlightBaseItems() {{
      return state.items.slice().sort(comparePriorityItems);
    }}

    function heroActionAttributes(action = {{}}) {{
      return [
        ["data-hero-reset", "true"],
        ["data-hero-view", action.view || "opportunities"],
        ["data-hero-audience", action.audience],
        ["data-hero-format", action.format],
        ["data-hero-topic", action.topic],
        ["data-hero-region", action.region],
        ["data-hero-deadline", action.deadline]
      ].filter(([, value]) => value).map(
        ([name, value]) => `${{name}}="${{escapeHtml(value)}}"`,
      ).join(" ");
    }}

    function spotlightPreviewMarkup(items, totalCount) {{
      if (!items.length) {{
        return `<div class="spotlight-empty">${{escapeHtml(copy.spotlight_empty)}}</div>`;
      }}
      const preview = items.slice(0, 3);
      const moreCount = Math.max(0, totalCount - preview.length);
      const previews = preview.map((item) => {{
        const opportunityId = escapeHtml(item.id);
        const cardUrl = escapeHtml(externalActionUrl(item));
        const sourceName = humanizeLabel(item.source);
        const metaBits = [sourceName, formatDeadline(item.deadline)].filter(Boolean);
        return `
          <button
            class="spotlight-item"
            type="button"
            data-opportunity-detail="${{opportunityId}}"
            data-opportunity-url="${{cardUrl}}"
          >
            <strong>${{escapeHtml(item.title || copy.detail_title_fallback)}}</strong>
            <span>${{escapeHtml(metaBits.join(" • "))}}</span>
          </button>
        `;
      }}).join("");
      const more = moreCount
        ? `<div class="spotlight-more">${{escapeHtml(
            text("spotlight_preview_more", {{ count: formatNumber.format(moreCount) }}),
          )}}</div>`
        : "";
      return `<div class="spotlight-list">${{previews}}${{more}}</div>`;
    }}

    function spotlightCardMarkup(config) {{
      return `
        <article
          class="spotlight-card"
          data-tone="${{escapeHtml(config.tone || "neutral")}}"
          data-avds-component="spotlight-card"
        >
          <div class="spotlight-head">
            <span class="spotlight-label">${{escapeHtml(config.kicker)}}</span>
            <span class="spotlight-count">${{escapeHtml(
              text("spotlight_count", {{ count: formatNumber.format(config.count) }}),
            )}}</span>
          </div>
          <div class="spotlight-copy">
            <h3>${{escapeHtml(config.title)}}</h3>
            <p class="spotlight-note">${{escapeHtml(config.note)}}</p>
          </div>
          ${{spotlightPreviewMarkup(config.preview, config.count)}}
          <div class="spotlight-footer">
            <button
              class="button slim soft spotlight-action"
              type="button"
              ${{heroActionAttributes(config.action)}}
              data-avds-component="button"
            >${{escapeHtml(copy.spotlight_action_open)}}</button>
          </div>
        </article>
      `;
    }}

    function takeUniqueSpotlightPreview(items, usedKeys, count = 3) {{
      const selected = [];
      for (const item of items) {{
        const key = String(item.id || item.source_url || item.title || "").trim();
        if (!key || usedKeys.has(key)) continue;
        usedKeys.add(key);
        selected.push(item);
        if (selected.length >= count) break;
      }}
      return selected;
    }}

    function renderSpotlights() {{
      const root = $("#spotlight-grid");
      if (!root) return;
      root.setAttribute("aria-busy", "false");
      const items = spotlightBaseItems();
      if (!items.length) {{
        root.innerHTML = "";
        return;
      }}
      const supportPreset = presetById(FORMAT_PRESETS, "support");
      const trendingItems = items.filter((item) => Number(item.score || 0) >= 0.5);
      const kazakhstanItems = items.filter((item) => regionalPriority(item) >= 3);
      const supportItems = items.filter(
        (item) => regionalPriority(item) >= 3 && supportPreset.matches(item),
      );
      const deadlineItems = items.filter((item) => {{
        const days = daysUntilDeadline(item);
        return days !== null && days >= 0 && days <= 21;
      }});
      const usedPreviewKeys = new Set();
      const cards = [
        {{
          tone: "brand",
          kicker: copy.spotlight_trending_kicker,
          title: copy.spotlight_trending_title,
          note: copy.spotlight_trending_note,
          count: trendingItems.length,
          preview: takeUniqueSpotlightPreview(trendingItems, usedPreviewKeys),
          action: {{ view: "opportunities" }}
        }},
        {{
          tone: "good",
          kicker: copy.spotlight_kazakhstan_kicker,
          title: copy.spotlight_kazakhstan_title,
          note: copy.spotlight_kazakhstan_note,
          count: kazakhstanItems.length,
          preview: takeUniqueSpotlightPreview(kazakhstanItems, usedPreviewKeys),
          action: {{ view: "opportunities", region: "kazakhstan" }}
        }},
        {{
          tone: "neutral",
          kicker: copy.spotlight_support_kicker,
          title: copy.spotlight_support_title,
          note: copy.spotlight_support_note,
          count: supportItems.length,
          preview: takeUniqueSpotlightPreview(supportItems, usedPreviewKeys),
          action: {{ view: "opportunities", format: "support", region: "kazakhstan" }}
        }},
        {{
          tone: "amber",
          kicker: copy.spotlight_deadline_kicker,
          title: copy.spotlight_deadline_title,
          note: copy.spotlight_deadline_note,
          count: deadlineItems.length,
          preview: takeUniqueSpotlightPreview(deadlineItems, usedPreviewKeys),
          action: {{ view: "opportunities", deadline: "soon" }}
        }}
      ].filter((card) => card.count > 0);
      root.innerHTML = cards.map(spotlightCardMarkup).join("");
    }}

    function pathwayCardMarkup(config) {{
      return `
        <article
          class="pathway-card"
          data-tone="${{escapeHtml(config.tone || "brand")}}"
          data-avds-component="pathway-card"
        >
          <div class="pathway-head">
            <span class="pathway-label">${{escapeHtml(config.kicker)}}</span>
            <span class="pathway-count">${{escapeHtml(
              text("pathways_count", {{ count: formatNumber.format(config.count) }}),
            )}}</span>
          </div>
          <div class="spotlight-copy">
            <h3>${{escapeHtml(config.title)}}</h3>
            <p class="pathway-note">${{escapeHtml(config.note)}}</p>
          </div>
          <div class="pathway-footer">
            <button
              class="button slim soft"
              type="button"
              ${{heroActionAttributes(config.action)}}
              data-avds-component="button"
            >${{escapeHtml(copy.pathways_action_open)}}</button>
          </div>
        </article>
      `;
    }}

    function renderPathways() {{
      const root = $("#pathways-grid");
      if (!root) return;
      root.setAttribute("aria-busy", "false");
      const items = spotlightBaseItems();
      if (!items.length) {{
        root.innerHTML = "";
        return;
      }}
      const startupPreset = presetById(AUDIENCE_PRESETS, "startup");
      const businessPreset = presetById(AUDIENCE_PRESETS, "business");
      const farmerPreset = presetById(AUDIENCE_PRESETS, "farmer");
      const sciencePreset = presetById(AUDIENCE_PRESETS, "science");
      const supportPreset = presetById(FORMAT_PRESETS, "support");
      const startupItems = items.filter((item) => startupPreset.matches(item));
      const businessItems = items.filter((item) => (
        businessPreset.matches(item)
        && supportPreset.matches(item)
        && regionalPriority(item) >= 3
      ));
      const farmerItems = items.filter((item) => farmerPreset.matches(item));
      const scienceItems = items.filter((item) => sciencePreset.matches(item));
      const cards = [
        {{
          tone: "brand",
          kicker: copy.pathway_startup_kicker,
          title: copy.pathway_startup_title,
          note: copy.pathway_startup_note,
          count: startupItems.length,
          action: {{ view: "opportunities", audience: "startup" }}
        }},
        {{
          tone: "good",
          kicker: copy.pathway_business_kicker,
          title: copy.pathway_business_title,
          note: copy.pathway_business_note,
          count: businessItems.length,
          action: {{
            view: "opportunities",
            audience: "business",
            format: "support",
            region: "kazakhstan"
          }}
        }},
        {{
          tone: "amber",
          kicker: copy.pathway_farmer_kicker,
          title: copy.pathway_farmer_title,
          note: copy.pathway_farmer_note,
          count: farmerItems.length,
          action: {{ view: "opportunities", audience: "farmer" }}
        }},
        {{
          tone: "violet",
          kicker: copy.pathway_science_kicker,
          title: copy.pathway_science_title,
          note: copy.pathway_science_note,
          count: scienceItems.length,
          action: {{ view: "opportunities", audience: "science" }}
        }}
      ].filter((card) => card.count > 0);
      root.innerHTML = cards.map(pathwayCardMarkup).join("");
    }}

    function themeCardMarkup(config) {{
      return `
        <article
          class="theme-card"
          data-tone="${{escapeHtml(config.tone || "neutral")}}"
          data-avds-component="theme-card"
        >
          <div class="theme-head">
            <span class="theme-label">${{escapeHtml(config.kicker)}}</span>
            <span class="theme-count">${{escapeHtml(
              text("themes_count", {{ count: formatNumber.format(config.count) }}),
            )}}</span>
          </div>
          <div class="spotlight-copy">
            <h3>${{escapeHtml(config.title)}}</h3>
            <p class="theme-note">${{escapeHtml(config.note)}}</p>
          </div>
          <div class="theme-footer">
            <button
              class="button slim soft"
              type="button"
              ${{heroActionAttributes(config.action)}}
              data-avds-component="button"
            >${{escapeHtml(copy.themes_action_open)}}</button>
          </div>
        </article>
      `;
    }}

    function renderThemes() {{
      const root = $("#themes-grid");
      if (!root) return;
      root.setAttribute("aria-busy", "false");
      const items = spotlightBaseItems();
      if (!items.length) {{
        root.innerHTML = "";
        return;
      }}
      const aiPreset = presetById(TOPIC_PRESETS, "ai");
      const agroPreset = presetById(TOPIC_PRESETS, "agro");
      const sciencePreset = presetById(TOPIC_PRESETS, "science");
      const publicPreset = presetById(TOPIC_PRESETS, "public");
      const businessPreset = presetById(TOPIC_PRESETS, "business");
      const ngoPreset = presetById(TOPIC_PRESETS, "ngo");
      const aiItems = items.filter((item) => aiPreset.matches(item));
      const agroItems = items.filter((item) => agroPreset.matches(item));
      const scienceItems = items.filter((item) => sciencePreset.matches(item));
      const publicItems = items.filter((item) => publicPreset.matches(item));
      const businessItems = items.filter((item) => businessPreset.matches(item));
      const ngoItems = items.filter((item) => ngoPreset.matches(item));
      const cards = [
        {{
          tone: "brand",
          kicker: copy.theme_ai_kicker,
          title: copy.theme_ai_title,
          note: copy.theme_ai_note,
          count: aiItems.length,
          action: {{ view: "opportunities", topic: "ai" }}
        }},
        {{
          tone: "amber",
          kicker: copy.theme_agro_kicker,
          title: copy.theme_agro_title,
          note: copy.theme_agro_note,
          count: agroItems.length,
          action: {{ view: "opportunities", topic: "agro" }}
        }},
        {{
          tone: "violet",
          kicker: copy.theme_science_kicker,
          title: copy.theme_science_title,
          note: copy.theme_science_note,
          count: scienceItems.length,
          action: {{ view: "opportunities", topic: "science" }}
        }},
        {{
          tone: "neutral",
          kicker: copy.theme_public_kicker,
          title: copy.theme_public_title,
          note: copy.theme_public_note,
          count: publicItems.length,
          action: {{ view: "opportunities", topic: "public" }}
        }},
        {{
          tone: "good",
          kicker: copy.theme_business_kicker,
          title: copy.theme_business_title,
          note: copy.theme_business_note,
          count: businessItems.length,
          action: {{ view: "opportunities", topic: "business", region: "kazakhstan" }}
        }},
        {{
          tone: "neutral",
          kicker: copy.theme_ngo_kicker,
          title: copy.theme_ngo_title,
          note: copy.theme_ngo_note,
          count: ngoItems.length,
          action: {{ view: "opportunities", topic: "ngo" }}
        }}
      ].filter((card) => card.count > 0);
      root.innerHTML = cards.map(themeCardMarkup).join("");
    }}

    function funderOverviewText(funder) {{
      const types = (Array.isArray(funder.top_types) ? funder.top_types : [])
        .slice(0, 2)
        .map(humanizeLabel)
        .join(", ");
      const topics = (Array.isArray(funder.top_tags) ? funder.top_tags : [])
        .slice(0, 2)
        .map(humanizeLabel)
        .join(", ");
      const regions = (Array.isArray(funder.top_regions) ? funder.top_regions : [])
        .slice(0, 2)
        .map(humanizeLabel)
        .join(", ");
      const bits = [copy.funder_overview_intro];
      if (types) {{
        bits.push(text("funder_overview_types", {{ types }}));
      }}
      if (topics) {{
        bits.push(text("funder_overview_topics", {{ topics }}));
      }}
      if (regions) {{
        bits.push(text("funder_overview_regions", {{ regions }}));
      }}
      return bits.join(" ").trim();
    }}

    function funderCardMarkup(funder) {{
      const tags = (Array.isArray(funder.top_tags) ? funder.top_tags : []).slice(0, 3);
      const forecastCount = Number(funder.forecast_items || 0);
      const rollingCount = Number(funder.rolling_items || 0);
      const sourceCount = Array.isArray(funder.sources) ? funder.sources.length : 0;
      const nextDeadline = funder.next_deadline
        ? formatDeadline(funder.next_deadline)
        : copy.open_rolling;
      return `
        <article class="funder-card" data-avds-component="funder-card">
          <div class="funder-card-head">
            <div>
              <span class="spotlight-label">${{escapeHtml(copy.funder_section_eyebrow)}}</span>
              <h3>${{escapeHtml(humanizeLabel(funder.slug || funder.name || ""))}}</h3>
            </div>
            <span class="funder-kpi">${{
              escapeHtml(copy.funder_live_now)
            }} · ${{formatNumber.format(Number(funder.current_items || 0))}}</span>
          </div>
          <p>${{escapeHtml(funderOverviewText(funder))}}</p>
          <div class="funder-meta">
            ${{tags.map((tag) => (
              `<span class="summary-pill">${{escapeHtml(humanizeLabel(tag))}}</span>`
            )).join("")}}
            ${{
              forecastCount
                ? (
                  `<span class="summary-pill">${{escapeHtml(copy.lifecycle_forecast)}}`
                  + ` · ${{formatNumber.format(forecastCount)}}</span>`
                )
                : ""
            }}
            ${{
              rollingCount
                ? (
                  `<span class="summary-pill">${{escapeHtml(copy.lifecycle_rolling)}}`
                  + ` · ${{formatNumber.format(rollingCount)}}</span>`
                )
                : ""
            }}
          </div>
          <div class="funder-actions">
            <span class="panel-summary">${{escapeHtml(
              `${{formatNumber.format(sourceCount)}} · ${{nextDeadline}}`
            )}}</span>
            <a
              class="button slim soft"
              href="${{escapeHtml(funderPageHref(funder.slug))}}"
              data-avds-component="button"
            >${{escapeHtml(copy.funder_open_profile)}}</a>
          </div>
        </article>
      `;
    }}

    function renderFunders() {{
      const root = $("#funder-grid");
      if (!root) return;
      root.setAttribute("aria-busy", "false");
      if (!state.funders.length) {{
        root.innerHTML = `<div class="message">${{escapeHtml(copy.funder_empty)}}</div>`;
        return;
      }}
      root.innerHTML = state.funders.slice(0, 6).map(funderCardMarkup).join("");
    }}

    function renderTopicBrief(items) {{
      const root = $("#topic-brief");
      if (!root) return;
      const brief = activeTopicBrief();
      if (!brief) {{
        root.className = "topic-brief hidden";
        root.innerHTML = "";
        return;
      }}
      const chips = (brief.focuses || []).map((label) => (
        `<span class="topic-brief-chip" data-avds-component="topic-chip">`
        + `${{escapeHtml(label)}}`
        + `</span>`
      )).join("");
      root.className = "topic-brief";
      root.innerHTML = `
        <div class="topic-brief-head">
          <span class="topic-brief-kicker">${{escapeHtml(copy.topic_brief_eyebrow)}}</span>
          <span class="topic-brief-count">${{escapeHtml(
            text("topic_brief_count", {{ count: formatNumber.format(items.length) }}),
          )}}</span>
        </div>
        <div class="spotlight-copy">
          <h3>${{escapeHtml(brief.title)}}</h3>
          <p class="topic-brief-note">${{escapeHtml(brief.note)}}</p>
        </div>
        <div class="topic-brief-grid">
          <div class="topic-brief-group">
            <span class="topic-brief-label">${{escapeHtml(copy.topic_brief_what)}}</span>
            <div class="topic-brief-chips">${{chips}}</div>
          </div>
          <div class="topic-brief-group">
            <span class="topic-brief-label">${{escapeHtml(copy.topic_brief_best_for)}}</span>
            <p class="topic-brief-audience">${{escapeHtml(brief.bestFor)}}</p>
            <div class="topic-brief-actions">
              <button
                class="text-button"
                type="button"
                data-topic-reset="true"
                data-avds-component="button"
              >${{escapeHtml(copy.topic_brief_reset)}}</button>
            </div>
          </div>
        </div>
      `;
    }}

    function syncControlsFromState() {{
      $("#search").value = state.query;
      $("#sort-filter").value = state.sort;
      $("#score-filter").value = String(state.minScore);
      $("#scope-filter").value = state.includeArchived ? "all" : "open";
      $("#lifecycle-filter").value = state.lifecycle;
      $("#region-filter").value = state.region;
      $("#deadline-filter").value = state.deadlineMode;
      const sourceFilter = $("#source-filter");
      if (sourceFilter) {{
        sourceFilter.value = state.source;
      }}
    }}

    function syncUrlState() {{
      const params = new URLSearchParams(window.location.search);
      params.set("lang", copy.lang || "ru");
      if (state.query.trim()) {{
        params.set("q", state.query.trim());
      }} else {{
        params.delete("q");
      }}
      if (state.source !== "all") {{
        params.set("source", state.source);
      }} else {{
        params.delete("source");
      }}
      if (state.audience !== DEFAULT_AUDIENCE) {{
        params.set("audience", state.audience);
      }} else {{
        params.delete("audience");
      }}
      if (state.format !== DEFAULT_FORMAT) {{
        params.set("format", state.format);
      }} else {{
        params.delete("format");
      }}
      if (state.topic !== DEFAULT_TOPIC) {{
        params.set("topic", state.topic);
      }} else {{
        params.delete("topic");
      }}
      if (state.lifecycle !== DEFAULT_LIFECYCLE) {{
        params.set("lifecycle", state.lifecycle);
      }} else {{
        params.delete("lifecycle");
      }}
      if (state.region !== DEFAULT_REGION) {{
        params.set("region", state.region);
      }} else {{
        params.delete("region");
      }}
      if (state.deadlineMode !== DEFAULT_DEADLINE) {{
        params.set("deadline", state.deadlineMode);
      }} else {{
        params.delete("deadline");
      }}
      if (state.includeArchived) {{
        params.set("scope", "all");
      }} else {{
        params.delete("scope");
      }}
      if (state.sort !== DEFAULT_SORT) {{
        params.set("sort", state.sort);
      }} else {{
        params.delete("sort");
      }}
      if (state.minScore !== scoreDefaultForScope()) {{
        params.set("score", String(state.minScore));
      }} else {{
        params.delete("score");
      }}
      const query = params.toString();
      const nextUrl = (
        `${{window.location.pathname}}`
        + `${{query ? `?${{query}}` : ""}}`
        + `${{window.location.hash}}`
      );
      window.history.replaceState(null, "", nextUrl);
    }}

    function applyStateFromUrl() {{
      const params = new URLSearchParams(window.location.search);
      state.query = params.get("q") || "";
      state.source = params.get("source") || "all";
      state.includeArchived = params.get("scope") === "all";
      const sort = params.get("sort") || DEFAULT_SORT;
      state.sort = SORT_OPTIONS.some((option) => option.id === sort)
        ? sort
        : DEFAULT_SORT;
      const scoreParam = params.get("score");
      const score = scoreParam === null ? Number.NaN : Number(scoreParam);
      state.minScore = [0, 0.3, 0.5, 0.7].includes(score)
        ? score
        : scoreDefaultForScope();
      const audience = params.get("audience") || DEFAULT_AUDIENCE;
      state.audience = AUDIENCE_PRESETS.some((preset) => preset.id === audience)
        ? audience
        : DEFAULT_AUDIENCE;
      const format = params.get("format") || DEFAULT_FORMAT;
      state.format = FORMAT_PRESETS.some((preset) => preset.id === format)
        ? format
        : DEFAULT_FORMAT;
      const topic = params.get("topic") || DEFAULT_TOPIC;
      state.topic = TOPIC_PRESETS.some((preset) => preset.id === topic)
        ? topic
        : DEFAULT_TOPIC;
      const lifecycle = params.get("lifecycle") || DEFAULT_LIFECYCLE;
      state.lifecycle = LIFECYCLE_FILTERS.some((preset) => preset.id === lifecycle)
        ? lifecycle
        : DEFAULT_LIFECYCLE;
      if (
        (state.lifecycle === "closed" || state.lifecycle === "awarded")
        && !state.includeArchived
      ) {{
        state.includeArchived = true;
      }}
      const region = params.get("region") || DEFAULT_REGION;
      state.region = REGION_FILTERS.some((preset) => preset.id === region)
        ? region
        : DEFAULT_REGION;
      const deadline = params.get("deadline") || DEFAULT_DEADLINE;
      state.deadlineMode = DEADLINE_FILTERS.some((preset) => preset.id === deadline)
        ? deadline
        : DEFAULT_DEADLINE;
    }}

    function readSavedViews() {{
      try {{
        const stored = window.localStorage.getItem(SAVED_VIEW_STORAGE_KEY);
        const parsed = stored ? JSON.parse(stored) : [];
        return Array.isArray(parsed) ? parsed : [];
      }} catch {{
        return [];
      }}
    }}

    function writeSavedViews(rows) {{
      try {{
        window.localStorage.setItem(SAVED_VIEW_STORAGE_KEY, JSON.stringify(rows));
      }} catch {{
        // ignore storage quota or privacy-mode errors
      }}
    }}

    function savedViewNameFromState() {{
      if (state.query.trim()) return state.query.trim();
      const labels = [];
      if (state.audience !== DEFAULT_AUDIENCE) labels.push(activeAudiencePreset().label);
      if (state.format !== DEFAULT_FORMAT) labels.push(activeFormatPreset().label);
      if (state.topic !== DEFAULT_TOPIC) labels.push(activeTopicPreset().label);
      if (state.lifecycle !== DEFAULT_LIFECYCLE) labels.push(activeLifecycleFilter().label);
      if (state.region !== DEFAULT_REGION) labels.push(activeRegionFilter().label);
      return labels.slice(0, 2).join(" • ") || copy.saved_view_default_name;
    }}

    function renderSavedViews() {{
      const root = $("#saved-views");
      if (!root) return;
      const views = readSavedViews();
      if (!views.length) {{
        root.innerHTML = `<span class="saved-empty">${{escapeHtml(copy.collections_empty)}}</span>`;
        return;
      }}
      root.innerHTML = views.map((view) => `
        <span class="saved-view-pill">
          <button
            class="saved-apply"
            type="button"
            data-saved-view="${{escapeHtml(String(view.query || ""))}}"
          >${{escapeHtml(String(view.name || copy.saved_view_default_name))}}</button>
          <button
            class="saved-remove"
            type="button"
            data-remove-saved-view="${{escapeHtml(String(view.query || ""))}}"
            aria-label="${{escapeHtml(copy.saved_view_remove_aria)}}"
          >×</button>
        </span>
      `).join("");
    }}

    function setSavedViewNotice(message) {{
      const root = $("#saved-view-notice");
      if (!root) return;
      const text = String(message || "").trim();
      root.textContent = text;
      root.classList.toggle("hidden", !text);
    }}

    function saveCurrentView() {{
      syncUrlState();
      const currentUrl = new URL(window.location.href);
      const params = new URLSearchParams(currentUrl.search);
      params.set("lang", copy.lang || "ru");
      const query = params.toString();
      const next = {{
        name: savedViewNameFromState(),
        query
      }};
      const deduped = readSavedViews().filter((view) => view.query !== query);
      deduped.unshift(next);
      writeSavedViews(deduped.slice(0, 8));
      renderSavedViews();
      setSavedViewNotice(copy.saved_view_saved);
    }}

    function applySavedView(query) {{
      if (!query) return;
      const nextUrl = `${{window.location.pathname}}?${{query}}${{window.location.hash || ""}}`;
      window.history.replaceState(null, "", nextUrl);
      applyStateFromUrl();
      resetVisibleLimit();
      reloadAll();
    }}

    function removeSavedView(query) {{
      const next = readSavedViews().filter((view) => view.query !== query);
      writeSavedViews(next);
      renderSavedViews();
      setSavedViewNotice(copy.saved_view_removed);
    }}

    async function shareCurrentView() {{
      syncUrlState();
      const href = window.location.href;
      try {{
        await navigator.clipboard.writeText(href);
        setSavedViewNotice(copy.saved_view_shared);
      }} catch {{
        window.prompt(copy.saved_view_share_prompt, href);
      }}
    }}

    function readSavedOpportunities() {{
      try {{
        const stored = window.localStorage.getItem(SAVED_OPPORTUNITY_STORAGE_KEY);
        const parsed = stored ? JSON.parse(stored) : [];
        return Array.isArray(parsed) ? parsed.map(String) : [];
      }} catch {{
        return [];
      }}
    }}

    function writeSavedOpportunities(ids) {{
      try {{
        window.localStorage.setItem(
          SAVED_OPPORTUNITY_STORAGE_KEY,
          JSON.stringify(Array.from(new Set(ids.map(String))).slice(0, 200))
        );
      }} catch {{
        // local-only feature; ignore private-mode or quota errors
      }}
    }}

    function readOpportunityWorkflow() {{
      try {{
        const stored = window.localStorage.getItem(WORKFLOW_STORAGE_KEY);
        const parsed = stored ? JSON.parse(stored) : {{}};
        return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {{}};
      }} catch {{
        return {{}};
      }}
    }}

    function writeOpportunityWorkflow(workflow) {{
      try {{
        window.localStorage.setItem(WORKFLOW_STORAGE_KEY, JSON.stringify(workflow));
      }} catch {{
        // local-only workflow; ignore private-mode or quota errors
      }}
    }}

    function workflowStatusFor(opportunityId) {{
      const value = readOpportunityWorkflow()[String(opportunityId || "")];
      return WORKFLOW_STATUSES.some((status) => status.id === value) ? value : "review";
    }}

    function setOpportunityWorkflowStatus(opportunityId, status) {{
      const id = String(opportunityId || "");
      if (!id || !WORKFLOW_STATUSES.some((entry) => entry.id === status)) return;
      const workflow = readOpportunityWorkflow();
      workflow[id] = status;
      writeOpportunityWorkflow(workflow);
      setSavedViewNotice(copy.workflow_updated);
      renderWorkspaceQueue();
    }}

    function removeOpportunityWorkflow(opportunityId) {{
      const workflow = readOpportunityWorkflow();
      delete workflow[String(opportunityId || "")];
      writeOpportunityWorkflow(workflow);
    }}

    function workflowOptionsMarkup(opportunityId) {{
      const active = workflowStatusFor(opportunityId);
      return WORKFLOW_STATUSES.map((status) => (
        `<option value="${{escapeHtml(status.id)}}"`
        + `${{status.id === active ? " selected" : ""}}>`
        + `${{escapeHtml(status.label)}}</option>`
      )).join("");
    }}

    function renderWorkspaceFilter() {{
      const button = $("#workspace-filter");
      if (!button) return;
      const count = readSavedOpportunities().length;
      if (!count && state.savedOnly) state.savedOnly = false;
      button.disabled = count === 0;
      button.setAttribute("aria-pressed", String(state.savedOnly));
      button.textContent = count
        ? text("workspace_filter_count", {{ count: formatNumber.format(count) }})
        : copy.workspace_filter;
    }}

    function workspaceActionFor(status) {{
      const actions = {{
        review: copy.workspace_action_review,
        fit: copy.workspace_action_fit,
        preparing: copy.workspace_action_preparing,
        submitted: copy.workspace_action_submitted,
        result: copy.workspace_action_result
      }};
      return actions[status] || actions.review;
    }}

    function workspaceDeadlineFor(item) {{
      const days = daysUntilDeadline(item);
      if (days === null) {{
        return {{ label: copy.workspace_deadline_rolling, urgent: false, rank: 2 }};
      }}
      if (days <= 0) {{
        return {{ label: copy.workspace_deadline_today, urgent: true, rank: 0 }};
      }}
      if (days <= 7) {{
        return {{
          label: text("workspace_deadline_days", {{ count: formatNumber.format(days) }}),
          urgent: true,
          rank: 0
        }};
      }}
      return {{
        label: text("workspace_deadline_date", {{ date: formatDeadline(item.deadline) }}),
        urgent: false,
        rank: 1
      }};
    }}

    function workspaceQueueItems() {{
      const savedIds = new Set(readSavedOpportunities());
      const workflowRank = {{ preparing: 0, fit: 1, review: 2, submitted: 3, result: 4 }};
      return state.items
        .filter((item) => savedIds.has(String(item.id)))
        .slice()
        .sort((left, right) => {{
          const leftDeadline = workspaceDeadlineFor(left);
          const rightDeadline = workspaceDeadlineFor(right);
          const leftWorkflow = workflowStatusFor(left.id);
          const rightWorkflow = workflowStatusFor(right.id);
          return (
            leftDeadline.rank - rightDeadline.rank
            || deadlineRank(left) - deadlineRank(right)
            || (workflowRank[leftWorkflow] ?? 99) - (workflowRank[rightWorkflow] ?? 99)
            || comparePriorityItems(left, right)
          );
        }});
    }}

    function renderWorkspaceQueue() {{
      const queue = $("#workspace-queue");
      const list = $("#workspace-queue-list");
      const more = $("#workspace-queue-more");
      if (!queue || !list || !more) return;
      if (!state.savedOnly) {{
        queue.hidden = true;
        list.innerHTML = "";
        more.textContent = "";
        return;
      }}
      const items = workspaceQueueItems();
      queue.hidden = false;
      if (!items.length) {{
        list.innerHTML = `<span class="workspace-queue-action">${{escapeHtml(
          copy.workspace_queue_empty
        )}}</span>`;
        more.textContent = "";
        return;
      }}
      const visible = items.slice(0, WORKSPACE_QUEUE_LIMIT);
      list.innerHTML = visible.map((item) => {{
        const status = workflowStatusFor(item.id);
        const statusLabel = WORKFLOW_STATUSES.find((entry) => entry.id === status)?.label
          || copy.workflow_review;
        const deadline = workspaceDeadlineFor(item);
        return `<article class="workspace-queue-item" data-avds-component="workspace-queue-item">
          <div class="workspace-queue-copy">
            <a class="workspace-queue-name" href="${{escapeHtml(opportunityPageHref(item.id))}}">
              ${{escapeHtml(item.title)}}
            </a>
            <span class="workspace-queue-action">${{escapeHtml(workspaceActionFor(status))}}</span>
          </div>
          <div class="workspace-queue-meta">
            <span>${{escapeHtml(statusLabel)}}</span>
            <span class="workspace-queue-deadline${{deadline.urgent ? " is-urgent" : ""}}">
              ${{escapeHtml(deadline.label)}}
            </span>
          </div>
        </article>`;
      }}).join("");
      const remaining = items.length - visible.length;
      more.textContent = remaining
        ? text("workspace_queue_more", {{ count: formatNumber.format(remaining) }})
        : "";
    }}

    function isOpportunitySaved(opportunityId) {{
      return readSavedOpportunities().includes(String(opportunityId || ""));
    }}

    function toggleSavedOpportunity(opportunityId) {{
      if (!opportunityId) return;
      const id = String(opportunityId);
      const current = readSavedOpportunities();
      const exists = current.includes(id);
      const next = exists ? current.filter((value) => value !== id) : [id, ...current];
      writeSavedOpportunities(next);
      if (exists) {{
        removeOpportunityWorkflow(id);
      }} else {{
        setOpportunityWorkflowStatus(id, "review");
      }}
      setSavedViewNotice(
        exists ? copy.saved_opportunity_removed : copy.saved_opportunity_saved
      );
      renderWorkspaceFilter();
      renderOpportunities();
    }}

    function csvCell(value) {{
      const textValue = String(value || "").replace(/\\s+/g, " ").trim();
      return `"${{textValue.replace(/"/g, '""')}}"`;
    }}

    function downloadText(filename, content, mimeType) {{
      const blob = new Blob([content], {{ type: mimeType }});
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
    }}

    function exportWorkspace() {{
      const payload = {{
        version: 1,
        exported_at: new Date().toISOString(),
        saved_views: readSavedViews(),
        saved_opportunities: readSavedOpportunities(),
        workflow: readOpportunityWorkflow()
      }};
      const stamp = new Date().toISOString().slice(0, 10);
      downloadText(
        `qazfund-workspace-${{stamp}}.json`,
        JSON.stringify(payload, null, 2),
        "application/json;charset=utf-8"
      );
      setSavedViewNotice(copy.workspace_exported);
      $("#workspace-backup").open = false;
    }}

    function sanitizeWorkspacePayload(payload) {{
      if (!payload || typeof payload !== "object" || Number(payload.version) !== 1) {{
        throw new Error("unsupported workspace backup");
      }}
      const savedOpportunities = Array.isArray(payload.saved_opportunities)
        ? Array.from(new Set(payload.saved_opportunities.map(String))).slice(0, 200)
        : [];
      const savedIds = new Set(savedOpportunities);
      const savedViews = (Array.isArray(payload.saved_views) ? payload.saved_views : [])
        .filter((view) => view && typeof view === "object" && view.query)
        .map((view) => ({{
          name: String(view.name || copy.saved_view_default_name).slice(0, 120),
          query: String(view.query).slice(0, 2_000)
        }}))
        .slice(0, 8);
      const workflow = {{}};
      const sourceWorkflow = payload.workflow && typeof payload.workflow === "object"
        ? payload.workflow
        : {{}};
      Object.entries(sourceWorkflow).forEach(([id, status]) => {{
        if (
          savedIds.has(String(id))
          && WORKFLOW_STATUSES.some((entry) => entry.id === status)
        ) {{
          workflow[String(id)] = status;
        }}
      }});
      return {{ savedViews, savedOpportunities, workflow }};
    }}

    async function importWorkspace(file) {{
      if (!file) return;
      try {{
        const payload = sanitizeWorkspacePayload(JSON.parse(await file.text()));
        writeSavedViews(payload.savedViews);
        writeSavedOpportunities(payload.savedOpportunities);
        writeOpportunityWorkflow(payload.workflow);
        state.savedOnly = false;
        renderSavedViews();
        renderWorkspaceFilter();
        renderOpportunities();
        setSavedViewNotice(copy.workspace_imported);
      }} catch {{
        setSavedViewNotice(copy.workspace_import_error);
      }} finally {{
        $("#import-workspace").value = "";
        $("#workspace-backup").open = false;
      }}
    }}

    function exportVisibleCsv() {{
      const rows = visibleItems();
      const header = [
        "title",
        "funder",
        "source",
        "format",
        "match",
        "deadline",
        "page_url",
        "source_url"
      ];
      const csvRows = [
        header.map(csvCell).join(","),
        ...rows.map((item) => [
          item.title,
          item.funder || humanizeLabel(item.source),
          humanizeLabel(item.source),
          opportunityFormatLabel(item),
          formatScore(item.score),
          item.deadline || "",
          new URL(opportunityPageHref(item.id), window.location.origin).href,
          item.source_url || ""
        ].map(csvCell).join(","))
      ];
      downloadText("qazfund-opportunities.csv", csvRows.join("\\n"), "text/csv;charset=utf-8");
    }}

    function icsDate(value) {{
      return String(value || "").replace(/-/g, "");
    }}

    function exportVisibleDeadlines() {{
      const rows = visibleItems().filter((item) => item.deadline);
      const escapeIcs = (value) => String(value || "")
        .replace(/\\\\/g, "\\\\\\\\")
        .replace(/,/g, "\\\\,")
        .replace(/;/g, "\\\\;")
        .replace(/\\n/g, "\\\\n");
      const now = new Date().toISOString().replace(/[-:]/g, "").split(".")[0] + "Z";
      const events = rows.map((item) => [
        "BEGIN:VEVENT",
        `UID:qazfund-${{item.id}}@qaz.fund`,
        `DTSTAMP:${{now}}`,
        `DTSTART;VALUE=DATE:${{icsDate(item.deadline)}}`,
        `SUMMARY:${{escapeIcs(item.title || copy.detail_title_fallback)}}`,
        `DESCRIPTION:${{escapeIcs((summarize(item) || "") + " " + opportunityPageHref(item.id))}}`,
        `URL:${{new URL(opportunityPageHref(item.id), window.location.origin).href}}`,
        "END:VEVENT"
      ].join("\\r\\n"));
      const body = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//QAZ.FUND//Opportunity Deadlines//EN",
        ...events,
        "END:VCALENDAR"
      ].join("\\r\\n");
      downloadText("qazfund-deadlines.ics", body, "text/calendar;charset=utf-8");
    }}

    function issueUrl(item) {{
      const params = new URLSearchParams();
      params.set("title", `Data issue: ${{item && item.title ? item.title : "opportunity"}}`);
      params.set("body", [
        "Public page:",
        new URL(opportunityPageHref(item && item.id), window.location.origin).href,
        "",
        "What should be corrected:"
      ].join("\\n"));
      return `https://github.com/belilovsky/grant-radar-public/issues/new?${{params.toString()}}`;
    }}

    function cleanSummaryText(value) {{
      const raw = String(value || "").replace(/\\s+/g, " ").trim();
      if (!raw) return "";
      return raw
        .split(/Читать далее|Read more/i)[0]
        .replace(/[\\s\\-:;,]+$/u, "")
        .trim();
    }}

    function summarize(item) {{
      if (item.summary) return cleanSummaryText(item.summary) || copy.no_summary;
      const agency = item.raw && (item.raw.agency || item.raw.agencyCode);
      return agency ? text("source_agency", {{ agency }}) : copy.no_summary;
    }}

    function formatDeadline(value) {{
      if (!value) return copy.open_rolling;
      const parsed = new Date(`${{value}}T00:00:00`);
      if (Number.isNaN(parsed.getTime())) return value;
      return new Intl.DateTimeFormat(copy.locale || "ru-KZ", {{
        month: "short",
        day: "numeric",
        year: "numeric"
      }}).format(parsed);
    }}

    function formatDateTime(value) {{
      if (!value) return "–";
      const parsed = new Date(value);
      if (Number.isNaN(parsed.getTime())) return "–";
      return new Intl.DateTimeFormat(copy.locale || "ru-KZ", {{
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      }}).format(parsed);
    }}

    function sourceRefreshInfo(source) {{
      const value = source && (
        source.last_discovered_at || source.last_refreshed_at || source.updated_at
      );
      if (!value) {{
        return {{ label: copy.source_refresh_unknown, tone: "is-unknown" }};
      }}
      const parsed = new Date(value);
      if (Number.isNaN(parsed.getTime())) {{
        return {{ label: copy.source_refresh_unknown, tone: "is-unknown" }};
      }}
      const date = new Intl.DateTimeFormat(copy.locale || "ru-KZ", {{
        day: "numeric",
        month: "short"
      }}).format(parsed);
      const ageHours = Math.max(0, Date.now() - parsed.getTime()) / 3600000;
      return {{
        label: text("source_refresh_value", {{ date }}),
        tone: ageHours > 72 ? "is-stale" : ""
      }};
    }}

    function hasActiveFilters() {{
      return Boolean(state.query.trim())
        || state.sort !== DEFAULT_SORT
        || state.source !== "all"
        || state.audience !== DEFAULT_AUDIENCE
        || state.format !== DEFAULT_FORMAT
        || state.topic !== DEFAULT_TOPIC
        || state.lifecycle !== DEFAULT_LIFECYCLE
        || state.region !== DEFAULT_REGION
        || state.deadlineMode !== DEFAULT_DEADLINE
        || state.includeArchived
        || state.savedOnly
        || state.minScore !== scoreDefaultForScope();
    }}

    function scoreDefaultForScope() {{
      return state.includeArchived ? ALL_INDEX_SCORE : DEFAULT_SCORE;
    }}

    function resetVisibleLimit() {{
      state.visibleLimit = DEFAULT_VISIBLE_ITEMS;
    }}

    function emptyStateActions() {{
      const actions = [];
      if (state.deadlineMode !== DEFAULT_DEADLINE) {{
        actions.push({{ id: "reset-deadline", label: copy.empty_action_deadline }});
      }}
      if (state.region !== DEFAULT_REGION) {{
        actions.push({{ id: "reset-region", label: copy.empty_action_region }});
      }}
      if (state.lifecycle !== DEFAULT_LIFECYCLE) {{
        actions.push({{ id: "reset-lifecycle", label: copy.lifecycle_all }});
      }}
      if (state.minScore !== scoreDefaultForScope()) {{
        actions.push({{ id: "reset-score", label: copy.empty_action_score }});
      }}
      if (!state.includeArchived) {{
        actions.push({{ id: "show-archive", label: copy.empty_action_scope }});
      }}
      if (hasActiveFilters()) {{
        actions.push({{ id: "clear", label: copy.empty_action_clear }});
      }}
      return actions.slice(0, 4);
    }}

    function renderEmptyState() {{
      const actions = emptyStateActions();
      return `
        <div class="message-shell">
          <div class="message-title">${{escapeHtml(copy.no_filtered_items)}}</div>
          <div class="message-note">${{escapeHtml(copy.no_filtered_items_hint)}}</div>
          ${{
            actions.length
              ? `<div class="message-actions">${{actions.map((action) => `
                  <button
                    class="text-button message-action"
                    type="button"
                    data-empty-action="${{escapeHtml(action.id)}}"
                    data-avds-component="button"
                  >${{escapeHtml(action.label)}}</button>
                `).join("")}}</div>`
              : ""
          }}
        </div>
      `;
    }}

    function applyEmptyAction(actionId) {{
      switch (actionId) {{
        case "reset-deadline":
          state.deadlineMode = DEFAULT_DEADLINE;
          resetVisibleLimit();
          renderOpportunities();
          return;
        case "reset-region":
          state.region = DEFAULT_REGION;
          resetVisibleLimit();
          renderOpportunities();
          return;
        case "reset-lifecycle":
          state.lifecycle = DEFAULT_LIFECYCLE;
          resetVisibleLimit();
          renderOpportunities();
          return;
        case "reset-score":
          state.minScore = scoreDefaultForScope();
          resetVisibleLimit();
          renderOpportunities();
          return;
        case "show-archive":
          state.includeArchived = true;
          state.minScore = scoreDefaultForScope();
          reloadAll();
          return;
        case "clear":
          clearAllFilters();
          return;
        default:
          return;
      }}
    }}

    function clearAllFilters() {{
      state.query = "";
      state.sort = DEFAULT_SORT;
      state.minScore = DEFAULT_SCORE;
      state.source = "all";
      state.audience = DEFAULT_AUDIENCE;
      state.format = DEFAULT_FORMAT;
      state.topic = DEFAULT_TOPIC;
      state.lifecycle = DEFAULT_LIFECYCLE;
      state.region = DEFAULT_REGION;
      state.deadlineMode = DEFAULT_DEADLINE;
      state.includeArchived = false;
      state.savedOnly = false;
      resetVisibleLimit();
      reloadAll();
    }}

    function applyHeroAction(button) {{
      if (!button) return;
      const shouldReset = button.getAttribute("data-hero-reset") === "true";
      const audience = button.getAttribute("data-hero-audience");
      const format = button.getAttribute("data-hero-format");
      const topic = button.getAttribute("data-hero-topic");
      const region = button.getAttribute("data-hero-region");
      const deadline = button.getAttribute("data-hero-deadline");
      const sort = button.getAttribute("data-hero-sort");
      const focus = button.getAttribute("data-hero-focus");
      const view = button.getAttribute("data-hero-view") || "opportunities";
      if (shouldReset) {{
        state.query = "";
        state.sort = DEFAULT_SORT;
        state.source = "all";
        state.minScore = DEFAULT_SCORE;
        state.audience = DEFAULT_AUDIENCE;
        state.format = DEFAULT_FORMAT;
        state.topic = DEFAULT_TOPIC;
        state.lifecycle = DEFAULT_LIFECYCLE;
        state.region = DEFAULT_REGION;
        state.deadlineMode = DEFAULT_DEADLINE;
        state.includeArchived = false;
        state.savedOnly = false;
      }}
      if (audience) {{
        state.audience = AUDIENCE_PRESETS.some((preset) => preset.id === audience)
          ? audience
          : DEFAULT_AUDIENCE;
      }}
      if (format) {{
        state.format = FORMAT_PRESETS.some((preset) => preset.id === format)
          ? format
          : DEFAULT_FORMAT;
      }}
      if (topic) {{
        state.topic = TOPIC_PRESETS.some((preset) => preset.id === topic)
          ? topic
          : DEFAULT_TOPIC;
      }}
      if (region) {{
        state.region = REGION_FILTERS.some((preset) => preset.id === region)
          ? region
          : DEFAULT_REGION;
      }}
      if (deadline) {{
        state.deadlineMode = DEADLINE_FILTERS.some((preset) => preset.id === deadline)
          ? deadline
          : DEFAULT_DEADLINE;
      }}
      if (sort) {{
        state.sort = SORT_OPTIONS.some((option) => option.id === sort)
          ? sort
          : DEFAULT_SORT;
      }}
      resetVisibleLimit();
      renderOpportunities();
      goToView(view);
      if (focus === "search") {{
        const disclosure = $("#filter-disclosure");
        const search = $("#search");
        if (disclosure) disclosure.open = true;
        window.requestAnimationFrame(() => {{
          search?.focus();
          search?.scrollIntoView({{ behavior: "auto", block: "center" }});
        }});
      }}
    }}

    function localDateISO(date = new Date()) {{
      const timezoneOffsetMs = date.getTimezoneOffset() * 60 * 1000;
      return new Date(date.getTime() - timezoneOffsetMs).toISOString().slice(0, 10);
    }}

    function localRelevantBySource() {{
      const today = localDateISO();
      return state.items.reduce((counts, item) => {{
        if (item.score >= 0.3 && (!item.deadline || item.deadline >= today)) {{
          counts.set(item.source, (counts.get(item.source) || 0) + 1);
        }}
        return counts;
      }}, new Map());
    }}

    function haystackFor(item) {{
      const tags = Array.isArray(item.tags) ? item.tags : [];
      const eligibility = Array.isArray(item.eligibility) ? item.eligibility : [];
      const raw = item.raw && typeof item.raw === "object" ? item.raw : {{}};
      return [
        item.title,
        item.summary,
        item.funder,
        item.source,
        tags.join(" "),
        eligibility.join(" "),
        raw.region,
        raw.country,
        raw.agency,
        raw.notice_type
      ].join(" ").toLowerCase();
    }}

    function normalizeSearchText(value) {{
      return String(value || "")
        .toLowerCase()
        .replace(/ё/g, "е")
        .normalize("NFKD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-zа-я0-9]+/gi, " ")
        .trim();
    }}

    function oneEditAway(left, right) {{
      const a = String(left || "");
      const b = String(right || "");
      if (Math.abs(a.length - b.length) > 1) return false;
      let i = 0;
      let j = 0;
      let edits = 0;
      while (i < a.length && j < b.length) {{
        if (a[i] === b[j]) {{
          i += 1;
          j += 1;
          continue;
        }}
        edits += 1;
        if (edits > 1) return false;
        if (a.length > b.length) i += 1;
        else if (b.length > a.length) j += 1;
        else {{
          i += 1;
          j += 1;
        }}
      }}
      return edits + Number(i < a.length || j < b.length) <= 1;
    }}

    function searchTokenGroup(token) {{
      const group = SEARCH_SYNONYM_GROUPS.find((entries) => (
        entries.some((entry) => token.startsWith(entry) || entry.startsWith(token))
      ));
      return group || [token];
    }}

    function matchesSearchQuery(item, query) {{
      const normalizedQuery = normalizeSearchText(query);
      if (!normalizedQuery) return true;
      const haystack = normalizeSearchText(haystackFor(item));
      if (haystack.includes(normalizedQuery)) return true;
      const haystackWords = haystack.split(" ").filter(Boolean);
      const tokens = normalizedQuery
        .split(" ")
        .filter((token) => token.length >= 2 && !SEARCH_STOP_WORDS.has(token));
      return tokens.every((token) => {{
        const group = searchTokenGroup(token);
        if (group.some((entry) => haystack.includes(normalizeSearchText(entry)))) {{
          return true;
        }}
        return token.length >= 5 && haystackWords.some((word) => oneEditAway(token, word));
      }});
    }}

    function regionalPriority(item) {{
      const textValue = haystackFor(item);
      const source = String(item.source || "");
      const hasKazakhstanSignal = /kazakhstan|казахстан|қазақстан/.test(textValue)
        || source.includes("_kazakhstan")
        || hasTag(item, "kazakhstan");
      const hasCentralAsiaSignal = /central[\\s_-]+asia|central[\\s_-]+asian/i.test(textValue)
        || /центральн(ая|ой)\\s+ази/i.test(textValue)
        || hasTag(item, "central_asia_eligible")
        || hasTag(item, "central_asia");
      if (hasKazakhstanSignal) {{
        return 3;
      }}
      if (
        hasCentralAsiaSignal
      ) {{
        return 2;
      }}
      if (/eurasia|cis|uzbekistan|kyrgyzstan|tajikistan|turkmenistan/.test(textValue)) {{
        return 1;
      }}
      return 0;
    }}

    function regionalBadgeLabel(item) {{
      const priority = regionalPriority(item);
      if (priority >= 3) return copy.regional_badge_kazakhstan;
      if (priority >= 2) return copy.regional_badge_central_asia;
      return "";
    }}

    function deadlineRank(item) {{
      if (!item.deadline) return Number.POSITIVE_INFINITY;
      const parsed = Date.parse(`${{item.deadline}}T00:00:00`);
      return Number.isNaN(parsed) ? Number.POSITIVE_INFINITY : parsed;
    }}

    function discoveredRank(item) {{
      const parsed = Date.parse(item.discovered_at || "");
      return Number.isNaN(parsed) ? 0 : parsed;
    }}

    function comparePriorityItems(left, right) {{
      return (
        regionalPriority(right) - regionalPriority(left)
        || Number(right.score || 0) - Number(left.score || 0)
        || deadlineRank(left) - deadlineRank(right)
        || discoveredRank(right) - discoveredRank(left)
      );
    }}

    function compareDeadlineItems(left, right) {{
      return (
        deadlineRank(left) - deadlineRank(right)
        || comparePriorityItems(left, right)
      );
    }}

    function compareUpdatedItems(left, right) {{
      return (
        discoveredRank(right) - discoveredRank(left)
        || comparePriorityItems(left, right)
      );
    }}

    function topicPriorityScore(item) {{
      const topicId = state.topic;
      if (!topicId || topicId === DEFAULT_TOPIC) return 0;
      let score = 0;
      if (topicId === "ai") {{
        if (matchesAnyTag(item, ["ai"])) score += 14;
        if (matchesAnyTag(item, ["cloud_credits"])) score += 12;
        if (matchesType(item, ["accelerator", "cloud_credit"])) score += 8;
        if (matchesAnyTag(item, ["digital_skills", "digitalization", "digital"])) {{
          score += 6;
        }}
      }} else if (topicId === "agro") {{
        if (matchesAnyTag(item, ["agrotech", "vettech", "ecotech"])) score += 12;
        if (matchesAnyTag(item, [
          "agriculture",
          "crop_production",
          "livestock",
          "animal_health"
        ])) {{
          score += 10;
        }}
        if (matchesAnyTag(item, ["water", "climate_change", "green_transition"])) {{
          score += 8;
        }}
      }} else if (topicId === "science") {{
        if (matchesAnyTag(item, ["commercialization"])) score += 12;
        if (matchesAnyTag(item, ["science", "research", "higher_education"])) score += 10;
        if (matchesAnyTag(item, ["education", "edtech", "teacher_training"])) score += 8;
      }} else if (topicId === "public") {{
        if (matchesType(item, ["tender"])) score += 16;
        if (matchesAnyTag(item, ["procurement", "project_pipeline"])) score += 12;
        if (matchesAnyTag(item, ["public_sector", "infrastructure", "development", "govtech"])) {{
          score += 9;
        }}
      }} else if (topicId === "business") {{
        if (presetById(FORMAT_PRESETS, "support").matches(item)) score += 12;
        if (matchesAnyTag(item, ["subsidy", "state_program", "business_support"])) score += 10;
        if (matchesAnyTag(item, [
          "preferential_financing",
          "loan_guarantee",
          "tax_benefit",
          "reimbursement",
          "leasing"
        ])) {{
          score += 8;
        }}
        if (regionalPriority(item) >= 3) score += 5;
      }} else if (topicId === "ngo") {{
        if (matchesAnyTag(item, ["ngo", "civil_society", "media", "journalism"])) score += 12;
        if (matchesAnyTag(item, [
          "nonprofit_required",
          "partnership",
          "internews",
          "fundsforngos"
        ])) {{
          score += 10;
        }}
      }}
      if (activeTopicPreset().matches(item)) score += 2;
      return score;
    }}

    function compareVisibleItems(left, right) {{
      if (state.sort === "deadline") {{
        return compareDeadlineItems(left, right);
      }}
      if (state.sort === "updated") {{
        return compareUpdatedItems(left, right);
      }}
      return (
        topicPriorityScore(right) - topicPriorityScore(left)
        || comparePriorityItems(left, right)
      );
    }}

    function visibleItems() {{
      const today = localDateISO();
      const historicalLifecycle = state.lifecycle === "closed" || state.lifecycle === "awarded";
      const audiencePreset = activeAudiencePreset();
      const formatPreset = activeFormatPreset();
      const topicPreset = activeTopicPreset();
      const lifecycleFilter = activeLifecycleFilter();
      const regionFilter = activeRegionFilter();
      const deadlineFilter = activeDeadlineFilter();
      const savedIds = state.savedOnly ? new Set(readSavedOpportunities()) : null;
      return state.items
        .filter((item) => {{
          return item.score >= state.minScore
            && (
              (state.includeArchived || historicalLifecycle)
              || !item.deadline
              || item.deadline >= today
            )
            && (state.source === "all" || item.source === state.source)
            && audiencePreset.matches(item)
            && formatPreset.matches(item)
            && topicPreset.matches(item)
            && lifecycleFilter.matches(item)
            && regionFilter.matches(item)
            && deadlineFilter.matches(item)
            && (!savedIds || savedIds.has(String(item.id)))
            && matchesSearchQuery(item, state.query);
        }})
        .slice()
        .sort(compareVisibleItems);
    }}

    function renderSourceFilter() {{
      const select = $("#source-filter");
      const sources = [
        ...new Set([
          ...state.items.map((item) => item.source),
          ...state.sources.map((source) => source.slug).filter(Boolean)
        ])
      ].sort();
      const options = sources.map((source) => (
        `<option value="${{escapeHtml(source)}}">`
        + `${{escapeHtml(humanizeLabel(source))}}</option>`
      ));
      select.innerHTML = (
        `<option value="all">${{escapeHtml(copy.all_sources)}}</option>`
        + options.join("")
      );
      select.value = state.source;
      if (select.value !== state.source) {{
        state.source = "all";
        select.value = state.source;
      }}
    }}

    function renderPresetControls() {{
      const audienceRoot = $("#audience-presets");
      const formatRoot = $("#format-presets");
      const topicRoot = $("#topic-presets");
      audienceRoot.innerHTML = AUDIENCE_PRESETS.map((preset) => `
        <button
          class="preset-button"
          type="button"
          data-preset-kind="audience"
          data-preset-id="${{escapeHtml(preset.id)}}"
          aria-pressed="${{String(state.audience === preset.id)}}"
          data-avds-component="preset-button"
        >${{escapeHtml(preset.label)}}</button>
      `).join("");
      formatRoot.innerHTML = FORMAT_PRESETS.map((preset) => `
        <button
          class="preset-button"
          type="button"
          data-preset-kind="format"
          data-preset-id="${{escapeHtml(preset.id)}}"
          aria-pressed="${{String(state.format === preset.id)}}"
          data-avds-component="preset-button"
        >${{escapeHtml(preset.label)}}</button>
      `).join("");
      topicRoot.innerHTML = TOPIC_PRESETS.map((preset) => `
        <button
          class="preset-button"
          type="button"
          data-preset-kind="topic"
          data-preset-id="${{escapeHtml(preset.id)}}"
          aria-pressed="${{String(state.topic === preset.id)}}"
          data-avds-component="preset-button"
        >${{escapeHtml(preset.label)}}</button>
      `).join("");
    }}

    function renderMetrics() {{
      const baselineRelevant = Number($("#metric-strong").dataset.catalogCount || 0);
      const highPriority = state.coverage
        && Number.isFinite(state.coverage.relevant_open_items)
        ? state.coverage.relevant_open_items
        : baselineRelevant;
      const sourceCount = new Set(state.items.map((item) => item.source)).size;
      $("#metric-total").textContent = formatNumber.format(
        state.health ? state.health.items : state.items.length
      );
      $("#metric-strong").textContent = formatNumber.format(highPriority);
      $("#metric-sources").textContent = formatNumber.format(
        state.coverage
          ? state.coverage.enabled_sources
          : state.sources.length || sourceCount || 0
      );
    }}

    function renderSourceControls() {{
      const summary = $("#source-summary");
      const toggle = $("#toggle-sources");
      const total = state.sources.length;
      if (!total) {{
        summary.textContent = copy.source_catalog_unavailable;
        toggle.classList.add("hidden");
        return;
      }}
      const shown = state.showAllSources ? total : Math.min(total, COLLAPSED_SOURCES);
      summary.textContent = total > COLLAPSED_SOURCES
        ? text("showing_sources", {{
            shown: formatNumber.format(shown),
            total: formatNumber.format(total)
          }})
        : text("sources_connected", {{ total: formatNumber.format(total) }});
      if (total <= COLLAPSED_SOURCES) {{
        toggle.classList.add("hidden");
        return;
      }}
      toggle.classList.remove("hidden");
      toggle.textContent = state.showAllSources
        ? copy.show_fewer_sources
        : text("show_all_sources_with_total", {{ total: formatNumber.format(total) }});
    }}

    function renderSources() {{
      const list = $("#source-list");
      if (!state.sourcesLoaded) {{
        list.innerHTML = (
          `<div class="message loading-state">`
          + `<span class="visually-hidden">${{escapeHtml(copy.loading_sources)}}</span>`
          + `</div>`
        );
        $("#source-summary").textContent = copy.loading_sources;
        $("#toggle-sources").classList.add("hidden");
        return;
      }}
      if (!state.sources.length) {{
        list.innerHTML = (
          `<div class="message">${{escapeHtml(copy.source_catalog_unavailable)}}</div>`
        );
        renderSourceControls();
        return;
      }}
      const localRelevantCounts = localRelevantBySource();
      const rankedSources = state.sources.slice().sort((left, right) => {{
        const leftLocal = localRelevantCounts.get(left.slug);
        const rightLocal = localRelevantCounts.get(right.slug);
        const leftRelevant = Number.isFinite(leftLocal)
          ? leftLocal
          : Number(left.relevant_open_items || 0);
        const rightRelevant = Number.isFinite(rightLocal)
          ? rightLocal
          : Number(right.relevant_open_items || 0);
        return (
          rightRelevant - leftRelevant
          || Number(right.items || 0) - Number(left.items || 0)
          || String(left.name || left.slug).localeCompare(String(right.name || right.slug))
        );
      }});
      const sources = state.showAllSources
        ? rankedSources
        : rankedSources.slice(0, COLLAPSED_SOURCES);
      list.innerHTML = sources.map((source) => {{
        const items = Number.isFinite(source.items) ? source.items : null;
        const relevant = Number.isFinite(source.relevant_open_items)
          ? source.relevant_open_items
          : null;
        const localRelevant = localRelevantCounts.get(source.slug);
        const relevantCount = Number.isFinite(localRelevant)
          ? localRelevant
          : relevant || 0;
        const countIndexed = items === null
          ? copy.coverage_unavailable
          : text("indexed_count", {{ count: formatNumber.format(items) }});
        const countRelevant = text("relevant_open_count", {{
          count: formatNumber.format(relevantCount)
        }});
        const iconVariant = sourceIconVariant(source);
        const sourceName = escapeHtml(sourceDisplayName(source));
        const refresh = sourceRefreshInfo(source);
        return `
        <a
          class="source-card avds-source-card"
          href="${{escapeHtml(source.base_url)}}"
          target="_blank"
          rel="noopener"
          aria-label="${{sourceName}}"
          data-avds-component="source-card"
        >
          <span
            class="
              source-icon
              avds-source-card__icon
              avds-source-card__icon--${{iconVariant}}
              source-icon--${{iconVariant}}
            "
            aria-hidden="true"
            data-avds-component="source-icon"
          >${{escapeHtml(sourceInitials(source))}}</span>
          <div
            class="source-main avds-source-card__body"
            data-avds-component="source-main"
          >
            <strong class="avds-source-card__name">${{sourceName}}</strong>
            <div class="source-meta" data-avds-component="source-meta">
              ${{sourceBadge(source)}}
              <span class="source-note">${{escapeHtml(sourceContextLabel(source))}}</span>
              <span
                class="source-freshness ${{refresh.tone}}"
                title="${{escapeHtml(copy.source_refresh_title)}}"
              >${{escapeHtml(refresh.label)}}</span>
            </div>
          </div>
          <span
            class="source-url avds-source-card__meta"
            title="${{escapeHtml(source.base_url)}}"
            data-avds-component="source-url"
          >${{escapeHtml(shortUrl(source.base_url))}}</span>
          <div class="source-count" data-avds-component="source-count">
            <span>${{escapeHtml(countIndexed)}}</span>
            <span>${{escapeHtml(countRelevant)}}</span>
          </div>
          <span
            class="source-arrow avds-source-card__arrow"
            aria-hidden="true"
          >›</span>
        </a>
      `;
      }}).join("");
      renderSourceControls();
    }}

    function renderHealth() {{
      const status = state.health && state.health.status ? state.health.status : "-";
      const statusValue = status === "ok"
        ? copy.health_ok_value
        : copy.health_attention_value;
      const items = state.health && Number.isFinite(state.health.items)
        ? formatNumber.format(state.health.items)
        : "-";
      const sources = state.coverage && Number.isFinite(state.coverage.enabled_sources)
        ? formatNumber.format(state.coverage.enabled_sources)
        : formatNumber.format(state.sources.length || 0);
      const staleSources = state.coverage && Number.isFinite(state.coverage.stale_sources)
        ? formatNumber.format(state.coverage.stale_sources)
        : formatNumber.format(
            state.sources.filter((source) => sourceRefreshInfo(source).tone === "is-stale").length
          );
      const latestUpdate = state.items.reduce((latest, item) => {{
        const rank = discoveredRank(item);
        return rank > latest ? rank : latest;
      }}, 0);
      const checkedAt = formatDateTime(state.lastCheckedAt);
      const updatedAt = latestUpdate
        ? formatDateTime(new Date(latestUpdate).toISOString())
        : "–";
      $("#health-status").textContent = statusValue;
      $("#health-items").textContent = items;
      $("#health-sources").textContent = sources;
      $("#health-stale-sources").textContent = staleSources;
      $("#health-note").textContent = latestUpdate
        ? text("health_note_ready", {{
            checked_at: checkedAt,
            updated_at: updatedAt
          }})
        : text("health_note_ready_no_items", {{
            checked_at: checkedAt
          }});
      $("#status-pill span:last-child").textContent = status === "ok"
        ? copy.api_online
        : copy.api_failed;
    }}

    function renderFilterSummary(resultCount) {{
      const summary = $("#filter-summary");
      const pills = [
        `<span class="summary-pill result">${{escapeHtml(
          text("summary_matches", {{ count: formatNumber.format(resultCount) }})
        )}}</span>`
      ];
      if (state.query.trim()) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(
            text("summary_search", {{ value: state.query.trim() }})
          )}}</span>`
        );
      }}
      if (state.audience !== DEFAULT_AUDIENCE) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(
            text("summary_audience", {{ value: activeAudiencePreset().label }})
          )}}</span>`
        );
      }}
      if (state.format !== DEFAULT_FORMAT) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(
            text("summary_format", {{ value: activeFormatPreset().label }})
          )}}</span>`
        );
      }}
      if (state.topic !== DEFAULT_TOPIC) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(
            text("summary_topic", {{ value: activeTopicPreset().label }})
          )}}</span>`
        );
      }}
      if (state.lifecycle !== DEFAULT_LIFECYCLE) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(
            text("summary_lifecycle", {{ value: activeLifecycleFilter().label }})
          )}}</span>`
        );
      }}
      if (state.region !== DEFAULT_REGION) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(
            text("summary_region", {{ value: activeRegionFilter().label }})
          )}}</span>`
        );
      }}
      if (state.deadlineMode !== DEFAULT_DEADLINE) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(
            text("summary_deadline", {{ value: activeDeadlineFilter().label }})
          )}}</span>`
        );
      }}
      if (state.sort !== DEFAULT_SORT) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(
            text("summary_sort", {{ value: activeSortOption().label }})
          )}}</span>`
        );
      }}
      if (state.source !== "all") {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(humanizeLabel(state.source))}}</span>`
        );
      }}
      if (state.includeArchived) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(copy.summary_scope_all)}}</span>`
        );
      }}
      if (state.savedOnly) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(copy.workspace_filter)}}</span>`
        );
      }}
      if (state.minScore !== DEFAULT_SCORE) {{
        pills.push(
          `<span class="summary-pill">${{escapeHtml(
            text("summary_score", {{ value: activeScoreOption().label }})
          )}}</span>`
        );
      }}
      summary.innerHTML = pills.join("");
      $("#clear-filters").disabled = !hasActiveFilters();
    }}

    function renderOpportunities() {{
      const list = $("#opportunities-list");
      const message = $("#opportunities-message");
      message.removeAttribute("aria-label");
      const loadMoreWrap = $("#load-more-wrap");
      const loadMore = $("#load-more");
      renderWorkspaceFilter();
      renderWorkspaceQueue();
      const items = visibleItems();
      renderPresetControls();
      syncControlsFromState();
      syncUrlState();
      $("#opportunities-description").textContent = state.includeArchived
        ? copy.opportunities_description_all
        : copy.opportunities_description;
      if (hasActiveFilters()) {{
        $("#opportunities-description").textContent = [
          text("summary_matches", {{ count: formatNumber.format(items.length) }}),
          state.audience !== DEFAULT_AUDIENCE ? activeAudiencePreset().label : "",
          state.format !== DEFAULT_FORMAT ? activeFormatPreset().label : "",
          state.topic !== DEFAULT_TOPIC ? activeTopicPreset().label : "",
          state.region !== DEFAULT_REGION ? activeRegionFilter().label : ""
        ].filter(Boolean).join(" • ");
      }}
      renderMetrics();
      renderSpotlights();
      renderPathways();
      renderThemes();
      renderTopicBrief(items);
      renderFilterSummary(items.length);

      if (!state.items.length) {{
        message.className = "message";
        message.textContent = copy.no_indexed_items;
        list.innerHTML = "";
        loadMoreWrap.classList.add("hidden");
        return;
      }}
      if (!items.length) {{
        message.className = "message empty";
        message.innerHTML = renderEmptyState();
        list.innerHTML = "";
        loadMoreWrap.classList.add("hidden");
        return;
      }}

      message.className = "message hidden";
      const visible = items.slice(0, state.visibleLimit);
      list.innerHTML = visible.map((item) => {{
        const tags = Array.from(
          new Map(
            (Array.isArray(item.tags) ? item.tags : []).map((tag) => [
              String(tag).trim().toLowerCase(),
              tag
            ])
          ).values()
        ).slice(0, 4);
        const scoreTone = scoreClass(item.score);
        const deadline = formatDeadline(item.deadline);
        const sourceName = humanizeLabel(item.source);
        const funderLabel = item.funder
          ? escapeHtml(humanizeLabel(item.funder))
          : escapeHtml(sourceName);
        const funderHref = escapeHtml(funderPageHref(funderSlug(item)));
        const funderProfileLink = (
          `<a class="footer-funder-link" href="${{funderHref}}">`
          + `${{escapeHtml(copy.view_funder)}}</a>`
        );
        const footerSource = item.funder
          && String(item.funder).toLowerCase() !== sourceName.toLowerCase()
          ? `${{funderLabel}}<span class="footer-sep">|</span>${{escapeHtml(sourceName)}}`
          : funderLabel;
        const badges = itemBadges(item);
        const cardTitleText = String(item.title || "");
        const cardTitle = escapeHtml(cardTitleText);
        const opportunityId = escapeHtml(item.id);
        const cardUrl = escapeHtml(externalActionUrl(item));
        const pageUrl = escapeHtml(opportunityPageHref(item.id));
        const saved = isOpportunitySaved(item.id);
        const saveLabel = saved ? copy.unsave_opportunity : copy.save_opportunity;
        const workflowMarkup = saved
          ? `<label class="workflow-control">
              <span>${{escapeHtml(copy.workflow_label)}}</span>
              <select data-workflow-status="${{opportunityId}}">
                ${{workflowOptionsMarkup(item.id)}}
              </select>
            </label>`
          : "";
        const clickLabel = escapeHtml(cardTitleText);
        const formatLabel = opportunityFormatLabel(item);
        const regionLabel = opportunityRegionLabel(item);
        const deadlineLabel = opportunityDeadlineLabel(item);
        return `<article
          class="opportunity avds-document-row ${{scoreTone}}"
          data-avds-component="opportunity-card"
        >
          <div class="opportunity-main">
            <div class="opportunity-content">
              <div class="opportunity-heading">
                <h3>
                  <a href="${{pageUrl}}">
                    ${{cardTitle}}
                  </a>
                </h3>
                <div class="tags">
                  ${{tags.map((tag) => (
                    `<span class="tag" data-avds-component="tag">`
                    + `${{escapeHtml(humanizeLabel(tag))}}</span>`
                  )).join("")}}
                </div>
              </div>
              <p class="opportunity-summary">${{escapeHtml(summarize(item))}}</p>
              <div class="card-actions">
                <button
                  class="detail-link"
                  type="button"
                  data-opportunity-detail="${{opportunityId}}"
                  data-opportunity-url="${{cardUrl}}"
                >${{escapeHtml(copy.open_details)}}</button>
                <a
                  class="more-link"
                  href="${{cardUrl}}"
                  target="_blank"
                  rel="noopener"
                >${{escapeHtml(copy.open_source_short)}}</a>
                <a
                  class="more-link"
                  href="${{pageUrl}}"
                  target="_blank"
                  rel="noopener"
                >${{escapeHtml(copy.read_more)}}</a>
              </div>
            </div>
            <aside class="opportunity-rail" aria-label="${{escapeHtml(copy.card_meta_label)}}">
              <div class="side">
                <span
                  class="score ${{scoreTone}}"
                  data-avds-component="score"
                  title="${{escapeHtml(copy.score_title)}}"
                >${{formatScore(item.score)}}</span>
                ${{badges}}
              </div>
              <div class="meta-rows" data-avds-component="opportunity-meta">
                <div class="meta-row">
                  <span>${{escapeHtml(copy.meta_format_label)}}</span>
                  <strong>${{escapeHtml(formatLabel)}}</strong>
                </div>
                <div class="meta-row">
                  <span>${{escapeHtml(copy.meta_region_label)}}</span>
                  <strong>${{escapeHtml(regionLabel)}}</strong>
                </div>
                <div class="meta-row">
                  <span>${{escapeHtml(copy.meta_deadline_label)}}</span>
                  <strong>${{escapeHtml(deadlineLabel)}}</strong>
                </div>
                <div class="meta-row">
                  <span>${{escapeHtml(copy.source_label)}}</span>
                  <strong>${{escapeHtml(sourceName)}}</strong>
                </div>
              </div>
              <div class="fit-block">
                <span class="fit-label">${{escapeHtml(copy.fit_label)}}</span>
                <div class="fit-pills">
                  ${{fitPillsMarkup(item)}}
                </div>
              </div>
              ${{workflowMarkup}}
              <div class="card-actions-secondary">
                <button
                  class="detail-link"
                  type="button"
                  data-save-opportunity="${{opportunityId}}"
                >${{escapeHtml(saveLabel)}}</button>
                ${{funderProfileLink}}
              </div>
            </aside>
            <button
              class="opportunity-click"
              type="button"
              data-opportunity-id="${{opportunityId}}"
              data-opportunity-url="${{cardUrl}}"
              aria-label="${{escapeHtml(copy.open_details)}}: ${{clickLabel}}"
            ></button>
          </div>
        </article>`;
      }}).join("");
      if (items.length > visible.length) {{
        loadMoreWrap.classList.remove("hidden");
        loadMore.textContent = text("results_button", {{
          count: formatNumber.format(Math.min(DEFAULT_VISIBLE_ITEMS, items.length - visible.length))
        }});
      }} else {{
        loadMoreWrap.classList.add("hidden");
      }}
      bindOpportunityCards();
    }}

    let searchRenderTimer = 0;
    function scheduleOpportunityRender() {{
      window.clearTimeout(searchRenderTimer);
      searchRenderTimer = window.setTimeout(renderOpportunities, 120);
    }}

    function bindOpportunityCards() {{
      const cards = document.querySelectorAll("[data-opportunity-id]");
      cards.forEach((button) => {{
        if (button.dataset.bound === "true") {{
          return;
        }}
        button.dataset.bound = "true";
        button.addEventListener("click", () => {{
          const opportunityId = button.getAttribute("data-opportunity-id");
          const fallbackUrl = button.getAttribute("data-opportunity-url") || "";
          openOpportunityDetail(opportunityId, fallbackUrl);
        }});
      }});
      const detailButtons = document.querySelectorAll("[data-opportunity-detail]");
      detailButtons.forEach((button) => {{
        if (button.dataset.bound === "true") {{
          return;
        }}
        button.dataset.bound = "true";
        button.addEventListener("click", () => {{
          const opportunityId = button.getAttribute("data-opportunity-detail");
          const fallbackUrl = button.getAttribute("data-opportunity-url") || "";
          openOpportunityDetail(opportunityId, fallbackUrl);
        }});
      }});
      const saveButtons = document.querySelectorAll("[data-save-opportunity]");
      saveButtons.forEach((button) => {{
        if (button.dataset.bound === "true") {{
          return;
        }}
        button.dataset.bound = "true";
        button.addEventListener("click", () => {{
          toggleSavedOpportunity(button.getAttribute("data-save-opportunity"));
        }});
      }});
      const workflowControls = document.querySelectorAll("[data-workflow-status]");
      workflowControls.forEach((control) => {{
        if (control.dataset.bound === "true") return;
        control.dataset.bound = "true";
        control.addEventListener("change", () => {{
          setOpportunityWorkflowStatus(
            control.getAttribute("data-workflow-status"),
            control.value
          );
        }});
      }});
    }}

    async function loadHealth() {{
      state.health = await fetchJson("/health");
      state.lastCheckedAt = new Date().toISOString();
      renderHealth();
      renderMetrics();
    }}

    async function loadSources() {{
      try {{
        state.coverage = await fetchJson("/coverage");
        state.sources = Array.isArray(state.coverage.sources)
          ? state.coverage.sources
          : [];
      }} catch (error) {{
        state.coverage = null;
        state.sources = await fetchJson("/sources");
      }}
      state.sourcesLoaded = true;
      state.lastCheckedAt = new Date().toISOString();
      renderSources();
      renderHealth();
      renderMetrics();
    }}

    async function loadFunders() {{
      try {{
        state.funders = await fetchJson("/funders?limit=24");
      }} catch {{
        state.funders = [];
      }}
      renderFunders();
    }}

    async function loadOpportunities() {{
      const message = $("#opportunities-message");
      const today = localDateISO();
      const params = state.includeArchived
        ? "limit=5000&min_score=0&include_irrelevant=true&compact=true"
        : `limit=5000&min_score=0&deadline_after=${{today}}&compact=true`;
      message.className = "message loading-state";
      message.setAttribute("aria-label", copy.loading_opportunities);
      message.innerHTML = `<span class="visually-hidden">${{escapeHtml(
        copy.loading_opportunities
      )}}</span>`;
      state.items = await fetchJson(withLang(`/opportunities?${{params}}`));
      state.lastCheckedAt = new Date().toISOString();
      resetVisibleLimit();
      renderSourceFilter();
      renderSources();
      renderOpportunities();
    }}

    async function reloadAll() {{
      try {{
        await Promise.all([loadHealth(), loadSources(), loadFunders(), loadOpportunities()]);
      }} catch (error) {{
        $("#opportunities-message").className = "message error";
        $("#opportunities-message").textContent = error.message;
        $("#status-pill span:last-child").textContent = copy.api_error;
      }} finally {{
        syncViewFromHash();
      }}
    }}

    const viewTargets = {{
      opportunities: "#opportunities-panel",
      sources: "#sources-panel",
      health: "#health-panel"
    }};
    const trustLibrary = $("#trust-library");
    const trustHashes = new Set(["sources-panel", "health-panel", "methodology-panel"]);
    const viewButtons = document.querySelectorAll("[data-view]");

    function setActiveView(view) {{
      viewButtons.forEach((button) => {{
        button.setAttribute(
          "aria-pressed",
          String(button.dataset.view === view)
        );
      }});
    }}

    function goToView(view, options = {{}}) {{
      const selector = viewTargets[view] || viewTargets.opportunities;
      const target = document.querySelector(selector);
      if (!target) return;
      if (view === "sources" || view === "health") {{
        trustLibrary.open = true;
      }}
      const shouldScroll = options.scroll !== false;
      setActiveView(view);
      const nextHash = `#${{view}}`;
      if (window.location.hash !== nextHash) {{
        window.history.replaceState(
          null,
          "",
          `${{window.location.pathname}}${{window.location.search}}${{nextHash}}`
        );
      }}
      if (shouldScroll) {{
        target.scrollIntoView({{ behavior: "auto", block: "start" }});
      }}
    }}

    function syncViewFromHash(options = {{}}) {{
      const view = window.location.hash.replace("#", "");
      if (viewTargets[view]) {{
        goToView(view, options);
      }} else if (trustHashes.has(view)) {{
        trustLibrary.open = true;
        setActiveView("sources");
        if (options.scroll !== false) {{
          window.requestAnimationFrame(() => {{
            document.getElementById(view)?.scrollIntoView({{
              behavior: "auto",
              block: "start"
            }});
          }});
        }}
      }} else {{
        setActiveView("opportunities");
      }}
    }}

    let resizeSyncTimer = 0;
    function scheduleHashViewSync() {{
      const view = window.location.hash.replace("#", "");
      if (!viewTargets[view]) return;
      window.clearTimeout(resizeSyncTimer);
      resizeSyncTimer = window.setTimeout(() => {{
        syncViewFromHash({{ scroll: false }});
      }}, 120);
    }}

    viewButtons.forEach((button) => {{
      button.addEventListener("click", () => {{
        goToView(button.dataset.view);
      }});
    }});
    document.querySelectorAll(
      'a[href="#methodology-panel"], a[href="#health-panel"]'
    ).forEach((link) => {{
      link.addEventListener("click", () => {{
        trustLibrary.open = true;
        setActiveView("sources");
      }});
    }});

    applyStateFromUrl();
    const filterDisclosure = $("#filter-disclosure");
    if (filterDisclosure && window.matchMedia("(max-width: 760px)").matches) {{
      filterDisclosure.open = false;
    }}
    document.documentElement.removeAttribute("data-compact-filters");
    renderSavedViews();
    renderWorkspaceFilter();
    window.addEventListener("hashchange", syncViewFromHash);
    window.addEventListener("resize", scheduleHashViewSync);
    window.requestAnimationFrame(syncViewFromHash);
    $("#detail-close").addEventListener("click", closeDetailShell);
    $("#detail-backdrop").addEventListener("click", closeDetailShell);
    window.addEventListener("keydown", (event) => {{
      const drawer = $("#detail-drawer");
      if (drawer.hidden) return;
      if (event.key === "Escape") {{
        closeDetailShell();
        return;
      }}
      if (event.key !== "Tab") return;
      const focusable = Array.from(drawer.querySelectorAll(
        'a[href]:not(.hidden), button:not([disabled]), select:not([disabled]), [tabindex="0"]'
      )).filter((element) => !element.hidden);
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {{
        event.preventDefault();
        last.focus();
      }} else if (!event.shiftKey && document.activeElement === last) {{
        event.preventDefault();
        first.focus();
      }}
    }});

    $("#toggle-sources").addEventListener("click", () => {{
      state.showAllSources = !state.showAllSources;
      renderSources();
    }});
    $("#reload").addEventListener("click", () => {{
      if (!window.confirm(copy.reload_confirm)) return;
      reloadAll();
    }});
    $("#load-more").addEventListener("click", () => {{
      state.visibleLimit += DEFAULT_VISIBLE_ITEMS;
      renderOpportunities();
    }});
    document.addEventListener("click", (event) => {{
      const heroAction = event.target.closest("[data-hero-view]");
      if (heroAction) {{
        applyHeroAction(heroAction);
        return;
      }}
      const emptyAction = event.target.closest("[data-empty-action]");
      if (emptyAction) {{
        applyEmptyAction(emptyAction.getAttribute("data-empty-action") || "");
        return;
      }}
      const topicReset = event.target.closest("[data-topic-reset]");
      if (topicReset) {{
        state.topic = DEFAULT_TOPIC;
        resetVisibleLimit();
        renderOpportunities();
        return;
      }}
      const button = event.target.closest("[data-preset-kind]");
      if (!button) return;
      const presetKind = button.getAttribute("data-preset-kind");
      const presetId = button.getAttribute("data-preset-id") || "all";
      if (presetKind === "audience") {{
        state.audience = presetId;
      }}
      if (presetKind === "format") {{
        state.format = presetId;
      }}
      if (presetKind === "topic") {{
        state.topic = presetId;
      }}
      resetVisibleLimit();
      renderOpportunities();
    }});
    $("#search").addEventListener("input", (event) => {{
      state.query = event.target.value;
      resetVisibleLimit();
      scheduleOpportunityRender();
    }});
    $("#sort-filter").addEventListener("change", (event) => {{
      state.sort = event.target.value;
      resetVisibleLimit();
      renderOpportunities();
    }});
    $("#score-filter").addEventListener("change", (event) => {{
      state.minScore = Number(event.target.value);
      resetVisibleLimit();
      renderOpportunities();
    }});
    $("#scope-filter").addEventListener("change", (event) => {{
      state.includeArchived = event.target.value === "all";
      state.minScore = scoreDefaultForScope();
      if (
        !state.includeArchived
        && (state.lifecycle === "closed" || state.lifecycle === "awarded")
      ) {{
        state.lifecycle = DEFAULT_LIFECYCLE;
      }}
      reloadAll();
    }});
    $("#lifecycle-filter").addEventListener("change", (event) => {{
      state.lifecycle = event.target.value;
      resetVisibleLimit();
      if (
        (state.lifecycle === "closed" || state.lifecycle === "awarded")
        && !state.includeArchived
      ) {{
        state.includeArchived = true;
        state.minScore = scoreDefaultForScope();
        reloadAll();
        return;
      }}
      renderOpportunities();
    }});
    $("#source-filter").addEventListener("change", (event) => {{
      state.source = event.target.value;
      resetVisibleLimit();
      renderOpportunities();
    }});
    $("#region-filter").addEventListener("change", (event) => {{
      state.region = event.target.value;
      resetVisibleLimit();
      renderOpportunities();
    }});
    $("#deadline-filter").addEventListener("change", (event) => {{
      state.deadlineMode = event.target.value;
      resetVisibleLimit();
      renderOpportunities();
    }});
    $("#clear-filters").addEventListener("click", () => {{
      if (!hasActiveFilters()) return;
      clearAllFilters();
    }});
    $("#workspace-filter").addEventListener("click", () => {{
      if (!readSavedOpportunities().length) {{
        setSavedViewNotice(copy.workspace_filter_empty);
        return;
      }}
      state.savedOnly = !state.savedOnly;
      resetVisibleLimit();
      renderOpportunities();
    }});
    $("#export-workspace").addEventListener("click", exportWorkspace);
    $("#import-workspace").addEventListener("change", (event) => {{
      importWorkspace(event.target.files && event.target.files[0]);
    }});
    $("#save-view").addEventListener("click", saveCurrentView);
    $("#share-view").addEventListener("click", () => {{
      shareCurrentView();
    }});
    $("#export-csv").addEventListener("click", exportVisibleCsv);
    $("#export-deadlines").addEventListener("click", exportVisibleDeadlines);
    document.addEventListener("click", (event) => {{
      const applyButton = event.target.closest("[data-saved-view]");
      if (applyButton) {{
        applySavedView(applyButton.getAttribute("data-saved-view") || "");
        return;
      }}
      const removeButton = event.target.closest("[data-remove-saved-view]");
      if (removeButton) {{
        removeSavedView(removeButton.getAttribute("data-remove-saved-view") || "");
      }}
    }});

    reloadAll();
  </script>
</body>
</html>"""  # nosec B608
