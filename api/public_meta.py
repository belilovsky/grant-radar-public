"""Shared public meta helpers for QAZ.FUND pages."""

from __future__ import annotations

import os
from html import escape

DEFAULT_GA4_ID = "G-9EF720PSER"
DEFAULT_YANDEX_METRICA_ID = "109803011"
DEFAULT_CLARITY_PROJECT_ID = "x5ualin2jv"
OG_FONT_FAMILY = "'IBM Plex Sans', 'Inter', sans-serif"
OG_IMAGE_SVG = "\n".join(
    [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630"',
        'viewBox="0 0 1200 630">',
        "  <defs>",
        '    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">',
        '      <stop offset="0%" stop-color="#0f172a"/>',
        '      <stop offset="100%" stop-color="#1d4ed8"/>',
        "    </linearGradient>",
        '    <radialGradient id="glow" cx="25%" cy="25%" r="70%">',
        '      <stop offset="0%" stop-color="#22c55e" stop-opacity="0.32"/>',
        '      <stop offset="100%" stop-color="#22c55e" stop-opacity="0"/>',
        "    </radialGradient>",
        "  </defs>",
        '  <rect width="1200" height="630" fill="url(#bg)"/>',
        '  <rect width="1200" height="630" fill="url(#glow)"/>',
        '  <g fill="#f8fafc">',
        (
            f'    <text x="88" y="156" font-family="{OG_FONT_FAMILY}" '
            'font-size="42" font-weight="600" opacity="0.92">'
        ),
        "      Kazakhstan funding navigator",
        "    </text>",
        (
            f'    <text x="88" y="300" font-family="{OG_FONT_FAMILY}" '
            'font-size="118" font-weight="700">'
        ),
        "      QAZ.FUND",
        "    </text>",
        (
            f'    <text x="88" y="382" font-family="{OG_FONT_FAMILY}" '
            'font-size="36" font-weight="500" opacity="0.88">'
        ),
        "      Grants, subsidies, accelerators and support programs",
        "    </text>",
        (
            f'    <text x="88" y="442" font-family="{OG_FONT_FAMILY}" '
            'font-size="36" font-weight="500" opacity="0.88">'
        ),
        "      for Kazakhstan-focused teams and institutions",
        "    </text>",
        "  </g>",
        '  <g transform="translate(882 118)">',
        (
            '    <rect width="230" height="372" rx="28" '
            'fill="rgba(248,250,252,0.08)" '
            'stroke="rgba(248,250,252,0.22)"/>'
        ),
        (
            '    <rect x="30" y="36" width="170" height="24" rx="12" '
            'fill="#22c55e" fill-opacity="0.28"/>'
        ),
        (
            '    <rect x="30" y="94" width="170" height="74" rx="18" '
            'fill="#f8fafc" fill-opacity="0.94"/>'
        ),
        (
            '    <rect x="30" y="190" width="170" height="18" rx="9" '
            'fill="#f8fafc" fill-opacity="0.76"/>'
        ),
        (
            '    <rect x="30" y="224" width="118" height="18" rx="9" '
            'fill="#f8fafc" fill-opacity="0.56"/>'
        ),
        (
            '    <rect x="30" y="282" width="170" height="54" rx="18" '
            'fill="#1d4ed8" fill-opacity="0.56"/>'
        ),
        "  </g>",
        "</svg>",
    ]
)


def _env_value(name: str, default: str) -> str:
    return os.environ.get(name, "").strip() or default


def _absolute_href(origin: str, path: str) -> str:
    clean_origin = origin.rstrip("/")
    if path.startswith(("http://", "https://")):
        return path
    if not clean_origin:
        return path or "/"
    return f"{clean_origin}{path}"


def og_image_url(site_origin: str, root_path: str = "") -> str:
    base = root_path.rstrip("/")
    path = f"{base}/og-image.svg" if base else "/og-image.svg"
    return _absolute_href(site_origin, path)


def analytics_head_html() -> str:
    ga4_id = _env_value("PUBLIC_GA4_MEASUREMENT_ID", DEFAULT_GA4_ID)
    yandex_id = _env_value("PUBLIC_YANDEX_METRICA_ID", DEFAULT_YANDEX_METRICA_ID)
    clarity_id = _env_value("PUBLIC_CLARITY_PROJECT_ID", DEFAULT_CLARITY_PROJECT_ID)
    parts: list[str] = []
    if ga4_id:
        escaped_ga4 = escape(ga4_id, quote=True)
        ga4_src = "https://www.googletagmanager.com/gtag/js" f"?id={escaped_ga4}"
        ga4_bootstrap = (
            "window.dataLayer=window.dataLayer||[];"
            "function gtag(){dataLayer.push(arguments);}"
            'gtag("js",new Date());'
            f'gtag("config","{escaped_ga4}");'
        )
        parts.extend(
            [
                f'  <script async src="{ga4_src}"></script>',
                f"  <script>{ga4_bootstrap}</script>",
            ]
        )
    if yandex_id:
        escaped_yandex = escape(yandex_id, quote=True)
        yandex_bootstrap = (
            "  <script>(function(m,e,t,r,i,k,a){m[i]=m[i]||function(){"
            "(m[i].a=m[i].a||[]).push(arguments)};"
            "m[i].l=1*new Date();for(var j=0;j<document.scripts.length;j++){"
            "if(document.scripts[j].src===r){return;}}"
        )
        yandex_loader = (
            "k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,"
            "k.src=r,a.parentNode.insertBefore(k,a);}}"
        )
        yandex_src = "https://mc.yandex.ru/metrika/tag.js" f"?id={escaped_yandex}"
        yandex_init = (
            f'(window,document,"script","{yandex_src}","ym");'
            f'ym({escaped_yandex},"init",'
            "{ssr:true,webvisor:true,clickmap:true,"
            'ecommerce:"dataLayer",accurateTrackBounce:true,'
            "trackLinks:true});</script>"
        )
        parts.append((f"{yandex_bootstrap}{yandex_loader}" f"{yandex_init}"))
    if clarity_id:
        escaped_clarity = escape(clarity_id, quote=True)
        clarity_bootstrap = (
            "  <script>(function(c,l,a,r,i,t,y){c[a]=c[a]||function(){"
            "(c[a].q=c[a].q||[]).push(arguments)};"
            "t=l.createElement(r);t.async=1;"
            't.src="https://www.clarity.ms/tag/"+i;'
            "y=l.getElementsByTagName(r)[0];"
        )
        parts.append(
            (
                f"{clarity_bootstrap}"
                f"y.parentNode.insertBefore(t,y);}})"
                f'(window,document,"clarity","script","{escaped_clarity}");'
                "</script>"
            )
        )
    return "\n".join(parts)
