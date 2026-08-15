"""Draft-only QPost editorial contract for QAZ.FUND opportunities."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, cast
from urllib.parse import urlencode

from api.edpol_language import (
    EDPOL_LANGUAGE_POLICY_URL,
    EDPOL_LANGUAGE_POLICY_VERSION,
    evaluate_social_copy,
)
from core.models import Opportunity
from core.opportunity_taxonomy import (
    TAXONOMY_VERSION,
    TEMPLATE_TRACKS,
    classify_opportunity,
    template_accepts_taxonomy,
)

QPOST_TEMPLATES = tuple(TEMPLATE_TRACKS)
_SINGLE_TEMPLATES = {
    "grant_day",
    "subsidy_day",
    "procurement_day",
    "finance_day",
    "education_day",
    "opportunity_day",
}

_CURRENCY_SYMBOLS = {
    "KZT": "₸",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "RUB": "₽",
    "CNY": "¥",
    "JPY": "¥",
}
_AMOUNT_SCALE = (
    r"(?:тыс(?:\.|яч[аи]?)?|млн|миллион(?:а|ов)?|млрд|миллиард(?:а|ов)?|"
    r"thousand|million|billion)"
)
_KAZAKHSTAN_TERMS = (
    r"\bkazakhstan\b",
    r"\bказахстан\w*\b",
    r"\bқазақстан\w*\b",
)
_GLOBAL_TERMS = (
    r"\bglobal\b",
    r"\bworldwide\b",
    r"\bany country\b",
    r"\ball countries\b",
    r"\bиз любой страны\b",
    r"\bвсе страны\b",
)
_CENTRAL_ASIA_TERMS = (
    r"\bcentral asia\b",
    r"\bцентральн\w+ ази\w*\b",
    r"\bорталық азия\b",
)


def _currency_symbols(value: str) -> str:
    """Render common monetary codes as compact symbols in social copy."""

    text = str(value or "")
    for code, symbol in _CURRENCY_SYMBOLS.items():
        text = re.sub(
            rf"\b{code}\s*(?=\d)",
            lambda _: symbol,
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            rf"(?P<amount>\d(?:[\d\s\u00a0.,]*\d)?(?:\s+{_AMOUNT_SCALE})?)\s*{code}\b",
            lambda match: f"{symbol}{match.group('amount').strip()}",
            text,
            flags=re.IGNORECASE,
        )
    return text


def _focus_text(item: Opportunity) -> str:
    raw = item.raw if isinstance(item.raw, dict) else {}
    values = [item.title, item.summary, *item.eligibility, *item.tags]
    values.append(json.dumps(raw, ensure_ascii=False, default=str))
    return " ".join(str(value) for value in values if value).casefold()


def _kazakhstan_focus_rank(item: Opportunity) -> int:
    """Prefer Kazakhstan, then worldwide access, then Central Asia."""

    text = _focus_text(item)
    if any(re.search(pattern, text) for pattern in _KAZAKHSTAN_TERMS):
        return 0
    if any(re.search(pattern, text) for pattern in _GLOBAL_TERMS):
        return 1
    if any(re.search(pattern, text) for pattern in _CENTRAL_ASIA_TERMS):
        return 2
    return 3


def _amount(item: Opportunity, lang: str) -> str:
    localized_amount = _localized_text(item, lang, "amount")
    if localized_amount:
        return _currency_symbols(localized_amount)
    raw = item.raw if isinstance(item.raw, dict) else {}
    raw_amount = str(raw.get("amount_raw") or "").strip()
    if raw_amount:
        return _currency_symbols(raw_amount)
    values = [
        value for value in (item.amount_min, item.amount_max) if value is not None
    ]
    if not values:
        return {"ru": "Не указана", "kk": "Көрсетілмеген", "en": "Not stated"}[lang]

    def display(value: Decimal) -> str:
        return f"{value:,.0f}".replace(",", " ")

    amount = "–".join(display(value) for value in values)
    symbol = _CURRENCY_SYMBOLS.get(str(item.currency).upper())
    return f"{symbol}{amount}" if symbol else f"{amount} {item.currency}".strip()


def _deadline(item: Opportunity, lang: str) -> str:
    localized_deadline = _localized_text(item, lang, "deadline_display")
    if localized_deadline:
        return localized_deadline
    if item.deadline is not None:
        return (
            item.deadline.strftime("%d.%m.%Y")
            if lang in {"ru", "kk"}
            else item.deadline.isoformat()
        )
    lifecycle = str(item.lifecycle or "").strip().lower()
    if lifecycle == "rolling":
        return {"ru": "Постоянный приём", "kk": "Тұрақты қабылдау", "en": "Rolling"}[
            lang
        ]
    return {"ru": "Не указан", "kk": "Көрсетілмеген", "en": "Not stated"}[lang]


def _audience(item: Opportunity, lang: str) -> str:
    values = _localized_list(item, lang, "eligibility") or [
        str(value).strip() for value in item.eligibility if str(value).strip()
    ]
    if values:
        audience = "; ".join(values[:3])
        if lang == "en" or re.search(r"[А-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі]", audience):
            return audience
    return {
        "ru": "Критерии участия нужно сверить на официальной странице программы",
        "kk": "Қатысу талаптарын бағдарламаның ресми парағынан тексеру керек",
        "en": "Check eligibility on the programme's official page",
    }[lang]


def _application_steps(lang: str) -> list[str]:
    return {
        "ru": [
            "Сверить критерии, срок и актуальные условия у организатора",
            "Подготовить краткое описание проекта, ожидаемый результат и бюджет",
            "Собрать документы и подать заявку через официальный канал",
        ],
        "kk": [
            "Талаптарды, мерзімді және өзекті шарттарды ұйымдастырушыдан тексеру",
            "Жобаның қысқаша сипаттамасын, күтілетін нәтижені және бюджетті дайындау",
            "Құжаттарды жинап, өтінімді ресми арна арқылы беру",
        ],
        "en": [
            "Verify eligibility, deadline and current terms with the organiser",
            "Prepare a concise project description, expected result and budget",
            "Collect the documents and apply through the official channel",
        ],
    }[lang]


def _localized_value(item: Opportunity, lang: str, key: str) -> Any:
    raw: dict[str, Any] = (
        cast(dict[str, Any], item.raw) if isinstance(item.raw, dict) else {}
    )
    i18n_value = raw.get("i18n")
    i18n: dict[str, Any] = (
        cast(dict[str, Any], i18n_value) if isinstance(i18n_value, dict) else {}
    )
    localized_value = i18n.get(lang)
    localized: dict[str, Any] = (
        cast(dict[str, Any], localized_value)
        if isinstance(localized_value, dict)
        else {}
    )
    return localized.get(key)


def _localized_text(item: Opportunity, lang: str, key: str) -> str | None:
    value = _localized_value(item, lang, key)
    text = str(value or "").strip()
    return _currency_symbols(text) or None


def _localized_list(item: Opportunity, lang: str, key: str) -> list[str]:
    value = _localized_value(item, lang, key)
    if not isinstance(value, list):
        return []
    return [
        _currency_symbols(str(entry).strip()) for entry in value if str(entry).strip()
    ]


def _campaign_url(
    base_url: str,
    item_id: str,
    *,
    lang: str,
    template: str,
    platform: str = "telegram",
) -> str:
    query_params: dict[str, str] = {"lang": lang, "utm_source": platform}
    if platform != "threads":
        query_params.update(
            {
                "utm_medium": "social",
                "utm_campaign": f"qazfund_{template}",
                "utm_content": item_id,
            }
        )
    query = urlencode(query_params)
    return f"{base_url.rstrip('/')}/opportunity/{item_id}?{query}"


def _safety(item: Opportunity) -> dict[str, Any]:
    raw: dict[str, Any] = (
        cast(dict[str, Any], item.raw) if isinstance(item.raw, dict) else {}
    )
    provenance_value = raw.get("provenance")
    provenance: dict[str, Any] = (
        cast(dict[str, Any], provenance_value)
        if isinstance(provenance_value, dict)
        else {}
    )
    readiness_value = raw.get("decision_readiness")
    readiness: dict[str, Any] = (
        cast(dict[str, Any], readiness_value)
        if isinstance(readiness_value, dict)
        else {}
    )
    evidence_state = str(provenance.get("evidence_state") or "unknown")
    source_grounded = (
        str(item.source_url).startswith("https://") and evidence_state == "sourced"
    )
    return {
        "status": (
            "source_grounded_review_required" if source_grounded else "review_required"
        ),
        "evidence_state": evidence_state,
        "decision_readiness": str(readiness.get("status") or "unknown"),
        "human_review_required": True,
    }


def _source_item(
    item: Opportunity, *, base_url: str, lang: str, template: str
) -> dict[str, Any]:
    item_id = str(item.id)
    taxonomy = classify_opportunity(item)
    return {
        "id": item_id,
        "title": _localized_text(item, lang, "title")
        or _currency_symbols(item.title.strip()),
        "summary": _localized_text(item, lang, "summary")
        or _currency_symbols(item.summary.strip()),
        "audience": _audience(item, lang),
        "amount": _amount(item, lang),
        "deadline": item.deadline.isoformat() if item.deadline else None,
        "deadline_display": _deadline(item, lang),
        "application_steps": (
            _localized_list(item, lang, "application_steps") or _application_steps(lang)
        ),
        "highlights": _localized_list(item, lang, "highlights"),
        "social_title": _localized_text(item, lang, "social_title"),
        "audience_label": _localized_text(item, lang, "audience_label"),
        "highlights_label": _localized_text(item, lang, "highlights_label"),
        "amount_label": _localized_text(item, lang, "amount_label"),
        "deadline_label": _localized_text(item, lang, "deadline_label"),
        "steps_title": _localized_text(item, lang, "steps_title"),
        "canonical_url": _campaign_url(
            base_url,
            item_id,
            lang=lang,
            template=template,
        ),
        "threads_url": _campaign_url(
            base_url,
            item_id,
            lang=lang,
            template=template,
            platform="threads",
        ),
        "source_url": str(item.source_url),
        "language": lang,
        "audience_focus": "kazakhstan",
        "focus_rank": _kazakhstan_focus_rank(item),
        "taxonomy": taxonomy,
        "safety": _safety(item),
    }


def _editorial_ready(item: Opportunity, lang: str) -> bool:
    """Only source-grounded, fully written records may enter the social feed."""

    steps = _localized_list(item, lang, "application_steps")
    audience = _localized_list(item, lang, "eligibility")
    return bool(
        _localized_text(item, lang, "social_title")
        and _localized_text(item, lang, "summary")
        and audience
        and len(steps) == 3
        and str(item.source_url).startswith("https://")
        and _safety(item)["evidence_state"] == "sourced"
    )


def _single_body(
    source: dict[str, Any], *, template: str, lang: str
) -> tuple[str, str]:
    labels = {
        "ru": (
            "Кому подходит",
            "Условия",
            "Дедлайн",
            "Как подготовиться",
            "Что внутри",
        ),
        "kk": (
            "Кімге арналған",
            "Шарттары",
            "Мерзім",
            "Қалай дайындалу керек",
            "Бағдарламада",
        ),
        "en": (
            "Who it is for",
            "Terms",
            "Deadline",
            "How to prepare",
            "What is included",
        ),
    }[lang]
    title = source["social_title"]
    steps = "\n".join(
        f"{index}. {step}" for index, step in enumerate(source["application_steps"], 1)
    )
    highlights = "\n".join(f"• {entry}" for entry in source.get("highlights", []))
    audience_label = source.get("audience_label") or labels[0]
    sections = [source["summary"], f"{audience_label}:\n{source['audience']}"]
    if highlights:
        highlights_label = source.get("highlights_label") or labels[4]
        sections.append(f"{highlights_label}:\n{highlights}")
    amount_label = source.get("amount_label") or labels[1]
    deadline_label = source.get("deadline_label") or labels[2]
    sections.append(
        f"{amount_label}: {source['amount']}\n"
        f"{deadline_label}: {source['deadline_display']}"
    )
    steps_title = source.get("steps_title") or labels[3]
    sections.append(f"{steps_title}:\n{steps}")
    body = "\n\n".join(sections)
    return title, body[:4096]


_UNKNOWN_SOCIAL_VALUES = {
    "не указан",
    "не указана",
    "көрсетілмеген",
    "not stated",
}


def _shorten_threads_text(value: str, limit: int) -> str:
    normalized = " ".join(str(value or "").split()).replace("\u2014", "\u2013")
    if len(normalized) <= limit:
        return normalized
    clipped = normalized[: max(1, limit - 1)].rstrip(" ,.;:")
    last_stop = max(clipped.rfind("."), clipped.rfind("!"), clipped.rfind("?"))
    if last_stop >= max(36, limit // 2):
        clipped = clipped[: last_stop + 1]
    return clipped.rstrip(" ,.;:") + "…"


def _known_social_value(value: Any) -> str | None:
    text = " ".join(str(value or "").split()).replace("\u2014", "\u2013")
    return text if text.casefold() not in _UNKNOWN_SOCIAL_VALUES else None


def _threads_body(source: dict[str, Any], *, lang: str) -> str:
    """Build a native Threads post, not a title-less link accompaniment."""

    labels = {
        "ru": ("Поддержка", "Срок"),
        "kk": ("Қолдау", "Мерзім"),
        "en": ("Support", "Deadline"),
    }[lang]
    title = _shorten_threads_text(str(source["social_title"]), 120)
    facts: list[str] = []
    amount = _known_social_value(source.get("amount"))
    if amount:
        facts.append(
            _shorten_threads_text(
                f"{source.get('amount_label') or labels[0]}: {amount}", 112
            )
        )
    deadline = _known_social_value(source.get("deadline_display"))
    if deadline:
        facts.append(
            _shorten_threads_text(
                f"{source.get('deadline_label') or labels[1]}: {deadline}", 112
            )
        )
    url = str(source["threads_url"])
    while True:
        facts_text = "\n".join(facts)
        fixed = "\n\n".join(part for part in (title, facts_text, url) if part)
        if len(fixed) <= 390 or not facts:
            break
        facts.pop()
    if len(fixed) > 450:
        title = _shorten_threads_text(title, max(64, 450 - len(url)))
        fixed = "\n\n".join(part for part in (title, facts_text, url) if part)
    summary_budget = max(0, 500 - len(fixed) - 4)
    summary = (
        _shorten_threads_text(str(source["summary"]), summary_budget)
        if summary_budget >= 2
        else ""
    )
    return "\n\n".join(part for part in (title, summary, facts_text, url) if part)


def _threads_draft(source: dict[str, Any], *, lang: str) -> dict[str, Any]:
    body = _threads_body(source, lang=lang)
    return {
        "body_text": body,
        "canonical_url": source["threads_url"],
        "character_count": len(body),
        "edpol": evaluate_social_copy(
            title="",
            body_text=body,
            link_label="",
            channel="threads",
        ),
    }


def _weekly_body(
    sources: list[dict[str, Any]], *, period_key: str, lang: str
) -> tuple[str, str]:
    title = {
        "ru": f"Что можно подать на этой неделе · {period_key}",
        "kk": f"Осы аптада неге өтінім беруге болады · {period_key}",
        "en": f"Applications to consider this week · {period_key}",
    }[lang]
    intro = {
        "ru": "Для заявителей из Казахстана: сроки, финансирование и первый шаг.",
        "kk": "Қазақстаннан өтінім берушілер үшін: мерзім, қаржыландыру және алғашқы қадам.",
        "en": "For applicants from Kazakhstan: deadlines, funding and the first step.",
    }[lang]
    lines = [intro, ""]
    for index, source in enumerate(sources, 1):
        lines.extend(
            [
                f"{index}. {source['title']}",
                f"{source['deadline_display']} · {source['amount']}",
                source["canonical_url"],
                "",
            ]
        )
    return title, "\n".join(lines).strip()[:4096]


def build_qpost_draft_feed(
    opportunities: list[Opportunity],
    *,
    base_url: str,
    lang: str,
    template: str,
    today: date,
    limit: int = 5,
) -> dict[str, Any]:
    """Build deterministic candidates that can only become QPost drafts."""
    active_lang = lang if lang in {"ru", "kk", "en"} else "ru"
    if template not in QPOST_TEMPLATES:
        raise ValueError(f"Unsupported QPost template: {template}")
    editorial = [
        item
        for item in opportunities
        if (
            _editorial_ready(item, active_lang)
            and _kazakhstan_focus_rank(item) < 3
            and classify_opportunity(item)["decision"] == "pass"
            and template_accepts_taxonomy(template, classify_opportunity(item))
        )
    ]
    ranked = sorted(
        editorial,
        key=lambda item: (
            _kazakhstan_focus_rank(item),
            -item.score,
            item.deadline or date.max,
            str(item.id),
        ),
    )
    if template.startswith("deadline_"):
        offset = 7 if template == "deadline_7d" else 2
        target = date.fromordinal(today.toordinal() + offset)
        selected = [item for item in ranked if item.deadline == target][:limit]
    else:
        selected = ranked[: max(1, limit)]

    candidates: list[dict[str, Any]] = []
    rejected_count = len(opportunities) - len(ranked)
    if template == "weekly" and selected:
        period = today.isocalendar()
        period_key = f"{period.year}-W{period.week:02d}"
        sources = [
            _source_item(item, base_url=base_url, lang=active_lang, template=template)
            for item in selected
        ]
        title, body = _weekly_body(sources, period_key=period_key, lang=active_lang)
        edpol = evaluate_social_copy(title=title, body_text=body)
        if edpol["decision"] != "pass":
            rejected_count += 1
            sources = []
        if sources:
            candidates.append(
                {
                    "idempotency_key": f"qazfund:weekly:{active_lang}:{period_key}",
                    "template": template,
                    "title": title,
                    "body_text": body,
                    "language": active_lang,
                    "canonical_url": (
                        f"{base_url.rstrip('/')}?utm_source=telegram"
                        "&utm_medium=social&utm_campaign=qazfund_weekly"
                    ),
                    "human_review_required": True,
                    "source_items": sources,
                    "edpol": edpol,
                }
            )
    elif template != "weekly":
        if template in _SINGLE_TEMPLATES:
            selected = selected[:1]
        for item in selected:
            source = _source_item(
                item, base_url=base_url, lang=active_lang, template=template
            )
            title, body = _single_body(source, template=template, lang=active_lang)
            edpol = evaluate_social_copy(title=title, body_text=body)
            threads = _threads_draft(source, lang=active_lang)
            if edpol["decision"] != "pass" or threads["edpol"]["decision"] != "pass":
                rejected_count += 1
                continue
            period_key = (
                item.deadline.isoformat() if item.deadline else today.isoformat()
            )
            candidates.append(
                {
                    "idempotency_key": f"qazfund:{template}:{active_lang}:{period_key}:{item.id}",
                    "template": template,
                    "title": title,
                    "body_text": body,
                    "language": active_lang,
                    "canonical_url": source["canonical_url"],
                    "human_review_required": True,
                    "source_items": [source],
                    "edpol": edpol,
                    "threads": threads,
                }
            )

    return {
        "schema_version": "qazfund-qpost-drafts.v3",
        "publication_mode": "draft_only",
        "human_review_required": True,
        "audience_focus": "kazakhstan",
        "currency_display": "symbols",
        "taxonomy_version": TAXONOMY_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "template": template,
        "edpol_policy": {
            "url": EDPOL_LANGUAGE_POLICY_URL,
            "version": EDPOL_LANGUAGE_POLICY_VERSION,
        },
        "rejected_count": rejected_count,
        "state": "ready" if candidates else "no_candidates",
        "items": candidates,
    }


__all__ = ["QPOST_TEMPLATES", "build_qpost_draft_feed"]
