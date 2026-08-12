"""Branded recovery page for human-facing route errors."""

from __future__ import annotations

from html import escape

from api.avds import AVDS_CSS, AVDS_FONT_HEAD
from core.localization import normalize_content_lang

COPY = {
    "ru": {
        "title": "Страница не найдена – QAZ.FUND",
        "eyebrow": "Ошибка 404",
        "heading": "Такой страницы нет",
        "text": ("Ссылка устарела или адрес введён с ошибкой. Вернитесь в каталог."),
        "action": "Вернуться в каталог",
        "insights": "Открыть аналитику",
        "status": "Проверить статус данных",
    },
    "en": {
        "title": "Page not found – QAZ.FUND",
        "eyebrow": "Error 404",
        "heading": "This page does not exist",
        "text": (
            "The link is outdated or the address is incorrect. Return to the catalog."
        ),
        "action": "Back to catalog",
        "insights": "Open insights",
        "status": "Check data status",
    },
    "kk": {
        "title": "Бет табылмады – QAZ.FUND",
        "eyebrow": "404 қатесі",
        "heading": "Мұндай бет жоқ",
        "text": "Сілтеме ескірген немесе мекенжай қате енгізілген. Каталогқа оралыңыз.",
        "action": "Каталогқа оралу",
        "insights": "Талдауды ашу",
        "status": "Деректер мәртебесін тексеру",
    },
}


def render_not_found_page(*, lang: str, root_path: str = "") -> str:
    """Render a concise noindex 404 page for browser navigation."""

    active_lang = normalize_content_lang(lang)
    copy = COPY[active_lang]
    base = root_path.rstrip("/")
    catalog_href = f"{base}/?lang={active_lang}" if base else f"/?lang={active_lang}"
    insights_href = (
        f"{base}/insights?lang={active_lang}"
        if base
        else f"/insights?lang={active_lang}"
    )
    status_href = (
        f"{base}/status?lang={active_lang}" if base else f"/status?lang={active_lang}"
    )
    ru_href = f"{base}/does-not-exist?lang=ru" if base else "/does-not-exist?lang=ru"
    kk_href = f"{base}/does-not-exist?lang=kk" if base else "/does-not-exist?lang=kk"
    en_href = f"{base}/does-not-exist?lang=en" if base else "/does-not-exist?lang=en"
    ru_current = ' aria-current="page"' if active_lang == "ru" else ""
    kk_current = ' aria-current="page"' if active_lang == "kk" else ""
    en_current = ' aria-current="page"' if active_lang == "en" else ""
    page_title = str(copy["title"])
    page_message = str(copy["text"])
    return f"""<!doctype html>
<html lang="{active_lang}" data-avds="grant-radar" data-av-theme="light" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <meta name="description" content="{escape(page_message, quote=True)}">
  <title>{escape(page_title)}</title>
{AVDS_FONT_HEAD}
  <style>
{AVDS_CSS}
    :root {{
      color-scheme:light;
      --ink:var(--color-text);
      --muted:var(--color-text-muted);
      --line:var(--color-border);
      --panel:var(--color-surface);
      --wash:var(--color-bg);
      --brand:var(--color-accent);
      --brand-soft:var(--color-accent-subtle);
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin: 0;
      min-height: 0;
      display: block;
      padding: 0;
      background: var(--color-bg);
      color: var(--color-text);
      font-family: var(--av-font-sans);
    }}
    header {{
      width: min(var(--av-container-dashboard), calc(100% - 48px));
      margin: 0 auto;
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:16px;
    }}
    header {{
      padding: 22px 0 16px;
      border-bottom: 1px solid var(--color-border-subtle);
    }}
    .brand {{
      color: var(--color-text);
      font-size: var(--av-text-base);
      font-weight: 800;
      text-decoration: none;
    }}
    .lang-switch {{ display:inline-flex; align-items:center; gap:4px; }}
    .lang-switch a {{ min-width:34px; padding:6px 8px; border-bottom:2px solid transparent;
      color:var(--color-text-muted); text-align:center; text-decoration:none;
      font-size:12px; font-weight:700; }}
    .lang-switch a[aria-current="page"] {{
      border-bottom-color:var(--color-accent); color:var(--color-text);
    }}
    main {{
      width: min(var(--av-container-dashboard), calc(100% - 48px));
      margin: 0 auto;
      padding: 64px 0 72px;
      border: 0;
      border-bottom: 1px solid var(--color-border-subtle);
      border-radius: 0;
      background: transparent;
      box-shadow: none;
    }}
    .top {{
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:18px;
    }}
    .brand {{ color:var(--ink); font-size:14px; font-weight:850; text-decoration:none; }}
    .code {{ color:var(--muted); font:700 12px/1 var(--av-font-mono); }}
    .eyebrow {{
      margin-top:54px;
      color:var(--brand);
      font-size:11px;
      font-weight:850;
      letter-spacing:.1em;
      text-transform:uppercase;
    }}
    h1 {{
      max-width:12ch;
      margin:10px 0 14px;
      font-size:clamp(40px,8vw,72px);
      line-height:.98;
      letter-spacing:-.055em;
    }}
    .lead {{ max-width:58ch; margin:0; color:var(--muted); font-size:17px; line-height:1.6; }}
    .actions {{ margin-top:28px; display:flex; flex-wrap:wrap; gap:8px; }}
    .action {{
      min-height:var(--av-control-height-lg);
      padding:10px 14px;
      display:inline-flex;
      align-items:center;
      justify-content:center;
      border:1px solid var(--line);
      border-radius:var(--av-radius-md);
      color:var(--ink);
      font-size:13px;
      font-weight:800;
      text-decoration:none;
    }}
    .action.primary {{ border-color:var(--brand); background:var(--brand); color:white; }}
    .primary-action {{
      display:inline-flex;
      align-items:center;
      justify-content:center;
      min-height:var(--av-control-height-lg);
      margin-top:28px;
      padding:10px 14px;
      border:1px solid var(--brand);
      border-radius:var(--av-radius-md);
      background:var(--brand);
      color:white;
      font-size:13px;
      font-weight:800;
      text-decoration:none;
    }}
    .hint {{
      margin:32px 0 0;
      padding:14px 16px;
      border-left:3px solid var(--brand);
      background:var(--brand-soft);
      color:var(--muted);
      font-size:12px;
      line-height:1.55;
    }}
    .primary-action:focus-visible {{ outline: 0; box-shadow: var(--color-focus-ring); }}
    @media (min-width: 901px) {{
      main {{
        padding-top: 72px;
        padding-bottom: 80px;
      }}
    }}
    @media (min-width: 2200px) {{
      header,
      main {{ width: min(1920px, calc(100% - 160px)); }}
    }}
    @media (max-width: 640px) {{
      header,
      main {{ width: calc(100% - 24px); }}
      main {{ padding: 40px 0 48px; }}
      h1 {{ font-size: 36px; }}
    }}
    @media (max-width: 820px) {{
      .brand,
      .lang-switch a {{
        display: inline-flex;
        align-items: center;
        min-height: var(--av-control-height-lg);
      }}
      .lang-switch a {{ min-width: var(--av-control-height-lg); justify-content: center; }}
    }}
  </style>
</head>
<body>
  <header>
    <a class="brand" href="{escape(catalog_href, quote=True)}">QAZ.FUND</a>
    <nav class="lang-switch" aria-label="Language">
      <a href="{escape(kk_href, quote=True)}" lang="kk"{kk_current}>KAZ</a>
      <a href="{escape(ru_href, quote=True)}" lang="ru"{ru_current}>RU</a>
      <a href="{escape(en_href, quote=True)}" lang="en"{en_current}>EN</a>
    </nav>
  </header>
  <main data-avds-component="not-found">
    <span class="eyebrow">{escape(copy["eyebrow"])}</span>
    <h1>{escape(copy["heading"])}</h1>
    <p>{escape(copy["text"])}</p>
    <div class="actions">
      <a class="primary-action" href="{escape(catalog_href, quote=True)}">
        {escape(copy["action"])}
      </a>
      <a class="action" href="{escape(insights_href, quote=True)}">{escape(copy["insights"])}</a>
      <a class="action" href="{escape(status_href, quote=True)}">{escape(copy["status"])}</a>
    </div>
  </main>
</body>
</html>"""


__all__ = ["render_not_found_page"]
