# flake8: noqa: E501

"""Public editorial-style media surface backed by QAZ.FUND records.

The page uses newsroom primitives proven in the Total.kz and ORTCOM products
(lead story, live feed, topic shelves and source metadata). It does not copy
external article text or private editorial data: every item is a public
QAZ.FUND opportunity and links back to its primary source.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from html import escape
from typing import Any

from qazstack.opportunities import public_lifecycle

from api.avds import AVDS_CSS, AVDS_FONT_HEAD
from api.public_meta import analytics_head_html, og_image_url
from core.localization import localize_opportunity
from core.models import Opportunity

MEDIA_COPY: dict[str, dict[str, str]] = {
    "ru": {
        "title": "Медиа QAZ.FUND – новости поддержки",
        "description": "Новости и обновления программ поддержки с прямыми ссылками на первоисточники.",
        "back": "Вернуться в каталог",
        "eyebrow": "Медиа QAZ.FUND",
        "heading": "Новости поддержки",
        "intro": "Что изменилось в программах, где появились новые условия и какие сроки приближаются.",
        "hero_note": "Редакционная витрина на основе открытых карточек QAZ.FUND.",
        "updates": "обновлений в потоке",
        "lead_eyebrow": "Главное",
        "lead_title": "Ключевое обновление",
        "lead_note": "Сначала – материал, который стоит проверить сегодня.",
        "latest_eyebrow": "Оперативная лента",
        "latest_title": "Последние обновления",
        "latest_note": "Новые и недавно обновлённые записи из официальных источников.",
        "topics_eyebrow": "Тематические полки",
        "topics_title": "По темам",
        "topics_note": "Направления, где сейчас больше всего открытых записей.",
        "sources_eyebrow": "В фокусе",
        "sources_title": "Источники и организации",
        "sources_note": "Кто публикует программы, которые сейчас видны в каталоге.",
        "open_card": "Открыть карточку",
        "open_source": "Перейти к источнику",
        "catalog": "Найти поддержку",
        "insights": "Смотреть аналитику",
        "source": "Источник",
        "updated": "Обновлено",
        "deadline": "Срок",
        "rolling": "Приём без фиксированного срока",
        "no_deadline": "Срок уточняется",
        "items_count": "карточек",
        "programs": "программ",
        "empty": "Новых открытых обновлений пока нет. Вернитесь после следующего обхода источников.",
        "method_title": "Как читать раздел",
        "method_text": "Это не независимые новости и не обещание финансирования. Каждая заметка ведёт к карточке QAZ.FUND и официальной странице организатора – условия и сроки проверяйте там.",
        "footer": "QAZ.FUND не выдаёт средства и не принимает заявки. Перед действием проверьте условия у организатора.",
        "topic_ai": "ИИ и цифровые решения",
        "topic_agro": "Агро, вода и климат",
        "topic_science": "Наука и образование",
        "topic_public": "Госсектор и инфраструктура",
        "topic_business": "Бизнес и субсидии",
        "topic_ngo": "Медиа и гражданский сектор",
        "topic_other": "Другие направления",
        "live": "Сейчас",
    },
    "en": {
        "title": "QAZ.FUND Media – support news",
        "description": "Support-program news and updates with direct links to primary sources.",
        "back": "Back to catalog",
        "eyebrow": "QAZ.FUND Media",
        "heading": "Support news",
        "intro": "What changed in programs, where new terms appeared, and which deadlines are approaching.",
        "hero_note": "An editorial surface built from QAZ.FUND public opportunity cards.",
        "updates": "updates in the stream",
        "lead_eyebrow": "Top update",
        "lead_title": "Key update",
        "lead_note": "Start with the item worth checking today.",
        "latest_eyebrow": "Live feed",
        "latest_title": "Latest updates",
        "latest_note": "New and recently refreshed records from official sources.",
        "topics_eyebrow": "Topic shelves",
        "topics_title": "By topic",
        "topics_note": "The areas with the largest number of open records right now.",
        "sources_eyebrow": "In focus",
        "sources_title": "Sources and organisations",
        "sources_note": "Who publishes the programs currently visible in the catalog.",
        "open_card": "Open card",
        "open_source": "Open source",
        "catalog": "Find support",
        "insights": "View analytics",
        "source": "Source",
        "updated": "Updated",
        "deadline": "Deadline",
        "rolling": "Rolling intake",
        "no_deadline": "Check the deadline",
        "items_count": "cards",
        "programs": "programs",
        "empty": "There are no new open updates yet. Check back after the next source refresh.",
        "method_title": "How to read this section",
        "method_text": "This is not independent reporting or a funding promise. Every item leads to a QAZ.FUND card and the organiser's official page – verify terms and deadlines there.",
        "footer": "QAZ.FUND does not award funds or process applications. Check the organiser's terms before acting.",
        "topic_ai": "AI and digital solutions",
        "topic_agro": "Agriculture, water and climate",
        "topic_science": "Science and education",
        "topic_public": "Public sector and infrastructure",
        "topic_business": "Business and subsidies",
        "topic_ngo": "Media and civil society",
        "topic_other": "Other directions",
        "live": "Now",
    },
    "kk": {
        "title": "QAZ.FUND медиа – қолдау жаңалықтары",
        "description": "Қолдау бағдарламаларының жаңалықтары мен өзгерістері, бастапқы дереккөздерге тікелей сілтемелермен.",
        "back": "Каталогқа оралу",
        "eyebrow": "QAZ.FUND медиа",
        "heading": "Қолдау жаңалықтары",
        "intro": "Бағдарламаларда не өзгерді, жаңа шарттар қайда жарияланды және қандай мерзімдер жақындап келеді.",
        "hero_note": "QAZ.FUND ашық карточкалары негізіндегі редакциялық витрина.",
        "updates": "жаңарту ағымда",
        "lead_eyebrow": "Бастысы",
        "lead_title": "Негізгі жаңарту",
        "lead_note": "Бүгін бірінші тексеруге тұрарлық материал.",
        "latest_eyebrow": "Жедел ағым",
        "latest_title": "Соңғы жаңартулар",
        "latest_note": "Ресми дереккөздерден жаңа және жақында жаңартылған жазбалар.",
        "topics_eyebrow": "Тақырыптық сөрелер",
        "topics_title": "Тақырыптар бойынша",
        "topics_note": "Қазір ашық жазбалары көп бағыттарды жинақтадық.",
        "sources_eyebrow": "Назарда",
        "sources_title": "Дереккөздер мен ұйымдар",
        "sources_note": "Каталогта қазір көрініп тұрған бағдарламаларды кім жариялайды.",
        "open_card": "Карточканы ашу",
        "open_source": "Дереккөзге өту",
        "catalog": "Қолдау іздеу",
        "insights": "Талдауды көру",
        "source": "Дереккөз",
        "updated": "Жаңартылды",
        "deadline": "Мерзім",
        "rolling": "Қабылдау тұрақты",
        "no_deadline": "Мерзімді нақтылау керек",
        "items_count": "карточка",
        "programs": "бағдарлама",
        "empty": "Жаңа ашық жаңартулар әзірге жоқ. Дереккөздер келесі рет тексерілгеннен кейін қайта кіріңіз.",
        "method_title": "Бөлімді қалай оқу керек",
        "method_text": "Бұл тәуелсіз жаңалықтар да, қаржыландыру уәдесі де емес. Әр жазба QAZ.FUND карточкасына және ұйымдастырушының ресми бетіне апарады – шарттар мен мерзімдерді сол жерден тексеріңіз.",
        "footer": "QAZ.FUND қаражат бөлмейді және өтінім қабылдамайды. Әрекет етпес бұрын ұйымдастырушының шарттарын тексеріңіз.",
        "topic_ai": "ЖИ және цифрлық шешімдер",
        "topic_agro": "Агро, су және климат",
        "topic_science": "Ғылым және білім",
        "topic_public": "Мемлекеттік сектор және инфрақұрылым",
        "topic_business": "Бизнес және субсидиялар",
        "topic_ngo": "Медиа және азаматтық сектор",
        "topic_other": "Басқа бағыттар",
        "live": "Қазір",
    },
}

_TOPIC_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("topic_ai", ("ai", "artificial intelligence", "digital", "цифр", "жасанды")),
    (
        "topic_agro",
        ("agro", "agriculture", "farm", "вет", "ветерин", "климат", "water", "ауыл"),
    ),
    (
        "topic_science",
        ("science", "research", "education", "university", "ғылым", "білім", "наука"),
    ),
    (
        "topic_public",
        (
            "public",
            "government",
            "infrastructure",
            "procurement",
            "госсектор",
            "мемлекеттік",
            "инфрақұрылым",
        ),
    ),
    ("topic_business", ("business", "sme", "startup", "subsid", "бизнес", "кәсіп")),
    ("topic_ngo", ("ngo", "media", "journal", "civil", "нко", "медиа", "азамат")),
)


def _copy(lang: str) -> dict[str, str]:
    return MEDIA_COPY.get(lang, MEDIA_COPY["ru"])


def _item_is_open(item: Opportunity, today: date) -> bool:
    if public_lifecycle(item) in {"closed", "awarded"}:
        return False
    return item.deadline is None or item.deadline >= today


def _observed_timestamp(item: Opportunity) -> float:
    value = item.discovered_at
    return value.timestamp() if isinstance(value, datetime) else 0.0


def _topic_key(item: Opportunity) -> str:
    blob = " ".join(
        [
            str(item.title or ""),
            str(item.summary or ""),
            " ".join(str(tag) for tag in item.tags),
        ]
    ).casefold()
    for key, tokens in _TOPIC_RULES:
        if any(token.casefold() in blob for token in tokens):
            return key
    return "topic_other"


def _source_name(item: Opportunity) -> str:
    return str(item.funder or item.source or "").replace("_", " ").strip() or "QAZ.FUND"


def _date_label(value: Any) -> str:
    if isinstance(value, datetime):
        value = value.date()
    return value.strftime("%d.%m.%Y") if isinstance(value, date) else ""


def _record(
    item: Opportunity, *, lang: str, base: str, copy: dict[str, str]
) -> dict[str, Any]:
    detail = (
        f"{base}/opportunity/{item.id}?lang={lang}"
        if base
        else f"/opportunity/{item.id}?lang={lang}"
    )
    return {
        "id": str(item.id),
        "title": str(item.title or "").strip() or copy["heading"],
        "summary": str(item.summary or "").strip(),
        "source": _source_name(item),
        "source_url": str(item.source_url),
        "type": str(getattr(item.type, "value", item.type)),
        "tags": [str(tag).strip() for tag in item.tags if str(tag).strip()][:4],
        "topic": _topic_key(item),
        "observed": _date_label(item.discovered_at),
        "deadline": _date_label(item.deadline),
        "rolling": bool((item.raw or {}).get("deadline_policy") == "rolling"),
        "score": round(float(item.score or 0.0), 3),
        "href": detail,
    }


def build_media_snapshot(
    *,
    items: list[Opportunity],
    lang: str = "ru",
    root_path: str = "",
    limit: int = 12,
    as_of: date | None = None,
) -> dict[str, Any]:
    """Build a deterministic newsroom read model without exposing ``raw``."""

    active_lang = lang if lang in MEDIA_COPY else "ru"
    copy = _copy(active_lang)
    base = root_path.rstrip("/")
    today = as_of or date.today()
    ordered = sorted(
        (
            localize_opportunity(item, active_lang)
            for item in items
            if _item_is_open(item, today)
        ),
        key=lambda item: (
            _observed_timestamp(item),
            float(item.score or 0.0),
            str(item.title).casefold(),
        ),
        reverse=True,
    )
    records = [
        _record(item, lang=active_lang, base=base, copy=copy)
        for item in ordered[: max(1, limit)]
    ]
    topic_counts = Counter(record["topic"] for record in records)
    topics = [
        {"key": key, "label": copy.get(key, copy["topic_other"]), "count": int(count)}
        for key, count in topic_counts.most_common(6)
    ]
    source_groups: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        source_groups.setdefault(record["source"], []).append(record)
    sources = [
        {
            "name": name,
            "count": len(group),
            "href": group[0]["source_url"],
            "latest": group[0]["observed"],
        }
        for name, group in sorted(
            source_groups.items(), key=lambda pair: (-len(pair[1]), pair[0].casefold())
        )[:6]
    ]
    return {
        "schema_version": "media.v1",
        "language": active_lang,
        "as_of": today.isoformat(),
        "count": len(records),
        "lead": records[0] if records else None,
        "latest": records[1:7] if len(records) > 1 else [],
        "cards": records,
        "topics": topics,
        "sources": sources,
    }


def _tag_markup(record: dict[str, Any]) -> str:
    return "".join(
        f'<span class="media-tag">{escape(str(tag))}</span>'
        for tag in (record.get("tags") or [])[:3]
    )


def _card_markup(
    record: dict[str, Any], *, copy: dict[str, str], variant: str = ""
) -> str:
    href = escape(str(record["href"]), quote=True)
    source_url = escape(str(record["source_url"]), quote=True)
    type_mark = escape(str(record.get("type") or "grant").replace("_", " ")[:12])
    summary = str(record.get("summary") or "")
    summary_markup = (
        f'<p class="media-card-summary">{escape(summary)}</p>' if summary else ""
    )
    return f"""<article class="media-card {variant}" data-avds-component="media-card" data-avds-pattern="feed-card">
      <a class="media-card-media" href="{href}" aria-hidden="true" tabindex="-1"><span class="media-card-mark">{type_mark}</span><span class="media-card-date">{escape(str(record.get("observed") or "–"))}</span></a>
      <div class="media-card-body"><div class="media-card-kicker"><span>{escape(str(record["source"]))}</span>{_tag_markup(record)}</div>
        <h3><a href="{href}">{escape(str(record["title"]))}</a></h3>{summary_markup}
        <div class="media-card-footer"><a class="media-card-link" href="{href}">{escape(copy["open_card"])} <span aria-hidden="true">↗</span></a><a class="media-card-source" href="{source_url}" target="_blank" rel="noopener">{escape(copy["open_source"])}</a></div>
      </div>
    </article>"""


def render_media_page(
    *, items: list[Opportunity], lang: str, root_path: str, site_origin: str
) -> str:
    active_lang = lang if lang in MEDIA_COPY else "ru"
    copy = _copy(active_lang)
    base = root_path.rstrip("/")
    snapshot = build_media_snapshot(items=items, lang=active_lang, root_path=base)
    home = (
        f"{base}/?lang={active_lang}#opportunities"
        if base
        else f"/?lang={active_lang}#opportunities"
    )
    insights = (
        f"{base}/insights?lang={active_lang}"
        if base
        else f"/insights?lang={active_lang}"
    )
    paths = {
        key: f"{base}/media?lang={key}" if base else f"/media?lang={key}"
        for key in ("kk", "ru", "en")
    }
    media_json = (
        f"{base}/media.json?lang={active_lang}"
        if base
        else f"/media.json?lang={active_lang}"
    )
    canonical = (
        f"{site_origin.rstrip('/')}{paths[active_lang]}"
        if site_origin
        else paths[active_lang]
    )
    lead = snapshot.get("lead")
    latest = snapshot.get("latest") or []
    cards = snapshot.get("cards") or []
    if lead:
        lead_markup = _card_markup(lead, copy=copy, variant="media-card--lead")
        live_rows = "".join(
            f'<li class="live-feed-row"><time>{escape(str(record.get("observed") or "–"))}</time><a href="{escape(str(record["href"]), quote=True)}">{escape(str(record["title"]))}</a><span>{escape(str(record["source"]))}</span></li>'
            for record in latest[:5]
        )
        live_markup = (
            f'<ul class="live-feed-list">{live_rows}</ul>'
            if live_rows
            else f'<div class="media-empty">{escape(copy["empty"])}</div>'
        )
    else:
        lead_markup = f'<div class="media-empty">{escape(copy["empty"])}</div>'
        live_markup = f'<div class="media-empty">{escape(copy["empty"])}</div>'
    topics = (
        "".join(
            f'<a class="topic-shelf" href="{escape(home, quote=True)}"><span class="topic-shelf-index">{index:02d}</span><span><strong>{escape(str(topic["label"]))}</strong><small>{int(topic["count"])} {escape(copy["programs"])}</small></span><span class="topic-shelf-arrow" aria-hidden="true">↗</span></a>'
            for index, topic in enumerate(snapshot.get("topics") or [], 1)
        )
        or f'<div class="media-empty">{escape(copy["empty"])}</div>'
    )
    sources = (
        "".join(
            f'<a class="source-shelf" href="{escape(str(source["href"]), quote=True)}" target="_blank" rel="noopener"><span class="source-shelf-avatar" aria-hidden="true">{escape(str(source["name"])[:2].upper())}</span><span><strong>{escape(str(source["name"]))}</strong><small>{int(source["count"])} {escape(copy["items_count"])} · {escape(str(source.get("latest") or "–"))}</small></span><span class="topic-shelf-arrow" aria-hidden="true">↗</span></a>'
            for source in snapshot.get("sources") or []
        )
        or f'<div class="media-empty">{escape(copy["empty"])}</div>'
    )
    latest_cards = (
        "".join(_card_markup(record, copy=copy) for record in cards[1:10])
        or f'<div class="media-empty">{escape(copy["empty"])}</div>'
    )
    return f"""<!doctype html>
<html lang="{escape(active_lang, quote=True)}" data-avds="grant-radar" data-av-theme="light" data-theme="light"><head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(copy["title"])}</title><meta name="description" content="{escape(copy["description"], quote=True)}"><link rel="canonical" href="{escape(canonical, quote=True)}">
  <link rel="alternate" hreflang="kk" href="{escape((site_origin.rstrip('/') if site_origin else '') + paths['kk'], quote=True)}"><link rel="alternate" hreflang="ru" href="{escape((site_origin.rstrip('/') if site_origin else '') + paths['ru'], quote=True)}"><link rel="alternate" hreflang="en" href="{escape((site_origin.rstrip('/') if site_origin else '') + paths['en'], quote=True)}"><link rel="alternate" type="application/json" href="{escape((site_origin.rstrip('/') if site_origin else '') + media_json, quote=True)}">
  <meta property="og:title" content="{escape(copy['title'], quote=True)}"><meta property="og:description" content="{escape(copy['description'], quote=True)}"><meta property="og:type" content="website"><meta property="og:url" content="{escape(canonical, quote=True)}"><meta property="og:image" content="{escape(og_image_url(site_origin, root_path), quote=True)}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{escape(copy['title'], quote=True)}"><meta name="twitter:description" content="{escape(copy['description'], quote=True)}"><meta name="twitter:image" content="{escape(og_image_url(site_origin, root_path), quote=True)}">
  {analytics_head_html()}{AVDS_FONT_HEAD}<style>
    {AVDS_CSS}
    *{{box-sizing:border-box}}body{{margin:0;background:var(--color-bg);color:var(--color-text);font-family:var(--av-font-sans);line-height:1.45}}a{{color:inherit}}.shell{{width:min(var(--av-container-dashboard),calc(100% - 48px));margin:0 auto;padding:20px 0 48px}}.topbar{{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:16px}}.back{{color:var(--color-text-muted);font-size:13px;font-weight:750;text-decoration:none}}.back:hover{{color:var(--color-accent)}}.langs{{display:flex;gap:6px}}.langs a{{padding:5px 9px;color:var(--color-text-muted);font-size:12px;font-weight:800;text-decoration:none;border-bottom:2px solid transparent}}.langs a.active{{color:var(--color-text);border-color:var(--color-accent)}}
    .media-hero{{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(300px,.65fr);gap:24px;padding:28px;border:1px solid var(--color-border);border-radius:var(--av-radius-lg);background:linear-gradient(130deg,var(--color-surface),var(--color-accent-subtle));box-shadow:var(--shadow-md)}}.eyebrow,.section-eyebrow{{color:var(--color-accent);font-size:11px;font-weight:850;letter-spacing:.06em;text-transform:uppercase}}h1{{max-width:14ch;margin:8px 0 12px;font-size:clamp(32px,5vw,58px);line-height:1.02;letter-spacing:-.035em}}.hero-intro{{max-width:62ch;margin:0;color:var(--color-text-muted);font-size:17px}}.hero-note{{margin:16px 0 0;color:var(--color-text-muted);font-size:12px}}.hero-signal{{display:grid;align-content:center;gap:10px;padding:22px;border:1px solid var(--color-border);border-radius:var(--av-radius-md);background:rgb(255 255 255 / .78)}}.hero-signal-kicker{{color:var(--color-text-muted);font-size:12px;font-weight:750}}.hero-signal strong{{font-size:48px;line-height:1;color:var(--color-accent)}}.hero-signal span{{color:var(--color-text-muted);font-size:13px}}.signal-rule{{height:8px;border-radius:999px;background:linear-gradient(90deg,var(--color-accent) 0 68%,var(--color-success) 68% 100%)}}
    .section{{margin-top:24px;padding:22px;border:1px solid var(--color-border);border-radius:var(--av-radius-lg);background:var(--color-surface);box-shadow:var(--shadow-xs)}}.section-head{{display:flex;justify-content:space-between;align-items:end;gap:18px;margin-bottom:16px}}.section-head h2{{margin:4px 0 0;font-size:24px;line-height:1.08}}.section-head p{{max-width:58ch;margin:0;color:var(--color-text-muted);font-size:13px}}.section-head a{{color:var(--color-accent);font-size:12px;font-weight:800;text-decoration:none;white-space:nowrap}}.lead-layout{{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(320px,.75fr);gap:16px}}.media-card{{display:grid;grid-template-rows:112px 1fr;min-width:0;overflow:hidden;border:1px solid var(--color-border);border-radius:var(--av-radius-md);background:var(--color-surface);box-shadow:var(--shadow-2xs)}}.media-card--lead{{grid-template-rows:168px 1fr;min-height:100%}}.media-card-media{{display:flex;align-items:flex-end;justify-content:space-between;gap:10px;padding:14px;text-decoration:none;background:linear-gradient(135deg,#0f2b65,#315fdc 52%,#147a66);color:#fff}}.media-card-mark{{max-width:12ch;font-size:12px;font-weight:850;letter-spacing:.06em;text-transform:uppercase}}.media-card-date{{font-size:12px;font-weight:750;opacity:.9}}.media-card-body{{display:grid;align-content:start;gap:10px;padding:16px}}.media-card-kicker{{display:flex;flex-wrap:wrap;align-items:center;gap:6px;color:var(--color-text-muted);font-size:11px;font-weight:750}}.media-tag{{padding:3px 7px;border-radius:999px;background:var(--color-bg-subtle);color:var(--color-text-muted);font-size:10px}}.media-card h3{{margin:0;font-size:19px;line-height:1.12}}.media-card:not(.media-card--lead) h3{{font-size:16px}}.media-card h3 a{{text-decoration:none}}.media-card h3 a:hover{{color:var(--color-accent)}}.media-card-summary{{margin:0;color:var(--color-text-muted);font-size:13px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}.media-card-footer{{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-top:auto;padding-top:8px;border-top:1px solid var(--color-border)}}.media-card-link,.media-card-source{{color:var(--color-accent);font-size:11px;font-weight:850;text-decoration:none}}.media-card-source{{color:var(--color-text-muted);font-weight:700}}
    .live-feed{{padding:16px;border:1px solid var(--color-border);border-radius:var(--av-radius-md);background:var(--color-bg-subtle)}}.live-feed-head{{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:8px}}.live-feed-head strong{{font-size:16px}}.live-pill{{display:inline-flex;align-items:center;gap:5px;color:var(--color-success);font-size:11px;font-weight:850}}.live-pill::before{{content:"";width:7px;height:7px;border-radius:50%;background:currentColor}}.live-feed-list{{display:grid;gap:0;margin:0;padding:0;list-style:none}}.live-feed-row{{display:grid;grid-template-columns:70px minmax(0,1fr);gap:5px 10px;padding:11px 0;border-top:1px solid var(--color-border)}}.live-feed-row:first-child{{border-top:0}}.live-feed-row time{{color:var(--color-accent);font-size:11px;font-weight:850}}.live-feed-row a{{grid-column:2;overflow:hidden;font-size:13px;font-weight:750;text-decoration:none;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}}.live-feed-row a:hover{{color:var(--color-accent)}}.live-feed-row span{{grid-column:2;overflow:hidden;color:var(--color-text-muted);font-size:11px;text-overflow:ellipsis;white-space:nowrap}}
    .cards-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}.shelves-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}.shelf{{display:grid;gap:10px}}.shelf-head{{display:flex;justify-content:space-between;align-items:end;gap:10px;margin-bottom:2px}}.shelf-head h2{{margin:4px 0 0;font-size:21px}}.shelf-head p{{margin:0;color:var(--color-text-muted);font-size:12px}}.topic-shelf,.source-shelf{{display:flex;align-items:center;gap:12px;padding:13px;border:1px solid var(--color-border);border-radius:var(--av-radius-md);text-decoration:none;background:var(--color-bg-subtle)}}.topic-shelf:hover,.source-shelf:hover{{border-color:var(--color-accent);background:var(--color-surface)}}.topic-shelf-index{{display:grid;place-items:center;width:28px;height:28px;border-radius:50%;background:var(--color-accent);color:#fff;font-size:11px;font-weight:850}}.topic-shelf strong,.source-shelf strong{{display:block;font-size:13px}}.topic-shelf small,.source-shelf small{{display:block;margin-top:3px;color:var(--color-text-muted);font-size:11px}}.topic-shelf-arrow{{margin-left:auto;color:var(--color-accent);font-size:17px;font-weight:850}}.source-shelf-avatar{{display:grid;place-items:center;width:32px;height:32px;border-radius:50%;background:var(--color-primary-subtle);color:var(--color-accent);font-size:11px;font-weight:850}}.media-empty{{display:grid;place-items:center;min-height:120px;padding:18px;color:var(--color-text-muted);font-size:13px;text-align:center;border:1px dashed var(--color-border-strong);border-radius:var(--av-radius-md)}}.method{{display:grid;grid-template-columns:auto minmax(0,1fr);gap:14px;margin-top:20px;padding:14px 16px;border-left:4px solid var(--color-accent);border-radius:var(--av-radius-md);background:var(--color-surface)}}.method strong{{font-size:14px}}.method p{{margin:0;color:var(--color-text-muted);font-size:13px}}.footer{{display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-top:24px;padding-top:16px;border-top:1px solid var(--color-border);color:var(--color-text-muted);font-size:12px}}.footer a{{font-weight:800;color:var(--color-text)}}
    @media(min-width:1440px){{.shell{{width:min(1760px,calc(100% - 96px))}}.media-hero{{grid-template-columns:minmax(0,1.45fr) minmax(360px,.55fr);padding:34px 38px}}.section{{padding:24px}}.cards-grid{{grid-template-columns:repeat(4,minmax(0,1fr))}}}}@media(min-width:2200px){{.shell{{width:min(2080px,calc(100% - 160px))}}.media-hero{{grid-template-columns:minmax(0,1.55fr) minmax(440px,.45fr);padding:38px 46px}}.section{{padding:28px}}.lead-layout{{grid-template-columns:minmax(0,1.6fr) minmax(420px,.7fr)}}}}@media(max-width:900px){{.media-hero,.lead-layout{{grid-template-columns:1fr}}.cards-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.shelves-grid{{grid-template-columns:1fr}}}}@media(max-width:640px){{.shell{{width:min(100% - 24px,680px);padding-top:12px}}.topbar{{align-items:flex-start}}.media-hero,.section{{padding:18px}}h1{{font-size:38px}}.hero-intro{{font-size:15px}}.hero-signal strong{{font-size:40px}}.section-head{{display:grid;gap:8px;align-items:start}}.cards-grid{{grid-template-columns:1fr}}.media-card--lead{{grid-template-rows:132px 1fr}}.method{{grid-template-columns:1fr;gap:6px}}}}
  </style></head>
<body><main class="shell">
  <div class="topbar"><a class="back" href="{escape(home, quote=True)}">← {escape(copy["back"])}</a><nav class="langs" aria-label="Language"><a class="{'active' if active_lang == 'kk' else ''}" href="{escape(paths['kk'], quote=True)}" lang="kk">KAZ</a><a class="{'active' if active_lang == 'ru' else ''}" href="{escape(paths['ru'], quote=True)}" lang="ru">RU</a><a class="{'active' if active_lang == 'en' else ''}" href="{escape(paths['en'], quote=True)}" lang="en">EN</a></nav></div>
  <section class="media-hero" data-avds-component="hero-band"><div><span class="eyebrow">{escape(copy["eyebrow"])}</span><h1>{escape(copy["heading"])}</h1><p class="hero-intro">{escape(copy["intro"])}</p><p class="hero-note">{escape(copy["hero_note"])}</p></div><div class="hero-signal" data-avds-component="live-feed"><span class="hero-signal-kicker">{escape(copy["live"])}</span><strong>{int(snapshot["count"])}</strong><span>{escape(copy["updates"])}</span><div class="signal-rule" aria-hidden="true"></div></div></section>
  <section class="section" data-avds-component="media-lead"><div class="section-head"><div><span class="section-eyebrow">{escape(copy["lead_eyebrow"])}</span><h2>{escape(copy["lead_title"])}</h2><p>{escape(copy["lead_note"])}</p></div><a href="{escape(insights, quote=True)}">{escape(copy["insights"])} ↗</a></div><div class="lead-layout"><div>{lead_markup}</div><aside class="live-feed" data-avds-component="live-feed"><div class="live-feed-head"><strong>{escape(copy["latest_eyebrow"])}</strong><span class="live-pill">{escape(copy["live"])}</span></div>{live_markup}</aside></div></section>
  <section class="section" data-avds-component="media-latest"><div class="section-head"><div><span class="section-eyebrow">{escape(copy["latest_eyebrow"])}</span><h2>{escape(copy["latest_title"])}</h2><p>{escape(copy["latest_note"])}</p></div><a href="{escape(home, quote=True)}">{escape(copy["catalog"])} ↗</a></div><div class="cards-grid">{latest_cards}</div></section>
  <section class="section" data-avds-component="media-shelves"><div class="shelves-grid"><div class="shelf"><div class="shelf-head"><div><span class="section-eyebrow">{escape(copy["topics_eyebrow"])}</span><h2>{escape(copy["topics_title"])}</h2></div><p>{escape(copy["topics_note"])}</p></div>{topics}</div><div class="shelf"><div class="shelf-head"><div><span class="section-eyebrow">{escape(copy["sources_eyebrow"])}</span><h2>{escape(copy["sources_title"])}</h2></div><p>{escape(copy["sources_note"])}</p></div>{sources}</div></div></section>
  <aside class="method" data-avds-component="method-card"><strong>{escape(copy["method_title"])}</strong><p>{escape(copy["method_text"])}</p></aside><footer class="footer"><span>{escape(copy["footer"])}</span><span><a href="{escape(home, quote=True)}">{escape(copy["catalog"])}</a> · <a href="{escape(insights, quote=True)}">{escape(copy["insights"])}</a></span></footer>
</main></body></html>"""
