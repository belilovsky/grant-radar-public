"""Public explanatory pages kept concise for people using the catalogue."""

from __future__ import annotations

from html import escape

from api.avds import AVDS_CSS, AVDS_FONT_HEAD
from api.public_meta import analytics_head_html, og_image_url


PAGES: dict[str, dict[str, dict[str, object]]] = {
    "terms": {
        "ru": {
            "title": "Условия использования – QAZ.FUND",
            "eyebrow": "Условия использования",
            "heading": "Как пользоваться QAZ.FUND",
            "intro": "QAZ.FUND помогает найти открытые программы поддержки, понять следующий шаг и перейти к условиям организатора.",
            "sections": [("Что делает сервис", "Собирает открытые сведения, приводит их к единому виду и ведёт к первоисточнику. Каталог не заменяет правила конкурса или программы финансирования."), ("Что проверить", "Перед подачей проверьте право на участие, срок, сумму, документы и способ отправки заявки на странице организатора."), ("Ответственность за решение", "QAZ.FUND не выдаёт гранты, не принимает заявки и не гарантирует финансирование. Условия могут измениться после публикации карточки.")],
        },
        "en": {
            "title": "Terms of use – QAZ.FUND", "eyebrow": "Terms of use", "heading": "How to use QAZ.FUND", "intro": "QAZ.FUND helps you find open support programs, understand the next step, and reach the organizer's terms.", "sections": [("What the service does", "It gathers public information, presents it consistently, and links to the primary source. The catalog does not replace program rules."), ("What to verify", "Before applying, check eligibility, deadline, amount, documents, and submission method on the organizer's page."), ("Decision responsibility", "QAZ.FUND does not award grants, accept applications, or guarantee funding. Terms can change after a card is published.")],
        },
    },
    "data-policy": {
        "ru": {
            "title": "Политика данных – QAZ.FUND", "eyebrow": "Политика данных", "heading": "Откуда берутся данные", "intro": "Показываем открытые сведения, которые можно сверить в первоисточнике, и отделяем их от навигационных подсказок.", "sections": [("Первичные источники", "Карточка ведёт на страницу организатора. Там находятся окончательные условия, формы, сроки и контакты."), ("Обновление и свежесть", "Источники проверяются регулярно. Если сведения устарели или недоступны, это отражается в статусе источника."), ("Публичность", "Каталог не запрашивает документы и персональные данные и не берёт плату за доступ к спискам и ссылкам.")],
        },
        "en": {
            "title": "Data policy – QAZ.FUND", "eyebrow": "Data policy", "heading": "Where the data comes from", "intro": "We show public information that can be checked in a primary source and separate it from navigation hints.", "sections": [("Primary sources", "Every card links to the organizer's page, which contains the final terms, forms, deadlines, and contacts."), ("Freshness", "Sources are checked regularly. If information is stale or unavailable, the source status shows it."), ("Public by design", "The catalog does not ask for documents or personal data or charge for access to listings and links.")],
        },
    },
    "attribution": {
        "ru": {
            "title": "Использование данных – QAZ.FUND", "eyebrow": "Использование данных", "heading": "Как ссылаться на QAZ.FUND", "intro": "QAZ.FUND можно использовать как навигатор и открытый индекс программ поддержки, если ссылка на первоисточник остаётся видимой.", "sections": [("Для публикаций", "Ссылайтесь на карточку QAZ.FUND и официальную страницу организатора, чтобы читатель мог проверить условия."), ("Для исследований", "Открытые выгрузки и API подходят для анализа. Указывайте дату выгрузки и не выдавайте индекс за официальный реестр."), ("Для ИИ-систем", "Машинные поверхности QAZ.FUND содержат ссылки на источники и статусы. Перед ответом проверяйте первоисточник.")],
        },
        "en": {
            "title": "Data attribution – QAZ.FUND", "eyebrow": "Data attribution", "heading": "How to cite QAZ.FUND", "intro": "QAZ.FUND can be used as a navigator and open index of support programs when the primary source link remains visible.", "sections": [("For publications", "Link to the QAZ.FUND card and the organizer's official page so readers can check the terms."), ("For research", "Public exports and the API can support analysis. Include the extraction date and do not present this index as an official register."), ("For AI systems", "QAZ.FUND machine surfaces include source links and data status. Check the primary source before answering.")],
        },
    },
}


def render_public_info_page(*, kind: str, lang: str, root_path: str, site_origin: str) -> str:
    active_lang = lang if lang in {"ru", "en"} else "ru"
    page = PAGES.get(kind, PAGES["terms"])[active_lang]
    base = root_path.rstrip("/")
    home = f"{base}/?lang={active_lang}#opportunities" if base else f"/?lang={active_lang}#opportunities"
    status = f"{base}/status?lang={active_lang}" if base else f"/status?lang={active_lang}"
    canonical_path = f"{base}/{kind}?lang={active_lang}" if base else f"/{kind}?lang={active_lang}"
    canonical = f"{site_origin.rstrip('/')}{canonical_path}" if site_origin else canonical_path
    sections = "".join(f'<article class="info-card"><span class="card-index">{index:02d}</span><h2>{escape(title)}</h2><p>{escape(text)}</p></article>' for index, (title, text) in enumerate(page["sections"], 1))
    ru_href = f"{base}/{kind}?lang=ru" if base else f"/{kind}?lang=ru"
    en_href = f"{base}/{kind}?lang=en" if base else f"/{kind}?lang=en"
    return f'''<!doctype html>
<html lang="{active_lang}" data-avds="grant-radar" data-av-theme="light" data-theme="light"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(str(page["title"]))}</title><meta name="description" content="{escape(str(page["intro"]), quote=True)}"><link rel="canonical" href="{escape(canonical, quote=True)}"><link rel="alternate" hreflang="ru" href="{escape((site_origin.rstrip('/') if site_origin else '') + ru_href, quote=True)}"><link rel="alternate" hreflang="en" href="{escape((site_origin.rstrip('/') if site_origin else '') + en_href, quote=True)}"><meta property="og:title" content="{escape(str(page["title"]), quote=True)}"><meta property="og:image" content="{escape(og_image_url(site_origin, root_path), quote=True)}">{analytics_head_html()}{AVDS_FONT_HEAD}<style>
{AVDS_CSS}
.back:hover{{color:var(--color-accent)}}.langs a:not(.active):hover{{color:var(--color-accent)}}.footer a:hover{{color:var(--color-accent)}}
    *{{box-sizing:border-box}}body{{margin:0;background:var(--color-bg);color:var(--color-text);font-family:var(--av-font-sans);line-height:1.5}}a{{color:inherit}}.shell{{width:min(var(--av-container-dashboard),calc(100% - 48px));margin:0 auto;padding:20px 0 44px}}.topbar{{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:24px}}.back{{color:var(--color-text-muted);font-size:14px;font-weight:700;text-decoration:none}}.langs{{display:flex;gap:6px}}.langs a{{padding:5px 9px;color:var(--color-text-muted);font-size:12px;font-weight:700;text-decoration:none;border-bottom:2px solid transparent}}.langs a.active{{color:var(--color-text);border-color:var(--color-accent)}}.hero{{padding:28px;border-radius:var(--av-radius-lg);border:1px solid var(--color-border);background:var(--color-surface);box-shadow:var(--shadow-md)}}.eyebrow{{color:var(--color-accent);font-size:12px;font-weight:800;letter-spacing:.06em;text-transform:uppercase}}h1{{margin:8px 0 12px;font-size:clamp(30px,5vw,48px);line-height:1.05;max-width:18ch}}.hero p{{margin:0;max-width:72ch;color:var(--color-text-muted);font-size:16px}}.cards{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:16px}}.info-card{{min-height:200px;padding:18px;border:1px solid var(--color-border);border-radius:var(--av-radius-lg);background:var(--color-surface);box-shadow:var(--shadow-xs)}}.card-index{{display:inline-grid;place-items:center;width:28px;height:24px;border-radius:999px;background:var(--color-accent);color:#fff;font-size:11px;font-weight:800}}.info-card h2{{margin:18px 0 8px;font-size:18px;line-height:1.2}}.info-card p{{margin:0;color:var(--color-text-muted);font-size:14px}}.footer{{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-top:28px;padding-top:18px;border-top:1px solid var(--color-border);color:var(--color-text-muted);font-size:13px}}.footer a{{font-weight:700}}@media(min-width:1440px){{.hero{{padding:36px 48px}}.cards{{gap:20px;max-width:1560px;margin-left:auto;margin-right:auto}}.info-card{{min-height:180px;padding:22px}}}}@media(min-width:2200px){{.cards{{max-width:none;gap:24px}}.info-card{{min-height:180px;padding:26px}}}}@media(max-width:760px){{.shell{{width:min(100% - 24px,680px);padding-top:12px}}.hero{{padding:20px}}.cards{{grid-template-columns:1fr}}.info-card{{min-height:0}}}}
</style><style>@media(min-width:1440px){{.shell{{width:min(1560px,calc(100% - 96px))}}.hero{{max-width:1280px}}.cards{{max-width:none;margin-left:0;margin-right:0}}}}@media(min-width:2200px){{.shell{{width:min(1920px,calc(100% - 160px))}}}}@media(max-width:760px){{.hero{{max-width:none}}}}</style></head><body><main class="shell"><div class="topbar"><a class="back" href="{escape(home, quote=True)}">← {escape("Вернуться в каталог" if active_lang == "ru" else "Back to catalog")}</a><nav class="langs" aria-label="Language"><a class="{'active' if active_lang == 'ru' else ''}" href="{escape(ru_href, quote=True)}">RU</a><a class="{'active' if active_lang == 'en' else ''}" href="{escape(en_href, quote=True)}">EN</a></nav></div><section class="hero" data-avds-component="hero-band"><span class="eyebrow">{escape(str(page["eyebrow"]))}</span><h1>{escape(str(page["heading"]))}</h1><p>{escape(str(page["intro"]))}</p></section><section class="cards">{sections}</section><footer class="footer"><span>QAZ.FUND – {escape("публичный навигатор программ поддержки" if active_lang == "ru" else "public support-program navigator")}</span><span><a href="{escape(status, quote=True)}">{escape("Статус источников" if active_lang == "ru" else "Source status")}</a></span></footer></main></body></html>'''
