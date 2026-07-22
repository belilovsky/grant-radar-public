"""Public source-status page for QAZ.FUND."""

from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any
from urllib.parse import urlparse

from api.avds import AVDS_CSS, AVDS_FONT_HEAD
from api.dashboard_copy import dashboard_copy

COPY = {
    "ru": {
        "title": "Статус источников – QAZ.FUND",
        "eyebrow": "Прозрачность данных",
        "heading": "Статус источников",
        "intro": (
            "Показываем покрытие и свежесть подключённых источников. "
            "Карточки всегда нужно сверять с официальной страницей программы."
        ),
        "back": "Вернуться в каталог",
        "sources": "Подключено",
        "fresh": "Свежие",
        "stale": "Требуют внимания",
        "unknown": "Без отметки",
        "source": "Источник",
        "coverage": "Записей / актуально",
        "updated": "Последняя проверка",
        "state": "Состояние",
        "fresh_label": "Свежий",
        "stale_label": "Требует внимания",
        "unknown_label": "Нет данных",
        "empty": "Подключённые источники пока не найдены.",
        "disclaimer": (
            "Статус отражает время последней успешной проверки или обнаруженной "
            "записи, а не юридическую актуальность каждой программы."
        ),
        "summary_aria": "Сводка состояния источников",
    },
    "en": {
        "title": "Source status – QAZ.FUND",
        "eyebrow": "Data transparency",
        "heading": "Source status",
        "intro": (
            "Coverage and freshness of connected sources. Always verify each "
            "opportunity against the official program page."
        ),
        "back": "Back to catalog",
        "sources": "Connected",
        "fresh": "Fresh",
        "stale": "Needs attention",
        "unknown": "Unknown",
        "source": "Source",
        "coverage": "Records / current",
        "updated": "Latest check",
        "state": "State",
        "fresh_label": "Fresh",
        "stale_label": "Needs attention",
        "unknown_label": "No data",
        "empty": "No connected sources are available yet.",
        "disclaimer": (
            "Freshness reflects the latest successful check or discovered record, "
            "not the legal validity of every program."
        ),
        "summary_aria": "Source status summary",
    },
}


def _date_label(value: Any, lang: str) -> str:
    if not value:
        return "–"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return str(value)
    if lang == "en":
        return parsed.strftime("%b %d, %Y %H:%M UTC")
    return parsed.strftime("%d.%m.%Y %H:%M UTC")


def _host(value: Any) -> str:
    return (urlparse(str(value or "")).hostname or "").removeprefix("www.")


def render_status_page(
    *,
    coverage: dict[str, Any],
    lang: str,
    root_path: str = "",
    site_origin: str = "",
) -> str:
    active_lang = lang if lang in COPY else "ru"
    copy = COPY[active_lang]
    base = root_path.rstrip("/")
    catalog_href = f"{base}/?lang={active_lang}" if base else f"/?lang={active_lang}"
    sources_href = f"{catalog_href}#sources"
    docs_href = (
        f"{base}/docs?lang={active_lang}" if base else f"/docs?lang={active_lang}"
    )
    product_copy = dashboard_copy(active_lang)
    ru_href = f"{base}/status?lang=ru" if base else "/status?lang=ru"
    en_href = f"{base}/status?lang=en" if base else "/status?lang=en"
    status_path = (
        f"{base}/status?lang={active_lang}" if base else f"/status?lang={active_lang}"
    )
    canonical = (
        f"{site_origin.rstrip('/')}{status_path}" if site_origin else status_path
    )
    ru_current = ' aria-current="page"' if active_lang == "ru" else ""
    en_current = ' aria-current="page"' if active_lang == "en" else ""
    sources = [row for row in coverage.get("sources", []) if row.get("enabled")]
    sources.sort(
        key=lambda row: (
            {"stale": 0, "unknown": 1, "fresh": 2}.get(
                str(row.get("freshness_status")), 1
            ),
            -int(row.get("relevant_open_items") or 0),
            str(row.get("name") or row.get("slug") or ""),
        )
    )
    state_labels = {
        "fresh": copy["fresh_label"],
        "stale": copy["stale_label"],
        "unknown": copy["unknown_label"],
    }
    rendered_rows = []
    for row in sources:
        last_checked = _date_label(
            row.get("last_checked_at") or row.get("last_discovered_at"), active_lang
        )
        freshness = str(row.get("freshness_status") or "unknown")
        mobile_updated = f'{copy["updated"]}: {last_checked}'
        rendered_rows.append(f"""
            <tr>
              <td>
                <strong>{escape(str(row.get("name") or row.get("slug") or ""))}</strong>
                <span>{escape(_host(row.get("base_url")))}</span>
                <span class="mobile-updated">{escape(mobile_updated)}</span>
              </td>
              <td>{int(row.get("items") or 0)} / {int(row.get("relevant_open_items") or 0)}</td>
              <td>{escape(last_checked)}</td>
              <td><span class="state state--{escape(freshness)}">
                {escape(str(state_labels.get(freshness, copy["unknown_label"])))}</span></td>
            </tr>
            """)
    rows = "".join(rendered_rows)
    if not rows:
        rows = (
            f'<tr><td colspan="4" class="empty">{escape(str(copy["empty"]))}</td></tr>'
        )

    return f"""<!doctype html>
<html lang="{active_lang}" data-avds="grant-radar" data-av-theme="light" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(str(copy["title"]))}</title>
  <meta name="description" content="{escape(str(copy["intro"]), quote=True)}">
  <link rel="canonical" href="{escape(canonical, quote=True)}">
  {AVDS_FONT_HEAD}
  <style>
    {AVDS_CSS}
    :root {{
      color-scheme: light;
      --ink: var(--color-text);
      --muted: var(--color-text-muted);
      --line: var(--color-border);
      --line-subtle: var(--color-border-subtle);
      --panel: var(--color-surface);
      --panel-subtle: var(--color-bg-subtle);
      --wash: var(--color-bg);
      --brand: var(--color-accent);
      --brand-soft: var(--color-accent-subtle);
      --good: var(--color-success);
      --good-soft: var(--color-success-subtle);
      --warn: var(--color-warning);
      --warn-soft: var(--color-warning-subtle);
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--wash); color:var(--ink);
      font-family:var(--av-font-sans); font-size:var(--av-text-base); }}
    a {{ color:var(--brand); }}
    main {{ width:min(var(--av-container-dashboard),calc(100% - 48px)); margin:0 auto;
      padding:20px 0 40px; }}
    .back {{ display:inline-flex; min-height:32px; align-items:center; margin-bottom:10px;
      font-weight:700; text-decoration:none; }}
    .status-topbar {{ display:flex; align-items:center; justify-content:space-between;
      gap:12px; margin-bottom:10px; }}
    .status-topbar .back {{ margin-bottom:0; }}
    .lang-switch {{ display:inline-flex; align-items:center; gap:4px; }}
    .lang-switch a {{ min-width:34px; padding:6px 8px; border-bottom:2px solid transparent;
      color:var(--muted); text-align:center; text-decoration:none; font-size:12px;
      font-weight:700; }}
    .lang-switch a[aria-current="page"] {{ border-bottom-color:var(--brand); color:var(--ink); }}
    .overview {{ display:grid; grid-template-columns:minmax(0,1.25fr) minmax(420px,.75fr);
      gap:0; margin-bottom:16px; border:0; border-top:1px solid var(--line);
      border-bottom:1px solid var(--line); border-radius:0;
      background:transparent; box-shadow:none; }}
    .hero {{ padding:24px 0; }}
    .eyebrow {{ color:var(--brand); font-size:var(--av-text-xs); font-weight:700; }}
    h1 {{ margin:5px 0; font-size:36px; line-height:1.08; letter-spacing:0; }}
    .hero p {{ max-width:720px; margin:0; color:var(--muted); line-height:1.5; }}
    .metrics {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr));
      align-content:stretch; margin:16px 0 16px 32px; border-left:1px solid var(--line); }}
    .metric {{ display:grid; align-content:center; padding:10px 14px;
      border-bottom:1px solid var(--line-subtle); background:transparent; }}
    .metric span {{ display:block; color:var(--muted); font-size:12px; }}
    .metric strong {{ display:block; margin-top:3px; font-size:22px; line-height:1; }}
    .table-wrap {{ overflow-x:auto; border:0; border-top:1px solid var(--line);
      border-bottom:1px solid var(--line); border-radius:0; background:transparent; }}
    table {{ width:100%; border-collapse:collapse; }}
    th,td {{ padding:10px 14px; border-bottom:1px solid var(--line-subtle); text-align:left;
      vertical-align:middle; }}
    th {{ position:sticky; top:0; z-index:1; color:var(--muted); background:var(--wash);
      font-size:12px; font-weight:700; }}
    td {{ font-size:14px; }}
    tbody tr:hover {{ background:color-mix(in oklab,var(--panel),var(--brand-soft) 10%); }}
    td strong,td span {{ display:block; }}
    td > span:not(.state) {{ margin-top:3px; color:var(--muted); font-size:12px; }}
    .mobile-updated {{ display:none; }}
    tr:last-child td {{ border-bottom:0; }}
    .state {{ display:inline-flex; width:max-content; min-height:24px; align-items:center;
      padding:2px 8px;
      border-radius:999px; background:var(--panel-subtle); font-size:12px; font-weight:700; }}
    .state--fresh {{ background:var(--good-soft); color:var(--good); }}
    .state--stale {{ background:var(--warn-soft); color:var(--warn); }}
    .note {{ margin:14px 2px 0; color:var(--muted); font-size:13px; line-height:1.5; }}
    .site-footer {{ display:grid; gap:8px; margin-top:24px; padding-top:20px;
      border-top:1px solid var(--line); color:var(--muted); font-size:14px; line-height:1.5; }}
    .site-footer-nav {{ display:flex; flex-wrap:wrap; gap:6px 16px;
      align-items:center; font-weight:650; }}
    .site-footer a {{ color:var(--ink); font-weight:700; text-decoration:none; }}
    a:focus-visible {{ outline:2px solid var(--brand); outline-offset:2px;
      border-radius:var(--av-radius-sm); }}
    .empty {{ color:var(--muted); text-align:center; }}
    @media (max-width:860px) {{
      .overview {{ grid-template-columns:1fr; }}
      .metrics {{ margin:0; padding:12px 0; border-top:1px solid var(--line); border-left:0; }}
    }}
    @media (max-width:720px) {{
      .lang-switch a {{
        display:inline-flex;
        align-items:center;
        justify-content:center;
        min-width:var(--av-control-height-lg);
        min-height:var(--av-control-height-lg);
      }}
      .status-topbar .back {{ min-height:var(--av-control-height-lg); }}
      main {{ width:min(100% - 20px,var(--av-container-dashboard)); padding-top:10px; }}
      .hero {{ padding:18px 0; }}
      .metrics {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
      thead {{ display:none; }}
      tbody, tr, td {{ display:block; }}
      tr {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:7px 12px;
        padding:14px 2px; border-bottom:1px solid var(--line-subtle); }}
      tr:last-child {{ border-bottom:0; }}
      td {{ padding:0; border:0; }}
      td:first-child {{ grid-column:1 / -1; }}
      td:nth-child(3) {{ display:none; }}
      .mobile-updated {{ display:block; }}
      td:nth-child(2) {{ align-self:center; font-variant-numeric:tabular-nums; }}
      td:nth-child(4) {{ justify-self:end; }}
      h1 {{ font-size:28px; }}
    }}
  </style>
</head>
<body>
  <main>
    <div class="status-topbar">
      <a class="back" href="{escape(catalog_href, quote=True)}">← {escape(str(copy["back"]))}</a>
      <nav class="lang-switch" aria-label="Language">
        <a href="{escape(ru_href, quote=True)}" lang="ru"{ru_current}>RU</a>
        <a href="{escape(en_href, quote=True)}" lang="en"{en_current}>EN</a>
      </nav>
    </div>
    <section class="overview">
      <div class="hero">
        <span class="eyebrow">{escape(str(copy["eyebrow"]))}</span>
        <h1>{escape(str(copy["heading"]))}</h1>
        <p>{escape(str(copy["intro"]))}</p>
      </div>
      <div class="metrics" aria-label="{escape(str(copy["summary_aria"]), quote=True)}">
        <div class="metric"><span>{escape(str(copy["sources"]))}</span>
          <strong>{int(coverage.get("enabled_sources") or 0)}</strong></div>
        <div class="metric"><span>{escape(str(copy["fresh"]))}</span>
          <strong>{int(coverage.get("fresh_sources") or 0)}</strong></div>
        <div class="metric"><span>{escape(str(copy["stale"]))}</span>
          <strong>{int(coverage.get("stale_sources") or 0)}</strong></div>
        <div class="metric"><span>{escape(str(copy["unknown"]))}</span>
          <strong>{int(coverage.get("unknown_freshness_sources") or 0)}</strong></div>
      </div>
    </section>
    <div class="table-wrap">
      <table>
        <thead><tr><th>{escape(str(copy["source"]))}</th>
          <th>{escape(str(copy["coverage"]))}</th>
          <th>{escape(str(copy["updated"]))}</th>
          <th>{escape(str(copy["state"]))}</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    <p class="note">{escape(str(copy["disclaimer"]))}</p>
    <footer class="site-footer">
      <nav class="site-footer-nav"
        aria-label="{escape(str(product_copy["views_aria"]), quote=True)}">
        <a href="{escape(catalog_href, quote=True)}"
          >{escape(str(product_copy["tab_opportunities"]))}</a>
        <a href="{escape(sources_href, quote=True)}"
          >{escape(str(product_copy["tab_sources"]))}</a>
        <a href="{escape(docs_href, quote=True)}">{escape(str(product_copy["api_docs"]))}</a>
      </nav>
    </footer>
  </main>
</body>
</html>"""
