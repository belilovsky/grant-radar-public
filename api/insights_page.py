"""Server-rendered analytics and data-centre page for QAZ.FUND."""

from __future__ import annotations

from html import escape
from typing import Any

from api.avds import AVDS_CSS, AVDS_FONT_HEAD
from api.public_meta import analytics_head_html, og_image_url


def _href(root_path: str, path: str, lang: str | None = None) -> str:
    base = root_path.rstrip("/")
    value = f"{base}{path}" if base else path
    if lang:
        separator = "&" if "?" in value else "?"
        value = f"{value}{separator}lang={lang}"
    return value


def _absolute(site_origin: str, value: str) -> str:
    if value.startswith(("http://", "https://")):
        return value
    return f"{site_origin.rstrip('/')}{value}" if site_origin else value


def _number(value: object, lang: str) -> str:
    try:
        number = int(str(value or 0))
    except (TypeError, ValueError):
        number = 0
    return f"{number:,}".replace(",", " ") if lang == "ru" else f"{number:,}"


def _percent(value: object, lang: str) -> str:
    try:
        number = float(str(value or 0))
    except (TypeError, ValueError):
        number = 0.0
    text = f"{number:.1f}".rstrip("0").rstrip(".")
    if lang == "ru":
        text = text.replace(".", ",")
    return f"{text}%"


def _bar_chart(
    rows: list[dict[str, Any]],
    *,
    chart_id: str,
    max_rows: int = 10,
) -> str:
    visible = rows[:max_rows]
    if not visible:
        return '<p class="empty-chart">Данных пока недостаточно.</p>'
    maximum = max(int(row.get("count") or 0) for row in visible) or 1
    return "".join(
        """
        <div class="bar-row" data-chart-id="{chart_id}">
          <div class="bar-label">
            <span>{label}</span>
            <strong
              class="bar-value"
              data-count="{count}"
              data-share="{share}"
            >{count}</strong>
          </div>
          <div
            class="bar-track"
            data-avds-component="Progress"
            role="img"
            aria-label="{label}: {count}"
          >
            <span style="width:{width:.2f}%"></span>
          </div>
        </div>
        """.format(
            label=escape(str(row.get("label") or row.get("key") or "")),
            count=int(row.get("count") or 0),
            share=float(row.get("share") or 0),
            width=max(1.5, (int(row.get("count") or 0) / maximum) * 100),
            chart_id=escape(chart_id, quote=True),
        )
        for row in visible
    )


def _quality_cards(
    rows: list[dict[str, Any]],
    *,
    lang: str,
) -> str:
    return "".join(
        """
        <article class="quality-card" data-avds-component="DataQualityScorecard">
          <div class="quality-top">
            <span>{label}</span>
            <strong>{share}</strong>
          </div>
          <div
            class="quality-track"
            data-avds-component="Progress"
            role="progressbar"
            aria-valuenow="{share_raw}"
            aria-valuemin="0"
            aria-valuemax="100"
            aria-label="{label}"
          ><span style="width:{share_raw:.1f}%"></span></div>
          <small>{count} {records}</small>
        </article>
        """.format(
            label=escape(str(row.get("label") or "")),
            share=escape(_percent(row.get("share"), lang)),
            share_raw=float(row.get("share") or 0),
            count=escape(_number(row.get("count"), lang)),
            records="карточек" if lang == "ru" else "records",
        )
        for row in rows
    )


def _deadline_chart(rows: list[dict[str, Any]], *, lang: str) -> str:
    segments = "".join(
        """
        <span
          class="deadline-segment deadline-segment--{index}"
          style="width:{width:.2f}%"
          title="{label}: {count}"
        ></span>
        """.format(
            index=index % 6,
            width=max(1.5, float(row.get("share") or 0)),
            label=escape(str(row.get("label") or ""), quote=True),
            count=int(row.get("count") or 0),
        )
        for index, row in enumerate(rows)
    )
    legend = "".join(
        """
        <div class="deadline-key">
          <span class="deadline-dot deadline-segment--{index}"></span>
          <div>
            <strong>{count}</strong>
            <small>{label}</small>
          </div>
        </div>
        """.format(
            index=index % 6,
            count=escape(_number(row.get("count"), lang)),
            label=escape(str(row.get("label") or "")),
        )
        for index, row in enumerate(rows)
    )
    return (
        f'<div class="deadline-band" aria-hidden="true">{segments}</div>'
        f'<div class="deadline-legend">{legend}</div>'
    )


def _source_rows(rows: list[dict[str, Any]], *, lang: str) -> str:
    return "".join(
        """
        <div class="source-rank" role="row">
          <span class="source-rank-number">{index:02d}</span>
          <strong>{label}</strong>
          <span>{count}</span>
          <small>{share}</small>
        </div>
        """.format(
            index=index,
            label=escape(str(row.get("label") or "")),
            count=escape(_number(row.get("count"), lang)),
            share=escape(_percent(row.get("share"), lang)),
        )
        for index, row in enumerate(rows[:10], 1)
    )


def _history_markup(history: dict[str, Any], *, lang: str) -> str:
    created = int(history.get("created") or 0)
    changed = int(history.get("changed") or 0)
    available = bool(history.get("available"))
    rows = history.get("items")
    items = rows if isinstance(rows, list) else []
    copy = {
        "ru": {
            "collecting": (
                "Журнал изменений включён. Он начнёт отличать новые программы "
                "от изменённых после очередного обхода источников."
            ),
            "empty": "За последние сутки содержательных изменений не зафиксировано.",
            "created": "Новых",
            "changed": "Изменено",
            "open": "Открыть",
        },
        "en": {
            "collecting": (
                "The change ledger is active. It will distinguish new records "
                "from updated ones after the next source run."
            ),
            "empty": "No semantic changes were captured during the past 24 hours.",
            "created": "New",
            "changed": "Updated",
            "open": "Open",
        },
    }[lang]
    if not available:
        return f'<div class="history-empty">{escape(copy["collecting"])}</div>'
    if not items:
        return (
            '<div class="history-summary">'
            f'<span><strong>{created}</strong>{escape(copy["created"])}</span>'
            f'<span><strong>{changed}</strong>{escape(copy["changed"])}</span>'
            "</div>"
            f'<div class="history-empty">{escape(copy["empty"])}</div>'
        )
    cards = "".join(
        """
        <article class="change-card" data-avds-component="Card">
          <span>{kind}</span>
          <h3>{title}</h3>
          <p>{fields}</p>
          <a href="{href}">{open_label}</a>
        </article>
        """.format(
            kind=escape(
                (
                    copy["created"]
                    if str(row.get("change_type")) == "created"
                    else copy["changed"]
                )
            ),
            title=escape(str(row.get("title") or "")),
            fields=escape(
                ", ".join(str(value) for value in row.get("changed_fields") or [])
                or ("Новая карточка" if lang == "ru" else "New record")
            ),
            href=escape(str(row.get("public_page") or "#"), quote=True),
            open_label=escape(copy["open"]),
        )
        for row in items[:6]
    )
    return (
        '<div class="history-summary">'
        f'<span><strong>{created}</strong>{escape(copy["created"])}</span>'
        f'<span><strong>{changed}</strong>{escape(copy["changed"])}</span>'
        "</div>"
        f'<div class="change-grid">{cards}</div>'
    )


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _row_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def render_insights_page(
    *,
    payload: dict[str, Any],
    lang: str,
    root_path: str,
    site_origin: str,
) -> str:
    """Render a dense, responsive analytics surface backed by public data."""

    active_lang = "en" if lang == "en" else "ru"
    scope = _mapping(payload.get("scope"))
    quality = _mapping(payload.get("quality"))
    distribution = _mapping(payload.get("distribution"))
    signals = _mapping(payload.get("signals"))
    history = _mapping(payload.get("history"))
    copy: dict[str, str] = {
        "ru": {
            "title": "Данные о финансировании Казахстана",
            "description": (
                "Открытые программы, источники, сроки и качество данных в одном "
                "проверяемом представлении."
            ),
            "eyebrow": "Центр данных QAZ.FUND",
            "lead": (
                "Карта текущего каталога: что доступно, кто может участвовать, "
                "где сосредоточены возможности и каких сведений пока не хватает."
            ),
            "catalog": "Открыть каталог",
            "api": "Данные для систем",
            "active": "В текущем каталоге",
            "sources": "Источников в выборке",
            "closing": "Срок в ближайшие 30 дней",
            "kz": "С прямым фокусом на Казахстан",
            "snapshot": "Срез каталога",
            "snapshot_title": "Из чего состоит доступная поддержка",
            "snapshot_text": (
                "Расчёт ведётся по текущему каталогу. Одна программа может "
                "относиться к нескольким темам и аудиториям, а основной формат "
                "считается один раз."
            ),
            "count": "Количество",
            "share": "Доля",
            "formats": "Форматы поддержки",
            "audiences": "Кому адресованы программы",
            "themes": "Основные темы",
            "deadlines": "Календарь решений",
            "deadlines_title": "Когда нужно действовать",
            "deadlines_text": (
                "Карточки текущего каталога по ближайшему сроку подачи."
            ),
            "quality": "Качество данных",
            "quality_title": "Что известно до перехода к источнику",
            "quality_text": (
                "Покрытие ключевых полей в текущем каталоге. Низкое значение "
                "означает недостаток сведений у первоисточника или в текущем "
                "адаптере."
            ),
            "quality_note": (
                "Статус «с источником» означает наличие проверяемой ссылки, а не "
                "независимое подтверждение права на участие."
            ),
            "complete": "Полный набор ключевых полей",
            "procurement": "Доля закупок и конкурсов",
            "sources_title": "Какие источники формируют каталог",
            "sources_text": (
                "Рейтинг показывает вклад источника в текущий каталог, а не его "
                "качество или объём финансирования."
            ),
            "changes": "Изменения",
            "changes_title": "Что появилось и изменилось за сутки",
            "changes_text": (
                "Журнал сравнивает содержательные поля и не считает обычную "
                "перепроверку новой программой."
            ),
            "reuse": "Открытые данные",
            "reuse_title": "Для исследований, редакций и ИИ-систем",
            "reuse_text": (
                "Версионированные записи, ссылки на первоисточники и машиночитаемые "
                "выгрузки доступны без отдельного кабинета."
            ),
            "json": "API каталога",
            "ndjson": "Скачать NDJSON",
            "changes_api": "Журнал изменений",
            "rss": "Лента RSS",
            "schema": "Схема данных",
            "docs": "Документация",
            "method": "Как читать показатели",
            "method_text": (
                "Текущий каталог совпадает с начальной выдачей: применимость к "
                "Казахстану, порог отбора 0,30, неистёкший срок и неархивное "
                "состояние. Полный релевантный индекс остаётся доступен через API. "
                "Суммы не складываются без сопоставимых валют и правил."
            ),
            "indexed": "Релевантных карточек в индексе",
            "revision": "Версия набора",
            "as_of": "Срез на",
            "home": "Каталог",
            "status": "Статус данных",
            "terms": "Условия",
            "data_policy": "Политика данных",
            "attribution": "Использование данных",
            "footer": (
                "QAZ.FUND не выдаёт финансирование и не подтверждает право на "
                "участие. Решение принимается по условиям организатора."
            ),
        },
        "en": {
            "title": "Funding data for Kazakhstan",
            "description": (
                "Open programmes, sources, deadlines and data quality in one "
                "auditable view."
            ),
            "eyebrow": "QAZ.FUND data centre",
            "lead": (
                "A map of the current catalogue: what is available, who it is for, "
                "where opportunities concentrate and which facts are still missing."
            ),
            "catalog": "Open catalogue",
            "api": "Data for systems",
            "active": "Current catalogue",
            "sources": "Sources in this set",
            "closing": "Due within 30 days",
            "kz": "Explicit Kazakhstan focus",
            "snapshot": "Catalogue snapshot",
            "snapshot_title": "What available support consists of",
            "snapshot_text": (
                "Figures use the current catalogue. A programme may belong to "
                "several themes and audiences, while its primary format is counted "
                "once."
            ),
            "count": "Count",
            "share": "Share",
            "formats": "Support formats",
            "audiences": "Intended applicants",
            "themes": "Main themes",
            "deadlines": "Decision calendar",
            "deadlines_title": "When action is needed",
            "deadlines_text": "Current catalogue records grouped by nearest deadline.",
            "quality": "Data quality",
            "quality_title": "What is known before opening the source",
            "quality_text": (
                "Coverage of key fields across the current catalogue. A low value "
                "means the primary source or current adapter does not provide "
                "enough detail."
            ),
            "quality_note": (
                "A sourced record has an auditable primary link. It does not mean "
                "eligibility was independently confirmed."
            ),
            "complete": "All core fields known",
            "procurement": "Procurement and call share",
            "sources_title": "Which sources shape the catalogue",
            "sources_text": (
                "The ranking reflects a source's contribution to the current set, "
                "not its quality or funding volume."
            ),
            "changes": "Changes",
            "changes_title": "What appeared or changed in the past day",
            "changes_text": (
                "The ledger compares semantic fields and does not treat a routine "
                "source check as a new opportunity."
            ),
            "reuse": "Open data",
            "reuse_title": "For research, media and AI systems",
            "reuse_text": (
                "Versioned records, primary-source links and machine-readable "
                "exports are available without a separate account."
            ),
            "json": "Catalogue API",
            "ndjson": "Download NDJSON",
            "changes_api": "Change ledger",
            "rss": "RSS feed",
            "schema": "Data schema",
            "docs": "Documentation",
            "method": "How to read the figures",
            "method_text": (
                "The current catalogue matches the default results: Kazakhstan "
                "relevance, a 0.30 public threshold, an unexpired deadline and a "
                "non-archival state. The full relevant index remains available "
                "through the API. Amounts are not summed across incompatible "
                "currencies or funding rules."
            ),
            "indexed": "Relevant records in the index",
            "revision": "Dataset revision",
            "as_of": "Snapshot date",
            "home": "Catalogue",
            "status": "Data status",
            "terms": "Terms",
            "data_policy": "Data policy",
            "attribution": "Data use",
            "footer": (
                "QAZ.FUND does not award funding or confirm eligibility. The "
                "organizer's current terms govern every application."
            ),
        },
    }[active_lang]

    catalog_href = _href(root_path, "/", active_lang)
    api_href = _href(root_path, "/api/v1")
    ndjson_href = _href(
        root_path,
        "/api/v1/opportunities.ndjson?limit=5000",
        active_lang,
    )
    changes_href = _href(root_path, "/api/v1/changes?hours=24", active_lang)
    rss_href = _href(root_path, "/media/v1/feed.rss", active_lang)
    schema_href = _href(root_path, "/api/v1/schema")
    docs_href = _href(root_path, "/docs", active_lang)
    status_href = _href(root_path, "/status", active_lang)
    terms_href = _href(root_path, "/terms", active_lang)
    data_policy_href = _href(root_path, "/data-policy", active_lang)
    attribution_href = _href(root_path, "/attribution", active_lang)
    ru_href = _href(root_path, "/insights", "ru")
    en_href = _href(root_path, "/insights", "en")
    canonical_path = _href(root_path, "/insights", active_lang)
    canonical_href = _absolute(site_origin, canonical_path)
    page_title = f"{copy['title']} – QAZ.FUND"
    social_image = og_image_url(site_origin, root_path)
    revision = str(payload.get("dataset_revision") or "")
    revision_short = revision[:18] + "…" if len(revision) > 19 else revision
    formats = _row_list(distribution.get("formats"))
    audiences = _row_list(distribution.get("audiences"))
    themes = _row_list(distribution.get("themes"))
    deadlines = _row_list(distribution.get("deadlines"))
    source_distribution = _row_list(distribution.get("sources"))
    completeness = _row_list(quality.get("completeness"))
    analytics_head = analytics_head_html()
    theme_cells = "".join(
        (
            '<div class="theme-cell">'
            f'<strong>{_number(row.get("count"), active_lang)}</strong>'
            f'<span>{escape(str(row.get("label") or ""))}</span>'
            "</div>"
        )
        for row in themes[:10]
    )
    quality_cards_markup = _quality_cards(completeness, lang=active_lang)
    complete_share = _percent(quality.get("complete_core_share"), active_lang)
    procurement_share = _percent(signals.get("procurement_share"), active_lang)
    source_rows_markup = _source_rows(source_distribution, lang=active_lang)
    history_markup = _history_markup(history, lang=active_lang)
    reuse_links = "".join(
        (
            f'<a class="reuse-link" href="{escape(href, quote=True)}" '
            'data-avds-component="Card">'
            f"<span>{escape(format_name)}</span>"
            f"<strong>{escape(label)}</strong>"
            "</a>"
        )
        for href, format_name, label in (
            (api_href, "JSON", copy["json"]),
            (ndjson_href, "NDJSON", copy["ndjson"]),
            (changes_href, "JSON", copy["changes_api"]),
            (rss_href, "RSS", copy["rss"]),
            (schema_href, "JSON Schema", copy["schema"]),
            (docs_href, "OpenAPI", copy["docs"]),
        )
    )

    return f"""<!doctype html>
<html lang="{active_lang}" data-avds="grant-radar" data-av-theme="light" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(page_title)}</title>
  <meta name="description" content="{escape(copy["description"], quote=True)}">
  <link rel="canonical" href="{escape(canonical_href, quote=True)}">
  <link rel="alternate" hreflang="ru" href="{escape(_absolute(site_origin, ru_href), quote=True)}">
  <link rel="alternate" hreflang="en" href="{escape(_absolute(site_origin, en_href), quote=True)}">
  <link
    rel="alternate"
    hreflang="x-default"
    href="{escape(_absolute(site_origin, ru_href), quote=True)}"
  >
  <meta property="og:type" content="website">
  <meta property="og:title" content="{escape(page_title, quote=True)}">
  <meta property="og:description" content="{escape(copy["description"], quote=True)}">
  <meta property="og:url" content="{escape(canonical_href, quote=True)}">
  <meta property="og:image" content="{escape(social_image, quote=True)}">
  <meta name="twitter:card" content="summary_large_image">
{analytics_head}
{AVDS_FONT_HEAD}
  <style>
{AVDS_CSS}
    :root {{
      color-scheme: light;
      --ink: var(--color-text);
      --muted: var(--color-text-muted);
      --line: var(--color-border);
      --soft: var(--color-bg-subtle);
      --panel: var(--color-surface);
      --navy: #08182c;
      --navy-2: #112b4b;
      --blue: var(--color-accent);
      --green: var(--color-success);
      --amber: var(--color-warning);
      --radius: var(--av-radius-lg);
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      background: var(--color-bg);
      color: var(--ink);
      font-family: var(--av-font-sans);
      line-height: 1.45;
    }}
    a {{ color: inherit; }}
    .shell {{
      width: min(1280px, calc(100% - 32px));
      margin: 16px auto 36px;
    }}
    .topbar {{
      min-height: 48px;
      padding: 0 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: var(--panel);
      box-shadow: 0 4px 16px rgb(15 23 42 / 0.04);
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 800;
      text-decoration: none;
      letter-spacing: -0.02em;
    }}
    .brand-mark {{
      width: 24px;
      height: 24px;
      display: grid;
      place-items: center;
      border-radius: var(--av-radius-md);
      background: var(--navy);
      color: white;
      font-size: 10px;
    }}
    .top-actions, .lang-switch {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .top-actions > a, .lang-switch a {{
      min-height: 32px;
      padding: 7px 9px;
      display: inline-flex;
      align-items: center;
      border-radius: 7px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-decoration: none;
    }}
    .lang-switch {{
      padding-left: 6px;
      border-left: 1px solid var(--line);
    }}
    .lang-switch a.active {{
      background: var(--soft);
      color: var(--ink);
    }}
    .hero {{
      margin-top: 12px;
      padding: 42px;
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(310px, .65fr);
      gap: 38px;
      border-radius: calc(var(--av-radius-lg) + var(--av-radius-sm));
      background: var(--navy);
      color: white;
      overflow: hidden;
      box-shadow: 0 16px 40px rgb(8 24 44 / 0.14);
    }}
    .eyebrow {{
      color: #84b6ff;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: .12em;
      text-transform: uppercase;
    }}
    h1 {{
      max-width: 780px;
      margin: 10px 0 14px;
      font-size: clamp(34px, 5vw, 66px);
      line-height: .98;
      letter-spacing: -0.055em;
    }}
    .lead {{
      max-width: 720px;
      margin: 0;
      color: #c8d6e8;
      font-size: 17px;
    }}
    .hero-actions {{
      margin-top: 24px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .button {{
      min-height: 42px;
      padding: 10px 14px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 1px solid rgb(255 255 255 / .2);
      border-radius: var(--av-radius-md);
      background: transparent;
      color: white;
      font-size: 13px;
      font-weight: 800;
      text-decoration: none;
    }}
    .button.primary {{
      border-color: white;
      background: white;
      color: var(--navy);
    }}
    .hero-metrics {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 1px;
      align-self: stretch;
      border: 1px solid rgb(255 255 255 / .15);
      border-radius: var(--av-radius-lg);
      background: rgb(255 255 255 / .15);
      overflow: hidden;
    }}
    .hero-metric {{
      min-height: 112px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      background: var(--navy-2);
    }}
    .hero-metric strong {{
      font-size: 32px;
      line-height: 1;
      letter-spacing: -0.04em;
    }}
    .hero-metric span {{
      color: #b8c8dc;
      font-size: 12px;
    }}
    .section {{
      margin-top: 12px;
      padding: 28px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--panel);
      box-shadow: 0 6px 20px rgb(15 23 42 / .035);
    }}
    .section-head {{
      margin-bottom: 22px;
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 24px;
    }}
    .section-head h2 {{
      margin: 4px 0 5px;
      font-size: 25px;
      line-height: 1.12;
      letter-spacing: -0.035em;
    }}
    .section-head p {{
      max-width: 720px;
      margin: 0;
      color: var(--muted);
      font-size: 13px;
    }}
    .chart-toggle {{
      padding: 3px;
      display: flex;
      gap: 2px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--soft);
    }}
    .chart-toggle button {{
      min-height: 30px;
      padding: 6px 9px;
      border: 0;
      border-radius: 6px;
      background: transparent;
      color: var(--muted);
      font: inherit;
      font-size: 11px;
      font-weight: 800;
      cursor: pointer;
    }}
    .chart-toggle button.active {{
      background: white;
      color: var(--ink);
      box-shadow: 0 1px 4px rgb(15 23 42 / .08);
    }}
    .chart-grid {{
      display: grid;
      grid-template-columns: 1.2fr .8fr;
      gap: 24px;
    }}
    .chart-panel {{
      min-width: 0;
      padding: 20px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: var(--color-bg-subtle);
    }}
    .chart-panel h3 {{
      margin: 0 0 18px;
      font-size: 15px;
    }}
    .bar-row + .bar-row {{ margin-top: 13px; }}
    .bar-label {{
      margin-bottom: 5px;
      display: flex;
      justify-content: space-between;
      gap: 12px;
      font-size: 12px;
    }}
    .bar-label span {{
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .bar-label strong {{
      color: var(--muted);
      font-variant-numeric: tabular-nums;
    }}
    .bar-track {{
      height: 7px;
      border-radius: 99px;
      background: var(--av-color-slate-200);
      overflow: hidden;
    }}
    .bar-track span {{
      height: 100%;
      display: block;
      border-radius: inherit;
      background: var(--blue);
    }}
    .chart-panel:nth-child(2) .bar-track span {{ background: var(--green); }}
    .theme-strip {{
      margin-top: 20px;
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 8px;
    }}
    .theme-cell {{
      min-height: 96px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: var(--panel);
    }}
    .theme-cell strong {{ font-size: 20px; }}
    .theme-cell span {{ color: var(--muted); font-size: 11px; }}
    .deadline-layout {{
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(260px, .65fr);
      gap: 28px;
      align-items: center;
    }}
    .deadline-band {{
      height: 38px;
      display: flex;
      border-radius: var(--av-radius-md);
      background: var(--soft);
      overflow: hidden;
    }}
    .deadline-segment {{ display: block; min-width: 4px; }}
    .deadline-segment--0 {{ background: #d34c4c; }}
    .deadline-segment--1 {{ background: #e49328; }}
    .deadline-segment--2 {{ background: #e8bc3d; }}
    .deadline-segment--3 {{ background: #2d77c8; }}
    .deadline-segment--4 {{ background: #218164; }}
    .deadline-segment--5 {{ background: #92a0b2; }}
    .deadline-legend {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 9px 16px;
    }}
    .deadline-key {{
      display: grid;
      grid-template-columns: 9px auto;
      gap: 9px;
      align-items: center;
    }}
    .deadline-dot {{
      width: 9px;
      height: 30px;
      border-radius: 5px;
    }}
    .deadline-key div {{ display: flex; flex-direction: column; }}
    .deadline-key strong {{ font-size: 15px; }}
    .deadline-key small {{ color: var(--muted); font-size: 10px; }}
    .quality-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }}
    .quality-card {{
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: var(--color-bg-subtle);
    }}
    .quality-top {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      font-size: 12px;
    }}
    .quality-top strong {{ font-size: 18px; }}
    .quality-track {{
      height: 7px;
      margin: 14px 0 8px;
      border-radius: 99px;
      background: var(--av-color-slate-200);
      overflow: hidden;
    }}
    .quality-track span {{
      height: 100%;
      display: block;
      background: var(--green);
    }}
    .quality-card small {{ color: var(--muted); font-size: 10px; }}
    .quality-summary {{
      margin-top: 10px;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }}
    .signal-card {{
      padding: 18px;
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 16px;
      border-radius: var(--av-radius-lg);
      background: var(--navy);
      color: white;
    }}
    .signal-card span {{ color: #b8c8dc; font-size: 12px; }}
    .signal-card strong {{ font-size: 25px; }}
    .quality-note {{
      margin: 12px 0 0;
      padding: 12px 14px;
      border-left: 3px solid var(--amber);
      background: #fff9ee;
      color: #72501b;
      font-size: 12px;
    }}
    .source-layout {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 320px;
      gap: 28px;
    }}
    .source-rank {{
      min-height: 44px;
      display: grid;
      grid-template-columns: 34px minmax(0, 1fr) 64px 64px;
      gap: 10px;
      align-items: center;
      border-bottom: 1px solid var(--line);
      font-size: 12px;
    }}
    .source-rank-number, .source-rank small {{ color: var(--muted); }}
    .source-rank > span:nth-last-of-type(1),
    .source-rank small {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .source-callout {{
      padding: 22px;
      border-radius: var(--av-radius-lg);
      background: var(--soft);
    }}
    .source-callout span {{ color: var(--muted); font-size: 11px; }}
    .source-callout strong {{
      margin: 8px 0;
      display: block;
      font-size: 28px;
      line-height: 1.05;
    }}
    .source-callout p {{ margin: 0; color: var(--muted); font-size: 12px; }}
    .history-summary {{
      margin-bottom: 14px;
      display: flex;
      gap: 8px;
    }}
    .history-summary span {{
      min-width: 112px;
      padding: 12px 14px;
      display: flex;
      align-items: baseline;
      gap: 8px;
      border-radius: var(--av-radius-md);
      background: var(--soft);
      color: var(--muted);
      font-size: 11px;
    }}
    .history-summary strong {{ color: var(--ink); font-size: 20px; }}
    .history-empty {{
      padding: 18px;
      border: 1px dashed #b9c6d6;
      border-radius: var(--av-radius-lg);
      color: var(--muted);
      font-size: 13px;
    }}
    .change-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }}
    .change-card {{
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: var(--color-bg-subtle);
    }}
    .change-card > span {{
      color: var(--green);
      font-size: 10px;
      font-weight: 800;
      letter-spacing: .08em;
      text-transform: uppercase;
    }}
    .change-card h3 {{ margin: 8px 0; font-size: 14px; line-height: 1.3; }}
    .change-card p {{ margin: 0 0 12px; color: var(--muted); font-size: 11px; }}
    .change-card a {{ color: var(--blue); font-size: 11px; font-weight: 800; }}
    .reuse-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 9px;
    }}
    .reuse-link {{
      min-height: 86px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: var(--color-bg-subtle);
      text-decoration: none;
    }}
    .reuse-link span {{ color: var(--muted); font-size: 10px; }}
    .reuse-link strong {{ font-size: 14px; }}
    .method-note {{
      margin-top: 14px;
      padding: 16px;
      border-radius: var(--av-radius-lg);
      background: var(--soft);
      color: var(--muted);
      font-size: 12px;
    }}
    .method-note strong {{ display: block; margin-bottom: 5px; color: var(--ink); }}
    .revision {{
      margin-top: 12px;
      padding: 14px 18px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px 24px;
      border: 1px solid var(--line);
      border-radius: var(--av-radius-lg);
      background: var(--panel);
      color: var(--muted);
      font-size: 11px;
    }}
    .revision strong {{ color: var(--ink); font-family: var(--av-font-mono); }}
    .footer {{
      padding: 24px 4px 0;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 24px;
      color: var(--muted);
      font-size: 11px;
    }}
    .footer p {{ max-width: 720px; margin: 0; }}
    .footer nav {{ display: flex; flex-wrap: wrap; gap: 12px; }}
    .footer a {{ font-weight: 700; }}
    @media (max-width: 900px) {{
      .chart-grid, .deadline-layout, .source-layout {{
        grid-template-columns: 1fr;
      }}
      .hero {{ grid-template-columns: minmax(0, 1fr); }}
      .quality-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .theme-strip {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
      .change-grid, .reuse-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 620px) {{
      .shell {{ width: min(100% - 16px, 1280px); margin-top: 8px; }}
      .topbar {{ min-height: 44px; padding: 0 10px; }}
      .top-actions > a {{ display: none; }}
      .hero {{ padding: 26px 20px; gap: 24px; border-radius: 14px; }}
      h1 {{ font-size: 39px; }}
      .lead {{ font-size: 15px; }}
      .hero-metric {{ min-height: 92px; padding: 14px; }}
      .hero-metric strong {{ font-size: 27px; }}
      .section {{ padding: 20px 16px; }}
      .section-head {{ align-items: flex-start; flex-direction: column; gap: 12px; }}
      .chart-toggle {{ width: 100%; }}
      .chart-toggle button {{ flex: 1; }}
      .theme-strip, .quality-grid, .quality-summary,
      .change-grid, .reuse-grid {{ grid-template-columns: 1fr; }}
      .deadline-legend {{ grid-template-columns: 1fr; }}
      .source-rank {{ grid-template-columns: 28px minmax(0, 1fr) 48px; }}
      .source-rank small {{ display: none; }}
      .footer {{ flex-direction: column; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      html {{ scroll-behavior: auto; }}
    }}
  </style>
</head>
<body>
  <main class="shell" data-avds-component="data-centre" data-avds-version="4.6.0">
    <header class="topbar" data-avds-component="Breadcrumbs">
      <a class="brand" href="{escape(catalog_href, quote=True)}">
        <span class="brand-mark">QF</span>
        <span>QAZ.FUND</span>
      </a>
      <div class="top-actions">
        <a href="{escape(catalog_href, quote=True)}">{escape(copy["home"])}</a>
        <a href="{escape(status_href, quote=True)}">{escape(copy["status"])}</a>
        <div class="lang-switch" aria-label="Language">
          <a
            class="{"active" if active_lang == "ru" else ""}"
            href="{escape(ru_href, quote=True)}"
          >RU</a>
          <a
            class="{"active" if active_lang == "en" else ""}"
            href="{escape(en_href, quote=True)}"
          >EN</a>
        </div>
      </div>
    </header>

    <section class="hero" data-avds-pattern="editorial-lead-rail">
      <div>
        <div class="eyebrow">{escape(copy["eyebrow"])}</div>
        <h1>{escape(copy["title"])}</h1>
        <p class="lead">{escape(copy["lead"])}</p>
        <div class="hero-actions">
          <a
            class="button primary"
            href="{escape(catalog_href, quote=True)}"
            data-avds-component="Button"
          >{escape(copy["catalog"])}</a>
          <a
            class="button"
            href="#reuse"
            data-avds-component="Button"
          >{escape(copy["api"])}</a>
        </div>
      </div>
      <div class="hero-metrics" data-avds-component="PublicSummaryStrip">
        <div class="hero-metric">
          <strong>{_number(scope.get("active"), active_lang)}</strong>
          <span>{escape(copy["active"])}</span>
        </div>
        <div class="hero-metric">
          <strong>{_number(scope.get("sources"), active_lang)}</strong>
          <span>{escape(copy["sources"])}</span>
        </div>
        <div class="hero-metric">
          <strong>{_number(scope.get("closing_within_30_days"), active_lang)}</strong>
          <span>{escape(copy["closing"])}</span>
        </div>
        <div class="hero-metric">
          <strong>{_number(scope.get("kazakhstan_explicit"), active_lang)}</strong>
          <span>{escape(copy["kz"])}</span>
        </div>
      </div>
    </section>

    <section
      class="section"
      id="snapshot"
      data-avds-component="Card"
      data-avds-pattern="catalogue-composition"
    >
      <div class="section-head">
        <div>
          <div class="eyebrow">{escape(copy["snapshot"])}</div>
          <h2>{escape(copy["snapshot_title"])}</h2>
          <p>{escape(copy["snapshot_text"])}</p>
        </div>
        <div class="chart-toggle" role="group" aria-label="Chart values">
          <button
            class="active"
            type="button"
            data-chart-mode="count"
            data-avds-component="Button"
          >{escape(copy["count"])}</button>
          <button
            type="button"
            data-chart-mode="share"
            data-avds-component="Button"
          >{escape(copy["share"])}</button>
        </div>
      </div>
      <div class="chart-grid">
        <div class="chart-panel" data-chart data-avds-component="Card">
          <h3>{escape(copy["formats"])}</h3>
          {_bar_chart(formats, chart_id="formats", max_rows=11)}
        </div>
        <div class="chart-panel" data-chart data-avds-component="Card">
          <h3>{escape(copy["audiences"])}</h3>
          {_bar_chart(audiences, chart_id="audiences", max_rows=8)}
        </div>
      </div>
      <div class="theme-strip" aria-label="{escape(copy["themes"], quote=True)}">
        {theme_cells}
      </div>
    </section>

    <section
      class="section"
      id="deadlines"
      data-avds-component="Card"
      data-avds-pattern="deadline-distribution"
    >
      <div class="section-head">
        <div>
          <div class="eyebrow">{escape(copy["deadlines"])}</div>
          <h2>{escape(copy["deadlines_title"])}</h2>
          <p>{escape(copy["deadlines_text"])}</p>
        </div>
      </div>
      <div class="deadline-layout">
        {_deadline_chart(deadlines, lang=active_lang)}
      </div>
    </section>

    <section
      class="section"
      id="quality"
      data-avds-component="Card"
      data-avds-pattern="data-quality-scorecard"
    >
      <div class="section-head">
        <div>
          <div class="eyebrow">{escape(copy["quality"])}</div>
          <h2>{escape(copy["quality_title"])}</h2>
          <p>{escape(copy["quality_text"])}</p>
        </div>
      </div>
      <div class="quality-grid">{quality_cards_markup}</div>
      <div class="quality-summary">
        <div class="signal-card">
          <span>{escape(copy["complete"])}</span>
          <strong>{complete_share}</strong>
        </div>
        <div class="signal-card">
          <span>{escape(copy["procurement"])}</span>
          <strong>{procurement_share}</strong>
        </div>
      </div>
      <p class="quality-note" data-avds-component="Alert">
        {escape(copy["quality_note"])}
      </p>
    </section>

    <section
      class="section"
      id="sources"
      data-avds-component="Card"
      data-avds-pattern="source-coverage"
    >
      <div class="section-head">
        <div>
          <div class="eyebrow">{escape(copy["sources"])}</div>
          <h2>{escape(copy["sources_title"])}</h2>
          <p>{escape(copy["sources_text"])}</p>
        </div>
      </div>
      <div class="source-layout">
        <div role="table" data-avds-component="Table">{source_rows_markup}</div>
        <aside class="source-callout" data-avds-component="Card">
          <span>{escape(copy["sources"])}</span>
          <strong>{_number(scope.get("sources"), active_lang)}</strong>
          <p>{escape(copy["sources_text"])}</p>
        </aside>
      </div>
    </section>

    <section
      class="section"
      id="changes"
      data-avds-component="Card"
      data-avds-pattern="change-ledger"
    >
      <div class="section-head">
        <div>
          <div class="eyebrow">{escape(copy["changes"])}</div>
          <h2>{escape(copy["changes_title"])}</h2>
          <p>{escape(copy["changes_text"])}</p>
        </div>
      </div>
      {history_markup}
    </section>

    <section
      class="section"
      id="reuse"
      data-avds-component="Card"
      data-avds-pattern="machine-entrypoints"
    >
      <div class="section-head">
        <div>
          <div class="eyebrow">{escape(copy["reuse"])}</div>
          <h2>{escape(copy["reuse_title"])}</h2>
          <p>{escape(copy["reuse_text"])}</p>
        </div>
      </div>
      <div class="reuse-grid">{reuse_links}</div>
      <div class="method-note" data-avds-component="Alert">
        <strong>{escape(copy["method"])}</strong>{escape(copy["method_text"])}
      </div>
    </section>

    <div class="revision">
      <span>
        {escape(copy["indexed"])}
        <strong>{_number(scope.get("indexed_relevant"), active_lang)}</strong>
      </span>
      <span>
        {escape(copy["as_of"])}
        <strong>{escape(str(payload.get("as_of") or ""))}</strong>
      </span>
      <span>
        {escape(copy["revision"])}
        <strong title="{escape(revision, quote=True)}">{escape(revision_short)}</strong>
      </span>
    </div>
    <footer class="footer">
      <p>{escape(copy["footer"])}</p>
      <nav>
        <a href="{escape(catalog_href, quote=True)}">{escape(copy["home"])}</a>
        <a href="{escape(status_href, quote=True)}">{escape(copy["status"])}</a>
        <a href="{escape(docs_href, quote=True)}">API</a>
        <a href="{escape(terms_href, quote=True)}">{escape(copy["terms"])}</a>
        <a href="{escape(data_policy_href, quote=True)}">{escape(copy["data_policy"])}</a>
        <a href="{escape(attribution_href, quote=True)}">{escape(copy["attribution"])}</a>
      </nav>
    </footer>
  </main>
  <script>
    (() => {{
      const buttons = [...document.querySelectorAll("[data-chart-mode]")];
      const values = [...document.querySelectorAll(".bar-value")];
      const setMode = (mode) => {{
        buttons.forEach((button) => button.classList.toggle(
          "active", button.dataset.chartMode === mode
        ));
        values.forEach((value) => {{
          value.textContent = mode === "share"
            ? `${{Number(value.dataset.share || 0).toLocaleString(
                "{'ru-RU' if active_lang == 'ru' else 'en-US'}",
                {{ maximumFractionDigits: 1 }}
              )}}%`
            : Number(value.dataset.count || 0).toLocaleString(
                "{'ru-RU' if active_lang == 'ru' else 'en-US'}"
              );
        }});
      }};
      buttons.forEach((button) => button.addEventListener(
        "click", () => setMode(button.dataset.chartMode || "count")
      ));
    }})();
  </script>
</body>
</html>
"""


__all__ = ["render_insights_page"]
