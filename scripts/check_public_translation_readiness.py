#!/usr/bin/env python3
"""Measure QAZ.FUND public translation readiness without emitting raw items."""

from __future__ import annotations

import argparse
import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

DEFAULT_BASE_URL = "https://qaz.fund"
LOCALES = ("kk", "ru", "en")
APPROVAL_FIELDS = (
    "review_status",
    "memory_eligibility",
    "reviewer_ref",
    "quality_score",
)


def present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def item_raw(item: dict[str, Any]) -> dict[str, Any]:
    raw = item.get("raw")
    return raw if isinstance(raw, dict) else {}


def item_value(item: dict[str, Any], field: str) -> Any:
    if field in item and present(item.get(field)):
        return item.get(field)
    return item_raw(item).get(field)


def i18n_bucket(item: dict[str, Any], locale: str) -> dict[str, Any]:
    i18n = item_raw(item).get("i18n")
    if not isinstance(i18n, dict):
        return {}
    bucket = i18n.get(locale)
    return bucket if isinstance(bucket, dict) else {}


def summarize_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    locale_item_counts: dict[str, int] = {}
    locale_field_counts: dict[str, int] = {}
    for locale in LOCALES:
        buckets = [i18n_bucket(item, locale) for item in items]
        locale_item_counts[locale] = sum(bool(bucket) for bucket in buckets)
        locale_field_counts[locale] = sum(
            sum(present(value) for value in bucket.values()) for bucket in buckets
        )

    field_counts = {
        field: sum(present(item_value(item, field)) for item in items)
        for field in APPROVAL_FIELDS
    }
    approved_only_count = sum(
        all(present(item_value(item, field)) for field in APPROVAL_FIELDS)
        and item_value(item, "review_status") == "approved"
        and item_value(item, "memory_eligibility") == "approved"
        for item in items
    )
    source_language_count = sum(
        present(item.get("languages"))
        or present(item_value(item, "source_language"))
        or present(item_value(item, "language"))
        or present(item_value(item, "detail_language"))
        for item in items
    )
    item_count = len(items)
    return {
        "item_count": item_count,
        "locale_item_counts": locale_item_counts,
        "locale_field_counts": locale_field_counts,
        "kk_content_coverage_rate": (
            round(locale_item_counts["kk"] / item_count, 6) if item_count else 0.0
        ),
        "source_language_metadata_count": source_language_count,
        "reviewer_ref_count": field_counts["reviewer_ref"],
        "quality_score_count": field_counts["quality_score"],
        "approved_only_ready_count": approved_only_count,
    }


def fetch_json(url: str) -> Any:
    with urlopen(url, timeout=30) as response:
        return json.load(response)


def build_public_report(base_url: str = DEFAULT_BASE_URL) -> dict[str, Any]:
    base = base_url.rstrip("/")
    query = urlencode({"lang": "kk", "scope": "all", "limit": "5000"})
    payload = fetch_json(f"{base}/opportunities?{query}")
    items = payload if isinstance(payload, list) else payload.get("items", [])
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        raise ValueError("public opportunities payload must contain an item list")
    health = fetch_json(f"{base}/health")
    report = summarize_items(items)
    report.update(
        {
            "schema_version": "qazstack-translation-holdout-readiness-v1",
            "contract_id": "qazstack.translation_holdout_readiness.v1",
            "project_id": "qaz-fund",
            "surface": "qaz.fund.public.opportunities",
            "approved_only": True,
            "decision": (
                "pass"
                if report["approved_only_ready_count"]
                and report["kk_content_coverage_rate"] == 1.0
                else "hold"
            ),
            "runtime": {
                "base_url": base,
                "endpoint": "/opportunities?lang=kk&scope=all",
                "health_item_count": (
                    health.get("items") if isinstance(health, dict) else None
                ),
                "returned_item_count": len(items),
                "health_status": (
                    health.get("status") if isinstance(health, dict) else None
                ),
            },
            "blockers": [
                "kk_content_coverage",
                "source_language_metadata",
                "reviewer_ref",
                "quality_score",
                "review_status",
                "memory_eligibility",
            ],
            "interpretation": {
                "missing_kk": "public fallback/source behavior; not an approved Kazakh translation",
                "locale_fields": "i18n bucket presence only; no quality approval implied",
            },
            "policy": {
                "raw_text_export": False,
                "remote_write": False,
                "automatic_memory_promotion": False,
            },
        }
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()
    print(
        json.dumps(
            build_public_report(args.base_url),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
