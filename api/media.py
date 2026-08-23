"""Reproducible media outputs generated from the public QAZ.FUND contract."""

from __future__ import annotations

import csv
import io
import json
import textwrap
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from email.utils import format_datetime
from html import escape
from typing import Literal

from core.public_clock import public_today
from core.public_contract import OpportunityV1

CARD_FORMATS: dict[str, tuple[int, int]] = {
    "og": (1200, 630),
    "square": (1080, 1080),
    "story": (1080, 1920),
    "wide": (1600, 900),
}

CHART_TYPES = {
    "active_by_theme",
    "active_by_audience",
    "status_mix",
    "deadline_timeline",
    "top_sources",
}


def _human_date(value: datetime | None, lang: str) -> str:
    if value is None:
        return {
            "ru": "дата проверки не опубликована",
            "kk": "тексеру күні жарияланбаған",
            "en": "check date unavailable",
        }.get(lang, "check date unavailable")
    current = value.date()
    if lang in {"ru", "kk"}:
        return current.strftime("%d.%m.%Y")
    return current.isoformat()


def _deadline(value: OpportunityV1, lang: str) -> str:
    if value.deadline is not None:
        return (
            value.deadline.strftime("%d.%m.%Y")
            if lang in {"ru", "kk"}
            else value.deadline.isoformat()
        )
    if value.deadline_type == "rolling":
        return {
            "ru": "Без фиксированного срока",
            "kk": "Белгіленген мерзім жоқ",
            "en": "Rolling",
        }.get(lang, "Rolling")
    return {
        "ru": "Срок не опубликован",
        "kk": "Мерзімі жарияланбаған",
        "en": "Deadline not published",
    }.get(lang, "Deadline not published")


def citation_text(
    item: OpportunityV1,
    *,
    style: Literal["plain", "markdown", "citation", "press"] = "citation",
    lang: str = "ru",
) -> str:
    checked = _human_date(item.timestamps.source_checked_at, lang)
    if lang == "ru":
        source_line = f"Источник: {item.source.name}. Проверено: {checked}."
        caution = "Перед подачей сверьте условия на официальной странице."
    elif lang == "kk":
        source_line = f"Дереккөз: {item.source.name}. Тексерілген күні: {checked}."
        caution = "Өтінім берер алдында шарттарды ресми беттен тексеріңіз."
    else:
        source_line = f"Source: {item.source.name}. Checked: {checked}."
        caution = "Check the current terms on the official page before applying."

    if style == "plain":
        return "\n\n".join(
            [item.title, item.summary, source_line, item.links.official_source]
        )
    if style == "markdown":
        return "\n\n".join(
            [
                f"## {item.title}",
                item.summary,
                f"- {source_line}",
                f"- {caution}",
                f"- [{item.source.name}]({item.links.official_source})",
            ]
        )
    if style == "press":
        return " ".join([item.title + ".", item.summary, source_line, caution])
    official_label = {
        "ru": "Официальный источник",
        "kk": "Ресми дереккөз",
        "en": "Official source",
    }.get(lang, "Official source")
    return (
        f"{item.title}. QAZ.FUND, {checked}. {item.links.public_page}. "
        f"{source_line} {official_label}: {item.links.official_source}."
    )


def content_payload(item: OpportunityV1, *, lang: str = "ru") -> dict[str, object]:
    return {
        "schema_version": "qazfund-media-content.v1",
        "id": str(item.id),
        "title": item.title,
        "summary": item.summary,
        "plain_text": citation_text(item, style="plain", lang=lang),
        "markdown": citation_text(item, style="markdown", lang=lang),
        "citation": citation_text(item, style="citation", lang=lang),
        "press_blurb": citation_text(item, style="press", lang=lang),
        "source_url": item.links.official_source,
        "public_url": item.links.public_page,
        "source_checked_at": (
            item.timestamps.source_checked_at.isoformat()
            if item.timestamps.source_checked_at
            else None
        ),
        "content_hash": item.provenance.content_hash,
        "evidence_state": item.provenance.evidence_state,
    }


def _svg_lines(
    text: str,
    *,
    width: int,
    font_size: int,
    max_lines: int,
) -> list[str]:
    approximate_chars = max(18, int(width / (font_size * 0.58)))
    lines = textwrap.wrap(
        " ".join(text.split()),
        width=approximate_chars,
        break_long_words=False,
        break_on_hyphens=False,
    )
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" .,:;") + "…"
    return lines


def render_opportunity_card_svg(
    item: OpportunityV1,
    *,
    card_format: str = "og",
    lang: str = "ru",
) -> str:
    width, height = CARD_FORMATS.get(card_format, CARD_FORMATS["og"])
    margin = max(56, int(width * 0.065))
    content_width = width - (margin * 2)
    title_size = 62 if width <= 1200 else 78
    summary_size = 30 if width <= 1200 else 38
    title_lines = _svg_lines(
        item.title,
        width=content_width,
        font_size=title_size,
        max_lines=4 if height > width else 3,
    )
    summary_lines = _svg_lines(
        item.summary,
        width=content_width,
        font_size=summary_size,
        max_lines=5 if height > width else 3,
    )
    checked = _human_date(item.timestamps.source_checked_at, lang)
    source_label = {
        "ru": f"Источник: {item.source.name} · проверено {checked}",
        "kk": f"Дереккөз: {item.source.name} · тексерілді {checked}",
        "en": f"Source: {item.source.name} · checked {checked}",
    }.get(lang, f"Source: {item.source.name} · checked {checked}")
    disclaimer = {
        "ru": "QAZ.FUND – навигатор, не грантодатель",
        "kk": "QAZ.FUND – грант беруші емес, навигатор",
        "en": "QAZ.FUND – a navigator, not a funder",
    }.get(lang, "QAZ.FUND – a navigator, not a funder")
    deadline = _deadline(item, lang)
    format_label = ", ".join(item.formats[:2]) or "opportunity"

    title_markup = "".join(
        f'<tspan x="{margin}" dy="{title_size * 1.13 if index else 0}">{escape(line)}</tspan>'
        for index, line in enumerate(title_lines)
    )
    title_y = margin + 112
    summary_y = title_y + (len(title_lines) * title_size * 1.13) + 46
    summary_markup = "".join(
        f'<tspan x="{margin}" dy="{summary_size * 1.42 if index else 0}">{escape(line)}</tspan>'
        for index, line in enumerate(summary_lines)
    )
    footer_y = height - margin
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}"
  height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#071426"/>
      <stop offset="1" stop-color="#153a67"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.15" cy="0.08" r="0.9">
      <stop offset="0" stop-color="#20c77a" stop-opacity="0.32"/>
      <stop offset="1" stop-color="#20c77a" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="{width}" height="{height}" fill="url(#bg)"/>
  <rect width="{width}" height="{height}" fill="url(#glow)"/>
  <text x="{margin}" y="{margin}" fill="#8cf0ba"
    font-family="Inter, Arial, sans-serif" font-size="28" font-weight="700"
    letter-spacing="2">QAZ.FUND</text>
  <text x="{width - margin}" y="{margin}" text-anchor="end" fill="#d8e6f5"
    font-family="Inter, Arial, sans-serif" font-size="24">
    {escape(format_label)} · {escape(deadline)}
  </text>
  <text x="{margin}" y="{title_y}" fill="#ffffff"
    font-family="Inter, Arial, sans-serif" font-size="{title_size}"
    font-weight="700">{title_markup}</text>
  <text x="{margin}" y="{summary_y}" fill="#d8e6f5"
    font-family="Inter, Arial, sans-serif"
    font-size="{summary_size}">{summary_markup}</text>
  <line x1="{margin}" x2="{width - margin}" y1="{footer_y - 58}"
    y2="{footer_y - 58}" stroke="#7d9abb" stroke-opacity="0.45"/>
  <text x="{margin}" y="{footer_y - 18}" fill="#d8e6f5"
    font-family="Inter, Arial, sans-serif"
    font-size="21">{escape(source_label)}</text>
  <text x="{width - margin}" y="{footer_y - 18}" text-anchor="end"
    fill="#8cf0ba" font-family="Inter, Arial, sans-serif"
    font-size="21">{escape(disclaimer)}</text>
</svg>"""


def chart_rows(
    items: list[OpportunityV1],
    chart_type: str,
    *,
    today: date | None = None,
    limit: int = 10,
) -> list[dict[str, int | str]]:
    current_day = today or public_today()
    counter: Counter[str] = Counter()
    if chart_type == "active_by_theme":
        counter.update(theme for item in items for theme in item.themes)
    elif chart_type == "active_by_audience":
        counter.update(audience for item in items for audience in item.target_audience)
    elif chart_type == "status_mix":
        counter.update(item.status or "unknown" for item in items)
    elif chart_type == "top_sources":
        counter.update(item.source.name for item in items)
    elif chart_type == "deadline_timeline":
        windows = (("0–30 дней", 0, 30), ("31–60 дней", 31, 60), ("61–90 дней", 61, 90))
        for label, start, end in windows:
            upper = current_day + timedelta(days=end)
            lower = current_day + timedelta(days=start)
            counter[label] = sum(
                1
                for item in items
                if item.deadline is not None and lower <= item.deadline <= upper
            )
        counter["Без фиксированного срока"] = sum(
            1 for item in items if item.deadline_type == "rolling"
        )
    else:
        raise ValueError(f"Unsupported chart type: {chart_type}")
    return [
        {"label": label, "value": int(value)}
        for label, value in counter.most_common(limit)
        if label and value > 0
    ]


def chart_title(chart_type: str, lang: str) -> str:
    ru = {
        "active_by_theme": "Активные возможности по темам",
        "active_by_audience": "Активные возможности по аудиториям",
        "status_mix": "Статусы возможностей",
        "deadline_timeline": "Сроки подачи на 90 дней",
        "top_sources": "Источники по числу активных возможностей",
    }
    en = {
        "active_by_theme": "Active opportunities by theme",
        "active_by_audience": "Active opportunities by audience",
        "status_mix": "Opportunity status mix",
        "deadline_timeline": "Deadlines over the next 90 days",
        "top_sources": "Sources by active opportunity count",
    }
    return (ru if lang == "ru" else en).get(chart_type, chart_type)


def render_chart_svg(
    rows: list[dict[str, int | str]],
    *,
    title: str,
    generated_at: datetime,
) -> str:
    width = 1200
    row_height = 62
    height = max(520, 240 + (len(rows) * row_height))
    left = 330
    right = 90
    max_value = max((int(row["value"]) for row in rows), default=1)
    bars: list[str] = []
    for index, row in enumerate(rows):
        y = 176 + (index * row_height)
        value = int(row["value"])
        bar_width = max(4, int((width - left - right) * value / max_value))
        label = textwrap.shorten(str(row["label"]), width=34, placeholder="…")
        bars.append(
            f'<text x="70" y="{y + 26}" fill="#dbe8f5" '
            'font-family="Inter, Arial, sans-serif" '
            f'font-size="23">{escape(label)}</text>'
            f'<rect x="{left}" y="{y}" width="{bar_width}" '
            'height="38" rx="10" fill="#28c781"/>'
            f'<text x="{left + bar_width + 14}" y="{y + 27}" '
            'fill="#ffffff" font-family="Inter, Arial, sans-serif" '
            f'font-size="23" font-weight="700">{value}</text>'
        )
    stamp = generated_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}"
  height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="#09182a"/>
  <text x="70" y="68" fill="#81e9b3"
    font-family="Inter, Arial, sans-serif" font-size="25" font-weight="700"
    letter-spacing="2">QAZ.FUND</text>
  <text x="70" y="124" fill="#ffffff"
    font-family="Inter, Arial, sans-serif" font-size="42"
    font-weight="700">{escape(title)}</text>
  {''.join(bars)}
  <line x1="70" x2="1130" y1="{height - 78}" y2="{height - 78}"
    stroke="#63809f" stroke-opacity="0.5"/>
  <text x="70" y="{height - 38}" fill="#b9cade"
    font-family="Inter, Arial, sans-serif" font-size="19">
    Данные: публичный набор QAZ.FUND · {stamp}
  </text>
</svg>"""


def chart_csv(rows: list[dict[str, int | str]]) -> str:
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=["label", "value"])
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def rss_feed(
    items: list[OpportunityV1],
    *,
    base_url: str,
    generated_at: datetime,
    lang: str,
) -> str:
    title = (
        "QAZ.FUND – новые возможности"
        if lang == "ru"
        else "QAZ.FUND – new opportunities"
    )
    description = (
        "Новые и обновлённые программы поддержки для Казахстана и Центральной Азии."
        if lang == "ru"
        else "New and updated support opportunities for Kazakhstan and Central Asia."
    )
    entries: list[str] = []
    for item in items[:50]:
        published = item.timestamps.source_checked_at or item.timestamps.discovered_at
        entries.append(
            "<item>"
            f'<guid isPermaLink="false">{item.id}:{item.provenance.content_hash}</guid>'
            f"<title>{escape(item.title)}</title>"
            f"<link>{escape(item.links.public_page)}</link>"
            f"<description>{escape(item.summary)}</description>"
            f"<pubDate>{format_datetime(published)}</pubDate>"
            f'<source url="{escape(item.links.official_source, quote=True)}">'
            f"{escape(item.source.name)}</source>"
            "</item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0"><channel>'
        f"<title>{escape(title)}</title>"
        f"<link>{escape(base_url)}</link>"
        f"<description>{escape(description)}</description>"
        f"<language>{escape(lang)}</language>"
        f"<lastBuildDate>{format_datetime(generated_at)}</lastBuildDate>"
        f"{''.join(entries)}"
        "</channel></rss>"
    )


def json_feed(
    items: list[OpportunityV1],
    *,
    base_url: str,
    lang: str,
) -> dict[str, object]:
    title = (
        "QAZ.FUND – новые возможности"
        if lang == "ru"
        else "QAZ.FUND – new opportunities"
    )
    return {
        "version": "https://jsonfeed.org/version/1.1",
        "title": title,
        "home_page_url": base_url,
        "feed_url": f"{base_url.rstrip('/')}/media/v1/feed.json?lang={lang}",
        "items": [
            {
                "id": f"{item.id}:{item.provenance.content_hash}",
                "url": item.links.public_page,
                "external_url": item.links.official_source,
                "title": item.title,
                "summary": item.summary,
                "date_modified": (
                    item.timestamps.source_checked_at or item.timestamps.discovered_at
                ).isoformat(),
                "tags": item.themes,
                "_qazfund": {
                    "schema_version": item.schema_version,
                    "evidence_state": item.provenance.evidence_state,
                    "content_hash": item.provenance.content_hash,
                },
            }
            for item in items[:50]
        ],
    }


def json_dumps(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
