"""Daily change digest suitable for feeds and explicit Telegram delivery."""

from __future__ import annotations

from typing import Any


def daily_digest_payload(
    history: dict[str, Any],
    *,
    lang: str,
    limit: int = 12,
) -> dict[str, Any]:
    active_lang = "en" if lang == "en" else "ru"
    items_value = history.get("items")
    items = items_value if isinstance(items_value, list) else []
    selected = items[:limit]
    available = bool(history.get("available"))
    if not available:
        state = "collecting"
    elif selected:
        state = "ready"
    else:
        state = "no_changes"
    return {
        "schema_version": "qazfund-daily-digest.v1",
        "state": state,
        "language": active_lang,
        "period_from": history.get("period_from"),
        "period_to": history.get("period_to"),
        "created": int(history.get("created") or 0),
        "changed": int(history.get("changed") or 0),
        "items": selected,
        "delivery": {
            "automatic": False,
            "telegram_ready": True,
            "activation": "explicit_credentials_and_schedule_required",
        },
    }


def daily_digest_text(payload: dict[str, Any]) -> str:
    lang = "en" if payload.get("language") == "en" else "ru"
    state = str(payload.get("state") or "collecting")
    if lang == "ru":
        title = "QAZ.FUND – изменения за сутки"
        if state == "collecting":
            return (
                f"{title}\n\n"
                "Журнал изменений только включён. Первый достоверный выпуск "
                "появится после следующего обхода источников."
            )
        if state == "no_changes":
            return f"{title}\n\nНовых или содержательно изменённых карточек нет."
        created_label = "Новых"
        changed_label = "Изменено"
        source_label = "Открыть карточку"
        new_label = "Новая программа"
        updated_label = "Обновление"
    else:
        title = "QAZ.FUND – daily changes"
        if state == "collecting":
            return (
                f"{title}\n\n"
                "The change ledger has just been enabled. The first reliable "
                "edition will follow the next source run."
            )
        if state == "no_changes":
            return f"{title}\n\nNo new or semantically updated records."
        created_label = "New"
        changed_label = "Updated"
        source_label = "Open record"
        new_label = "New opportunity"
        updated_label = "Update"

    lines = [
        title,
        "",
        f"{created_label}: {int(payload.get('created') or 0)} · "
        f"{changed_label}: {int(payload.get('changed') or 0)}",
        "",
    ]
    items_value = payload.get("items")
    items = items_value if isinstance(items_value, list) else []
    for index, item in enumerate(items, 1):
        kind = new_label if str(item.get("change_type")) == "created" else updated_label
        lines.extend(
            [
                f"{index}. {item.get('title') or ''}",
                f"{kind} · {item.get('source', {}).get('name') or ''}",
                f"{source_label}: {item.get('public_page') or ''}",
                "",
            ]
        )
    return "\n".join(lines).strip()


__all__ = ["daily_digest_payload", "daily_digest_text"]
