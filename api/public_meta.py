"""Shared public meta helpers for QAZ.FUND pages."""

from __future__ import annotations

import io
from functools import lru_cache
from pathlib import Path
from typing import TypedDict, cast

from PIL import Image, ImageDraw, ImageFont, ImageOps

from api.branding import BRANDING_ASSET_DIR
from api.page_primitives import absolute_href as _absolute_href

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
        '      <stop offset="0%" stop-color="#8FC8C1" stop-opacity="0.28"/>',
        '      <stop offset="100%" stop-color="#8FC8C1" stop-opacity="0"/>',
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
            'fill="#8FC8C1" fill-opacity="0.48"/>'
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
            'fill="#8FC8C1" fill-opacity="0.56"/>'
        ),
        "  </g>",
        "</svg>",
    ]
)


_OG_IMAGE_SIZE = (1200, 630)
_OG_BACKGROUND = BRANDING_ASSET_DIR / "qaz-fund-ornamental-background-1920x1080.webp"
_FONT_PATHS = {
    "regular": (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    ),
    "bold": (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    ),
}


class _SocialCopy(TypedDict):
    eyebrow: str
    title: tuple[str, str]
    subtitle: str
    steps: tuple[str, str, str]
    country: str
    alt: str


_OG_COPY: dict[str, _SocialCopy] = {
    "ru": {
        "eyebrow": "НАВИГАТОР ПОДДЕРЖКИ",
        "title": ("Найти. Проверить.", "Сравнить. Подготовить."),
        "subtitle": "Открытые программы, источники и сроки",
        "steps": ("Источник", "Срок", "Условия"),
        "country": "Казахстан",
        "alt": "QAZ.FUND: найти, проверить, сравнить и подготовить программу поддержки",
    },
    "kk": {
        "eyebrow": "ҚОЛДАУ НАВИГАТОРЫ",
        "title": ("Табу. Тексеру.", "Салыстыру. Дайындау."),
        "subtitle": "Ашық бағдарламалар, дереккөздер және мерзімдер",
        "steps": ("Дереккөз", "Мерзім", "Шарттар"),
        "country": "Қазақстан",
        "alt": "QAZ.FUND: қолдау бағдарламасын табу, тексеру, салыстыру және дайындау",
    },
    "en": {
        "eyebrow": "SUPPORT NAVIGATOR",
        "title": ("Find. Verify.", "Compare. Prepare."),
        "subtitle": "Open programmes, sources and deadlines",
        "steps": ("Source", "Deadline", "Terms"),
        "country": "Kazakhstan",
        "alt": "QAZ.FUND: find, verify, compare and prepare a support programme",
    },
}


@lru_cache(maxsize=16)
def _font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    for path in _FONT_PATHS[weight]:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return cast(ImageFont.FreeTypeFont, ImageFont.load_default(size=size))


@lru_cache(maxsize=3)
def social_image_png(lang: str = "ru") -> bytes:
    """Render one localized, fact-led social preview in approved brand art."""

    active_lang = lang if lang in _OG_COPY else "ru"
    copy = _OG_COPY[active_lang]
    with Image.open(_OG_BACKGROUND) as source:
        image = ImageOps.fit(
            source.convert("RGB"),
            _OG_IMAGE_SIZE,
            method=Image.Resampling.LANCZOS,
            centering=(0.72, 0.5),
        ).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((0, 0, 755, _OG_IMAGE_SIZE[1]), fill=(0, 52, 59, 255))
    draw.rectangle((755, 0, 763, _OG_IMAGE_SIZE[1]), fill=(8, 116, 123, 255))
    draw.rectangle((763, 0, 1200, 630), fill=(0, 52, 59, 86))

    draw.text((64, 52), "QAZ.FUND", fill="#FFFDFC", font=_font(27, "bold"))
    draw.text((64, 94), copy["eyebrow"], fill="#B9DDD8", font=_font(17, "bold"))
    title_font = _font(51, "bold")
    draw.text((64, 164), copy["title"][0], fill="#FFFDFC", font=title_font)
    draw.text((64, 226), copy["title"][1], fill="#FFFDFC", font=title_font)
    draw.text((64, 326), copy["subtitle"], fill="#D9ECE9", font=_font(23))
    draw.line((64, 550, 696, 550), fill=(185, 221, 216, 190), width=2)
    draw.text(
        (64, 570),
        f'{copy["country"]} · qaz.fund',
        fill="#D9ECE9",
        font=_font(18, "bold"),
    )

    card_x = 812
    for index, label in enumerate(copy["steps"], start=1):
        y = 86 + (index - 1) * 154
        draw.rounded_rectangle(
            (card_x, y, 1140, y + 124),
            radius=18,
            fill=(255, 253, 252, 244),
            outline=(185, 221, 216, 255),
            width=2,
        )
        draw.ellipse((card_x + 24, y + 33, card_x + 82, y + 91), fill="#00545B")
        number = str(index)
        number_font = _font(24, "bold")
        bbox = draw.textbbox((0, 0), number, font=number_font)
        draw.text(
            (
                card_x + 53 - (bbox[2] - bbox[0]) / 2,
                y + 62 - (bbox[3] - bbox[1]) / 2 - bbox[1],
            ),
            number,
            fill="#FFFDFC",
            font=number_font,
        )
        draw.text((card_x + 104, y + 45), label, fill="#00343B", font=_font(25, "bold"))

    output = io.BytesIO()
    image.convert("RGB").save(output, format="PNG", optimize=True)
    return output.getvalue()


OG_IMAGE_PNG = social_image_png("ru")


def social_image_alt(lang: str = "ru") -> str:
    active_lang = lang if lang in _OG_COPY else "ru"
    return str(_OG_COPY[active_lang]["alt"])


def og_image_url(site_origin: str, root_path: str = "", *, lang: str = "ru") -> str:
    base = root_path.rstrip("/")
    path = f"{base}/og-image.png" if base else "/og-image.png"
    active_lang = lang if lang in _OG_COPY else "ru"
    return _absolute_href(site_origin, f"{path}?lang={active_lang}")


def analytics_head_html() -> str:
    """Return no telemetry markup; QAZ.FUND public pages are tracker-free."""

    return ""
