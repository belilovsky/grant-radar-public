"""Build and evaluate an expert review queue for QAZ.FUND ranking."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urljoin

import httpx

from core.ranking_evaluation import (
    REVIEW_SCHEMA_VERSION,
    RankingEvaluationError,
    evaluate_judgments,
    gate_failures,
    judgment_from_mapping,
)


def _api_url(base_url: str) -> str:
    return urljoin(
        f"{base_url.rstrip('/')}/",
        "opportunities?lang=ru&scope=all&limit=5000"
        "&include_irrelevant=true&min_score=0",
    )


def _ranking(item: Mapping[str, Any]) -> dict[str, Any]:
    raw = item.get("raw")
    if not isinstance(raw, Mapping):
        return {}
    ranking = raw.get("ranking")
    return dict(ranking) if isinstance(ranking, Mapping) else {}


def _score_bin(value: Any) -> str:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return "missing"
    if score < 0.3:
        return "below_public"
    if score < 0.5:
        return "baseline"
    if score < 0.7:
        return "good"
    return "high"


def _stratum(item: Mapping[str, Any]) -> tuple[str, str, str, str]:
    ranking = _ranking(item)
    return (
        str(ranking.get("confidence") or "unknown"),
        str(ranking.get("geography") or "unspecified"),
        _score_bin(ranking.get("relevance")),
        str(item.get("source") or "unknown"),
    )


def stratified_sample(
    items: Iterable[Mapping[str, Any]], *, size: int
) -> list[Mapping[str, Any]]:
    """Select a deterministic round-robin sample across model and source strata."""

    if size < 1:
        raise RankingEvaluationError("sample size must be at least 1")
    buckets: dict[tuple[str, str, str, str], deque[Mapping[str, Any]]] = defaultdict(
        deque
    )
    for item in items:
        ranking = _ranking(item)
        if not ranking:
            continue
        buckets[_stratum(item)].append(item)
    for bucket in buckets.values():
        ordered = sorted(
            bucket,
            key=lambda item: (
                str(item.get("deadline") or "9999-12-31"),
                str(item.get("id") or ""),
            ),
        )
        bucket.clear()
        bucket.extend(ordered)

    selected: list[Mapping[str, Any]] = []
    keys = deque(sorted(buckets))
    while keys and len(selected) < size:
        key = keys.popleft()
        bucket = buckets[key]
        if bucket:
            selected.append(bucket.popleft())
        if bucket:
            keys.append(key)
    return selected


def review_row(item: Mapping[str, Any]) -> dict[str, Any]:
    """Create a review-safe row without inventing expert labels."""

    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "item_id": str(item.get("id") or ""),
        "title": str(item.get("title") or ""),
        "summary": str(item.get("summary") or ""),
        "source": str(item.get("source") or ""),
        "source_url": str(item.get("source_url") or ""),
        "type": str(item.get("type") or ""),
        "deadline": item.get("deadline"),
        "ranking": _ranking(item),
        "relevance_label": None,
        "action_priority_label": None,
        "reviewer": None,
        "reviewed_at": None,
        "notes": "",
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RankingEvaluationError(
                f"{path}:{line_number}: invalid JSON: {exc.msg}"
            ) from exc
        if not isinstance(value, dict):
            raise RankingEvaluationError(
                f"{path}:{line_number}: each row must be an object"
            )
        rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            output.write("\n")


def _sample(args: argparse.Namespace) -> int:
    output = Path(args.output)
    if output.exists() and not args.force:
        raise RankingEvaluationError(
            f"{output} already exists; pass --force to replace it"
        )
    with httpx.Client(timeout=args.timeout, follow_redirects=True) as client:
        response = client.get(_api_url(args.base_url))
        response.raise_for_status()
        payload = response.json()
    if not isinstance(payload, list):
        raise RankingEvaluationError("opportunities endpoint must return a list")
    sample = stratified_sample(payload, size=args.size)
    if len(sample) < args.size:
        raise RankingEvaluationError(
            f"only {len(sample)} ranked rows are available for a sample of {args.size}"
        )
    _write_jsonl(output, (review_row(item) for item in sample))
    print(
        json.dumps(
            {
                "status": "ok",
                "output": str(output),
                "rows": len(sample),
                "source_rows": len(payload),
                "labels_added": 0,
            },
            ensure_ascii=False,
        )
    )
    return 0


def _evaluate(args: argparse.Namespace) -> int:
    rows = _read_jsonl(Path(args.input))
    judgments = [judgment_from_mapping(row) for row in rows]
    report = evaluate_judgments(
        judgments,
        precision_k=args.precision_k,
        recall_k=args.recall_k,
        ndcg_k=args.ndcg_k,
        threshold=args.public_threshold,
    )
    failures = gate_failures(
        report,
        min_labeled=args.min_labeled,
        min_ndcg_at_k=args.min_ndcg_at_k,
        min_precision_at_k=args.min_precision_at_k,
        max_false_positive_rate=args.max_false_positive_rate,
        min_priority_labeled=args.min_priority_labeled,
        min_priority_ndcg_at_k=args.min_priority_ndcg_at_k,
        min_priority_precision_at_k=args.min_priority_precision_at_k,
    )
    report["gate"] = {
        "status": "failed" if failures else "passed",
        "failures": failures,
        "thresholds": {
            "min_labeled": args.min_labeled,
            "min_ndcg_at_k": args.min_ndcg_at_k,
            "min_precision_at_k": args.min_precision_at_k,
            "max_false_positive_rate": args.max_false_positive_rate,
            "min_priority_labeled": args.min_priority_labeled,
            "min_priority_ndcg_at_k": args.min_priority_ndcg_at_k,
            "min_priority_precision_at_k": args.min_priority_precision_at_k,
        },
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(f"{rendered}\n", encoding="utf-8")
    print(rendered)
    return 1 if failures else 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare and evaluate QAZ.FUND ranking judgments."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sample = subparsers.add_parser(
        "sample", help="Export a deterministic, stratified review queue."
    )
    sample.add_argument("--base-url", default="https://qaz.fund")
    sample.add_argument("--output", required=True)
    sample.add_argument("--size", type=int, default=200)
    sample.add_argument("--timeout", type=float, default=60.0)
    sample.add_argument("--force", action="store_true")
    sample.set_defaults(handler=_sample)

    evaluate = subparsers.add_parser(
        "evaluate", help="Evaluate an adjudicated JSONL review queue."
    )
    evaluate.add_argument("--input", required=True)
    evaluate.add_argument("--output")
    evaluate.add_argument("--precision-k", type=int, default=10)
    evaluate.add_argument("--recall-k", type=int, default=50)
    evaluate.add_argument("--ndcg-k", type=int, default=10)
    evaluate.add_argument("--public-threshold", type=float, default=0.3)
    evaluate.add_argument("--min-labeled", type=int, default=200)
    evaluate.add_argument("--min-ndcg-at-k", type=float, default=0.75)
    evaluate.add_argument("--min-precision-at-k", type=float, default=0.75)
    evaluate.add_argument("--max-false-positive-rate", type=float, default=0.2)
    evaluate.add_argument("--min-priority-labeled", type=int, default=200)
    evaluate.add_argument("--min-priority-ndcg-at-k", type=float, default=0.7)
    evaluate.add_argument("--min-priority-precision-at-k", type=float, default=0.7)
    evaluate.set_defaults(handler=_evaluate)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the requested review-queue operation."""

    parser = _parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (RankingEvaluationError, httpx.HTTPError) as exc:
        print(f"ranking evaluation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
