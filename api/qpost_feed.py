"""Draft-only QPost editorial contract for QAZ.FUND opportunities."""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

from core.models import Opportunity

QPOST_TEMPLATES = ("grant_day", "deadline_7d", "deadline_2d", "weekly")


def _amount(item: Opportunity, lang: str) -> str:
    localized_amount = _localized_text(item, lang, "amount")
    if localized_amount:
        return localized_amount
    raw = item.raw if isinstance(item.raw, dict) else {}
    raw_amount = str(raw.get("amount_raw") or "").strip()
    if raw_amount:
        return raw_amount
    values = [
        value for value in (item.amount_min, item.amount_max) if value is not None
    ]
    if not values:
        return {"ru": "Не указана", "kk": "Көрсетілмеген", "en": "Not stated"}[lang]

    def display(value: Decimal) -> str:
        return f"{value:,.0f}".replace(",", " ")

    amount = "–".join(display(value) for value in values)
    return f"{amount} {item.currency}".strip()


def _deadline(item: Opportunity, lang: str) -> str:
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
    raw = item.raw if isinstance(item.raw, dict) else {}
    i18n = raw.get("i18n") if isinstance(raw.get("i18n"), dict) else {}
    localized = i18n.get(lang) if isinstance(i18n.get(lang), dict) else {}
    return localized.get(key)


def _localized_text(item: Opportunity, lang: str, key: str) -> str | None:
    value = _localized_value(item, lang, key)
    text = str(value or "").strip()
    return text or None


def _localized_list(item: Opportunity, lang: str, key: str) -> list[str]:
    value = _localized_value(item, lang, key)
    if not isinstance(value, list):
        return []
    return [str(entry).strip() for entry in value if str(entry).strip()]


def _campaign_url(base_url: str, item_id: str, *, lang: str, template: str) -> str:
    query = urlencode(
        {
            "lang": lang,
            "utm_source": "telegram",
            "utm_medium": "social",
            "utm_campaign": f"qazfund_{template}",
            "utm_content": item_id,
        }
    )
    return f"{base_url.rstrip('/')}/opportunity/{item_id}?{query}"


def _safety(item: Opportunity) -> dict[str, Any]:
    raw = item.raw if isinstance(item.raw, dict) else {}
    provenance = (
        raw.get("provenance") if isinstance(raw.get("provenance"), dict) else {}
    )
    readiness = (
        raw.get("decision_readiness")
        if isinstance(raw.get("decision_readiness"), dict)
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
    return {
        "id": item_id,
        "title": _localized_text(item, lang, "title") or item.title.strip(),
        "summary": _localized_text(item, lang, "summary") or item.summary.strip(),
        "audience": _audience(item, lang),
        "amount": _amount(item, lang),
        "deadline": item.deadline.isoformat() if item.deadline else None,
        "deadline_display": _deadline(item, lang),
        "application_steps": (
            _localized_list(item, lang, "application_steps") or _application_steps(lang)
        ),
        "highlights": _localized_list(item, lang, "highlights"),
        "social_title": _localized_text(item, lang, "social_title"),
        "amount_label": _localized_text(item, lang, "amount_label"),
        "steps_title": _localized_text(item, lang, "steps_title"),
        "canonical_url": _campaign_url(base_url, item_id, lang=lang, template=template),
        "source_url": str(item.source_url),
        "language": lang,
        "safety": _safety(item),
    }


def _single_body(
    source: dict[str, Any], *, template: str, lang: str
) -> tuple[str, str]:
    prefix = {
        "grant_day": {
            "ru": "Возможность дня",
            "kk": "Күн мүмкіндігі",
            "en": "Opportunity of the day",
        },
        "deadline_7d": {
            "ru": "Дедлайн через 7 дней",
            "kk": "Мерзімге 7 күн",
            "en": "Deadline in 7 days",
        },
        "deadline_2d": {
            "ru": "Дедлайн через 2 дня",
            "kk": "Мерзімге 2 күн",
            "en": "Deadline in 2 days",
        },
    }[template][lang]
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
    title = source.get("social_title") or f"{prefix}: {source['title']}"
    steps = "\n".join(
        f"{index}. {step}" for index, step in enumerate(source["application_steps"], 1)
    )
    highlights = "\n".join(f"• {entry}" for entry in source.get("highlights", []))
    sections = [
        source["summary"],
        f"{labels[0]}:\n{source['audience']}",
    ]
    if highlights:
        sections.append(f"{labels[4]}:\n{highlights}")
    amount_label = source.get("amount_label") or labels[1]
    sections.append(
        f"{amount_label}: {source['amount']}\n"
        f"{labels[2]}: {source['deadline_display']}"
    )
    steps_title = source.get("steps_title") or labels[3]
    sections.append(f"{steps_title}:\n{steps}")
    body = "\n\n".join(sections)
    return title, body[:4096]


def _weekly_body(
    sources: list[dict[str, Any]], *, period_key: str, lang: str
) -> tuple[str, str]:
    title = {
        "ru": f"Возможности недели · {period_key}",
        "kk": f"Апта мүмкіндіктері · {period_key}",
        "en": f"Opportunities of the week · {period_key}",
    }[lang]
    intro = {
        "ru": "Подборка QAZ.FUND для ручной редакторской проверки:",
        "kk": "Редактор қолмен тексеретін QAZ.FUND топтамасы:",
        "en": "A QAZ.FUND selection for manual editorial review:",
    }[lang]
    lines = [f"📌 {title}", "", intro, ""]
    for index, source in enumerate(sources, 1):
        lines.extend(
            [
                f"{index}. {source['title']}",
                f"{source['deadline_display']} · {source['amount']}",
                source["canonical_url"],
                "",
            ]
        )
    lines.append(
        {
            "ru": "Перед публикацией редактор сверяет условия и актуальность каждой карточки.",
            "kk": "Жариялар алдында редактор әр карточканың шарттары мен өзектілігін тексереді.",
            "en": "Before publication, an editor verifies every record and its current terms.",
        }[lang]
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
    ranked = sorted(
        opportunities,
        key=lambda item: (-item.score, item.deadline or date.max, str(item.id)),
    )
    if template.startswith("deadline_"):
        offset = 7 if template == "deadline_7d" else 2
        target = date.fromordinal(today.toordinal() + offset)
        selected = [item for item in ranked if item.deadline == target][:limit]
    else:
        selected = ranked[: max(1, limit)]

    candidates: list[dict[str, Any]] = []
    if template == "weekly" and selected:
        period = today.isocalendar()
        period_key = f"{period.year}-W{period.week:02d}"
        sources = [
            _source_item(item, base_url=base_url, lang=active_lang, template=template)
            for item in selected
        ]
        title, body = _weekly_body(sources, period_key=period_key, lang=active_lang)
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
            }
        )
    elif template != "weekly":
        if template == "grant_day":
            selected = selected[:1]
        for item in selected:
            source = _source_item(
                item, base_url=base_url, lang=active_lang, template=template
            )
            title, body = _single_body(source, template=template, lang=active_lang)
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
                }
            )

    return {
        "schema_version": "qazfund-qpost-drafts.v1",
        "publication_mode": "draft_only",
        "human_review_required": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "template": template,
        "state": "ready" if candidates else "no_candidates",
        "items": candidates,
    }


__all__ = ["QPOST_TEMPLATES", "build_qpost_draft_feed"]
