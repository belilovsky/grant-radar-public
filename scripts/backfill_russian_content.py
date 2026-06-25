"""Backfill Russian localized content into opportunity raw payloads.

Usage:
    python -m scripts.backfill_russian_content
    python -m scripts.backfill_russian_content --limit 50
    python -m scripts.backfill_russian_content --force
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import urllib.parse
from collections.abc import Iterable
from copy import deepcopy
from datetime import datetime
from typing import Any, cast

import httpx
from sqlalchemy import select

from api import main as api_main
from api.opportunity_detail import build_opportunity_detail
from core.db import OpportunityRow, SqlRepository
from core.localization import raw_localization_target

_CYRILLIC_RE = re.compile(r"[А-Яа-яӘәҒғҚқҢңӨөҰұҮүҺһІіЁё]")
_DEFAULT_TIMEOUT = 20.0
_TRANSLATE_ENDPOINT = "https://translate.googleapis.com/translate_a/single"


def _string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _string_list(values: Iterable[Any]) -> list[str]:
    return [str(value).strip() for value in values if str(value).strip()]


def _contains_cyrillic(value: str) -> bool:
    return bool(_CYRILLIC_RE.search(value))


def _detail_sections_payload(detail: Any) -> list[dict[str, str]]:
    return [
        {"heading": section.heading.strip(), "text": section.text.strip()}
        for section in getattr(detail, "detail_sections", [])
        if section.text.strip()
    ]


def _detail_text_from_sections(sections: list[dict[str, str]]) -> str:
    blocks: list[str] = []
    for section in sections:
        heading = _string(section.get("heading"))
        text = _string(section.get("text"))
        if not text:
            continue
        blocks.append(f"{heading}\n{text}".strip() if heading else text)
    return "\n\n".join(blocks).strip()


class GoogleTranslateClient:
    def __init__(self, *, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout
        self._cache: dict[str, str] = {}

    def translate_text(self, text: str) -> str:
        normalized = _string(text)
        if not normalized or _contains_cyrillic(normalized):
            return normalized
        cached = self._cache.get(normalized)
        if cached is not None:
            return cached
        params = urllib.parse.urlencode(
            {
                "client": "gtx",
                "sl": "auto",
                "tl": "ru",
                "dt": "t",
                "q": normalized,
            }
        )
        response = httpx.get(
            f"{_TRANSLATE_ENDPOINT}?{params}",
            headers={"User-Agent": "grant-radar/0.1"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        parts = payload[0] if isinstance(payload, list) and payload else []
        translated = "".join(
            part[0]
            for part in parts
            if isinstance(part, list) and part and isinstance(part[0], str)
        ).strip()
        if not translated:
            raise RuntimeError(f"Empty translation payload for text: {normalized[:80]}")
        self._cache[normalized] = translated
        return translated

    def translate_list(self, values: Iterable[str]) -> list[str]:
        return [self.translate_text(value) for value in values if _string(value)]


async def _hydrate_detail_payload(row: OpportunityRow) -> dict[str, Any]:
    item = api_main._stored_opportunity(row)
    detail = await build_opportunity_detail(item, lang="en")
    payload: dict[str, Any] = {}
    sections = _detail_sections_payload(detail)
    if sections:
        payload["detail_sections"] = sections
        payload["detail_text"] = _string(
            detail.detail_text
        ) or _detail_text_from_sections(sections)
    if detail.detail_fetch_status:
        payload["detail_fetch_status"] = detail.detail_fetch_status
    payload["detail_excerpt_only"] = bool(detail.detail_excerpt_only)
    if isinstance(detail.detail_fetched_at, datetime):
        payload["detail_fetched_at"] = detail.detail_fetched_at.isoformat()
    return payload


async def _localize_row(
    row: OpportunityRow,
    *,
    translator: GoogleTranslateClient,
    force: bool,
    hydrate_detail: bool,
) -> tuple[bool, list[str]]:
    item = api_main._stored_opportunity(row)
    raw: dict[str, Any] = (
        cast(dict[str, Any], row.raw) if isinstance(row.raw, dict) else {}
    )
    updated_raw = deepcopy(raw)
    content_raw = raw_localization_target(updated_raw)
    i18n = dict(content_raw.get("i18n") or {})
    ru = dict(i18n.get("ru") or {})
    changed_fields: list[str] = []

    if hydrate_detail and (force or not content_raw.get("detail_sections")):
        detail_payload = await _hydrate_detail_payload(row)
        for key, value in detail_payload.items():
            if content_raw.get(key) != value:
                content_raw[key] = value
                changed_fields.append(key)

    if force or not _string(ru.get("title")):
        title_ru = translator.translate_text(item.title)
        if title_ru and ru.get("title") != title_ru:
            ru["title"] = title_ru
            changed_fields.append("i18n.ru.title")

    if item.summary and (force or not _string(ru.get("summary"))):
        summary_ru = translator.translate_text(item.summary)
        if summary_ru and ru.get("summary") != summary_ru:
            ru["summary"] = summary_ru
            changed_fields.append("i18n.ru.summary")

    if item.eligibility and (force or not ru.get("eligibility")):
        eligibility_ru = translator.translate_list(_string_list(item.eligibility))
        if eligibility_ru and ru.get("eligibility") != eligibility_ru:
            ru["eligibility"] = eligibility_ru
            changed_fields.append("i18n.ru.eligibility")

    status_note = _string(content_raw.get("status_note"))
    if status_note and (force or not _string(ru.get("status_note"))):
        status_note_ru = translator.translate_text(status_note)
        if status_note_ru and ru.get("status_note") != status_note_ru:
            ru["status_note"] = status_note_ru
            changed_fields.append("i18n.ru.status_note")

    detail_sections = content_raw.get("detail_sections")
    if isinstance(detail_sections, list) and (force or not ru.get("detail_sections")):
        translated_sections: list[dict[str, str]] = []
        for section in detail_sections:
            if not isinstance(section, dict):
                continue
            text = _string(section.get("text"))
            if not text:
                continue
            translated_sections.append(
                {
                    "heading": translator.translate_text(
                        _string(section.get("heading"))
                    ),
                    "text": translator.translate_text(text),
                }
            )
        if translated_sections and ru.get("detail_sections") != translated_sections:
            ru["detail_sections"] = translated_sections
            changed_fields.append("i18n.ru.detail_sections")
        translated_detail_text = _detail_text_from_sections(translated_sections)
        if translated_detail_text and ru.get("detail_text") != translated_detail_text:
            ru["detail_text"] = translated_detail_text
            changed_fields.append("i18n.ru.detail_text")

    if not changed_fields:
        return False, []

    i18n["ru"] = ru
    content_raw["i18n"] = i18n
    row.raw = cast(Any, updated_raw)
    return True, changed_fields


async def _run(args: argparse.Namespace) -> int:
    url = (
        args.url
        or os.environ.get("GRANT_RADAR_DB_URL")
        or os.environ.get("DATABASE_URL")
        or ""
    ).strip()
    if not url or url in {"memory", ":memory:"}:
        print(
            "error: GRANT_RADAR_DB_URL/DATABASE_URL is not set; pass --url or export it",
            file=sys.stderr,
        )
        return 2

    repo = SqlRepository(url)
    translator = GoogleTranslateClient(timeout=args.timeout)
    changed = 0
    scanned = 0

    with repo._Session() as session:  # noqa: SLF001 - operator script uses repo session.
        rows = list(session.scalars(select(OpportunityRow)).all())
        if not args.include_inactive:
            rows = [
                row
                for row in rows
                if api_main._is_active_item(api_main._stored_opportunity(row))
            ]
        rows.sort(key=lambda row: str(row.id))
        if args.offset:
            rows = rows[args.offset :]
        if args.limit:
            rows = rows[: args.limit]

        total = len(rows)
        for index, row in enumerate(rows, start=1):
            scanned += 1
            updated, fields = await _localize_row(
                row,
                translator=translator,
                force=args.force,
                hydrate_detail=not args.skip_detail,
            )
            if not updated:
                print(f"[{index}/{total}] skip {row.id}")
                continue
            changed += 1
            session.add(row)
            if args.dry_run:
                session.rollback()
            else:
                session.commit()
            print(f"[{index}/{total}] updated {row.id} -> {', '.join(fields)}")

    print(
        json.dumps(
            {
                "status": "ok",
                "scanned": scanned,
                "changed": changed,
                "dry_run": bool(args.dry_run),
            },
            ensure_ascii=False,
        )
    )
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Backfill Russian localized opportunity content."
    )
    parser.add_argument(
        "--url",
        default=None,
        help="Database URL (overrides $GRANT_RADAR_DB_URL / $DATABASE_URL).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Process at most N rows after filtering (0 = all).",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Skip the first N filtered rows.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=_DEFAULT_TIMEOUT,
        help="HTTP timeout for translation calls in seconds.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing Russian localized fields.",
    )
    parser.add_argument(
        "--include-inactive",
        action="store_true",
        help="Include retired/stale rows hidden from the live dashboard.",
    )
    parser.add_argument(
        "--skip-detail",
        action="store_true",
        help="Do not hydrate or translate detailed source excerpts.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute changes but roll them back before commit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
