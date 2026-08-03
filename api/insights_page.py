"""Public data-story page for QAZ.FUND.

The page is deliberately server-rendered: the numbers are taken from the same
public read model as the catalogue, while the small SVG charts remain useful
with JavaScript disabled and are easy for assistive technology to describe.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from html import escape
from typing import Any

from api.avds import AVDS_CSS, AVDS_FONT_HEAD
from api.public_meta import analytics_head_html, og_image_url
from core.models import Opportunity
from qazstack.opportunities import public_lifecycle


COPY: dict[str, dict[str, str]] = {
    "ru": {
        "title": "Аналитика каталога – QAZ.FUND",
        "description": "Открытые программы поддержки для Казахстана: направления, сроки и источники.",
        "back": "Вернуться в каталог",
        "eyebrow": "Обзор каталога",
        "heading": "Где доступна поддержка",
        "intro": "Краткий обзор открытых возможностей из источников каталога.",
        "total": "Открытых программ",
        "sources": "Официальных источников",
        "soon": "Срок в ближайшие 30 дней",
        "rolling": "Программ без фиксированного срока",
        "formats": "Форматы поддержки",
        "formats_note": "Какие форматы чаще всего встречаются в каталоге.",
        "sources_title": "Кто публикует программы",
        "sources_note": "Источники с наибольшим числом открытых карточек.",
        "deadlines": "Распределение по срокам",
        "deadlines_note": "Срок помогает выбрать, что проверить первым.",
        "freshness": "Статус источников",
        "freshness_note": "Показан результат последнего успешного обновления.",
        "high": "Высокое соответствие",
        "good": "Хорошее соответствие",
        "base": "Базовое соответствие",
        "within_30": "До 30 дней",
        "within_90": "31–90 дней",
        "later": "Позже 90 дней",
        "rolling_label": "Бессрочные",
        "no_deadline": "Срок не указан",
        "fresh": "Свежие",
        "watch": "Требуют внимания",
        "stale": "Устаревшие",
        "unknown": "Без отметки",
        "method": "Как читать срез",
        "method_text": "Это не рейтинг доноров и не прогноз финансирования. Графики показывают карточки, которые проходят публичный фильтр QAZ.FUND.",
        "source_link": "Проверить источники",
        "catalog_link": "Открыть каталог",
        "no_data": "Данных для этого среза пока недостаточно.",
        "footer": "QAZ.FUND не выдаёт гранты и не принимает заявки. Условия проверяйте у организатора.",
    },
    "en": {
        "title": "Catalog insights – QAZ.FUND",
        "description": "Open support programs for Kazakhstan: formats, deadlines, and sources.",
        "back": "Back to catalog",
        "eyebrow": "Catalog overview",
        "heading": "Where support is available",
        "intro": "A compact view of open opportunities from the catalog sources.",
        "total": "Open programs",
        "sources": "Official sources",
        "soon": "Deadline within 30 days",
        "rolling": "Programs without a fixed deadline",
        "formats": "Support formats",
        "formats_note": "The formats most common in the catalog.",
        "sources_title": "Who publishes the programs",
        "sources_note": "Sources with the largest number of open cards.",
        "deadlines": "Deadline distribution",
        "deadlines_note": "Deadlines show what to check first.",
        "freshness": "Source status",
        "freshness_note": "Shows the latest successful update.",
        "high": "High match",
        "good": "Good match",
        "base": "Base match",
        "within_30": "Within 30 days",
        "within_90": "31–90 days",
        "later": "More than 90 days",
        "rolling_label": "Rolling",
        "no_deadline": "No deadline shown",
        "fresh": "Fresh",
        "watch": "Needs attention",
        "stale": "Stale",
        "unknown": "Not marked",
        "method": "How to read this view",
        "method_text": "This is not a donor ranking or funding forecast. The charts show cards that pass the QAZ.FUND public filter.",
        "source_link": "Check sources",
        "catalog_link": "Open catalog",
        "no_data": "There is not enough data for this view yet.",
        "footer": "QAZ.FUND does not award grants or accept applications. Check terms with the organizer.",
    },
}


def _copy(lang: str) -> dict[str, str]:
    return COPY.get(lang, COPY["ru"])


def _label(raw: str, lang: str) -> str:
    labels = {
        "grant": ("Гранты", "Grants"),
        "contest": ("Конкурсы", "Contests"),
        "accelerator": ("Акселераторы", "Accelerators"),
        "cloud_credit": ("Облачные кредиты", "Cloud credits"),
        "tender": ("Тендеры", "Tenders"),
        "fellowship": ("Стипендии", "Fellowships"),
    }
    return labels.get(raw, (raw.replace("_", " ").title(), raw.replace("_", " ").title()))[lang == "en"]


def _open_items(items: list[Opportunity]) -> list[Opportunity]:
    today = date.today()
    return [
        item
        for item in items
        if public_lifecycle(item) not in {"closed", "awarded"}
        and (item.deadline is None or item.deadline >= today)
    ]


def _count_rows(counter: Counter[str], labels: dict[str, str], limit: int = 6) -> list[tuple[str, int]]:
    rows = [(labels.get(key, key), int(value)) for key, value in counter.most_common(limit)]
    return rows or [("–", 0)]


def _bar_chart(rows: list[tuple[str, int]], *, chart_id: str, color: str, empty_label: str) -> str:
    max_value = max((value for _, value in rows), default=0)
    width = 620
    bar_height = 24
    gap = 10
    height = max(120, len(rows) * (bar_height + gap) + 24)
    chunks: list[str] = []
    for index, (label, value) in enumerate(rows):
        y = 12 + index * (bar_height + gap)
        ratio = value / max_value if max_value else 0
        bar_width = max(0, round(390 * ratio))
        chunks.append(
            f'<g class="chart-row"><text x="0" y="{y + 16}" class="chart-label">{escape(label)}</text>'
            f'<rect x="188" y="{y}" width="390" height="{bar_height}" rx="8" class="chart-track" />'
            f'<rect x="188" y="{y}" width="{bar_width}" height="{bar_height}" rx="8" fill="{color}" />'
            f'<text x="596" y="{y + 16}" text-anchor="end" class="chart-value">{value}</text></g>'
        )
    return (
        f'<svg class="data-chart" data-avds-component="DataViz" data-avds-pattern="{escape(chart_id)}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(empty_label)}">'
        + "".join(chunks)
        + "</svg>"
    )


def _metric(label: str, value: int, tone: str = "") -> str:
    return f'<div class="insight-metric {tone}"><span>{escape(label)}</span><strong>{value:,}</strong></div>'.replace(",", " ")


def render_insights_page(
    *,
    items: list[Opportunity],
    coverage: dict[str, Any],
    lang: str,
    root_path: str,
    site_origin: str,
) -> str:
    copy = _copy(lang)
    base = root_path.rstrip("/")
    home = f"{base}/?lang={lang}#opportunities" if base else f"/?lang={lang}#opportunities"
    status = f"{base}/status?lang={lang}" if base else f"/status?lang={lang}"
    sources = f"{base}/?lang={lang}#sources" if base else f"/?lang={lang}#sources"
    en_href = f"{base}/insights?lang=en" if base else "/insights?lang=en"
    ru_href = f"{base}/insights?lang=ru" if base else "/insights?lang=ru"
    open_items = _open_items(items)
    today = date.today()
    soon = sum(1 for item in open_items if item.deadline and today <= item.deadline <= today + timedelta(days=30))
    rolling = sum(1 for item in open_items if item.deadline is None)
    type_rows = _count_rows(Counter(item.type.value for item in open_items), {}, 6)
    type_rows = [(_label(label, lang), value) for label, value in type_rows]
    source_rows = _count_rows(Counter(item.funder or item.source for item in open_items), {}, 6)
    deadline_rows = [
        (copy["within_30"], soon),
        (copy["within_90"], sum(1 for item in open_items if item.deadline and today + timedelta(days=30) < item.deadline <= today + timedelta(days=90))),
        (copy["later"], sum(1 for item in open_items if item.deadline and item.deadline > today + timedelta(days=90))),
        (copy["rolling_label"], rolling),
        (copy["no_deadline"], max(0, len(open_items) - soon - rolling - sum(1 for item in open_items if item.deadline and item.deadline > today + timedelta(days=90)) - sum(1 for item in open_items if item.deadline and today + timedelta(days=30) < item.deadline <= today + timedelta(days=90)))),
    ]
    freshness = Counter(str(row.get("freshness_status") or "unknown") for row in coverage.get("sources", []) if isinstance(row, dict))
    freshness_rows = [
        (copy["fresh"], freshness.get("fresh", 0)),
        (copy["watch"], freshness.get("watch", 0)),
        (copy["stale"], freshness.get("stale", 0)),
        (copy["unknown"], freshness.get("unknown", 0)),
    ]
    score_rows = [
        (copy["high"], sum(1 for item in open_items if item.score >= 0.7)),
        (copy["good"], sum(1 for item in open_items if 0.5 <= item.score < 0.7)),
        (copy["base"], sum(1 for item in open_items if item.score < 0.5)),
    ]
    html_lang = escape(lang, quote=True)
    canonical = f"{site_origin.rstrip('/')}{base}/insights?lang={lang}" if site_origin else f"{base}/insights?lang={lang}"
    return f'''<!doctype html>
<html lang="{html_lang}" data-avds="grant-radar" data-av-theme="light" data-theme="light">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(copy["title"])}</title>
  <meta name="description" content="{escape(copy["description"], quote=True)}">
  <link rel="canonical" href="{escape(canonical, quote=True)}">
  <link rel="alternate" hreflang="ru" href="{escape((site_origin.rstrip('/') if site_origin else '') + ru_href, quote=True)}">
  <link rel="alternate" hreflang="en" href="{escape((site_origin.rstrip('/') if site_origin else '') + en_href, quote=True)}">
  <meta property="og:title" content="{escape(copy["title"], quote=True)}"><meta property="og:description" content="{escape(copy["description"], quote=True)}">
  <meta property="og:image" content="{escape(og_image_url(site_origin, root_path), quote=True)}">
  {analytics_head_html()}{AVDS_FONT_HEAD}
  <style>
    {AVDS_CSS}
    *{{box-sizing:border-box}} body{{margin:0;background:var(--color-bg);color:var(--color-text);font-family:var(--av-font-sans);line-height:1.5}}
    a{{color:inherit}} .shell{{width:min(var(--av-container-dashboard),calc(100% - 48px));margin:0 auto;padding:20px 0 44px}}
    .topbar{{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:18px}}
    .back{{color:var(--color-text-muted);font-size:14px;font-weight:700;text-decoration:none}} .back:hover{{color:var(--color-accent)}}
    .langs{{display:flex;gap:6px}} .langs a{{padding:5px 9px;font-size:12px;font-weight:700;text-decoration:none;color:var(--color-text-muted);border-bottom:2px solid transparent}} .langs a.active{{color:var(--color-text);border-color:var(--color-accent)}}
    .hero{{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(260px,.8fr);gap:28px;padding:28px;border:1px solid var(--color-border);border-radius:var(--av-radius-lg);background:linear-gradient(135deg,var(--color-surface),var(--color-accent-subtle));box-shadow:var(--shadow-md)}}
    .eyebrow{{color:var(--color-accent);font-size:12px;font-weight:800;letter-spacing:.06em;text-transform:uppercase}} h1{{font-size:clamp(30px,5vw,48px);line-height:1.05;margin:8px 0 12px;max-width:16ch}} .hero p{{max-width:60ch;color:var(--color-text-muted);margin:0;font-size:16px}}
    .hero-actions{{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}} .button{{display:inline-flex;align-items:center;min-height:38px;padding:0 14px;border-radius:var(--av-radius-md);border:1px solid var(--color-border);font-size:14px;font-weight:750;text-decoration:none;background:var(--color-surface)}} .button:hover{{border-color:var(--color-border-strong);background:var(--color-surface-raised)}} .button.primary{{background:var(--color-accent);border-color:var(--color-accent);color:#fff}} .button.primary:hover{{border-color:var(--color-accent-hover);background:var(--color-accent-hover)}}
    .metric-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;align-content:start}} .insight-metric{{display:grid;gap:5px;padding:14px;border:1px solid var(--color-border);border-radius:var(--av-radius-md);background:rgb(255 255 255 / .75)}} .insight-metric span{{color:var(--color-text-muted);font-size:12px;font-weight:700}} .insight-metric strong{{font-size:28px;line-height:1}}
    .insight-metric.good strong{{color:var(--color-success)}} .insight-metric.warn strong{{color:var(--color-warning)}}
    .section-head{{display:grid;gap:5px;margin:30px 0 12px}} .section-head h2{{margin:0;font-size:24px;line-height:1.15}} .section-head p{{margin:0;color:var(--color-text-muted);font-size:14px}}
    .viz-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}} .viz-card{{padding:18px;border:1px solid var(--color-border);border-radius:var(--av-radius-lg);background:var(--color-surface);box-shadow:var(--shadow-xs)}} .viz-card h3{{margin:0;font-size:17px}} .viz-card p{{margin:4px 0 14px;color:var(--color-text-muted);font-size:13px}}
    .data-chart{{display:block;width:100%;height:auto;min-height:130px;overflow:visible}} .chart-label{{font:600 12px var(--av-font-sans);fill:var(--color-text)}} .chart-value{{font:800 13px var(--av-font-sans);fill:var(--color-text)}} .chart-track{{fill:var(--color-bg-subtle)}}
    .method{{display:grid;grid-template-columns:auto 1fr;gap:14px;align-items:start;margin-top:22px;padding:16px 18px;border-left:4px solid var(--color-accent);border-radius:var(--av-radius-md);background:var(--color-surface)}} .method strong{{font-size:15px}} .method p{{margin:3px 0 0;color:var(--color-text-muted);font-size:14px}}
    .footer{{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-top:28px;padding-top:18px;border-top:1px solid var(--color-border);color:var(--color-text-muted);font-size:13px}} .footer a{{font-weight:700}}
    @media(min-width:1440px){{
      .hero{{grid-template-columns:minmax(0,1.55fr) minmax(420px,.8fr);gap:48px;padding:36px}}
      .section-head{{margin-top:40px}}
    }}
    @media(min-width:1920px){{
      .metric-grid{{grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}}
      .viz-grid{{grid-template-columns:repeat(4,minmax(0,1fr));gap:18px}}
      .viz-card{{padding:20px}}
    }}
    @media(max-width:760px){{.shell{{width:min(100% - 24px,680px);padding-top:12px}} .hero{{grid-template-columns:1fr;padding:20px}} .metric-grid{{grid-template-columns:repeat(4,minmax(0,1fr))}} .insight-metric{{padding:10px}} .insight-metric strong{{font-size:22px}} .viz-grid{{grid-template-columns:1fr}} .method{{grid-template-columns:1fr;gap:5px}}}}
    @media(max-width:480px){{.metric-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}} h1{{font-size:34px}}}}
  </style>
</head>
<body><main class="shell">
  <div class="topbar"><a class="back" href="{escape(home, quote=True)}">← {escape(copy["back"])}</a><nav class="langs" aria-label="Language"><a class="{'active' if lang == 'ru' else ''}" href="{escape(ru_href, quote=True)}">RU</a><a class="{'active' if lang == 'en' else ''}" href="{escape(en_href, quote=True)}">EN</a></nav></div>
  <section class="hero" data-avds-component="hero-band"><div><span class="eyebrow">{escape(copy["eyebrow"])}</span><h1>{escape(copy["heading"])}</h1><p>{escape(copy["intro"])}</p><div class="hero-actions"><a class="button primary" href="{escape(home, quote=True)}">{escape(copy["catalog_link"])}</a><a class="button" href="{escape(status, quote=True)}">{escape(copy["source_link"])}</a></div></div><div class="metric-grid" aria-label="Key catalog metrics">{_metric(copy["total"],len(open_items),"good")}{_metric(copy["sources"],int(coverage.get("enabled_sources") or 0))}{_metric(copy["soon"],soon,"warn")}{_metric(copy["rolling"],rolling)}</div></section>
  <div class="section-head"><h2>{escape(copy["formats"])}</h2><p>{escape(copy["formats_note"])}</p></div>
  <div class="viz-grid"><article class="viz-card"><h3>{escape(copy["formats"])}</h3><p>{escape(copy["formats_note"])}</p>{_bar_chart(type_rows,chart_id="format-distribution",color="#315fdc",empty_label=copy["no_data"])}</article><article class="viz-card"><h3>{escape(copy["sources_title"])}</h3><p>{escape(copy["sources_note"])}</p>{_bar_chart(source_rows,chart_id="source-distribution",color="#15724e",empty_label=copy["no_data"])}</article><article class="viz-card"><h3>{escape(copy["deadlines"])}</h3><p>{escape(copy["deadlines_note"])}</p>{_bar_chart(deadline_rows,chart_id="deadline-distribution",color="#9a6414",empty_label=copy["no_data"])}</article><article class="viz-card"><h3>{escape(copy["freshness"])}</h3><p>{escape(copy["freshness_note"])}</p>{_bar_chart(freshness_rows,chart_id="source-freshness",color="#7c3aed",empty_label=copy["no_data"])}</article></div>
  <section class="viz-card" style="margin-top:14px"><h3>{escape(copy["good"])}</h3><p>{escape(copy["formats_note"])}</p>{_bar_chart(score_rows,chart_id="match-quality",color="#315fdc",empty_label=copy["no_data"])}</section>
  <aside class="method" data-avds-component="method-card"><strong>{escape(copy["method"])}</strong><p>{escape(copy["method_text"])}</p></aside>
  <footer class="footer"><span>{escape(copy["footer"])}</span><span><a href="{escape(home, quote=True)}">{escape(copy["catalog_link"])}</a> · <a href="{escape(sources, quote=True)}">{escape(copy["source_link"])}</a></span></footer>
</main></body></html>'''
