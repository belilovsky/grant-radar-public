"""Public terms, data-use and attribution pages."""

from __future__ import annotations

from html import escape

from api.avds import AVDS_CSS, AVDS_FONT_HEAD
from api.public_meta import analytics_head_html

POLICY_COPY: dict[str, dict[str, dict[str, str] | str]] = {
    "terms": {
        "ru_title": "Условия использования",
        "en_title": "Terms of use",
        "ru_intro": (
            "QAZ.FUND помогает находить программы поддержки и переходить к их "
            "официальным условиям. Сервис не выдаёт финансирование, не принимает "
            "заявки и не подтверждает право на участие."
        ),
        "en_intro": (
            "QAZ.FUND helps people discover support programmes and reach their "
            "official terms. The service does not award funding, accept applications "
            "or confirm eligibility."
        ),
        "ru_sections": {
            "Граница ответственности": (
                "Карточка предназначена для поиска и первичного анализа. Перед решением "
                "о подаче проверьте срок, сумму, требования, документы и способ подачи "
                "на странице организатора. При расхождении действует официальный источник."
            ),
            "Допустимое использование": (
                "Можно искать, сохранять, цитировать и передавать ссылки на публичные "
                "страницы. Нельзя выдавать QAZ.FUND за грантодателя, скрывать первоисточник "
                "или использовать данные для вводящих в заблуждение обещаний финансирования."
            ),
            "Исправления": (
                "Если запись устарела или содержит неточность, сообщите об этом через "
                "публичную форму обратной связи. В сообщении укажите адрес карточки и ссылку "
                "на актуальный официальный документ."
            ),
        },
        "en_sections": {
            "Scope and responsibility": (
                "A record supports discovery and initial review. Check the deadline, amount, "
                "requirements, documents and submission route on the provider's page before "
                "acting. The official source prevails if information differs."
            ),
            "Permitted use": (
                "You may search, save, cite and share public page links. Do not present "
                "QAZ.FUND as a funder, conceal the official source or use the data for "
                "misleading funding promises."
            ),
            "Corrections": (
                "Report outdated or inaccurate records through the public feedback form. "
                "Include the record URL and an authoritative current source."
            ),
        },
    },
    "data-policy": {
        "ru_title": "Политика данных",
        "en_title": "Data policy",
        "ru_intro": (
            "Публичный набор QAZ.FUND отделяет сведения источника от редакционной "
            "нормализации. Машинные интерфейсы публикуют происхождение, дату проверки "
            "источника, состояние доказательности и контрольную сумму содержания."
        ),
        "en_intro": (
            "The QAZ.FUND public dataset separates source evidence from editorial "
            "normalisation. Machine interfaces expose provenance, source-check time, "
            "evidence state and a content checksum."
        ),
        "ru_sections": {
            "Единый публичный набор": (
                "Сайт, программный интерфейс, выгрузки и материалы для публикаций "
                "формируются из одного публичного слоя. Служебные заметки и "
                "непроверенные заготовки в него не входят."
            ),
            "Степень подтверждения": (
                "Состояние «есть источник» означает наличие прямой публичной ссылки, но не "
                "независимую юридическую проверку. Поле уверенности оценивает полноту записи "
                "и опору на источник, а не вероятность одобрения заявки."
            ),
            "История и исправления": (
                "Изменения существенных полей получают новую контрольную сумму. Снимки и "
                "журнал наблюдений используются для аудита, исправления ошибок и объяснения "
                "расхождений между выпусками."
            ),
            "Персональные данные": (
                "Публичный каталог не требует учётной записи. Сохранённые карточки и этапы "
                "работы остаются в браузере пользователя. Серверные профили и рассылки не "
                "включаются без отдельного согласия, правил хранения и удаления данных."
            ),
        },
        "en_sections": {
            "One public dataset": (
                "The site, API, exports and media outputs are generated from one public "
                "layer. Internal notes and unreviewed drafts are excluded."
            ),
            "Evidence level": (
                "A sourced record has a direct public source link; this is not an independent "
                "legal verification. The confidence field describes record completeness and "
                "source evidence, not the chance of application approval."
            ),
            "History and corrections": (
                "Material field changes produce a new content checksum. Snapshots and "
                "observation history support audits, corrections and release comparisons."
            ),
            "Personal data": (
                "The public catalogue does not require an account. Saved records and workflow "
                "stages remain in the user's browser. Server-side profiles and alerts require "
                "separate consent, retention and deletion rules before launch."
            ),
        },
    },
    "attribution": {
        "ru_title": "Цитирование и повторное использование",
        "en_title": "Attribution and reuse",
        "ru_intro": (
            "QAZ.FUND рассчитан на цитирование в СМИ, исследованиях, блогах и ответах "
            "систем искусственного интеллекта. Цитата должна сохранять адрес карточки, "
            "официальный источник и дату проверки."
        ),
        "en_intro": (
            "QAZ.FUND is designed for citation by media, researchers, bloggers and AI "
            "systems. A citation should preserve the record URL, official source and "
            "source-check date."
        ),
        "ru_sections": {
            "Рекомендуемая ссылка": (
                "Название программы. QAZ.FUND, дата проверки. Адрес карточки. Официальный "
                "источник: название организации и её адрес."
            ),
            "Лицензионная граница": (
                "Собственные описания QAZ.FUND, структура программного интерфейса и схема "
                "данных доступны по лицензии CC BY 4.0 при указании источника. Тексты, "
                "документы, товарные знаки и изображения внешних организаций сохраняют "
                "условия соответствующих правообладателей."
            ),
            "Массовое использование": (
                "Для автоматической обработки используйте версионированный программный "
                "интерфейс и выгрузку NDJSON. Сохраняйте идентификатор, контрольную сумму, "
                "состояние доказательности и прямую ссылку на официальный источник."
            ),
        },
        "en_sections": {
            "Recommended citation": (
                "Programme title. QAZ.FUND, source-check date. Record URL. Official source: "
                "organisation name and URL."
            ),
            "Licence boundary": (
                "Original QAZ.FUND descriptions, API structure and data schema are available "
                "under CC BY 4.0 with attribution. Text, documents, trademarks and images from "
                "external organisations remain subject to their respective rights."
            ),
            "Bulk use": (
                "Use the versioned API and NDJSON export for automated processing. Preserve "
                "the stable identifier, content checksum, evidence state and direct official "
                "source URL."
            ),
        },
    },
}


def render_policy_page(
    page: str,
    *,
    lang: str,
    root_path: str,
    site_origin: str,
) -> str:
    active_lang = "en" if lang == "en" else "ru"
    copy = POLICY_COPY[page]
    title = str(copy[f"{active_lang}_title"])
    intro = str(copy[f"{active_lang}_intro"])
    sections = copy[f"{active_lang}_sections"]
    assert isinstance(sections, dict)
    base = root_path.rstrip("/")
    path = f"/{page}"
    canonical = f"{site_origin.rstrip('/')}{base}{path}?lang={active_lang}"
    ru_href = f"{base}{path}?lang=ru" if base else f"{path}?lang=ru"
    en_href = f"{base}{path}?lang=en" if base else f"{path}?lang=en"
    home = f"{base}/?lang={active_lang}" if base else f"/?lang={active_lang}"
    ru_current = ' aria-current="page"' if active_lang == "ru" else ""
    en_current = ' aria-current="page"' if active_lang == "en" else ""
    section_markup = "".join(
        f"<section><h2>{escape(heading)}</h2><p>{escape(body)}</p></section>"
        for heading, body in sections.items()
    )
    analytics = analytics_head_html()
    footer = (
        "Редакция от 26.07.2026"
        if active_lang == "ru"
        else "Version dated 26 July 2026"
    )
    policy_links = []
    for policy_slug in ("terms", "data-policy", "attribution"):
        policy_copy = POLICY_COPY[policy_slug]
        policy_title = str(policy_copy[f"{active_lang}_title"])
        policy_href = (
            f"{base}/{policy_slug}?lang={active_lang}"
            if base
            else f"/{policy_slug}?lang={active_lang}"
        )
        current = ' aria-current="page"' if policy_slug == page else ""
        policy_links.append(
            f'<a href="{escape(policy_href, quote=True)}"{current}>'
            f"{escape(policy_title)}</a>"
        )
    policy_navigation = "".join(policy_links)
    return f"""<!doctype html>
<html lang="{active_lang}" data-avds="grant-radar" data-av-theme="light" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} · QAZ.FUND</title>
  <meta name="description" content="{escape(intro, quote=True)}">
  <link rel="canonical" href="{escape(canonical, quote=True)}">
  <link rel="alternate" hreflang="ru" href="{escape(ru_href, quote=True)}">
  <link rel="alternate" hreflang="en" href="{escape(en_href, quote=True)}">
  {analytics}
  {AVDS_FONT_HEAD}
  <style>
    {AVDS_CSS}
    :root {{
      color-scheme: light;
      --bg:var(--color-bg);
      --panel:var(--color-surface);
      --panel-subtle:var(--color-bg-subtle);
      --line:var(--color-border);
      --muted:var(--color-text-muted);
      --ink:var(--color-text);
      --brand:var(--color-accent);
      --brand-soft:var(--color-accent-subtle);
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin:0;
      background:radial-gradient(circle at 12% 0%,var(--brand-soft),transparent 28rem),
        var(--bg);
      color:var(--ink);
      font-family:var(--av-font-sans);
    }}
    header {{
      width:min(var(--av-container-dashboard),calc(100% - 64px));
      margin:18px auto 0;
    }}
    article {{ width:min(960px,calc(100% - 64px)); margin:18px auto 44px; }}
    header {{
      position:sticky;
      top:12px;
      z-index:20;
      display:flex;
      justify-content:space-between;
      align-items:center;
      padding:10px 14px;
      border:1px solid color-mix(in oklab,var(--line),transparent 18%);
      border-radius:var(--av-radius-lg);
      background:color-mix(in oklab,var(--panel),transparent 7%);
      box-shadow:var(--av-shadow-sm);
      backdrop-filter:blur(16px);
    }}
    header a {{ color:var(--ink); text-decoration:none; font-weight:750; }}
    header nav {{ display:flex; gap:4px; }}
    header nav a {{
      display:inline-flex;
      min-width:34px;
      min-height:34px;
      align-items:center;
      justify-content:center;
      border-bottom:2px solid transparent;
      color:var(--muted);
      font-size:12px;
    }}
    header nav a[aria-current="page"] {{ border-bottom-color:var(--brand); color:var(--ink); }}
    article {{
      padding:clamp(28px, 5vw, 56px);
      border:1px solid var(--line);
      border-radius:24px;
      background:var(--panel);
      box-shadow:var(--av-shadow-md);
    }}
    h1 {{
      margin:0 0 18px;
      font-size:clamp(34px, 6vw, 58px);
      letter-spacing:-.035em;
      line-height:1.02;
    }}
    section {{ margin-top:30px; padding-top:26px; border-top:1px solid var(--line); }}
    h2 {{ margin:0 0 10px; font-size:23px; line-height:1.2; }}
    p {{ margin:0; color:var(--muted); font-size:17px; line-height:1.7; }}
    .intro {{ max-width:68ch; color:var(--ink); font-size:20px; }}
    footer {{
      margin-top:38px;
      padding-top:22px;
      border-top:1px solid var(--line);
      color:var(--muted);
      font-size:14px;
    }}
    .policy-nav {{
      margin-top:22px;
      display:flex;
      flex-wrap:wrap;
      gap:8px 16px;
    }}
    .policy-nav a {{
      color:var(--muted);
      font-size:13px;
      font-weight:700;
      text-decoration:none;
    }}
    .policy-nav a[aria-current="page"] {{ color:var(--ink); text-decoration:underline; }}
    a:focus-visible {{ outline:2px solid var(--brand); outline-offset:3px;
      border-radius:var(--av-radius-sm); }}
    @media (max-width:640px) {{
      header,article {{ width:calc(100% - 24px); }}
      header {{ top:8px; margin-top:14px; padding:8px 10px; }}
      header nav a {{
        min-width:var(--av-control-height-lg);
        min-height:var(--av-control-height-lg);
      }}
      article {{ padding:26px 20px; border-radius:20px; }}
      .intro {{ font-size:18px; }}
    }}
  </style>
</head>
<body>
  <header>
    <a href="{escape(home, quote=True)}">QAZ.FUND</a>
    <nav>
      <a href="{escape(ru_href, quote=True)}"{ru_current}>RU</a>
      <a href="{escape(en_href, quote=True)}"{en_current}>EN</a>
    </nav>
  </header>
  <article>
    <h1>{escape(title)}</h1>
    <p class="intro">{escape(intro)}</p>
    {section_markup}
    <footer>
      <div>{escape(footer)}</div>
      <nav class="policy-nav" aria-label="{escape(title, quote=True)}">
        {policy_navigation}
      </nav>
    </footer>
  </article>
</body>
</html>"""
