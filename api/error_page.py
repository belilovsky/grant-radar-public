"""Branded recovery page for human-facing route errors."""

from __future__ import annotations

from html import escape

from api.avds import AVDS_CSS, AVDS_FONT_HEAD


def _href(root_path: str, path: str, lang: str) -> str:
    base = root_path.rstrip("/")
    value = f"{base}{path}" if base else path
    separator = "&" if "?" in value else "?"
    return f"{value}{separator}lang={lang}"


def render_error_page(
    *,
    status_code: int,
    lang: str,
    root_path: str,
    title: str | None = None,
    message: str | None = None,
) -> str:
    """Render a short recovery route without exposing framework details."""

    active_lang = "en" if lang == "en" else "ru"
    copy = {
        "ru": {
            "eyebrow": "Маршрут не найден",
            "title": "Такой страницы нет",
            "message": (
                "Ссылка могла устареть или содержать ошибку. Откройте каталог и "
                "найдите программу по названию, источнику или условиям."
            ),
            "catalog": "Вернуться в каталог",
            "insights": "Открыть аналитику",
            "status": "Проверить статус данных",
            "hint": (
                "Если исчезла ранее доступная карточка, проверьте официальный "
                "источник: программа могла завершиться или сменить адрес."
            ),
        },
        "en": {
            "eyebrow": "Route not found",
            "title": "This page does not exist",
            "message": (
                "The link may be outdated or incorrect. Open the catalogue and "
                "search by programme, source or eligibility."
            ),
            "catalog": "Return to catalogue",
            "insights": "Open insights",
            "status": "Check data status",
            "hint": (
                "If a previously available record disappeared, check the official "
                "source: the programme may have closed or moved."
            ),
        },
    }[active_lang]
    page_title = title or copy["title"]
    page_message = message or copy["message"]
    catalog = _href(root_path, "/", active_lang)
    insights = _href(root_path, "/insights", active_lang)
    status = _href(root_path, "/status", active_lang)
    return f"""<!doctype html>
<html lang="{active_lang}" data-avds="grant-radar" data-av-theme="light" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <meta name="description" content="{escape(page_message, quote=True)}">
  <title>{escape(page_title)} – QAZ.FUND</title>
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
      min-height:100vh;
      margin:0;
      display:grid;
      place-items:center;
      padding:24px;
      background:
        radial-gradient(circle at 18% 8%,var(--brand-soft),transparent 32rem),
        var(--wash);
      color:var(--ink);
      font-family:var(--av-font-sans);
    }}
    main {{
      width:min(780px,100%);
      padding:clamp(28px,6vw,64px);
      border:1px solid var(--line);
      border-radius:calc(var(--av-radius-lg) + var(--av-radius-sm));
      background:var(--panel);
      box-shadow:var(--av-shadow-md);
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
    .hint {{
      margin:32px 0 0;
      padding:14px 16px;
      border-left:3px solid var(--brand);
      background:var(--brand-soft);
      color:var(--muted);
      font-size:12px;
      line-height:1.55;
    }}
    @media (max-width:540px) {{
      body {{ padding:10px; }}
      main {{ padding:28px 20px; }}
      .eyebrow {{ margin-top:38px; }}
      .actions {{ display:grid; }}
      .action {{ width:100%; }}
    }}
  </style>
</head>
<body>
  <main data-avds-component="StatePanel" data-avds-version="4.6.0">
    <div class="top">
      <a class="brand" href="{escape(catalog, quote=True)}">QAZ.FUND</a>
      <span class="code">{status_code}</span>
    </div>
    <div class="eyebrow">{escape(copy["eyebrow"])}</div>
    <h1>{escape(page_title)}</h1>
    <p class="lead">{escape(page_message)}</p>
    <nav class="actions" aria-label="{escape(copy["catalog"], quote=True)}">
      <a
        class="action primary primary-action"
        href="{escape(catalog, quote=True)}"
        data-avds-component="Button"
      >{escape(copy["catalog"])}</a>
      <a
        class="action"
        href="{escape(insights, quote=True)}"
        data-avds-component="Button"
      >{escape(copy["insights"])}</a>
      <a
        class="action"
        href="{escape(status, quote=True)}"
        data-avds-component="Button"
      >{escape(copy["status"])}</a>
    </nav>
    <p class="hint" data-avds-component="Alert">{escape(copy["hint"])}</p>
  </main>
</body>
</html>"""


__all__ = ["render_error_page"]
