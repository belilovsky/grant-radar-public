"""Shared public meta helpers for QAZ.FUND pages."""

from __future__ import annotations

import json
import os
import struct
import zlib

from api.page_primitives import absolute_href as _absolute_href

DEFAULT_GA4_ID = "G-9EF720PSER"
DEFAULT_YANDEX_METRICA_ID = "109803011"
DEFAULT_CLARITY_PROJECT_ID = "x5ualin2jv"
OG_FONT_FAMILY = "Arial, Helvetica, sans-serif"
OG_IMAGE_SVG = "\n".join(
    [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630"',
        'viewBox="0 0 1200 630">',
        "  <defs>",
        '    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">',
        '      <stop offset="0%" stop-color="#00343B"/>',
        '      <stop offset="100%" stop-color="#00464D"/>',
        "    </linearGradient>",
        '    <radialGradient id="glow" cx="25%" cy="25%" r="70%">',
        '      <stop offset="0%" stop-color="#F0C64D" stop-opacity="0.32"/>',
        '      <stop offset="100%" stop-color="#F0C64D" stop-opacity="0"/>',
        "    </radialGradient>",
        "  </defs>",
        '  <rect width="1200" height="630" fill="url(#bg)"/>',
        '  <rect width="1200" height="630" fill="url(#glow)"/>',
        '  <g fill="#FFFDFC">',
        (
            f'    <text x="88" y="156" font-family="{OG_FONT_FAMILY}" '
            'font-size="42" font-weight="600" opacity="0.92">'
        ),
        "      Kazakhstan support navigator",
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
        "      Open programs, source links and next steps",
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
            'fill="#F0C64D" fill-opacity="0.48"/>'
        ),
        (
            '    <rect x="30" y="94" width="170" height="74" rx="18" '
            'fill="#FFFDFC" fill-opacity="0.94"/>'
        ),
        (
            '    <rect x="30" y="190" width="170" height="18" rx="9" '
            'fill="#FFFDFC" fill-opacity="0.76"/>'
        ),
        (
            '    <rect x="30" y="224" width="118" height="18" rx="9" '
            'fill="#FFFDFC" fill-opacity="0.56"/>'
        ),
        (
            '    <rect x="30" y="282" width="170" height="54" rx="18" '
            'fill="#F0C64D" fill-opacity="0.56"/>'
        ),
        "  </g>",
        "</svg>",
    ]
)


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    """Return one standards-compliant PNG chunk without extra dependencies."""

    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


_OG_GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
}


def _build_og_image_png() -> bytes:
    """Create a crawler-safe raster social card without optional dependencies."""

    width, height = 1200, 630
    pixels = bytearray(width * height * 3)

    def put(x: int, y: int, color: tuple[int, int, int]) -> None:
        if not (0 <= x < width and 0 <= y < height):
            return
        offset = (y * width + x) * 3
        pixels[offset : offset + 3] = bytes(color)

    def rect(x: int, y: int, w: int, h: int, color: tuple[int, int, int]) -> None:
        for row in range(max(0, y), min(height, y + h)):
            start = (row * width + max(0, x)) * 3
            end = (row * width + min(width, x + w)) * 3
            pixels[start:end] = bytes(color) * max(0, min(width, x + w) - max(0, x))

    for y in range(height):
        for x in range(width):
            progress = (x + y * 0.42) / (width + height * 0.42)
            put(
                x,
                y,
                (
                    0,
                    int(52 + 18 * progress),
                    int(59 + 18 * progress),
                ),
            )

    rect(72, 72, 188, 10, (240, 198, 77))
    rect(72, 102, 320, 16, (217, 232, 229))

    def word(text: str, x: int, y: int, scale: int) -> None:
        cursor = x
        for character in text:
            if character == ".":
                rect(cursor + scale * 2, y + scale * 6, scale, scale, (255, 253, 252))
                cursor += scale * 3
                continue
            glyph = _OG_GLYPHS[character]
            for row, row_bits in enumerate(glyph):
                for column, bit in enumerate(row_bits):
                    if bit == "1":
                        rect(
                            cursor + column * scale,
                            y + row * scale,
                            scale,
                            scale,
                            (255, 253, 252),
                        )
            cursor += scale * 6

    word("QAZ.FUND", 72, 164, 16)
    rect(72, 340, 566, 14, (217, 232, 229))
    rect(72, 374, 462, 14, (138, 190, 186))
    rect(72, 422, 150, 44, (240, 198, 77))
    rect(238, 422, 196, 44, (0, 84, 91))
    rect(810, 72, 318, 486, (0, 45, 52))
    rect(844, 112, 172, 22, (240, 198, 77))
    rect(844, 170, 242, 108, (255, 253, 252))
    rect(870, 204, 190, 16, (0, 52, 59))
    rect(870, 236, 126, 14, (98, 132, 128))
    rect(844, 314, 242, 14, (138, 190, 186))
    rect(844, 348, 170, 14, (98, 132, 128))
    rect(844, 418, 242, 84, (0, 84, 91))
    rect(870, 448, 190, 14, (255, 242, 168))
    rect(870, 478, 134, 12, (138, 190, 186))

    raw = b"".join(
        b"\x00" + bytes(pixels[row * width * 3 : (row + 1) * width * 3])
        for row in range(height)
    )
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _png_chunk(b"IDAT", zlib.compress(raw, level=9))
        + _png_chunk(b"IEND", b"")
    )


OG_IMAGE_PNG = _build_og_image_png()


def _env_value(name: str, default: str) -> str:
    return os.environ.get(name, "").strip() or default


def og_image_url(site_origin: str, root_path: str = "") -> str:
    base = root_path.rstrip("/")
    path = f"{base}/og-image.png" if base else "/og-image.png"
    return _absolute_href(site_origin, path)


def analytics_head_html() -> str:
    ga4_id = _env_value("PUBLIC_GA4_MEASUREMENT_ID", DEFAULT_GA4_ID)
    yandex_id = _env_value("PUBLIC_YANDEX_METRICA_ID", DEFAULT_YANDEX_METRICA_ID)
    clarity_id = _env_value("PUBLIC_CLARITY_PROJECT_ID", DEFAULT_CLARITY_PROJECT_ID)
    loaders: list[str] = []
    if ga4_id:
        ga4_json = json.dumps(ga4_id).replace("<", "\\u003c")
        ga4_src_json = json.dumps(
            f"https://www.googletagmanager.com/gtag/js?id={ga4_id}"
        ).replace("<", "\\u003c")
        loaders.append(
            "window.dataLayer=window.dataLayer||[];"
            "window.gtag=window.gtag||function(){window.dataLayer.push(arguments);};"
            'window.gtag("js",new Date());'
            f'window.gtag("config",{ga4_json});'
            f"loadScript({ga4_src_json});"
        )
    if yandex_id:
        yandex_json = json.dumps(yandex_id).replace("<", "\\u003c")
        yandex_src_json = json.dumps(
            f"https://mc.yandex.ru/metrika/tag.js?id={yandex_id}"
        ).replace("<", "\\u003c")
        loaders.append(
            "window.ym=window.ym||function(){"
            "(window.ym.a=window.ym.a||[]).push(arguments);};"
            "window.ym.l=Date.now();"
            f"loadScript({yandex_src_json});"
            f'window.ym({yandex_json},"init",'
            "{ssr:true,webvisor:true,clickmap:true,"
            'ecommerce:"dataLayer",accurateTrackBounce:true,'
            "trackLinks:true});"
        )
    if clarity_id:
        clarity_src_json = json.dumps(
            f"https://www.clarity.ms/tag/{clarity_id}"
        ).replace("<", "\\u003c")
        loaders.append(
            "window.clarity=window.clarity||function(){"
            "(window.clarity.q=window.clarity.q||[]).push(arguments);};"
            f"loadScript({clarity_src_json});"
        )
    if not loaders:
        return ""
    loader_body = "".join(loaders)
    return f"""  <script>
  (() => {{
    let analyticsStarted = false;
    const loadScript = (src) => {{
      const script = document.createElement("script");
      script.async = true;
      script.src = src;
      document.head.appendChild(script);
    }};
    const startAnalytics = () => {{
      if (analyticsStarted) return;
      if (navigator.doNotTrack === "1" || navigator.globalPrivacyControl === true) return;
      analyticsStarted = true;
      {loader_body}
    }};
    ["pointerdown", "keydown", "touchstart"].forEach((eventName) => {{
      window.addEventListener(eventName, startAnalytics, {{ once: true, passive: true }});
    }});
    window.setTimeout(startAnalytics, 20000);
  }})();
  </script>"""
