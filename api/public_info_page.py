"""Public explanatory pages kept concise for people using the catalogue."""

from __future__ import annotations

from html import escape
from typing import cast

from api.avds import AVDS_CSS, AVDS_FONT_HEAD
from api.public_meta import analytics_head_html, og_image_url
from core.localization import normalize_content_lang

PAGES: dict[str, dict[str, dict[str, object]]] = {
    "terms": {
        "ru": {
            "title": "Условия использования – QAZ.FUND",
            "eyebrow": "Условия использования",
            "heading": "Как пользоваться QAZ.FUND",
            "intro": "QAZ.FUND помогает найти открытые программы поддержки, понять следующий шаг и перейти к условиям организатора.",
            "sections": [
                (
                    "Что делает сервис",
                    "Собирает открытые сведения, приводит их к единому виду и ведёт к первоисточнику. Каталог не заменяет правила конкурса или программы финансирования.",
                ),
                (
                    "Что проверить",
                    "Перед подачей проверьте право на участие, срок, сумму, документы и способ отправки заявки на странице организатора.",
                ),
                (
                    "Ответственность за решение",
                    "QAZ.FUND не выдаёт гранты, не принимает заявки и не гарантирует финансирование. Условия могут измениться после публикации карточки.",
                ),
            ],
        },
        "en": {
            "title": "Terms of use – QAZ.FUND",
            "eyebrow": "Terms of use",
            "heading": "How to use QAZ.FUND",
            "intro": "QAZ.FUND helps you find open support programs, understand the next step, and reach the organizer's terms.",
            "sections": [
                (
                    "What the service does",
                    "It gathers public information, presents it consistently, and links to the primary source. The catalog does not replace program rules.",
                ),
                (
                    "What to verify",
                    "Before applying, check eligibility, deadline, amount, documents, and submission method on the organizer's page.",
                ),
                (
                    "Decision responsibility",
                    "QAZ.FUND does not award grants, accept applications, or guarantee funding. Terms can change after a card is published.",
                ),
            ],
        },
        "kk": {
            "title": "Пайдалану шарттары – QAZ.FUND",
            "eyebrow": "Пайдалану шарттары",
            "heading": "QAZ.FUND қызметін қалай пайдалану керек",
            "intro": "QAZ.FUND ашық қолдау бағдарламаларын табуға, келесі қадамды түсінуге және ұйымдастырушының талаптарына өтуге көмектеседі.",
            "sections": [
                (
                    "Сервис не істейді",
                    "Ашық мәліметтерді жинап, бірізді түрде ұсынады және бастапқы дереккөзге апарады. Каталог конкурс немесе қаржыландыру бағдарламасының ережелерін алмастырмайды.",
                ),
                (
                    "Нені тексеру керек",
                    "Өтініш бермес бұрын ұйымдастырушының парақшасынан қатысу құқығын, мерзімді, соманы, құжаттарды және өтінім жіберу тәсілін тексеріңіз.",
                ),
                (
                    "Шешімге жауапкершілік",
                    "QAZ.FUND грант бермейді, өтініш қабылдамайды және қаржыландыруға кепілдік бермейді. Карточка жарияланғаннан кейін шарттар өзгеруі мүмкін.",
                ),
            ],
        },
    },
    "data-policy": {
        "ru": {
            "title": "Политика данных – QAZ.FUND",
            "eyebrow": "Политика данных",
            "heading": "Откуда берутся данные",
            "intro": "Показываем открытые сведения, которые можно сверить в первоисточнике, и отделяем их от навигационных подсказок.",
            "sections": [
                (
                    "Первичные источники",
                    "Карточка ведёт на страницу организатора. Там находятся окончательные условия, формы, сроки и контакты.",
                ),
                (
                    "Обновление и свежесть",
                    "Источники проверяются регулярно. Если сведения устарели или недоступны, это отражается в статусе источника.",
                ),
                (
                    "Публичность",
                    "Каталог не запрашивает документы и персональные данные и не берёт плату за доступ к спискам и ссылкам.",
                ),
            ],
        },
        "en": {
            "title": "Data policy – QAZ.FUND",
            "eyebrow": "Data policy",
            "heading": "Where the data comes from",
            "intro": "We show public information that can be checked in a primary source and separate it from navigation hints.",
            "sections": [
                (
                    "Primary sources",
                    "Every card links to the organizer's page, which contains the final terms, forms, deadlines, and contacts.",
                ),
                (
                    "Freshness",
                    "Sources are checked regularly. If information is stale or unavailable, the source status shows it.",
                ),
                (
                    "Public by design",
                    "The catalog does not ask for documents or personal data or charge for access to listings and links.",
                ),
            ],
        },
        "kk": {
            "title": "Деректер саясаты – QAZ.FUND",
            "eyebrow": "Деректер саясаты",
            "heading": "Деректер қайдан алынады",
            "intro": "Біз бастапқы дереккөзден тексеруге болатын ашық мәліметтерді көрсетіп, оларды навигациялық ұсыныстардан бөлек береміз.",
            "sections": [
                (
                    "Бастапқы дереккөздер",
                    "Әр карточка ұйымдастырушының парақшасына апарады. Соңғы шарттар, нысандар, мерзімдер мен байланыстар сол жерде көрсетіледі.",
                ),
                (
                    "Жаңарту және өзектілік",
                    "Дереккөздер тұрақты түрде тексеріледі. Мәлімет ескірсе немесе қолжетімсіз болса, бұл дереккөз мәртебесінде көрсетіледі.",
                ),
                (
                    "Ашықтық қағидаты",
                    "Каталог құжаттар мен жеке деректерді сұрамайды және тізімдер мен сілтемелерге қолжетімділік үшін ақы алмайды.",
                ),
            ],
        },
    },
    "attribution": {
        "ru": {
            "title": "Использование данных – QAZ.FUND",
            "eyebrow": "Использование данных",
            "heading": "Как ссылаться на QAZ.FUND",
            "intro": "QAZ.FUND можно использовать как навигатор и открытый индекс программ поддержки, если ссылка на первоисточник остаётся видимой.",
            "sections": [
                (
                    "Для публикаций",
                    "Ссылайтесь на карточку QAZ.FUND и официальную страницу организатора, чтобы читатель мог проверить условия.",
                ),
                (
                    "Для исследований",
                    "Открытые выгрузки и API подходят для анализа. Указывайте дату выгрузки и не выдавайте индекс за официальный реестр.",
                ),
                (
                    "Для ИИ-систем",
                    "Машинные поверхности QAZ.FUND содержат ссылки на источники и статусы. Перед ответом проверяйте первоисточник.",
                ),
            ],
        },
        "en": {
            "title": "Data attribution – QAZ.FUND",
            "eyebrow": "Data attribution",
            "heading": "How to cite QAZ.FUND",
            "intro": "QAZ.FUND can be used as a navigator and open index of support programs when the primary source link remains visible.",
            "sections": [
                (
                    "For publications",
                    "Link to the QAZ.FUND card and the organizer's official page so readers can check the terms.",
                ),
                (
                    "For research",
                    "Public exports and the API can support analysis. Include the extraction date and do not present this index as an official register.",
                ),
                (
                    "For AI systems",
                    "QAZ.FUND machine surfaces include source links and data status. Check the primary source before answering.",
                ),
            ],
        },
        "kk": {
            "title": "Деректерді пайдалану – QAZ.FUND",
            "eyebrow": "Деректерді пайдалану",
            "heading": "QAZ.FUND-қа қалай сілтеме жасау керек",
            "intro": "Бастапқы дереккөзге сілтеме көрініп тұрса, QAZ.FUND-ты навигатор және қолдау бағдарламаларының ашық индексі ретінде пайдалануға болады.",
            "sections": [
                (
                    "Жарияланымдар үшін",
                    "Оқырман шарттарды тексере алуы үшін QAZ.FUND карточкасына және ұйымдастырушының ресми парақшасына сілтеме жасаңыз.",
                ),
                (
                    "Зерттеулер үшін",
                    "Ашық экспорттар мен API талдауға жарайды. Экспорт күнін көрсетіп, бұл индексті ресми тізілім ретінде ұсынбаңыз.",
                ),
                (
                    "AI жүйелері үшін",
                    "QAZ.FUND машиналық беттерінде дереккөз сілтемелері мен деректер мәртебесі бар. Жауап бермес бұрын бастапқы дереккөзді тексеріңіз.",
                ),
            ],
        },
    },
}


def render_public_info_page(
    *, kind: str, lang: str, root_path: str, site_origin: str
) -> str:
    active_lang = normalize_content_lang(lang)
    page = PAGES.get(kind, PAGES["terms"])[active_lang]
    base = root_path.rstrip("/")
    home = (
        f"{base}/?lang={active_lang}#opportunities"
        if base
        else f"/?lang={active_lang}#opportunities"
    )
    status = (
        f"{base}/status?lang={active_lang}" if base else f"/status?lang={active_lang}"
    )
    canonical_path = (
        f"{base}/{kind}?lang={active_lang}" if base else f"/{kind}?lang={active_lang}"
    )
    canonical = (
        f"{site_origin.rstrip('/')}{canonical_path}" if site_origin else canonical_path
    )
    section_rows = cast(list[tuple[str, str]], page["sections"])
    sections = "".join(
        f'<article class="info-card"><span class="card-index">{index:02d}</span><h2>{escape(title)}</h2><p>{escape(text)}</p></article>'
        for index, (title, text) in enumerate(section_rows, 1)
    )
    ru_href = f"{base}/{kind}?lang=ru" if base else f"/{kind}?lang=ru"
    kk_href = f"{base}/{kind}?lang=kk" if base else f"/{kind}?lang=kk"
    en_href = f"{base}/{kind}?lang=en" if base else f"/{kind}?lang=en"
    back_label = {
        "ru": "Вернуться в каталог",
        "kk": "Каталогқа оралу",
        "en": "Back to catalog",
    }[active_lang]
    footer_label = {
        "ru": "публичный навигатор программ поддержки",
        "kk": "қолдау бағдарламаларының ашық навигаторы",
        "en": "public support-program navigator",
    }[active_lang]
    return f"""<!doctype html>
<html lang="{active_lang}" data-avds="grant-radar" data-av-theme="light" data-theme="light"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(str(page["title"]))}</title><meta name="description" content="{escape(str(page["intro"]), quote=True)}"><link rel="canonical" href="{escape(canonical, quote=True)}"><link rel="alternate" hreflang="ru" href="{escape((site_origin.rstrip('/') if site_origin else '') + ru_href, quote=True)}"><link rel="alternate" hreflang="kk" href="{escape((site_origin.rstrip('/') if site_origin else '') + kk_href, quote=True)}"><link rel="alternate" hreflang="en" href="{escape((site_origin.rstrip('/') if site_origin else '') + en_href, quote=True)}"><meta property="og:title" content="{escape(str(page["title"]), quote=True)}"><meta property="og:image" content="{escape(og_image_url(site_origin, root_path), quote=True)}">{analytics_head_html()}{AVDS_FONT_HEAD}<style>
{AVDS_CSS}
.back:hover{{color:var(--color-accent)}}.langs a:not(.active):hover{{color:var(--color-accent)}}.footer a:hover{{color:var(--color-accent)}}.shell{{min-height:auto!important;grid-template-rows:auto auto auto!important}}.info-layout{{align-self:start!important;min-height:0!important}}.hero{{height:auto!important;background:color-mix(in oklab,var(--color-surface),var(--color-accent-subtle) 28%)!important}}.cards{{height:auto!important;grid-template-rows:none!important}}.info-card{{min-height:0!important;background:var(--color-surface-raised)!important}}
    *{{box-sizing:border-box}}body{{margin:0;background:var(--color-bg);color:var(--color-text);font-family:var(--av-font-sans);line-height:1.5}}a{{color:inherit}}.shell{{width:min(var(--av-container-dashboard),calc(100% - 48px));min-height:100svh;margin:0 auto;padding:20px 0 44px;display:grid;grid-template-rows:auto minmax(0,1fr) auto;gap:18px}}.topbar{{display:flex;justify-content:space-between;align-items:center;gap:16px}}.back{{color:var(--color-text-muted);font-size:14px;font-weight:700;text-decoration:none}}.langs{{display:flex;gap:6px}}.langs a{{padding:5px 9px;color:var(--color-text-muted);font-size:12px;font-weight:700;text-decoration:none;border-bottom:2px solid transparent}}.langs a.active{{color:var(--color-text);border-color:var(--color-accent)}}.info-layout{{display:grid;gap:16px;align-self:stretch}}.hero{{padding:28px;border-radius:var(--av-radius-lg);border:1px solid var(--color-border);background:var(--color-surface);box-shadow:var(--shadow-md)}}.eyebrow{{color:var(--color-accent);font-size:12px;font-weight:800;letter-spacing:.06em;text-transform:uppercase}}h1{{margin:8px 0 12px;font-size:clamp(30px,5vw,48px);line-height:1.05;max-width:18ch}}.hero p{{margin:0;max-width:72ch;color:var(--color-text-muted);font-size:16px}}.cards{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}.info-card{{min-height:200px;padding:18px;border:1px solid var(--color-border);border-radius:var(--av-radius-lg);background:var(--color-surface);box-shadow:var(--shadow-xs)}}.card-index{{display:inline-grid;place-items:center;width:28px;height:24px;border-radius:999px;background:var(--color-accent);color:#fff;font-size:11px;font-weight:800}}.info-card h2{{margin:18px 0 8px;font-size:18px;line-height:1.2}}.info-card p{{margin:0;color:var(--color-text-muted);font-size:14px}}.footer{{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;padding-top:18px;border-top:1px solid var(--color-border);color:var(--color-text-muted);font-size:13px}}.footer a{{font-weight:700}}@media(min-width:1440px){{.shell{{width:min(1560px,calc(100% - 96px));gap:22px}}.info-layout{{grid-template-columns:minmax(520px,.9fr) minmax(560px,1.1fr);align-items:stretch;min-height:clamp(520px,calc(100svh - 154px),760px)}}.hero{{height:100%;display:grid;align-content:center;padding:36px 48px}}.cards{{height:100%;grid-template-columns:1fr;grid-template-rows:repeat(3,minmax(0,1fr));gap:16px}}.info-card{{min-height:0;padding:22px;display:grid;align-content:center}}}}@media(min-width:2200px){{.shell{{width:min(1920px,calc(100% - 160px))}}.info-layout{{grid-template-columns:minmax(680px,.88fr) minmax(720px,1.12fr);min-height:clamp(560px,calc(100svh - 164px),820px)}}.cards{{gap:20px}}.info-card{{padding:26px}}}}@media(max-width:760px){{.shell{{width:min(100% - 24px,680px);min-height:0;padding-top:12px}}.hero{{padding:20px}}.cards{{grid-template-columns:1fr}}.info-card{{min-height:0}}}}
</style></head><body><main class="shell"><div class="topbar"><a class="back" href="{escape(home, quote=True)}">← {escape(back_label)}</a><nav class="langs" aria-label="Language"><a class="{'active' if active_lang == 'ru' else ''}" href="{escape(ru_href, quote=True)}" lang="ru"{' aria-current="page"' if active_lang == 'ru' else ''}>RU</a><a class="{'active' if active_lang == 'kk' else ''}" href="{escape(kk_href, quote=True)}" lang="kk"{' aria-current="page"' if active_lang == 'kk' else ''}>ҚАЗ</a><a class="{'active' if active_lang == 'en' else ''}" href="{escape(en_href, quote=True)}" lang="en"{' aria-current="page"' if active_lang == 'en' else ''}>EN</a></nav></div><div class="info-layout"><section class="hero" data-avds-component="hero-band"><span class="eyebrow">{escape(str(page["eyebrow"]))}</span><h1>{escape(str(page["heading"]))}</h1><p>{escape(str(page["intro"]))}</p></section><section class="cards">{sections}</section></div><footer class="footer"><span>QAZ.FUND – {escape(footer_label)}</span><span><a href="{escape(status, quote=True)}">{escape({"ru": "Статус источников", "kk": "Дереккөз мәртебесі", "en": "Source status"}[active_lang])}</a></span></footer></main></body></html>"""
