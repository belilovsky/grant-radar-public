"""Raster, fact-led Open Graph cards for individual QAZ.FUND programmes."""

from __future__ import annotations

import hashlib
import io
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from PIL import Image, ImageDraw, ImageFont, ImageOps

from api.branding import BRANDING_ASSET_DIR
from api.page_primitives import absolute_href as _absolute_href
from core.public_contract import OpportunityV1

OG_IMAGE_SIZE = (1200, 630)
_BRAND_BACKGROUND_PATH = (
    BRANDING_ASSET_DIR / "qaz-fund-ornamental-background-1920x1080.webp"
)
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
_SPACE_RE = re.compile(r"\s+")


def _clean_text(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "")).strip().replace("\u2014", "\u2013")


def opportunity_og_version(**fields: Any) -> str:
    """Return a stable content revision for crawler cache invalidation."""

    payload = json.dumps(
        fields,
        ensure_ascii=False,
        default=str,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def opportunity_og_image_url(
    site_origin: str,
    root_path: str,
    *,
    opportunity_id: str,
    lang: str,
    content_version: str,
) -> str:
    """Build one absolute, versioned Open Graph URL per programme and language."""

    base = root_path.rstrip("/")
    path = (
        f"{base}/opportunity/{opportunity_id}/og.png"
        if base
        else (f"/opportunity/{opportunity_id}/og.png")
    )
    return _absolute_href(
        site_origin,
        f"{path}?{urlencode({'lang': lang, 'v': content_version})}",
    )


@lru_cache(maxsize=1)
def _brand_background() -> Image.Image:
    with Image.open(_BRAND_BACKGROUND_PATH) as source:
        return ImageOps.fit(
            source.convert("RGB"),
            OG_IMAGE_SIZE,
            method=Image.Resampling.LANCZOS,
            centering=(0.72, 0.5),
        )


@lru_cache(maxsize=32)
def _font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    for path in _FONT_PATHS[weight]:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    raise RuntimeError("No Cyrillic-capable Open Graph font is available")


def _text_width(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont
) -> int:
    return int(draw.textlength(text, font=font))


def _truncate_to_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    font: ImageFont.FreeTypeFont,
    width: int,
) -> str:
    normalized = _clean_text(text)
    if _text_width(draw, normalized, font) <= width:
        return normalized
    marker = "…"
    clipped = normalized
    while clipped and _text_width(draw, clipped + marker, font) > width:
        clipped = clipped[:-1].rstrip()
    return (clipped.rstrip(" ,.;:") + marker) if clipped else marker


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    font: ImageFont.FreeTypeFont,
    width: int,
    max_lines: int,
) -> list[str]:
    words = _clean_text(text).split(" ")
    if not words:
        return []
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if not current or _text_width(draw, candidate, font) <= width:
            current = candidate
            continue
        lines.append(current)
        current = word
        if len(lines) == max_lines:
            break
    if len(lines) < max_lines and current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    consumed = " ".join(lines)
    source = _clean_text(text)
    if source.startswith(consumed) and len(consumed) < len(source):
        lines[-1] = _truncate_to_width(
            draw,
            lines[-1].rstrip(" ,.;:") + "…",
            font=font,
            width=width,
        )
    return lines


def _title_layout(
    draw: ImageDraw.ImageDraw,
    title: str,
    *,
    width: int,
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    for size in (56, 52, 48, 44, 40, 36):
        font = _font(size, "bold")
        lines = _wrap_text(draw, title, font=font, width=width, max_lines=3)
        if lines and not lines[-1].endswith("…"):
            return font, lines
    return _font(36, "bold"), _wrap_text(
        draw, title, font=_font(36, "bold"), width=width, max_lines=3
    )


def _localized(labels: dict[str, tuple[str, str, str]], key: str, lang: str) -> str:
    index = {"ru": 0, "kk": 1, "en": 2}.get(lang, 0)
    return labels[key][index]


def _deadline_text(item: OpportunityV1, lang: str) -> str | None:
    if item.deadline is not None:
        return (
            item.deadline.strftime("%d.%m.%Y")
            if lang in {"ru", "kk"}
            else item.deadline.isoformat()
        )
    if item.deadline_type == "rolling":
        return _localized(
            {
                "rolling": (
                    "Постоянный приём",
                    "Тұрақты қабылдау",
                    "Rolling intake",
                )
            },
            "rolling",
            lang,
        )
    return None


def _amount_text(item: OpportunityV1, lang: str) -> str | None:
    display = _clean_text(item.funding_amount.display)
    if display:
        return _clean_text(
            display.replace(
                "₸", {"ru": "тенге", "kk": "теңге", "en": "KZT"}.get(lang, "KZT")
            )
        )
    amounts = [
        value
        for value in (item.funding_amount.minimum, item.funding_amount.maximum)
        if value is not None
    ]
    if not amounts:
        return None
    rendered = "–".join(f"{value:,.0f}".replace(",", " ") for value in amounts)
    currency = _clean_text(item.funding_amount.currency)
    return f"{rendered} {currency}".strip()


def _format_text(item: OpportunityV1, lang: str) -> str | None:
    if not item.formats:
        return None
    labels = {
        "grant": ("Грант", "Грант", "Grant"),
        "reimbursement": ("Возмещение затрат", "Шығындарды өтеу", "Cost reimbursement"),
        "subsidy": ("Субсидия", "Субсидия", "Subsidy"),
        "preferential_finance": (
            "Льготное финансирование",
            "Жеңілдетілген қаржыландыру",
            "Preferential finance",
        ),
        "leasing": ("Лизинг", "Лизинг", "Leasing"),
        "loan_guarantee": ("Гарантия", "Кепілдік", "Guarantee"),
        "tax_benefit": ("Налоговая льгота", "Салық жеңілдігі", "Tax benefit"),
        "accelerator": ("Акселератор", "Акселератор", "Accelerator"),
        "in_kind_support": (
            "Нефинансовая поддержка",
            "Қаржылай емес қолдау",
            "In-kind support",
        ),
        "procurement": ("Закупка", "Сатып алу", "Procurement"),
        "scholarship": ("Стипендия", "Стипендия", "Scholarship"),
        "contest": ("Конкурс", "Байқау", "Competition"),
        "education_admission": ("Обучение", "Оқу", "Education"),
    }
    values = [
        labels[value][{"ru": 0, "kk": 1, "en": 2}.get(lang, 0)]
        for value in item.formats
        if value in labels
    ]
    return ", ".join(values[:2]) or None


def _facts(item: OpportunityV1, lang: str) -> list[tuple[str, str]]:
    labels = {
        "amount": ("Поддержка", "Қолдау", "Support"),
        "deadline": ("Срок", "Мерзім", "Deadline"),
        "format": ("Формат", "Формат", "Format"),
        "source": ("Источник", "Дереккөз", "Source"),
    }
    facts: list[tuple[str, str]] = []
    amount = _amount_text(item, lang)
    if amount:
        facts.append((_localized(labels, "amount", lang), amount))
    deadline = _deadline_text(item, lang)
    if deadline:
        facts.append((_localized(labels, "deadline", lang), deadline))
    format_text = _format_text(item, lang)
    if format_text:
        facts.append((_localized(labels, "format", lang), format_text))
    source = _clean_text(item.source.name)
    if source:
        facts.append((_localized(labels, "source", lang), source))
    return facts[:3]


def render_opportunity_og_png(item: OpportunityV1, *, lang: str = "ru") -> bytes:
    """Render one crawler-safe 1200×630 PNG using only approved QAZ.FUND art."""

    image = _brand_background().copy().convert("RGBA")
    draw = ImageDraw.Draw(image)
    left_panel_right = 715
    draw.rectangle((0, 0, left_panel_right, OG_IMAGE_SIZE[1]), fill="#00343B")
    draw.rectangle(
        (left_panel_right - 8, 0, left_panel_right, OG_IMAGE_SIZE[1]), fill="#08747B"
    )

    margin = 64
    brand_font = _font(25, "bold")
    label_font = _font(17, "bold")
    body_font = _font(21, "regular")
    draw.text((margin, 58), "QAZ.FUND", fill="#FFFDFC", font=brand_font)
    category = _localized(
        {
            "label": (
                "КАРТОЧКА ПРОГРАММЫ",
                "БАҒДАРЛАМА КАРТОЧКАСЫ",
                "PROGRAMME CARD",
            )
        },
        "label",
        lang,
    )
    draw.text((margin, 98), category, fill="#B9DDD8", font=label_font)

    title_font, title_lines = _title_layout(
        draw,
        _clean_text(item.title),
        width=left_panel_right - margin - 44,
    )
    title_y = 151
    line_height = int(title_font.size * 1.12)
    for index, line in enumerate(title_lines):
        draw.text(
            (margin, title_y + index * line_height),
            line,
            fill="#FFFDFC",
            font=title_font,
        )

    source_label = _localized(
        {"source": ("Источник", "Дереккөз", "Source")}, "source", lang
    )
    source = _truncate_to_width(
        draw,
        _clean_text(item.source.name),
        font=body_font,
        width=left_panel_right - margin - 44,
    )
    draw.text(
        (margin, 548),
        f"{source_label}: {source}",
        fill="#D9ECE9",
        font=body_font,
    )

    facts = _facts(item, lang)
    fact_x = 770
    fact_width = 365
    fact_height = 126
    fact_gap = 16
    fact_y = 102
    for index, (label, value) in enumerate(facts):
        y = fact_y + index * (fact_height + fact_gap)
        draw.rounded_rectangle(
            (fact_x, y, fact_x + fact_width, y + fact_height),
            radius=18,
            fill="#FFFDFC",
            outline="#B9DDD8",
            width=2,
        )
        draw.text((fact_x + 28, y + 23), label.upper(), fill="#4A7975", font=label_font)
        value_font = _font(26, "bold")
        lines = _wrap_text(
            draw,
            value,
            font=value_font,
            width=fact_width - 56,
            max_lines=2,
        )
        for line_index, line in enumerate(lines):
            draw.text(
                (fact_x + 28, y + 54 + line_index * 31),
                line,
                fill="#00343B",
                font=value_font,
            )

    output = io.BytesIO()
    image.convert("RGB").save(output, format="PNG", optimize=True)
    return output.getvalue()


__all__ = [
    "OG_IMAGE_SIZE",
    "opportunity_og_image_url",
    "opportunity_og_version",
    "render_opportunity_og_png",
]
