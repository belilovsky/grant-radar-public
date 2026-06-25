"""Audit visible Grant Radar text quality and lightweight entity coverage."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.parse import urljoin

import httpx

from core.nlp import (
    clean_source_summary,
    extract_rule_based_entities,
    text_quality_flags,
)


@dataclass(frozen=True)
class NlpAuditIssue:
    title: str
    source: str
    flags: list[str]
    summary: str


@dataclass(frozen=True)
class NlpAuditResult:
    status: str
    checked: int
    issue_count: int
    missing_entity_count: int
    flag_counts: dict[str, int] = field(default_factory=dict)
    issues: list[NlpAuditIssue] = field(default_factory=list)


def _url(base_url: str, path: str) -> str:
    return urljoin(f"{base_url.rstrip('/')}/", path.lstrip("/"))


def analyze_nlp_quality(
    opportunities: list[dict[str, Any]],
    *,
    lang: str = "ru",
    max_issues: int = 30,
) -> NlpAuditResult:
    issues: list[NlpAuditIssue] = []
    flag_counts: dict[str, int] = {}
    missing_entity_count = 0

    for item in opportunities:
        title = str(item.get("title") or "")
        summary = str(item.get("summary") or "")
        source = str(item.get("source") or "")
        tags = item.get("tags") or []
        entities = extract_rule_based_entities(
            title=title,
            summary=summary,
            tags=tags,
        )
        flags = text_quality_flags(title=title, summary=summary, lang=lang)
        if not entities.get("support_types"):
            flags.append("missing_support_type_entity")
            missing_entity_count += 1
        if not entities.get("regions"):
            flags.append("missing_region_entity")
            missing_entity_count += 1
        for flag in flags:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1
        if flags and len(issues) < max_issues:
            issues.append(
                NlpAuditIssue(
                    title=title,
                    source=source,
                    flags=sorted(set(flags)),
                    summary=clean_source_summary(summary)[:300],
                )
            )

    status = "ok" if not issues else "needs_attention"
    return NlpAuditResult(
        status=status,
        checked=len(opportunities),
        issue_count=sum(flag_counts.values()),
        missing_entity_count=missing_entity_count,
        flag_counts=dict(sorted(flag_counts.items())),
        issues=issues,
    )


def run_audit(
    *,
    base_url: str,
    lang: str,
    limit: int,
    timeout: float,
) -> NlpAuditResult:
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        response = client.get(
            _url(base_url, f"/opportunities?lang={lang}&scope=all&limit={limit}")
        )
        response.raise_for_status()
        opportunities = response.json()
    if not isinstance(opportunities, list):
        raise RuntimeError("Unexpected /opportunities payload")
    return analyze_nlp_quality(opportunities, lang=lang)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://qaz.fund")
    parser.add_argument("--lang", default="ru")
    parser.add_argument("--limit", type=int, default=250)
    parser.add_argument("--timeout", type=float, default=30.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = run_audit(
            base_url=args.base_url,
            lang=args.lang,
            limit=args.limit,
            timeout=args.timeout,
        )
    except (httpx.HTTPError, RuntimeError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    return 0 if result.status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
