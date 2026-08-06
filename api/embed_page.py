"""Small, read-only QAZ.FUND surfaces intended for trusted site embeds."""

from __future__ import annotations

from datetime import date
from html import escape
from typing import Any, Iterable
from urllib.parse import urlparse

from qazstack.opportunities import public_lifecycle

from api.avds import AVDS_CSS
from core.localization import localize_opportunity
from core.models import Opportunity

COPY: dict[str, dict[str, str]] = {
    "ru": {
        "opportunities_title": "Актуальные возможности",
        "opportunities_intro": (
            "Открытые карточки QAZ.FUND, которые стоит проверить у организатора."
        ),
        "coverage_title": "Покрытие источников",
        "coverage_intro": "Состояние подключённых источников и свежесть последней проверки.",
        "open": "Открыто",
        "closing": "Срок близко",
        "rolling": "Без фиксированного срока",
        "forecast": "Ожидается",
        "deadline": "До",
        "no_deadline": "Срок не указан",
        "source": "Источник",
        "review": "Проверить условия",
        "catalog": "Открыть каталог",
        "fresh": "Свежий",
        "stale": "Требует внимания",
        "unknown": "Нет отметки",
        "watch": "На контроле",
        "connected": "Подключено",
        "relevant": "актуально",
        "disclaimer": (
            "QAZ.FUND не выдаёт средства и не принимает заявки. "
            "Условия определяет организатор."
        ),
        "empty": "Подходящих открытых карточек пока нет.",
    },
    "kk": {
        "opportunities_title": "Өзекті мүмкіндіктер",
        "opportunities_intro": (
            "QAZ.FUND каталогындағы ұйымдастырушыдан тексеруге болатын ашық карточкалар."
        ),
        "coverage_title": "Дереккөздер қамтуы",
        "coverage_intro": "Қосылған дереккөздердің күйі және соңғы тексерудің жаңалығы.",
        "open": "Ашық",
        "closing": "Мерзімі жақын",
        "rolling": "Нақты мерзімі жоқ",
        "forecast": "Күтілуде",
        "deadline": "Дейін",
        "no_deadline": "Мерзім көрсетілмеген",
        "source": "Дереккөз",
        "review": "Шарттарды тексеру",
        "catalog": "Каталогты ашу",
        "fresh": "Жаңартылған",
        "stale": "Назар аударуды қажет етеді",
        "unknown": "Белгі жоқ",
        "watch": "Бақылауда",
        "connected": "Қосылғаны",
        "relevant": "өзекті",
        "disclaimer": (
            "QAZ.FUND қаражат бөлмейді және өтінім қабылдамайды. "
            "Шарттарды ұйымдастырушы белгілейді."
        ),
        "empty": "Сәйкес ашық карточкалар әзірше жоқ.",
    },
    "en": {
        "opportunities_title": "Current opportunities",
        "opportunities_intro": "Open QAZ.FUND cards worth checking with the organiser.",
        "coverage_title": "Source coverage",
        "coverage_intro": "The state of connected sources and the freshness of the latest check.",
        "open": "Open",
        "closing": "Closing soon",
        "rolling": "No fixed deadline",
        "forecast": "Expected",
        "deadline": "Until",
        "no_deadline": "No deadline shown",
        "source": "Source",
        "review": "Check terms",
        "catalog": "Open catalogue",
        "fresh": "Fresh",
        "stale": "Needs attention",
        "unknown": "Not marked",
        "watch": "Watch",
        "connected": "connected",
        "relevant": "relevant",
        "disclaimer": (
            "QAZ.FUND does not award funds or process applications. "
            "The organiser sets the terms."
        ),
        "empty": "There are no matching open cards yet.",
    },
}


EMBED_CSS = AVDS_CSS + """
    :root {
      --embed-ink: var(--color-text);
      --embed-muted: var(--color-text-muted);
      --embed-line: var(--color-border);
      --embed-panel: var(--color-surface);
      --embed-wash: var(--color-bg);
      --embed-brand: var(--color-accent);
      --embed-brand-soft: var(--color-accent-subtle);
      --embed-good: var(--color-success);
      --embed-good-soft: var(--color-success-subtle);
      --embed-warn: var(--color-warning);
      --embed-warn-soft: var(--color-warning-subtle);
    }
    *, *::before, *::after { box-sizing: border-box; }
    html { background: var(--embed-wash); }
    body {
      margin: 0;
      background: var(--embed-wash);
      color: var(--embed-ink);
      font-family: var(--av-font-sans);
      font-size: var(--av-text-base);
    }
    a { color: var(--embed-brand); }
    .embed-shell {
      max-width: 1120px;
      margin: 0 auto;
      padding: 18px 20px 20px;
    }
    .embed-header {
      align-items: center;
      border-bottom: 1px solid var(--embed-line);
      display: flex;
      gap: 12px;
      justify-content: space-between;
      padding-bottom: 10px;
    }
    .eyebrow, .widget-label {
      color: var(--embed-brand);
      font-size: var(--av-text-xs);
      font-weight: 700;
      letter-spacing: .06em;
      text-transform: uppercase;
    }
    .widget-label { color: var(--embed-muted); }
    h1 {
      font-size: clamp(24px, 3vw, 36px);
      letter-spacing: -.02em;
      line-height: 1.08;
      margin: 18px 0 7px;
    }
    .intro { color: var(--embed-muted); line-height: 1.45; margin: 0; max-width: 760px; }
    .embed-list, .embed-stats { margin-top: 16px; }
    .embed-list {
      background: var(--embed-panel);
      border: 1px solid var(--embed-line);
      border-radius: var(--av-radius-lg);
      overflow: hidden;
    }
    .embed-row {
      align-items: center;
      border-bottom: 1px solid var(--embed-line);
      display: grid;
      gap: 16px;
      grid-template-columns: minmax(0, 1fr) auto;
      padding: 15px 16px;
    }
    .embed-row:last-child { border-bottom: 0; }
    .embed-row:hover { background: var(--embed-brand-soft); }
    .embed-row h2 { font-size: 16px; line-height: 1.22; margin: 0; }
    .embed-row h2 a { color: var(--embed-ink); text-decoration: none; }
    .embed-row h2 a:hover { color: var(--embed-brand); }
    .embed-meta {
      color: var(--embed-muted);
      display: flex;
      flex-wrap: wrap;
      font-size: 12px;
      gap: 6px 14px;
      margin-top: 6px;
    }
    .embed-meta span + span::before { content: "·"; margin-right: 14px; }
    .embed-state {
      align-items: end;
      display: flex;
      flex-direction: column;
      gap: 7px;
      text-align: right;
    }
    .embed-badge {
      background: var(--embed-brand-soft);
      border-radius: var(--av-radius-full);
      color: var(--embed-brand);
      display: inline-flex;
      font-size: 11px;
      font-weight: 700;
      padding: 5px 9px;
      white-space: nowrap;
    }
    .embed-deadline { color: var(--embed-muted); font-size: 12px; white-space: nowrap; }
    .embed-footer {
      border-top: 1px solid var(--embed-line);
      color: var(--embed-muted);
      display: flex;
      flex-wrap: wrap;
      font-size: 12px;
      gap: 8px 18px;
      justify-content: space-between;
      line-height: 1.45;
      margin-top: 16px;
      padding-top: 12px;
    }
    .embed-footer p { margin: 0; max-width: 760px; }
    .embed-footer a { font-weight: 700; white-space: nowrap; }
    .embed-empty { color: var(--embed-muted); padding: 20px 16px; }
    .embed-stats { display: grid; gap: 8px; grid-template-columns: repeat(4, minmax(0, 1fr)); }
    .embed-stat {
      background: var(--embed-panel);
      border: 1px solid var(--embed-line);
      border-radius: var(--av-radius-md);
      padding: 12px 14px;
    }
    .embed-stat span {
      color: var(--embed-muted);
      display: block;
      font-size: 11px;
      line-height: 1.25;
    }
    .embed-stat strong { display: block; font-size: 24px; line-height: 1; margin-top: 7px; }
    .coverage-row { align-items: center; }
    .coverage-name { min-width: 0; }
    .coverage-name strong { display: block; font-size: 14px; }
    .coverage-name span {
      color: var(--embed-muted);
      display: block;
      font-size: 11px;
      margin-top: 4px;
      overflow-wrap: anywhere;
    }
    .coverage-facts {
      align-items: end;
      display: flex;
      flex-direction: column;
      gap: 5px;
      text-align: right;
    }
    .coverage-count { font-size: 12px; font-variant-numeric: tabular-nums; }
    .coverage-state {
      border-radius: var(--av-radius-full);
      display: inline-flex;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 8px;
      white-space: nowrap;
    }
    .coverage-state--fresh { background: var(--embed-good-soft); color: var(--embed-good); }
    .coverage-state--stale { background: var(--embed-warn-soft); color: var(--embed-warn); }
    .coverage-state--unknown, .coverage-state--watch {
      background: var(--embed-brand-soft);
      color: var(--embed-brand);
    }
    :where(a):focus-visible {
      border-radius: var(--av-radius-sm);
      outline: 2px solid var(--embed-brand);
      outline-offset: 3px;
    }
    @media (max-width: 600px) {
      .embed-shell { padding: 14px 12px 16px; }
      .embed-row { align-items: start; grid-template-columns: 1fr; gap: 9px; padding: 13px 12px; }
      .embed-state, .coverage-facts { align-items: start; flex-direction: row; text-align: left; }
      .embed-meta span + span::before { margin-right: 9px; }
      .embed-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .embed-stat strong { font-size: 21px; }
      .embed-footer { display: block; }
      .embed-footer a { display: inline-block; margin-top: 8px; }
    }
"""


def _copy(lang: str) -> dict[str, str]:
    return COPY.get(lang, COPY["ru"])


def _safe_url(value: Any) -> str:
    candidate = str(value or "").strip()
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return candidate


def _date_label(value: Any, lang: str) -> str:
    if not value:
        return "–"
    if isinstance(value, date):
        parsed = value
    else:
        try:
            parsed = date.fromisoformat(str(value)[:10])
        except ValueError:
            return str(value)
    if lang == "en":
        return parsed.strftime("%b %d, %Y")
    if lang == "kk":
        return parsed.strftime("%Y-%m-%d")
    return parsed.strftime("%d.%m.%Y")


def _source_label(value: Any) -> str:
    text = str(value or "").strip()
    return text.replace("_", " ").replace("-", " ").title() or "QAZ.FUND"


def _lifecycle_label(item: Opportunity, copy: dict[str, str]) -> tuple[str, str]:
    lifecycle = str(item.lifecycle or public_lifecycle(item))
    labels = {
        "open": copy["open"],
        "closing_soon": copy["closing"],
        "rolling": copy["rolling"],
        "forecast": copy["forecast"],
    }
    return lifecycle, labels.get(lifecycle, copy["open"])


def _base_document(
    *, lang: str, title: str, intro: str, body: str, catalog_url: str
) -> str:
    return f"""<!doctype html>
<html lang="{escape(lang)}" data-avds="qaz-fund-embed" data-avds-version="4.3.2"
      data-av-theme="light" data-theme="light">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex, nofollow">
    <meta name="description" content="{escape(intro, quote=True)}">
    <title>{escape(title)}</title>
    <style>{EMBED_CSS}</style>
  </head>
  <body>
    <main class="embed-shell" data-avds-component="embed-widget">
      {body}
      <footer class="embed-footer">
        <p>{escape(_copy(lang)['disclaimer'])}</p>
        <a href="{escape(catalog_url, quote=True)}" target="_blank"
           rel="noopener noreferrer">{escape(_copy(lang)['catalog'])} ↗</a>
      </footer>
    </main>
  </body>
</html>"""


def render_opportunities_embed(
    *,
    items: Iterable[Opportunity],
    lang: str = "ru",
    catalog_url: str = "https://qaz.fund/",
) -> str:
    active_lang = lang if lang in COPY else "ru"
    copy = _copy(active_lang)
    today = date.today()
    candidates = [
        localize_opportunity(item, active_lang)
        for item in items
        if item.deadline is None or item.deadline >= today
    ]
    candidates.sort(
        key=lambda item: (
            item.deadline is None,
            item.deadline or date.max,
            -float(item.score or 0),
        )
    )
    rows = []
    for item in candidates[:5]:
        href = _safe_url(item.source_url)
        lifecycle, lifecycle_label = _lifecycle_label(item, copy)
        deadline = (
            f"{copy['deadline']} {_date_label(item.deadline, active_lang)}"
            if item.deadline
            else copy["no_deadline"]
        )
        title = escape(str(item.title or "Untitled"))
        title_html = (
            f'<a href="{escape(href, quote=True)}" target="_blank" '
            f'rel="noopener noreferrer">{title} ↗</a>'
            if href
            else title
        )
        rows.append(f"""<article class="embed-row" data-avds-pattern="ListItem">
              <div><h2>{title_html}</h2>
                <div class="embed-meta"><span>{escape(_source_label(item.source))}</span>
                  <span>{escape(copy["source"])}</span></div>
              </div>
              <div class="embed-state"><span class="embed-badge"
                data-lifecycle="{escape(lifecycle)}">{escape(lifecycle_label)}</span>
                <span class="embed-deadline">{escape(deadline)}</span></div>
            </article>""")
    list_html = "".join(rows) or f'<p class="embed-empty">{escape(copy["empty"])}</p>'
    body = f"""
      <div class="embed-header"><span class="eyebrow">QAZ.FUND</span>
        <span class="widget-label">{escape(copy["review"])}</span></div>
      <h1>{escape(copy["opportunities_title"])}</h1>
      <p class="intro">{escape(copy["opportunities_intro"])}</p>
      <section class="embed-list"
        aria-label="{escape(copy["opportunities_title"], quote=True)}"
        data-avds-pattern="List">{list_html}</section>
    """
    return _base_document(
        lang=active_lang,
        title=f"{copy['opportunities_title']} – QAZ.FUND",
        intro=copy["opportunities_intro"],
        body=body,
        catalog_url=catalog_url,
    )


def _coverage_state_label(state: str, copy: dict[str, str]) -> str:
    return {
        "fresh": copy["fresh"],
        "stale": copy["stale"],
        "unknown": copy["unknown"],
        "watch": copy["watch"],
    }.get(state, copy["unknown"])


def render_coverage_embed(
    *,
    coverage: dict[str, Any],
    lang: str = "ru",
    catalog_url: str = "https://qaz.fund/",
) -> str:
    active_lang = lang if lang in COPY else "ru"
    copy = _copy(active_lang)
    sources = [row for row in coverage.get("sources", []) if row.get("enabled")]
    sources.sort(
        key=lambda row: (
            {"stale": 0, "unknown": 1, "watch": 2, "fresh": 3}.get(
                str(row.get("freshness_status") or "unknown"), 1
            ),
            -int(row.get("relevant_open_items") or 0),
            str(row.get("name") or row.get("slug") or ""),
        )
    )
    rows = []
    for row in sources[:5]:
        state = str(row.get("freshness_status") or "unknown")
        source_url = _safe_url(row.get("base_url"))
        label = escape(str(row.get("name") or _source_label(row.get("slug"))))
        name_html = (
            f'<a href="{escape(source_url, quote=True)}" target="_blank" '
            f'rel="noopener noreferrer">{label} ↗</a>'
            if source_url
            else label
        )
        count = (
            f"{int(row.get('relevant_open_items') or 0)} {copy['relevant']} / "
            f"{int(row.get('items') or 0)}"
        )
        rows.append(
            f"""<article class="embed-row coverage-row" data-avds-pattern="ListItem">
              <div class="coverage-name"><strong>{name_html}</strong>
                <span>{escape(str(row.get("base_url") or ""))}</span>
              </div>
              <div class="coverage-facts"><span class="coverage-count">{escape(count)}</span>
                <span class="coverage-state coverage-state--{escape(state)}">
                  {escape(_coverage_state_label(state, copy))}</span>
              </div>
            </article>"""
        )
    list_html = "".join(rows) or f'<p class="embed-empty">{escape(copy["empty"])}</p>'
    metrics = "".join(
        f'<div class="embed-stat"><span>{escape(label)}</span>'
        f"<strong>{int(coverage.get(key) or 0)}</strong></div>"
        for label, key in (
            (copy["connected"], "enabled_sources"),
            (copy["fresh"], "fresh_sources"),
            (copy["stale"], "stale_sources"),
            (copy["unknown"], "unknown_freshness_sources"),
        )
    )
    body = f"""
      <div class="embed-header"><span class="eyebrow">QAZ.FUND</span>
        <span class="widget-label">{escape(copy["source"])}</span></div>
      <h1>{escape(copy["coverage_title"])}</h1>
      <p class="intro">{escape(copy["coverage_intro"])}</p>
      <div class="embed-stats" data-avds-pattern="StatGroup"
        aria-label="{escape(copy["coverage_title"], quote=True)}">{metrics}</div>
      <section class="embed-list"
        aria-label="{escape(copy["coverage_title"], quote=True)}"
        data-avds-pattern="List">{list_html}</section>
    """
    return _base_document(
        lang=active_lang,
        title=f"{copy['coverage_title']} – QAZ.FUND",
        intro=copy["coverage_intro"],
        body=body,
        catalog_url=catalog_url,
    )
