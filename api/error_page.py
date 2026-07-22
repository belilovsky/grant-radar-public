"""Branded browser error pages for public QAZ.FUND routes."""

from __future__ import annotations

from html import escape

from api.avds import AVDS_CSS, AVDS_FONT_HEAD

COPY = {
    "ru": {
        "title": "Страница не найдена – QAZ.FUND",
        "eyebrow": "Ошибка 404",
        "heading": "Такой страницы нет",
        "text": (
            "Возможно, ссылка устарела или адрес введён с ошибкой. "
            "Вернитесь в каталог и продолжите поиск возможностей."
        ),
        "action": "Вернуться в каталог",
    },
    "en": {
        "title": "Page not found – QAZ.FUND",
        "eyebrow": "Error 404",
        "heading": "This page does not exist",
        "text": (
            "The link may be outdated or the address may be incorrect. "
            "Return to the catalog to continue exploring opportunities."
        ),
        "action": "Back to catalog",
    },
}


def render_not_found_page(*, lang: str, root_path: str = "") -> str:
    """Render a concise noindex 404 page for browser navigation."""

    active_lang = lang if lang in COPY else "ru"
    copy = COPY[active_lang]
    base = root_path.rstrip("/")
    catalog_href = f"{base}/?lang={active_lang}" if base else f"/?lang={active_lang}"
    return f"""<!doctype html>
<html lang="{active_lang}" data-avds="grant-radar" data-av-theme="light" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,follow">
  <meta name="description" content="{escape(copy["text"], quote=True)}">
  <title>{escape(copy["title"])}</title>
{AVDS_FONT_HEAD}
  <style>
{AVDS_CSS}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr auto;
      place-items: stretch;
      padding: 0;
      background: var(--color-bg);
      color: var(--color-text);
      font-family: var(--av-font-sans);
    }}
    header {{
      width: min(var(--av-container-dashboard), calc(100% - 48px));
      margin: 0 auto;
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
    main {{
      align-self: center;
      justify-self: stretch;
      width: min(var(--av-container-dashboard), calc(100% - 48px));
      margin: 0 auto;
      padding: 64px 0;
      border: 0;
      border-bottom: 1px solid var(--color-border-subtle);
      border-radius: 0;
      background: transparent;
      box-shadow: none;
    }}
    .eyebrow {{
      color: var(--color-accent);
      font-size: var(--av-text-sm);
      font-weight: 700;
    }}
    h1 {{
      margin: 8px 0 12px;
      font-size: 48px;
      line-height: 1.05;
    }}
    p {{
      max-width: 52ch;
      margin: 0;
      color: var(--color-text-muted);
      line-height: 1.65;
    }}
    .primary-action {{
      display: inline-flex;
      align-items: center;
      min-height: var(--av-control-height-md);
      margin-top: 24px;
      padding: 0 16px;
      border-radius: var(--av-radius-md);
      background: var(--color-accent);
      color: white;
      font-weight: 700;
      text-decoration: none;
    }}
    .primary-action:focus-visible {{ outline: 0; box-shadow: var(--color-focus-ring); }}
    @media (max-width: 640px) {{
      header,
      main {{ width: calc(100% - 24px); }}
      main {{ padding: 44px 0; }}
      h1 {{ font-size: 36px; }}
    }}
  </style>
</head>
<body>
  <header>
    <a class="brand" href="{escape(catalog_href, quote=True)}">QAZ.FUND</a>
  </header>
  <main>
    <span class="eyebrow">{escape(copy["eyebrow"])}</span>
    <h1>{escape(copy["heading"])}</h1>
    <p>{escape(copy["text"])}</p>
    <a class="primary-action" href="{escape(catalog_href, quote=True)}">{escape(copy["action"])}</a>
  </main>
</body>
</html>"""
