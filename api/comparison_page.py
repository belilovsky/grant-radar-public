"""AVDS4 server-rendered comparison view for public opportunity cards."""

from __future__ import annotations

from html import escape
from typing import Any

from api.avds import AVDS_CSS, AVDS_FONT_HEAD
from api.comparison import comparison_copy, comparison_field_labels
from api.public_meta import analytics_head_html, og_image_url

_VALUE_LABELS: dict[str, dict[str, dict[str, str]]] = {
    "type": {
        "ru": {
            "grant": "Грант",
            "contest": "Конкурс",
            "accelerator": "Акселератор",
            "cloud_credit": "Облачный кредит",
            "tender": "Тендер",
            "fellowship": "Стипендия",
        },
        "kk": {
            "grant": "Грант",
            "contest": "Конкурс",
            "accelerator": "Акселератор",
            "cloud_credit": "Бұлттық кредит",
            "tender": "Тендер",
            "fellowship": "Стипендия",
        },
        "en": {
            "grant": "Grant",
            "contest": "Contest",
            "accelerator": "Accelerator",
            "cloud_credit": "Cloud credit",
            "tender": "Tender",
            "fellowship": "Fellowship",
        },
    },
    "lifecycle": {
        "ru": {
            "open": "Открыта",
            "closing_soon": "Скоро закрывается",
            "rolling": "Бессрочный приём",
            "forecast": "Анонс",
            "closed": "Закрыта",
            "awarded": "Результат опубликован",
        },
        "kk": {
            "open": "Ашық",
            "closing_soon": "Жабылуға жақын",
            "rolling": "Мерзімсіз қабылдау",
            "forecast": "Анонс",
            "closed": "Жабық",
            "awarded": "Нәтиже жарияланған",
        },
        "en": {
            "open": "Open",
            "closing_soon": "Closing soon",
            "rolling": "Rolling",
            "forecast": "Forecast",
            "closed": "Closed",
            "awarded": "Awarded",
        },
    },
}

_STATUS_LABELS = {
    "ru": {"ready": "Готово", "partial": "Частично", "insufficient": "Нужно ещё"},
    "kk": {"ready": "Дайын", "partial": "Ішінара", "insufficient": "Тағы керек"},
    "en": {"ready": "Ready", "partial": "Partial", "insufficient": "Need more"},
}


def _display(value: Any, *, field: str, lang: str) -> str:
    if isinstance(value, dict):
        return str(value.get("display") or "")
    if isinstance(value, list):
        return " · ".join(
            str(part).replace("_", " ").replace("-", " ").strip()
            for part in value
            if str(part).strip()
        )
    normalized = str(value or "")
    return _VALUE_LABELS.get(field, {}).get(lang, {}).get(normalized, normalized)


def render_comparison_page(
    *,
    payload: dict[str, Any],
    lang: str,
    root_path: str,
    site_origin: str,
) -> str:
    """Render the same bounded read model as ``/compare.json``."""

    copy = comparison_copy(lang)
    labels = comparison_field_labels(lang)
    base = root_path.rstrip("/")
    query = ",".join(str(value) for value in payload["selection"]["requested_ids"])
    suffix = f"?ids={query}&lang={lang}" if query else f"?lang={lang}"
    home = (
        f"{base}/?lang={lang}#opportunities" if base else f"/?lang={lang}#opportunities"
    )
    json_href = f"{base}/compare.json{suffix}" if base else f"/compare.json{suffix}"
    language_hrefs = {
        value: (
            f"{base}/compare{suffix.replace(f'lang={lang}', f'lang={value}')}"
            if base
            else f"/compare{suffix.replace(f'lang={lang}', f'lang={value}')}"
        )
        for value in ("kk", "ru", "en")
    }
    language_current = {
        value: ' aria-current="page"' if lang == value else ""
        for value in ("kk", "ru", "en")
    }
    canonical = (
        f"{site_origin.rstrip('/')}{base}/compare{suffix}"
        if site_origin
        else f"{base}/compare{suffix}"
    )
    cards = list(payload.get("cards") or [])
    status_value = str(payload.get("status") or "insufficient")
    status_label = _STATUS_LABELS.get(lang, _STATUS_LABELS["ru"]).get(
        status_value, status_value
    )
    fields = list(labels)
    header_cards = "".join(
        f'<th scope="col"><a href="{escape((base + "/opportunity/" if base else "/opportunity/") + str(card["id"]) + "?lang=" + lang, quote=True)}">{escape(str(card.get("title") or copy["unknown"]))}</a></th>'
        for card in cards
    )
    rows: list[str] = []
    for field in fields:
        cells = []
        for card in cards:
            raw_value = (card.get("fields") or {}).get(field)
            if field == "source":
                raw_value = card.get("source_label") or raw_value
            if field == "source_url" and str(raw_value or "").strip():
                cells.append(
                    '<td><a class="source-link" target="_blank" '
                    'rel="noopener noreferrer" href="'
                    f'{escape(str(raw_value), quote=True)}">'
                    f'{escape(copy["source_link"])}</a></td>'
                )
                continue
            value = _display(raw_value, field=field, lang=lang) or copy["unknown"]
            cells.append(f"<td>{escape(value)}</td>")
        rows.append(
            f'<tr><th scope="row">{escape(labels[field])}</th>{"".join(cells)}</tr>'
        )
    table_markup = (
        '<div class="table-wrap"><table class="compare-table" '
        'data-avds-component="comparison-table" data-avds-pattern="comparison">'
        f'<thead><tr><th scope="col">&nbsp;</th>{header_cards}</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
        if cards
        else f'<div class="empty" data-avds-component="empty-state">{escape(copy["not_enough"])}</div>'
    )
    warnings = " ".join(str(value) for value in payload.get("warnings") or [])
    warning_markup = (
        f'<aside class="notice" data-avds-component="evidence-summary">{escape(warnings)}</aside>'
        if warnings
        else ""
    )
    html_lang = escape(lang, quote=True)
    return f"""<!doctype html>
<html lang="{html_lang}" data-avds="grant-radar" data-av-theme="light" data-theme="light">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(copy["title"])}</title>
  <meta name="description" content="{escape(copy["intro"], quote=True)}">
  <link rel="canonical" href="{escape(canonical, quote=True)}">
  <link rel="alternate" type="application/json" href="{escape((site_origin.rstrip('/') if site_origin else '') + json_href, quote=True)}">
  <link rel="alternate" hreflang="kk" href="{escape((site_origin.rstrip('/') if site_origin else '') + language_hrefs['kk'], quote=True)}">
  <link rel="alternate" hreflang="ru" href="{escape((site_origin.rstrip('/') if site_origin else '') + language_hrefs['ru'], quote=True)}">
  <link rel="alternate" hreflang="en" href="{escape((site_origin.rstrip('/') if site_origin else '') + language_hrefs['en'], quote=True)}">
  <meta property="og:title" content="{escape(copy["title"], quote=True)}"><meta property="og:description" content="{escape(copy["intro"], quote=True)}">
  <meta property="og:image" content="{escape(og_image_url(site_origin, root_path), quote=True)}">
  {analytics_head_html()}{AVDS_FONT_HEAD}
  <style>
    {AVDS_CSS}
    *{{box-sizing:border-box}} body{{margin:0;background:var(--color-bg);color:var(--color-text);font-family:var(--av-font-sans);line-height:1.5}}
    .shell{{width:min(1920px,calc(100% - 48px));margin:0 auto;padding:20px 0 48px}} .topbar{{display:flex;justify-content:space-between;align-items:center;gap:18px;margin-bottom:16px}} .back{{font-size:13px;font-weight:750;text-decoration:none;color:var(--color-text-muted)}} .back:hover{{color:var(--color-accent)}} .langs{{display:flex;gap:6px}} .langs a{{padding:5px 8px;border-bottom:2px solid transparent;color:var(--color-text-muted);font-size:12px;font-weight:800;text-decoration:none}} .langs a.active{{color:var(--color-text);border-color:var(--color-accent)}}
    .hero{{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:24px;align-items:end;padding:28px;border:1px solid var(--color-border);border-radius:var(--av-radius-lg);background:linear-gradient(135deg,var(--color-surface),var(--color-accent-subtle));box-shadow:var(--shadow-md)}} .eyebrow{{color:var(--color-accent);font-size:12px;font-weight:800;letter-spacing:.06em;text-transform:uppercase}} h1{{margin:8px 0 10px;font-size:clamp(30px,4vw,48px);line-height:1.06}} .hero p{{max-width:70ch;margin:0;color:var(--color-text-muted);font-size:15px}} .hero-meta{{display:grid;grid-template-columns:repeat(2,minmax(120px,1fr));gap:10px}} .meta{{padding:13px;border:1px solid var(--color-border);border-radius:var(--av-radius-md);background:rgb(255 255 255 / .76)}} .meta strong{{display:block;font-size:25px;line-height:1}} .meta span{{display:block;margin-top:5px;color:var(--color-text-muted);font-size:11px;font-weight:750}}
    .section{{margin-top:22px;padding:22px;border:1px solid var(--color-border);border-radius:var(--av-radius-lg);background:var(--color-surface);box-shadow:var(--shadow-xs)}} .section-head{{display:flex;justify-content:space-between;align-items:end;gap:16px;margin-bottom:15px}} .section h2{{margin:0;font-size:23px;line-height:1.15}} .section-note{{margin:3px 0 0;color:var(--color-text-muted);font-size:13px}} .json-link{{color:var(--color-accent);font-size:12px;font-weight:750;text-decoration:none;white-space:nowrap}} .table-wrap{{overflow:auto;border:1px solid var(--color-border);border-radius:var(--av-radius-md)}} .compare-table{{width:100%;min-width:760px;border-collapse:collapse;font-size:13px}} .compare-table th,.compare-table td{{padding:13px 14px;border-bottom:1px solid var(--color-border-subtle);text-align:left;vertical-align:top}} .compare-table thead th{{background:var(--color-surface-subtle);font-size:13px}} .compare-table thead th:not(:first-child){{min-width:190px}} .compare-table thead a{{color:var(--color-text);font-size:14px;font-weight:800;text-decoration:none}} .compare-table tbody th{{width:150px;background:var(--color-surface-subtle);color:var(--color-text-muted);font-size:12px;font-weight:800}} .compare-table tbody tr:last-child th,.compare-table tbody tr:last-child td{{border-bottom:0}} .source-link{{color:var(--color-accent);font-weight:750;text-decoration:none}} .notice{{margin-top:14px;padding:12px 14px;border-left:4px solid var(--color-accent);border-radius:var(--av-radius-md);background:var(--color-accent-subtle);color:var(--color-text-muted);font-size:13px}} .empty{{padding:36px 20px;text-align:center;color:var(--color-text-muted)}} .footer{{display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;margin-top:22px;padding-top:16px;border-top:1px solid var(--color-border);color:var(--color-text-muted);font-size:12px}} .footer a{{font-weight:750}}
    @media(min-width:1800px){{.shell{{width:min(2080px,calc(100% - 128px))}} .hero{{grid-template-columns:minmax(0,1fr) 440px;padding:34px 38px}} .section{{padding:28px}} .compare-table{{font-size:14px}} .compare-table thead th:not(:first-child){{min-width:240px}}}}
    @media(max-width:760px){{.shell{{width:min(100% - 24px,680px);padding-top:12px}} .hero{{grid-template-columns:1fr;padding:20px}} .section{{padding:16px}} .section-head{{align-items:start;flex-direction:column}} .hero-meta{{grid-template-columns:repeat(2,minmax(0,1fr))}} .compare-table{{min-width:680px}}}}
  </style>
</head>
<body><main class="shell">
  <div class="topbar"><a class="back" href="{escape(home, quote=True)}">← {escape(copy["back"])}</a><nav class="langs" aria-label="Language"><a class="{'active' if lang == 'kk' else ''}" href="{escape(language_hrefs['kk'], quote=True)}" lang="kk"{language_current['kk']}>KAZ</a><a class="{'active' if lang == 'ru' else ''}" href="{escape(language_hrefs['ru'], quote=True)}" lang="ru"{language_current['ru']}>RU</a><a class="{'active' if lang == 'en' else ''}" href="{escape(language_hrefs['en'], quote=True)}" lang="en"{language_current['en']}>EN</a></nav></div>
  <section class="hero" data-avds-component="hero-band"><div><span class="eyebrow">QAZ.FUND</span><h1>{escape(copy["heading"])}</h1><p>{escape(copy["intro"])}</p></div><div class="hero-meta"><div class="meta"><strong>{len(cards)}</strong><span>{escape(copy["cards"])}</span></div><div class="meta"><strong>{escape(status_label)}</strong><span>{escape(copy["status"])}</span></div></div></section>
  <section class="section"><div class="section-head"><div><h2>{escape(copy["heading"])}</h2><p class="section-note">{escape(copy["warning"])}</p></div><a class="json-link" href="{escape(json_href, quote=True)}">JSON</a></div>{table_markup}{warning_markup}</section>
  <footer class="footer"><span>{escape(copy["footer"])}</span><a href="{escape(home, quote=True)}">{escape(copy["back"])}</a></footer>
</main></body></html>"""
