"""Backfill DeepSeek NLP enrichment into opportunity raw payloads.

The script is intentionally operator-controlled: it writes only with --apply and
keeps the current public title/summary untouched unless --apply-summary is set.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, cast

import httpx
from sqlalchemy import select

from api import main as api_main
from api.opportunity_detail import build_opportunity_detail
from core.db import OpportunityRow, SqlRepository
from core.localization import raw_localization_target
from core.nlp import extract_rule_based_entities, text_quality_flags

DEFAULT_DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"


def _string(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("DeepSeek response does not contain a JSON object")
    payload = json.loads(text[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("DeepSeek response JSON is not an object")
    return payload


def _normalize_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()][:12]


def normalize_deepseek_payload(payload: dict[str, Any]) -> dict[str, Any]:
    summary_ru = _string(payload.get("summary_ru"))
    entities = payload.get("entities")
    entities = entities if isinstance(entities, dict) else {}
    normalized_entities = {
        key: _normalize_list(entities.get(key))
        for key in (
            "funders",
            "programs",
            "countries",
            "regions",
            "sectors",
            "support_types",
            "audiences",
            "eligibility",
            "deadlines",
        )
    }
    normalized_entities = {
        key: value for key, value in normalized_entities.items() if value
    }
    flags = _normalize_list(payload.get("quality_flags"))
    result: dict[str, Any] = {
        "summary_ru": summary_ru,
        "entities": normalized_entities,
        "quality_flags": flags,
    }
    if not summary_ru:
        result.pop("summary_ru")
    return result


def _prompt_payload(item: Any, detail_text: str) -> list[dict[str, str]]:
    content = {
        "title": item.title,
        "summary": item.summary,
        "source": item.source,
        "source_url": str(item.source_url),
        "tags": item.tags,
        "eligibility": item.eligibility,
        "detail_text": detail_text[:6000],
    }
    return [
        {
            "role": "system",
            "content": (
                "You enrich grant/support opportunities for Kazakhstan users. "
                "Return strict JSON only. Do not invent facts. Use Russian for "
                "summary_ru. Extract concise entities from the provided text."
            ),
        },
        {
            "role": "user",
            "content": (
                "Return JSON with keys: summary_ru, entities, quality_flags. "
                "entities keys: funders, programs, countries, regions, sectors, "
                "support_types, audiences, eligibility, deadlines.\n\n"
                f"{json.dumps(content, ensure_ascii=False)}"
            ),
        },
    ]


async def call_deepseek(
    *,
    client: httpx.AsyncClient,
    api_key: str,
    model: str,
    url: str,
    item: Any,
    detail_text: str,
) -> dict[str, Any]:
    response = await client.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": _prompt_payload(item, detail_text),
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        },
    )
    response.raise_for_status()
    payload = response.json()
    content = (
        ((payload.get("choices") or [{}])[0].get("message") or {}).get("content")
        if isinstance(payload, dict)
        else ""
    )
    return normalize_deepseek_payload(_json_object(str(content or "")))


async def _row_detail_text(row: OpportunityRow) -> tuple[Any, str]:
    item = api_main._stored_opportunity(row)
    detail = await build_opportunity_detail(item, lang="en")
    return item, _string(getattr(detail, "detail_text", ""))


async def _run(args: argparse.Namespace) -> int:
    db_url = (
        args.url
        or os.environ.get("GRANT_RADAR_DB_URL")
        or os.environ.get("DATABASE_URL")
        or ""
    ).strip()
    if not db_url or db_url in {"memory", ":memory:"}:
        print("error: database URL is required", file=sys.stderr)
        return 2

    api_key = (args.api_key or os.environ.get("DEEPSEEK_API_KEY") or "").strip()
    if not api_key and not args.no_provider:
        print(
            "error: DEEPSEEK_API_KEY is not set; use --no-provider for heuristic run",
            file=sys.stderr,
        )
        return 2

    repo = SqlRepository(db_url)
    changed = 0
    scanned = 0

    with repo._Session() as session:  # noqa: SLF001 - operator script.
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

        async with httpx.AsyncClient(timeout=args.timeout) as client:
            for index, row in enumerate(rows, start=1):
                scanned += 1
                item, detail_text = await _row_detail_text(row)
                heuristic_entities = extract_rule_based_entities(
                    title=item.title,
                    summary=item.summary,
                    tags=item.tags,
                    detail_text=detail_text,
                )
                heuristic_flags = text_quality_flags(
                    title=item.title,
                    summary=item.summary,
                    lang="ru",
                )
                if args.no_provider:
                    enrichment = {
                        "entities": heuristic_entities,
                        "quality_flags": heuristic_flags,
                    }
                else:
                    enrichment = await call_deepseek(
                        client=client,
                        api_key=api_key,
                        model=args.model,
                        url=args.endpoint,
                        item=item,
                        detail_text=detail_text,
                    )
                    merged_entities: dict[str, list[str]] = dict(heuristic_entities)
                    provider_entities = enrichment.get("entities")
                    if isinstance(provider_entities, dict):
                        merged_entities.update(
                            cast(dict[str, list[str]], provider_entities)
                        )
                    enrichment["entities"] = merged_entities
                    provider_flags = enrichment.get("quality_flags")
                    provider_flag_list = (
                        cast(list[str], provider_flags)
                        if isinstance(provider_flags, list)
                        else []
                    )
                    enrichment["quality_flags"] = sorted(
                        set([*heuristic_flags, *provider_flag_list])
                    )

                row_raw: dict[str, Any] = (
                    cast(dict[str, Any], row.raw) if isinstance(row.raw, dict) else {}
                )
                updated_raw = deepcopy(row_raw)
                target = raw_localization_target(updated_raw)
                target["nlp"] = {
                    "provider": "heuristic" if args.no_provider else "deepseek",
                    "model": None if args.no_provider else args.model,
                    "enriched_at": datetime.now(timezone.utc).isoformat(),
                    **enrichment,
                }
                if args.apply_summary and enrichment.get("summary_ru"):
                    i18n = dict(target.get("i18n") or {})
                    ru = dict(i18n.get("ru") or {})
                    ru["summary"] = enrichment["summary_ru"]
                    i18n["ru"] = ru
                    target["i18n"] = i18n

                if updated_raw == row_raw:
                    print(f"[{index}/{len(rows)}] skip {row.id}")
                    continue
                changed += 1
                row.raw = cast(Any, updated_raw)
                if args.apply:
                    session.add(row)
                    session.commit()
                    action = "updated"
                else:
                    session.rollback()
                    action = "dry-run"
                print(f"[{index}/{len(rows)}] {action} {row.id}")

    print(
        json.dumps(
            {
                "status": "ok",
                "scanned": scanned,
                "changed": changed,
                "applied": args.apply,
            },
            ensure_ascii=False,
        )
    )
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=None)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--endpoint", default=DEFAULT_DEEPSEEK_URL)
    parser.add_argument("--model", default=DEFAULT_DEEPSEEK_MODEL)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--include-inactive", action="store_true")
    parser.add_argument("--no-provider", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--apply-summary", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(_run(_parser().parse_args(argv)))


if __name__ == "__main__":
    raise SystemExit(main())
