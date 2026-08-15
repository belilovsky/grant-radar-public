"""Local EdPol language evaluation for QAZ.FUND social copy."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

EDPOL_LANGUAGE_POLICY_URL = "https://edpol.pro/rules/editorial-language-policy.json"
EDPOL_LANGUAGE_POLICY_VERSION = "1.1.0"
EDPOL_TYPOGRAPHY_POLICY_URL = "https://edpol.pro/rules/typography-policy.json"
EDPOL_TYPOGRAPHY_POLICY_VERSION = "1.1.1"
QAZ_FUND_TELEGRAM_LINK_LABEL = "Открыть карточку и подать заявку"

_BLOCKED_PHRASES: dict[str, tuple[str, ...]] = {
    "generic-opportunity-framing": (
        "возможность дня",
        "данная программа",
        "данная возможность",
        "уникальная возможность",
        "предоставляет возможность",
        "открывает новые горизонты",
        "широкий спектр возможностей",
        "күн мүмкіндігі",
        "бұл бағдарлама",
        "бұл мүмкіндік",
        "бірегей мүмкіндік",
        "мүмкіндік береді",
        "жаңа мүмкіндіктер ашады",
        "opportunity of the day",
        "this programme",
        "this program",
        "this opportunity",
        "unique opportunity",
        "provides an opportunity",
        "opens new horizons",
        "wide range of opportunities",
    ),
    "empty-source-disclaimer": (
        "условия, сроки и порядок подачи опубликованы у организатора",
        "критерии участия нужно сверить на официальной странице программы",
        "перед подачей условия нужно проверить вручную",
        "актуальные условия уточняйте у организатора",
        "қатысу талаптарын бағдарламаның ресми парағынан тексеру керек",
        "өзекті шарттарды ұйымдастырушыдан тексеріңіз",
        "өтінім берер алдында шарттарды қолмен тексеру керек",
        "check eligibility on the programme's official page",
        "check eligibility on the program's official page",
        "verify current terms with the organiser",
        "verify current terms with the organizer",
        "check the terms manually before applying",
    ),
    "inflated-importance": (
        "играет ключевую роль",
        "имеет важное значение",
        "важно отметить",
        "стоит отметить",
        "в современном мире",
        "динамично развивающийся",
        "инновационное решение",
        "впечатляющие результаты",
        "маңызды рөл атқарады",
        "атап өту маңызды",
        "қазіргі әлемде",
        "инновациялық шешім",
        "әсерлі нәтижелер",
        "plays a key role",
        "it is important to note",
        "in today's world",
        "dynamic environment",
        "innovative solution",
        "impressive results",
    ),
    "mechanical-transition": (
        "таким образом",
        "в заключение",
        "подводя итог",
        "следует подчеркнуть",
        "нельзя не отметить",
        "осылайша",
        "қорытындылай келе",
        "атап өткен жөн",
        "thus",
        "in conclusion",
        "to sum up",
        "it should be emphasized",
    ),
}

_EMOJI_RE = re.compile(
    "[" "\U0001f1e6-\U0001f1ff" "\U0001f300-\U0001faff" "\u2600-\u27bf" "]"
)
_UNKNOWN_VALUE_RE = re.compile(
    r"\b(?:не\s+указан(?:о|а)?|неизвестно|уточняется|көрсетілмеген|"
    r"белгісіз|нақтылануда|not\s+(?:stated|specified)|unknown|to\s+be\s+confirmed)\b",
    re.IGNORECASE,
)
_EM_DASH_NAMED_ENTITY = "&" + "mdash;"
_EM_DASH_DECIMAL_ENTITY = "&#" + "8212;"
_URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)


def _normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def evaluate_social_copy(
    *,
    title: str,
    body_text: str,
    link_label: str = QAZ_FUND_TELEGRAM_LINK_LABEL,
    channel: str = "telegram",
) -> dict[str, Any]:
    """Return the exact local decision QPost must reproduce before publication."""

    title = str(title or "").strip()
    body = str(body_text or "").strip()
    channel = str(channel or "telegram").strip().lower()
    visible_text = "\n".join(part for part in (title, body, link_label) if part)
    normalized = _normalized(visible_text)
    findings: list[dict[str, str]] = []
    for finding_id, phrases in _BLOCKED_PHRASES.items():
        for phrase in phrases:
            if _normalized(phrase) in normalized:
                findings.append({"id": finding_id, "excerpt": phrase})
                break
    if _EMOJI_RE.search(visible_text):
        findings.append({"id": "decorative-emoji", "excerpt": "emoji"})
    if (
        "\u2014" in visible_text
        or _EM_DASH_NAMED_ENTITY in visible_text
        or _EM_DASH_DECIMAL_ENTITY in visible_text
    ):
        findings.append({"id": "typography-em-dash", "excerpt": "em dash"})
    first_body_line = next(
        (line.strip() for line in body.splitlines() if line.strip()), ""
    )
    if title and first_body_line and _normalized(title) == _normalized(first_body_line):
        findings.append({"id": "duplicate-title", "excerpt": first_body_line})
    placeholder = _UNKNOWN_VALUE_RE.search(visible_text)
    if placeholder:
        findings.append(
            {"id": "unknown-value-placeholder", "excerpt": placeholder.group(0)}
        )
    if channel == "threads":
        if len(visible_text) > 500:
            findings.append(
                {
                    "id": "threads-character-limit",
                    "excerpt": str(len(visible_text)),
                }
            )
        context = _URL_RE.sub("", body).strip()
        if len(_normalized(context)) < 80:
            findings.append(
                {"id": "threads-link-only-copy", "excerpt": "short context"}
            )
        urls = _URL_RE.findall(body)
        if urls:
            last_line = next(
                (line.strip() for line in reversed(body.splitlines()) if line.strip()),
                "",
            )
            if last_line != urls[-1]:
                findings.append({"id": "threads-link-placement", "excerpt": urls[-1]})
    fingerprint = hashlib.sha256(visible_text.encode("utf-8")).hexdigest()
    return {
        "contract": "edpol-editorial-language-decision-v1",
        "decision": "blocked" if findings else "pass",
        "policy_url": EDPOL_LANGUAGE_POLICY_URL,
        "policy_version": EDPOL_LANGUAGE_POLICY_VERSION,
        "typography_policy_url": EDPOL_TYPOGRAPHY_POLICY_URL,
        "typography_policy_version": EDPOL_TYPOGRAPHY_POLICY_VERSION,
        "channel": channel,
        "content_fingerprint": f"sha256:{fingerprint}",
        "finding_ids": [finding["id"] for finding in findings],
        "findings": findings,
        "evaluated_at": datetime.now(tz=timezone.utc).isoformat(),
        "raw_content_sent_to_edpol": False,
    }


__all__ = [
    "EDPOL_LANGUAGE_POLICY_URL",
    "EDPOL_LANGUAGE_POLICY_VERSION",
    "QAZ_FUND_TELEGRAM_LINK_LABEL",
    "evaluate_social_copy",
]
