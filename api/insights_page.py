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

from qazstack.opportunities import public_lifecycle

from api.avds import AVDS_CSS, AVDS_FONT_HEAD
from api.dashboard_copy import dashboard_copy
from api.public_meta import analytics_head_html, og_image_url
from core.models import Opportunity

COPY: dict[str, dict[str, str]] = {
    "ru": {
        "title": "Срез возможностей – QAZ.FUND",
        "description": "Открытый срез программ поддержки: форматы, сроки и источники из текущего каталога.",
        "back": "Вернуться в каталог",
        "eyebrow": "Срез каталога",
        "heading": "Где искать поддержку",
        "intro": "Публичный срез возможностей, сроков и источников из текущего каталога.",
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
        "quality": "Качество совпадения",
        "quality_note": "Распределение карточек по рабочему сигналу релевантности.",
        "readiness": "Готовность карточек",
        "readiness_note": "Какие ключевые поля уже опубликованы в карточках.",
        "complete": "Ключевые поля на месте",
        "partial": "Нужно уточнить",
        "high": "Сильные сигналы",
        "good": "Умеренные сигналы",
        "base": "Базовые сигналы",
        "within_30": "До 30 дней",
        "within_90": "31–90 дней",
        "later": "Позже 90 дней",
        "rolling_label": "Бессрочные",
        "no_deadline": "Срок не указан",
        "upcoming": "Ближайшие сроки",
        "upcoming_note": "Карточки, которые стоит проверить в первую очередь.",
        "today": "сегодня",
        "day_many": "дн.",
        "fresh": "Свежие",
        "watch": "Требуют внимания",
        "stale": "Устаревшие",
        "unknown": "Без отметки",
        "method": "Как читать этот срез",
        "method_text": "Это не рейтинг доноров и не прогноз финансирования. Графики показывают распределение карточек по рабочим сигналам QAZ.FUND; условия проверяйте у организатора.",
        "source_link": "Проверить источники",
        "catalog_link": "Найти поддержку",
        "no_data": "Данных для этого среза пока недостаточно.",
        "footer": "QAZ.FUND не выдаёт средства и не принимает заявки. Перед действием проверьте условия на странице организатора.",
    },
    "en": {
        "title": "Support opportunity snapshot – QAZ.FUND",
        "description": "A public snapshot of support programs, formats, deadlines, and sources in the current catalog.",
        "back": "Back to catalog",
        "eyebrow": "Catalog snapshot",
        "heading": "Where to look for support",
        "intro": "A public view of opportunities, deadlines, and sources in the current catalog.",
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
        "quality": "Match quality",
        "quality_note": "Cards grouped by the working relevance signal.",
        "readiness": "Card readiness",
        "readiness_note": "Which key fields are already published in the cards.",
        "complete": "Key fields present",
        "partial": "Needs checking",
        "high": "Strong signals",
        "good": "Moderate signals",
        "base": "Baseline signals",
        "within_30": "Within 30 days",
        "within_90": "31–90 days",
        "later": "More than 90 days",
        "rolling_label": "Rolling",
        "no_deadline": "No deadline shown",
        "upcoming": "Upcoming deadlines",
        "upcoming_note": "Cards worth checking first.",
        "today": "today",
        "day_many": "days",
        "fresh": "Fresh",
        "watch": "Needs attention",
        "stale": "Stale",
        "unknown": "Not marked",
        "method": "How to read this snapshot",
        "method_text": "This is not a donor ranking or funding forecast. The charts show how cards are distributed across QAZ.FUND working signals; verify terms with the organizer.",
        "source_link": "Check sources",
        "catalog_link": "Find support",
        "no_data": "There is not enough data for this view yet.",
        "footer": "QAZ.FUND does not award funds or process applications. Check the organizer's terms before acting.",
    },
    "kk": {
        "title": "Мүмкіндіктер шолуы – QAZ.FUND",
        "description": "Ағымдағы каталогтағы қолдау бағдарламалары, форматтар, мерзімдер мен дереккөздердің ашық шолуы.",
        "back": "Каталогқа оралу",
        "eyebrow": "Каталог шолуы",
        "heading": "Қолдауды қайдан іздеу керек",
        "intro": "Ағымдағы каталогтағы мүмкіндіктер, мерзімдер мен дереккөздердің ашық көрінісі.",
        "total": "Ашық бағдарламалар",
        "sources": "Ресми дереккөздер",
        "soon": "30 күн ішіндегі мерзім",
        "rolling": "Нақты мерзімі жоқ бағдарламалар",
        "formats": "Қолдау форматтары",
        "formats_note": "Каталогта жиі кездесетін форматтар.",
        "sources_title": "Бағдарламаларды кім жариялайды",
        "sources_note": "Ашық карточкалары ең көп дереккөздер.",
        "deadlines": "Мерзімдер бөлінісі",
        "deadlines_note": "Мерзім қай бағдарламаны алдымен тексеру керегін көрсетеді.",
        "freshness": "Дереккөздер мәртебесі",
        "freshness_note": "Соңғы сәтті жаңартудың нәтижесі көрсетілген.",
        "quality": "Сәйкестік сапасы",
        "quality_note": "Карточкалар жұмыс істейтін өзектілік белгісі бойынша бөлінген.",
        "readiness": "Карточкалардың дайындығы",
        "readiness_note": "Карточкаларда негізгі өрістердің қаншасы жарияланғанын көрсетеді.",
        "complete": "Негізгі өрістер бар",
        "partial": "Нақтылау керек",
        "high": "Күшті белгілер",
        "good": "Орташа белгілер",
        "base": "Негізгі белгілер",
        "within_30": "30 күнге дейін",
        "within_90": "31–90 күн",
        "later": "90 күннен кейін",
        "rolling_label": "Мерзімсіз",
        "no_deadline": "Мерзім көрсетілмеген",
        "upcoming": "Жақын мерзімдер",
        "upcoming_note": "Алдымен тексеруге тұрарлық карточкалар.",
        "today": "бүгін",
        "day_many": "күн",
        "fresh": "Жаңартылған",
        "watch": "Назар аударуды қажет етеді",
        "stale": "Ескірген",
        "unknown": "Белгіленбеген",
        "method": "Бұл шолуды қалай оқу керек",
        "method_text": "Бұл донорлардың рейтингі де, қаржыландыру болжамы да емес. Диаграммалар QAZ.FUND жұмыс белгілері бойынша карточкалардың бөлінісін көрсетеді; шарттарды ұйымдастырушыдан тексеріңіз.",
        "source_link": "Дереккөздерді тексеру",
        "catalog_link": "Қолдау іздеу",
        "no_data": "Бұл көрініс үшін дерек әзірге жеткіліксіз.",
        "footer": "QAZ.FUND қаражат бөлмейді және өтінім қабылдамайды. Әрекет етпес бұрын ұйымдастырушының шарттарын тексеріңіз.",
    },
}

_KK_SOURCE_LABELS = {
    "kazakhstan_domestic_support": "Қазақстандағы қолдау бағдарламалары",
    "national_institutes_of_health": "АҚШ Ұлттық денсаулық сақтау институттары (NIH)",
    "world_bank": "Дүниежүзілік банк",
    "united_nations_development_programme": "БҰҰ-ның Даму бағдарламасы (БҰҰДБ)",
}


def _copy(lang: str) -> dict[str, str]:
    if lang == "kk":
        copy = dict(COPY["kk"])
        copy["language_fallback_note"] = (
            "Кейбір карточкалардағы сипаттама әзірге бастапқы тілде көрсетіледі. "
            "Соңғы шарттарды ұйымдастырушының ресми бетінен тексеріңіз."
        )
        return copy
    return COPY.get(lang, COPY["ru"])


def _label(raw: str, lang: str) -> str:
    labels = {
        "grant": ("Гранты", "Grants", "Гранттар"),
        "contest": ("Конкурсы", "Contests", "Конкурстар"),
        "accelerator": ("Акселераторы", "Accelerators", "Акселераторлар"),
        "cloud_credit": ("Облачные кредиты", "Cloud credits", "Бұлттық кредиттер"),
        "tender": ("Тендеры", "Tenders", "Тендерлер"),
        "fellowship": ("Стипендии", "Fellowships", "Стипендиялар"),
    }
    values = labels.get(
        raw,
        (
            raw.replace("_", " ").title(),
            raw.replace("_", " ").title(),
            raw.replace("_", " ").title(),
        ),
    )
    if lang == "en":
        return values[1]
    if lang == "kk":
        return values[2]
    return values[0]


def _source_label(raw: str, lang: str) -> str:
    """Render a source name for people without exposing adapter identifiers."""

    value = str(raw or "").strip()
    if not value:
        return "–"
    label_map = dashboard_copy(lang).get("label_map")
    if lang == "kk":
        localized = _KK_SOURCE_LABELS.get(
            value.lower().replace("-", "_").replace(" ", "_")
        )
        if localized:
            return localized
    if isinstance(label_map, dict):
        normalized = value.lower().replace("-", "_").replace(" ", "_")
        mapped = label_map.get(normalized) or label_map.get(value.lower())
        if isinstance(mapped, str) and mapped.strip():
            return mapped.strip()
    return value.replace("_", " ").strip()


def _count_rows(
    counter: Counter[str], labels: dict[str, str], limit: int = 6
) -> list[tuple[str, int]]:
    rows = [
        (labels.get(key, key), int(value)) for key, value in counter.most_common(limit)
    ]
    return rows or [("–", 0)]


def _bar_chart(
    rows: list[tuple[str, int]],
    *,
    chart_id: str,
    color: str,
    empty_label: str,
    aria_label: str | None = None,
) -> str:
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
        chart_label = label if len(label) <= 24 else f"{label[:23].rstrip()}…"
        chunks.append(
            f'<g class="chart-row"><title>{escape(label)}: {value}</title>'
            f'<text x="0" y="{y + 16}" class="chart-label">{escape(chart_label)}</text>'
            f'<rect x="188" y="{y}" width="390" height="{bar_height}" rx="8" class="chart-track" />'
            f'<rect x="188" y="{y}" width="{bar_width}" height="{bar_height}" rx="8" fill="{color}" />'
            f'<text x="596" y="{y + 16}" text-anchor="end" class="chart-value">{value}</text></g>'
        )
    return (
        f'<svg class="data-chart" data-avds-component="DataViz" data-avds-pattern="{escape(chart_id)}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(aria_label or empty_label)}">'
        + "".join(chunks)
        + "</svg>"
    )


def _metric(label: str, value: int, tone: str = "") -> str:
    return f'<div class="insight-metric {tone}"><span>{escape(label)}</span><strong>{value:,}</strong></div>'.replace(
        ",", " "
    )


def build_insights_snapshot(
    *,
    items: list[Opportunity],
    coverage: dict[str, Any],
    as_of: date | None = None,
    upcoming_limit: int = 8,
) -> dict[str, Any]:
    """Build the versioned analytics read model used by the page and API.

    The snapshot deliberately contains counts and source-grounded next steps,
    not recommendations inferred from missing fields. ``as_of`` is injectable
    so contract tests and downstream jobs can reproduce the same bucket logic.
    """

    today = as_of or date.today()
    open_items = _open_items_as_of(items, today)
    deadline_buckets = {
        "within_30": 0,
        "within_90": 0,
        "later": 0,
        "rolling": 0,
        "no_deadline": 0,
    }
    for item in open_items:
        if item.deadline is None:
            policy = str((item.raw or {}).get("deadline_policy") or "").strip().lower()
            deadline_buckets["rolling" if policy == "rolling" else "no_deadline"] += 1
        elif item.deadline <= today + timedelta(days=30):
            deadline_buckets["within_30"] += 1
        elif item.deadline <= today + timedelta(days=90):
            deadline_buckets["within_90"] += 1
        else:
            deadline_buckets["later"] += 1

    upcoming = sorted(
        (item for item in open_items if item.deadline is not None),
        key=lambda item: (item.deadline, -item.score, item.title.casefold()),
    )[: max(1, upcoming_limit)]
    upcoming_rows = [
        {
            "id": str(item.id),
            "title": item.title,
            "source": item.funder or item.source,
            "deadline": item.deadline.isoformat() if item.deadline else None,
            "days_left": (item.deadline - today).days if item.deadline else None,
            "score": round(float(item.score), 4),
        }
        for item in upcoming
    ]
    freshness = Counter(
        str(row.get("freshness_status") or "unknown")
        for row in coverage.get("sources", [])
        if isinstance(row, dict)
    )
    readiness_fields = {"deadline": 0, "amount": 0, "eligibility": 0, "application": 0}
    complete_count = 0
    for item in open_items:
        raw = item.raw if isinstance(item.raw, dict) else {}
        present = {
            "deadline": bool(item.deadline or raw.get("deadline_policy") == "rolling"),
            "amount": bool(
                item.amount_min is not None
                or item.amount_max is not None
                or raw.get("amount_raw")
            ),
            "eligibility": bool(item.eligibility or raw.get("eligibility")),
            "application": bool(item.source_url or raw.get("application_url")),
        }
        for field, available in present.items():
            if available:
                readiness_fields[field] += 1
        if all(present.values()):
            complete_count += 1
    return {
        "schema_version": "insights.v1",
        "as_of": today.isoformat(),
        "catalog": {
            "open_items": len(open_items),
            "official_sources": int(coverage.get("enabled_sources") or 0),
            "relevant_open_items": len(open_items),
            "coverage_relevant_open_items": int(
                coverage.get("relevant_open_items") or 0
            ),
        },
        "formats": {
            key: int(value)
            for key, value in Counter(
                item.type.value for item in open_items
            ).most_common()
        },
        "sources": {
            str(key): int(value)
            for key, value in Counter(
                item.funder or item.source for item in open_items
            ).most_common(12)
        },
        "deadlines": {
            "buckets": deadline_buckets,
            "upcoming": upcoming_rows,
        },
        "freshness": {
            "fresh": int(freshness.get("fresh", 0)),
            "watch": int(freshness.get("watch", 0)),
            "stale": int(freshness.get("stale", 0)),
            "unknown": int(freshness.get("unknown", 0)),
        },
        "match_quality": {
            "high": sum(1 for item in open_items if item.score >= 0.7),
            "good": sum(1 for item in open_items if 0.5 <= item.score < 0.7),
            "base": sum(1 for item in open_items if item.score < 0.5),
        },
        "decision_readiness": {
            "complete": complete_count,
            "partial": len(open_items) - complete_count,
            "field_coverage": readiness_fields,
        },
    }


def _open_items_as_of(items: list[Opportunity], as_of: date) -> list[Opportunity]:
    """Return public open items using a supplied calendar date."""

    return [
        item
        for item in items
        if public_lifecycle(item) not in {"closed", "awarded"}
        and (item.deadline is None or item.deadline >= as_of)
    ]


def _days_label(days_left: int, *, lang: str, copy: dict[str, str]) -> str:
    if days_left <= 0:
        return copy["today"]
    if lang == "ru":
        if days_left == 1:
            return "1 день"
        return f"{days_left} {copy['day_many']}"
    if lang == "kk":
        return f"{days_left} {copy['day_many']}"
    if days_left == 1:
        return "1 day"
    return f"{days_left} {copy['day_many']}"


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
    home = (
        f"{base}/?lang={lang}#opportunities" if base else f"/?lang={lang}#opportunities"
    )
    status = f"{base}/status?lang={lang}" if base else f"/status?lang={lang}"
    sources = f"{base}/?lang={lang}#sources" if base else f"/?lang={lang}#sources"
    en_href = f"{base}/insights?lang=en" if base else "/insights?lang=en"
    ru_href = f"{base}/insights?lang=ru" if base else "/insights?lang=ru"
    kk_href = f"{base}/insights?lang=kk" if base else "/insights?lang=kk"
    kk_current = ' aria-current="page"' if lang == "kk" else ""
    ru_current = ' aria-current="page"' if lang == "ru" else ""
    en_current = ' aria-current="page"' if lang == "en" else ""
    insights_json_href = (
        f"{base}/insights.json?lang={lang}" if base else f"/insights.json?lang={lang}"
    )
    snapshot = build_insights_snapshot(items=items, coverage=coverage)
    open_count = int(snapshot["catalog"]["open_items"])
    soon = int(snapshot["deadlines"]["buckets"]["within_30"])
    rolling = int(snapshot["deadlines"]["buckets"]["rolling"])
    type_rows = _count_rows(Counter(snapshot["formats"]), {}, 6)
    type_rows = [(_label(label, lang), value) for label, value in type_rows]
    source_rows = _count_rows(Counter(snapshot["sources"]), {}, 6)
    source_rows = [(_source_label(label, lang), value) for label, value in source_rows]
    deadline_rows = [
        (copy["within_30"], int(snapshot["deadlines"]["buckets"]["within_30"])),
        (copy["within_90"], int(snapshot["deadlines"]["buckets"]["within_90"])),
        (copy["later"], int(snapshot["deadlines"]["buckets"]["later"])),
        (copy["rolling_label"], rolling),
        (copy["no_deadline"], int(snapshot["deadlines"]["buckets"]["no_deadline"])),
    ]
    freshness_rows = [
        (copy["fresh"], int(snapshot["freshness"]["fresh"])),
        (copy["watch"], int(snapshot["freshness"]["watch"])),
        (copy["stale"], int(snapshot["freshness"]["stale"])),
        (copy["unknown"], int(snapshot["freshness"]["unknown"])),
    ]
    score_rows = [
        (copy["high"], int(snapshot["match_quality"]["high"])),
        (copy["good"], int(snapshot["match_quality"]["good"])),
        (copy["base"], int(snapshot["match_quality"]["base"])),
    ]
    readiness_rows = [
        (copy["complete"], int(snapshot["decision_readiness"]["complete"])),
        (copy["partial"], int(snapshot["decision_readiness"]["partial"])),
    ]
    upcoming_rows = list(snapshot["deadlines"]["upcoming"])
    html_lang = escape(lang, quote=True)
    fallback_note = escape(str(copy.get("language_fallback_note") or ""))
    fallback_note_markup = (
        f'<p class="language-fallback-note" lang="kk" data-language-fallback="source">{fallback_note}</p>'
        if fallback_note
        else ""
    )
    canonical = (
        f"{site_origin.rstrip('/')}{base}/insights?lang={lang}"
        if site_origin
        else f"{base}/insights?lang={lang}"
    )
    if upcoming_rows:
        upcoming_items: list[str] = []
        for row in upcoming_rows:
            deadline = str(row["deadline"])
            detail_href = (
                f"{base}/opportunity/{row['id']}?lang={lang}"
                if base
                else f"/opportunity/{row['id']}?lang={lang}"
            )
            upcoming_items.append(
                '<li class="upcoming-item">'
                f'<time class="upcoming-date" datetime="{escape(deadline, quote=True)}">'
                f"{escape(deadline[8:10] + '.' + deadline[5:7])}</time>"
                "<div>"
                f'<a class="upcoming-title" href="{escape(detail_href, quote=True)}">'
                f"{escape(str(row['title']))}</a>"
                f'<span class="upcoming-source">{escape(_source_label(str(row["source"]), lang))}</span>'
                "</div>"
                f'<span class="upcoming-days">{escape(_days_label(int(row["days_left"]), lang=lang, copy=copy))}</span>'
                "</li>"
            )
        upcoming_markup = (
            '<ul class="upcoming-list">' + "".join(upcoming_items) + "</ul>"
        )
    else:
        upcoming_markup = f'<p class="no-data">{escape(copy["no_data"])}</p>'
    return f"""<!doctype html>
<html lang="{html_lang}" data-avds="grant-radar" data-av-theme="light" data-theme="light">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(copy["title"])}</title>
  <meta name="description" content="{escape(copy["description"], quote=True)}">
  <link rel="canonical" href="{escape(canonical, quote=True)}">
  <link rel="alternate" hreflang="kk" href="{escape((site_origin.rstrip('/') if site_origin else '') + kk_href, quote=True)}">
  <link rel="alternate" hreflang="ru" href="{escape((site_origin.rstrip('/') if site_origin else '') + ru_href, quote=True)}">
  <link rel="alternate" hreflang="en" href="{escape((site_origin.rstrip('/') if site_origin else '') + en_href, quote=True)}">
  <link rel="alternate" type="application/json" href="{escape((site_origin.rstrip('/') if site_origin else '') + insights_json_href, quote=True)}">
  <meta property="og:title" content="{escape(copy["title"], quote=True)}"><meta property="og:description" content="{escape(copy["description"], quote=True)}">
  <meta property="og:image" content="{escape(og_image_url(site_origin, root_path), quote=True)}">
  {analytics_head_html()}{AVDS_FONT_HEAD}
  <style>
    {AVDS_CSS}
    *{{box-sizing:border-box}} body{{margin:0;background:var(--color-bg);color:var(--color-text);font-family:var(--av-font-sans);line-height:1.5}}
    a{{color:inherit}} .shell{{width:min(var(--av-container-dashboard),calc(100% - 48px));margin:0 auto;padding:20px 0 44px}}
    .topbar{{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:18px}}
    .back{{color:var(--color-text-muted);font-size:14px;font-weight:700;text-decoration:none}} .back:hover{{color:var(--color-accent)}}
    .language-fallback-note{{margin:0 0 14px;padding:9px 12px;border-left:3px solid var(--color-accent);color:var(--color-text-muted);background:var(--color-bg-subtle);font-size:12px;line-height:1.45}}
    .langs{{display:flex;gap:6px}} .langs a{{padding:5px 9px;font-size:12px;font-weight:700;text-decoration:none;color:var(--color-text-muted);border-bottom:2px solid transparent}} .langs a.active{{color:var(--color-text);border-color:var(--color-accent)}}
    .hero{{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(260px,.8fr);gap:28px;padding:28px;border:1px solid var(--color-border);border-radius:var(--av-radius-lg);background:linear-gradient(135deg,var(--color-surface),var(--color-accent-subtle));box-shadow:var(--shadow-md)}}
    .eyebrow{{color:var(--color-accent);font-size:12px;font-weight:800;letter-spacing:.06em;text-transform:uppercase}} h1{{font-size:clamp(30px,5vw,48px);line-height:1.05;margin:8px 0 12px;max-width:16ch}} .hero p{{max-width:60ch;color:var(--color-text-muted);margin:0;font-size:16px}}
    .hero-actions{{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}} .button{{display:inline-flex;align-items:center;min-height:38px;padding:0 14px;border-radius:var(--av-radius-md);border:1px solid var(--color-border);font-size:14px;font-weight:750;text-decoration:none;background:var(--color-surface)}} .button:hover{{border-color:var(--color-border-strong);background:var(--color-surface-raised)}} .button.primary{{background:var(--color-accent);border-color:var(--color-accent);color:#fff}} .button.primary:hover{{border-color:var(--color-accent-hover);background:var(--color-accent-hover)}}
    .metric-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;align-content:start}} .insight-metric{{display:grid;gap:5px;padding:14px;border:1px solid var(--color-border);border-radius:var(--av-radius-md);background:rgb(255 255 255 / .75)}} .insight-metric span{{color:var(--color-text-muted);font-size:12px;font-weight:700}} .insight-metric strong{{font-size:28px;line-height:1}}
    .insight-metric.good strong{{color:var(--color-success)}} .insight-metric.warn strong{{color:var(--color-warning)}}
    .section-head{{display:grid;gap:5px;margin:30px 0 12px}} .section-head h2{{margin:0;font-size:24px;line-height:1.15}} .section-head p{{margin:0;color:var(--color-text-muted);font-size:14px}}
    .viz-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}} .viz-card{{padding:18px;border:1px solid var(--color-border);border-radius:var(--av-radius-lg);background:var(--color-surface);box-shadow:var(--shadow-xs)}} .viz-card h3{{margin:0;font-size:17px}} .viz-card p{{margin:4px 0 14px;color:var(--color-text-muted);font-size:13px}}
    .insight-lower{{display:grid;grid-template-columns:minmax(0,.8fr) minmax(0,1.2fr);align-items:start;gap:14px;margin-top:14px}} .insight-stack{{display:grid;gap:14px;align-content:start}} .upcoming-list{{display:grid;gap:0;margin:0;padding:0;list-style:none}} .upcoming-item{{display:grid;grid-template-columns:74px minmax(0,1fr) auto;align-items:center;gap:10px;padding:10px 0;border-top:1px solid var(--color-border)}} .upcoming-item:first-child{{border-top:0;padding-top:0}} .upcoming-date{{color:var(--color-accent);font-size:12px;font-weight:800;white-space:nowrap}} .upcoming-title{{display:block;overflow:hidden;color:var(--color-text);font-size:13px;font-weight:750;text-overflow:ellipsis;white-space:nowrap;text-decoration:none}} .upcoming-source{{display:block;overflow:hidden;color:var(--color-text-muted);font-size:11px;text-overflow:ellipsis;white-space:nowrap}} .upcoming-days{{color:var(--color-text-muted);font-size:11px;font-weight:700;white-space:nowrap}}
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
      .insight-lower{{grid-template-columns:minmax(0,.75fr) minmax(0,1.25fr);gap:18px}}
      .viz-card{{padding:20px}}
    }}
    @media(min-width:2200px){{
      .shell{{width:min(1920px,calc(100% - 160px))}}
      .hero{{grid-template-columns:minmax(0,1.35fr) minmax(420px,.65fr);gap:64px}}
      h1{{max-width:24ch}}
      .hero p{{max-width:72ch}}
    }}
    @media(max-width:760px){{.shell{{width:min(100% - 24px,680px);padding-top:12px}} .hero{{grid-template-columns:1fr;padding:20px}} .metric-grid{{grid-template-columns:repeat(4,minmax(0,1fr))}} .insight-metric{{padding:10px}} .insight-metric strong{{font-size:22px}} .viz-grid{{grid-template-columns:1fr}} .insight-lower{{grid-template-columns:1fr}} .upcoming-item{{grid-template-columns:66px minmax(0,1fr);gap:8px}} .upcoming-days{{grid-column:2}} .method{{grid-template-columns:1fr;gap:5px}}}}
    @media(max-width:480px){{.metric-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}} h1{{font-size:34px}}}}
  </style>
</head>
<body><main class="shell">
  <div class="topbar"><a class="back" href="{escape(home, quote=True)}">← {escape(copy["back"])}</a><nav class="langs" aria-label="Language"><a class="{'active' if lang == 'kk' else ''}" href="{escape(kk_href, quote=True)}" lang="kk"{kk_current}>KAZ</a><a class="{'active' if lang == 'ru' else ''}" href="{escape(ru_href, quote=True)}" lang="ru"{ru_current}>RU</a><a class="{'active' if lang == 'en' else ''}" href="{escape(en_href, quote=True)}" lang="en"{en_current}>EN</a></nav></div>
  {fallback_note_markup}
  <section class="hero" data-avds-component="hero-band"><div><span class="eyebrow">{escape(copy["eyebrow"])}</span><h1>{escape(copy["heading"])}</h1><p>{escape(copy["intro"])}</p><div class="hero-actions"><a class="button primary" href="{escape(home, quote=True)}">{escape(copy["catalog_link"])}</a><a class="button" href="{escape(status, quote=True)}">{escape(copy["source_link"])}</a></div></div><div class="metric-grid" aria-label="Key catalog metrics">{_metric(copy["total"],open_count,"good")}{_metric(copy["sources"],int(coverage.get("enabled_sources") or 0))}{_metric(copy["soon"],soon,"warn")}{_metric(copy["rolling"],rolling)}</div></section>
  <div class="section-head"><h2>{escape(copy["formats"])}</h2><p>{escape(copy["formats_note"])}</p></div>
  <div class="viz-grid"><article class="viz-card"><h3>{escape(copy["formats"])}</h3><p>{escape(copy["formats_note"])}</p>{_bar_chart(type_rows,chart_id="format-distribution",color="#315fdc",empty_label=copy["no_data"],aria_label=copy["formats"])}</article><article class="viz-card"><h3>{escape(copy["sources_title"])}</h3><p>{escape(copy["sources_note"])}</p>{_bar_chart(source_rows,chart_id="source-distribution",color="#15724e",empty_label=copy["no_data"],aria_label=copy["sources_title"])}</article><article class="viz-card"><h3>{escape(copy["deadlines"])}</h3><p>{escape(copy["deadlines_note"])}</p>{_bar_chart(deadline_rows,chart_id="deadline-distribution",color="#9a6414",empty_label=copy["no_data"],aria_label=copy["deadlines"])}</article><article class="viz-card"><h3>{escape(copy["freshness"])}</h3><p>{escape(copy["freshness_note"])}</p>{_bar_chart(freshness_rows,chart_id="source-freshness",color="#7c3aed",empty_label=copy["no_data"],aria_label=copy["freshness"])}</article></div>
  <div class="insight-lower"><div class="insight-stack"><section class="viz-card"><h3>{escape(copy["quality"])}</h3><p>{escape(copy["quality_note"])}</p>{_bar_chart(score_rows,chart_id="match-quality",color="#315fdc",empty_label=copy["no_data"],aria_label=copy["quality"])}</section><section class="viz-card"><h3>{escape(copy["readiness"])}</h3><p>{escape(copy["readiness_note"])}</p>{_bar_chart(readiness_rows,chart_id="decision-readiness",color="#0f766e",empty_label=copy["no_data"],aria_label=copy["readiness"])}</section></div><section class="viz-card" data-avds-component="DataViz"><h3>{escape(copy["upcoming"])}</h3><p>{escape(copy["upcoming_note"])}</p>{upcoming_markup}</section></div>
  <aside class="method" data-avds-component="method-card"><strong>{escape(copy["method"])}</strong><p>{escape(copy["method_text"])}</p></aside>
  <footer class="footer"><span>{escape(copy["footer"])}</span><span><a href="{escape(home, quote=True)}">{escape(copy["catalog_link"])}</a> · <a href="{escape(sources, quote=True)}">{escape(copy["source_link"])}</a></span></footer>
</main></body></html>"""
