"""Backfill decision-safe QazCompute enrichment into opportunity payloads.

The script is intentionally operator-controlled: it writes only with --apply and
keeps public text untouched unless a benchmarked response is decision-ready.

The legacy module name is preserved for operator compatibility. Provider access
is centralized through QazCompute; this script no longer accepts provider keys.
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

DEFAULT_QAZCOMPUTE_URL = "http://127.0.0.1:8201"
OPPORTUNITY_ENRICH_PATH = "/api/v1/tasks/opportunity-enrich"
OPPORTUNITY_ENRICH_SCHEMA = "opportunity_enrich.v1"
VALID_RUNTIME_STATUSES = frozenset({"available", "degraded"})
VALID_QUALITY_TIERS = frozenset({"estimated", "degraded"})


def _string(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _normalize_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()][:12]


def _normalize_evidence(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, str]] = []
    for item in value[:30]:
        if not isinstance(item, dict):
            continue
        field = _string(item.get("field"))[:120]
        evidence_value = _string(item.get("value"))[:500]
        quote = _string(item.get("quote"))[:500]
        if field and evidence_value and quote:
            normalized.append({"field": field, "value": evidence_value, "quote": quote})
    return normalized


def normalize_enrichment_payload(payload: dict[str, Any]) -> dict[str, Any]:
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
        "evidence": _normalize_evidence(payload.get("evidence")),
    }
    if not summary_ru:
        result.pop("summary_ru")
    return result


normalize_deepseek_payload = normalize_enrichment_payload


def _validated_runtime(payload: dict[str, Any]) -> dict[str, Any]:
    status = payload.get("status")
    quality_tier = payload.get("quality_tier")
    decision_ready = payload.get("decision_ready")
    provider = _string(payload.get("provider"))
    model = _string(payload.get("model"))
    if status not in VALID_RUNTIME_STATUSES:
        raise ValueError("QazCompute returned an invalid runtime status")
    if quality_tier not in VALID_QUALITY_TIERS:
        raise ValueError("QazCompute returned an invalid quality tier")
    if not isinstance(decision_ready, bool):
        raise ValueError("QazCompute returned an invalid decision-ready flag")
    if not provider or not model:
        raise ValueError("QazCompute returned incomplete runtime provenance")
    if decision_ready and (status != "available" or quality_tier == "degraded"):
        raise ValueError("QazCompute returned inconsistent publication readiness")

    fallback_reason = payload.get("fallback_reason")
    if fallback_reason is not None and not isinstance(fallback_reason, str):
        raise ValueError("QazCompute returned an invalid fallback reason")

    return {
        "schema_version": OPPORTUNITY_ENRICH_SCHEMA,
        "status": status,
        "provider": provider,
        "model": model,
        "quality_tier": quality_tier,
        "decision_ready": decision_ready,
        "fallback_reason": fallback_reason,
        "omitted_capabilities": _normalize_list(payload.get("omitted_capabilities")),
    }


async def call_qazcompute(
    *,
    client: httpx.AsyncClient,
    api_key: str,
    base_url: str,
    item: Any,
    detail_text: str,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}{OPPORTUNITY_ENRICH_PATH}"
    response = await client.post(
        url,
        headers={
            "X-API-Key": api_key,
            "X-Caller": "qaz-fund",
        },
        json={
            "schema_version": OPPORTUNITY_ENRICH_SCHEMA,
            "allow_degraded": True,
            "items": [
                {
                    "id": str(item.id),
                    "title": item.title,
                    "summary": item.summary,
                    "detail_text": detail_text[:100_000],
                    "source": item.source,
                    "tags": item.tags,
                    "eligibility": item.eligibility,
                }
            ],
        },
    )
    response.raise_for_status()
    payload = response.json()
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != OPPORTUNITY_ENRICH_SCHEMA
    ):
        raise ValueError(
            "QazCompute returned an invalid opportunity enrichment contract"
        )
    results = payload.get("results")
    if (
        not isinstance(results, list)
        or len(results) != 1
        or not isinstance(results[0], dict)
    ):
        raise ValueError("QazCompute returned an invalid result count")
    if str(results[0].get("id") or "") != str(item.id):
        raise ValueError("QazCompute returned a mismatched opportunity id")
    normalized = normalize_enrichment_payload(cast(dict[str, Any], results[0]))
    normalized["runtime"] = _validated_runtime(payload)
    return normalized


def summary_is_decision_ready(enrichment: dict[str, Any]) -> bool:
    """Return whether a computed summary may replace public copy."""

    runtime = enrichment.get("runtime")
    return bool(
        enrichment.get("summary_ru")
        and enrichment.get("evidence")
        and isinstance(runtime, dict)
        and runtime.get("status") == "available"
        and runtime.get("quality_tier") == "estimated"
        and runtime.get("decision_ready") is True
    )


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

    compute_url = (
        args.compute_url or os.environ.get("QAZCOMPUTE_URL") or DEFAULT_QAZCOMPUTE_URL
    ).strip()
    api_key = (os.environ.get("QAZCOMPUTE_API_KEY") or "").strip()
    if not api_key and not args.no_provider:
        print(
            "error: QAZCOMPUTE_API_KEY is not set; use --no-provider for heuristic run",
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
                    enrichment = await call_qazcompute(
                        client=client,
                        api_key=api_key,
                        base_url=compute_url,
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
                    "provider": "heuristic" if args.no_provider else "qazcompute",
                    "enriched_at": datetime.now(timezone.utc).isoformat(),
                    **enrichment,
                }
                if args.apply_summary and summary_is_decision_ready(enrichment):
                    i18n = dict(target.get("i18n") or {})
                    ru = dict(i18n.get("ru") or {})
                    ru["summary"] = enrichment["summary_ru"]
                    i18n["ru"] = ru
                    target["i18n"] = i18n
                elif args.apply_summary and enrichment.get("summary_ru"):
                    print(
                        f"[{index}/{len(rows)}] summary blocked: "
                        "QazCompute result is not decision-ready",
                        file=sys.stderr,
                    )

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
    parser.add_argument("--compute-url", default=None)
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
