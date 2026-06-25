"""Простое правила-based скоринг релевантности.

0.0..1.0. На первом этапе — ключевые слова + буст по региону и deadline.
Позже можно заменить на LLM-rerank.
"""

from __future__ import annotations

import re
from datetime import date

from core.geofit import (
    has_positive_geo_signal,
    is_excluded_for_kazakhstan_focus,
    is_low_confidence_for_kazakhstan_focus,
)
from core.models import Opportunity

THEMATIC_WEIGHTS = {
    "ai": 0.30,
    "artificial intelligence": 0.30,
    "machine learning": 0.25,
    "agrotech": 0.20,
    "agritech": 0.20,
    "agriculture": 0.18,
    "food systems": 0.18,
    "irrigation": 0.15,
    "livestock": 0.18,
    "vettech": 0.20,
    "veterinary": 0.20,
    "animal health": 0.20,
    "zoonotic": 0.18,
    "ecotech": 0.20,
    "cleantech": 0.20,
    "climate tech": 0.20,
    "environment": 0.18,
    "biodiversity": 0.18,
    "circular economy": 0.18,
    "waste management": 0.16,
    "water resilience": 0.16,
    "media": 0.20,
    "journalism": 0.20,
    "open data": 0.20,
    "govtech": 0.25,
    "governance": 0.20,
    "edtech": 0.20,
    "education": 0.15,
    "democracy": 0.15,
    "anti-corruption": 0.20,
    "transparency": 0.20,
    "data journalism": 0.25,
    "digital skills": 0.20,
    "stem": 0.15,
    "startup": 0.15,
    "accelerator": 0.15,
    "program": 0.10,
    "technology": 0.10,
    "it hub": 0.10,
    "innovation": 0.10,
    "innovation grant": 0.20,
    "commercialization": 0.15,
    "subsidy": 0.10,
    "sme": 0.10,
    "business support": 0.10,
    "domestic support": 0.10,
    "state program": 0.08,
    "reimbursement": 0.08,
    "preferential financing": 0.10,
    "leasing": 0.08,
    "tax benefit": 0.08,
    "loan guarantee": 0.08,
    "venture": 0.08,
    "private equity": 0.08,
    "export": 0.08,
    "industry": 0.08,
    "investment": 0.08,
    "civic": 0.15,
}

REGION_BOOST = {
    "kazakhstan": 0.20,
    "central asia": 0.20,
    "kz": 0.15,
    "cis": 0.10,
    "eurasia": 0.08,
}

SOURCE_BOOST = {
    "astana_hub": 0.15,
}


def _contains_keyword(text: str, keyword: str) -> bool:
    normalized_keyword = re.escape(keyword.lower()).replace(r"\ ", r"[\s_-]+")
    pattern = rf"(?<![a-z0-9]){normalized_keyword}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def score(opp: Opportunity, today: date | None = None) -> float:
    today = today or date.today()
    text = f"{opp.title} {opp.summary} {' '.join(opp.tags)}".lower()
    s = 0.0

    for kw, w in THEMATIC_WEIGHTS.items():
        if _contains_keyword(text, kw):
            s += w

    for kw, w in REGION_BOOST.items():
        if _contains_keyword(text, kw):
            s += w

    s += SOURCE_BOOST.get(opp.source, 0.0)

    if has_positive_geo_signal(opp):
        s += 0.05

    if is_excluded_for_kazakhstan_focus(opp):
        s -= 0.85
    elif is_low_confidence_for_kazakhstan_focus(opp):
        s -= 0.25

    # deadline urgency: больше за ближайшие дедлайны (но не просроченные)
    if opp.deadline:
        days = (opp.deadline - today).days
        if 0 <= days <= 14:
            s += 0.15
        elif 14 < days <= 60:
            s += 0.08
        elif days < 0:
            s -= 0.20

    return max(0.0, min(1.0, s))
