"""Offline metrics for adjudicated QAZ.FUND ranking judgments."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Iterable, Mapping, Sequence

REVIEW_SCHEMA_VERSION = "qazfund-ranking-review-v1"
MIN_LABEL = 0
MAX_LABEL = 3
POSITIVE_LABEL = 2


class RankingEvaluationError(ValueError):
    """Raised when an evaluation row violates the review contract."""


@dataclass(frozen=True)
class RankingJudgment:
    """One reviewed opportunity with model outputs and ordinal judgments."""

    item_id: str
    model_version: str
    source: str
    opportunity_type: str
    geography: str
    confidence: str
    matched_themes: tuple[str, ...]
    predicted_relevance: float
    predicted_priority: float
    relevance_label: int | None
    action_priority_label: int | None


@dataclass(frozen=True)
class MetricSet:
    """Ranking and threshold metrics for one reviewed target."""

    labeled: int
    positives: int
    precision_k: int
    precision_at_k: float | None
    recall_k: int
    recall_at_k: float | None
    ndcg_k: int
    ndcg_at_k: float | None
    unique_sources_at_k: int
    source_diversity_at_k: float | None
    graded_mae: float | None
    false_positive_rate: float | None
    false_negative_rate: float | None


def _bounded_score(value: Any, *, field: str) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise RankingEvaluationError(f"{field} must be a number") from exc
    if not math.isfinite(score) or not 0.0 <= score <= 1.0:
        raise RankingEvaluationError(f"{field} must be between 0 and 1")
    return score


def _optional_label(value: Any, *, field: str) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise RankingEvaluationError(f"{field} must be an integer from 0 to 3")
    label = value
    if not MIN_LABEL <= label <= MAX_LABEL:
        raise RankingEvaluationError(f"{field} must be an integer from 0 to 3")
    return label


def judgment_from_mapping(row: Mapping[str, Any]) -> RankingJudgment:
    """Validate and normalize one JSON-compatible review row."""

    if row.get("schema_version") != REVIEW_SCHEMA_VERSION:
        raise RankingEvaluationError(
            f"schema_version must be {REVIEW_SCHEMA_VERSION!r}"
        )
    item_id = str(row.get("item_id") or "").strip()
    if not item_id:
        raise RankingEvaluationError("item_id is required")
    ranking = row.get("ranking")
    if not isinstance(ranking, Mapping):
        raise RankingEvaluationError("ranking must be an object")
    model_version = str(ranking.get("model_version") or "").strip()
    if not model_version:
        raise RankingEvaluationError("ranking.model_version is required")
    relevance_label = _optional_label(
        row.get("relevance_label"), field="relevance_label"
    )
    action_priority_label = _optional_label(
        row.get("action_priority_label"), field="action_priority_label"
    )
    if relevance_label is not None or action_priority_label is not None:
        reviewer = str(row.get("reviewer") or "").strip()
        reviewed_at = str(row.get("reviewed_at") or "").strip()
        if not reviewer:
            raise RankingEvaluationError("reviewer is required for labeled rows")
        try:
            parsed_reviewed_at = datetime.fromisoformat(
                reviewed_at.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise RankingEvaluationError(
                "reviewed_at must be an ISO 8601 timestamp for labeled rows"
            ) from exc
        if parsed_reviewed_at.tzinfo is None:
            raise RankingEvaluationError(
                "reviewed_at must include a timezone for labeled rows"
            )
    raw_themes = ranking.get("matched_themes")
    matched_themes = (
        tuple(str(theme) for theme in raw_themes)
        if isinstance(raw_themes, list)
        else ()
    )
    return RankingJudgment(
        item_id=item_id,
        model_version=model_version,
        source=str(row.get("source") or "unknown").strip() or "unknown",
        opportunity_type=str(row.get("type") or "unknown").strip() or "unknown",
        geography=str(ranking.get("geography") or "unspecified"),
        confidence=str(ranking.get("confidence") or "unknown"),
        matched_themes=matched_themes,
        predicted_relevance=_bounded_score(
            ranking.get("relevance"), field="ranking.relevance"
        ),
        predicted_priority=_bounded_score(
            ranking.get("priority"), field="ranking.priority"
        ),
        relevance_label=relevance_label,
        action_priority_label=action_priority_label,
    )


def _dcg(labels: Sequence[int]) -> float:
    return sum(
        (2**label - 1) / math.log2(index + 2) for index, label in enumerate(labels)
    )


def _metric_set(
    rows: Sequence[tuple[float, int, str]],
    *,
    precision_k: int,
    recall_k: int,
    ndcg_k: int,
    threshold: float,
) -> MetricSet:
    if not rows:
        return MetricSet(
            0,
            0,
            precision_k,
            None,
            recall_k,
            None,
            ndcg_k,
            None,
            0,
            None,
            None,
            None,
            None,
        )

    ordered = sorted(rows, key=lambda row: row[0], reverse=True)
    precision_top = ordered[: min(precision_k, len(ordered))]
    recall_top = ordered[: min(recall_k, len(ordered))]
    ndcg_top = ordered[: min(ndcg_k, len(ordered))]
    positives = sum(label >= POSITIVE_LABEL for _, label, _ in ordered)
    precision_true_positives = sum(
        label >= POSITIVE_LABEL for _, label, _ in precision_top
    )
    recall_true_positives = sum(label >= POSITIVE_LABEL for _, label, _ in recall_top)
    negatives = len(ordered) - positives
    false_positives = sum(
        score >= threshold and label < POSITIVE_LABEL for score, label, _ in ordered
    )
    false_negatives = sum(
        score < threshold and label >= POSITIVE_LABEL for score, label, _ in ordered
    )
    ranked_labels = [label for _, label, _ in ndcg_top]
    ideal_labels = sorted((label for _, label, _ in ordered), reverse=True)[
        : len(ndcg_top)
    ]
    ideal_dcg = _dcg(ideal_labels)
    unique_sources = len({source for _, _, source in precision_top})

    return MetricSet(
        labeled=len(ordered),
        positives=positives,
        precision_k=precision_k,
        precision_at_k=round(precision_true_positives / len(precision_top), 4),
        recall_k=recall_k,
        recall_at_k=round(recall_true_positives / positives, 4) if positives else None,
        ndcg_k=ndcg_k,
        ndcg_at_k=round(_dcg(ranked_labels) / ideal_dcg, 4) if ideal_dcg else None,
        unique_sources_at_k=unique_sources,
        source_diversity_at_k=round(unique_sources / len(precision_top), 4),
        graded_mae=round(
            sum(abs(score - label / MAX_LABEL) for score, label, _ in ordered)
            / len(ordered),
            4,
        ),
        false_positive_rate=(
            round(false_positives / negatives, 4) if negatives else None
        ),
        false_negative_rate=(
            round(false_negatives / positives, 4) if positives else None
        ),
    )


def _slice_summary(rows: Iterable[RankingJudgment], *, field: str) -> dict[str, Any]:
    groups: dict[str, list[RankingJudgment]] = {}
    for row in rows:
        value = str(getattr(row, field))
        groups.setdefault(value, []).append(row)
    return {
        value: {
            "rows": len(items),
            "relevance_labeled": sum(
                item.relevance_label is not None for item in items
            ),
            "priority_labeled": sum(
                item.action_priority_label is not None for item in items
            ),
            "mean_predicted_relevance": round(
                sum(item.predicted_relevance for item in items) / len(items), 4
            ),
        }
        for value, items in sorted(groups.items())
    }


def _theme_slice_summary(rows: Iterable[RankingJudgment]) -> dict[str, Any]:
    groups: dict[str, list[RankingJudgment]] = {}
    for row in rows:
        themes = row.matched_themes or ("unmatched",)
        for theme in themes:
            groups.setdefault(theme, []).append(row)
    return {
        theme: {
            "rows": len(items),
            "relevance_labeled": sum(
                item.relevance_label is not None for item in items
            ),
            "priority_labeled": sum(
                item.action_priority_label is not None for item in items
            ),
        }
        for theme, items in sorted(groups.items())
    }


def evaluate_judgments(
    judgments: Sequence[RankingJudgment],
    *,
    precision_k: int = 10,
    recall_k: int = 50,
    ndcg_k: int = 10,
    threshold: float = 0.3,
) -> dict[str, Any]:
    """Calculate reproducible ranking metrics and coverage slices."""

    if min(precision_k, recall_k, ndcg_k) < 1:
        raise RankingEvaluationError("metric windows must be at least 1")
    if not 0.0 <= threshold <= 1.0:
        raise RankingEvaluationError("threshold must be between 0 and 1")
    identifiers = [row.item_id for row in judgments]
    if len(set(identifiers)) != len(identifiers):
        raise RankingEvaluationError("item_id values must be unique")
    model_versions = sorted({row.model_version for row in judgments})
    if len(model_versions) > 1:
        raise RankingEvaluationError(
            f"review queue mixes model versions: {', '.join(model_versions)}"
        )

    relevance_rows = [
        (row.predicted_relevance, row.relevance_label, row.source)
        for row in judgments
        if row.relevance_label is not None
    ]
    priority_rows = [
        (row.predicted_priority, row.action_priority_label, row.source)
        for row in judgments
        if row.action_priority_label is not None
    ]
    return {
        "schema_version": "qazfund-ranking-evaluation-v1",
        "review_schema_version": REVIEW_SCHEMA_VERSION,
        "model_version": model_versions[0] if model_versions else None,
        "rows": len(judgments),
        "threshold": threshold,
        "relevance": asdict(
            _metric_set(
                relevance_rows,
                precision_k=precision_k,
                recall_k=recall_k,
                ndcg_k=ndcg_k,
                threshold=threshold,
            )
        ),
        "action_priority": asdict(
            _metric_set(
                priority_rows,
                precision_k=precision_k,
                recall_k=recall_k,
                ndcg_k=ndcg_k,
                threshold=threshold,
            )
        ),
        "slices": {
            "geography": _slice_summary(judgments, field="geography"),
            "confidence": _slice_summary(judgments, field="confidence"),
            "source": _slice_summary(judgments, field="source"),
            "opportunity_type": _slice_summary(judgments, field="opportunity_type"),
            "matched_theme": _theme_slice_summary(judgments),
        },
    }


def gate_failures(
    report: Mapping[str, Any],
    *,
    min_labeled: int,
    min_ndcg_at_k: float,
    min_precision_at_k: float,
    max_false_positive_rate: float,
    min_priority_labeled: int,
    min_priority_ndcg_at_k: float,
    min_priority_precision_at_k: float,
) -> list[str]:
    """Return explicit release-gate failures for both ranking targets."""

    relevance = report.get("relevance")
    if not isinstance(relevance, Mapping):
        return ["relevance metrics are missing"]
    failures: list[str] = []
    labeled = int(relevance.get("labeled") or 0)
    if labeled < min_labeled:
        failures.append(f"labeled rows {labeled} < required {min_labeled}")
    checks = (
        ("ndcg_at_k", min_ndcg_at_k, "<", "minimum"),
        ("precision_at_k", min_precision_at_k, "<", "minimum"),
    )
    for field, boundary, operator, label in checks:
        value = relevance.get(field)
        if value is None or float(value) < boundary:
            failures.append(f"{field} {value} {operator} {label} {boundary}")
    false_positive_rate = relevance.get("false_positive_rate")
    if (
        false_positive_rate is None
        or float(false_positive_rate) > max_false_positive_rate
    ):
        failures.append(
            "false_positive_rate "
            f"{false_positive_rate} > maximum {max_false_positive_rate}"
        )
    priority = report.get("action_priority")
    if not isinstance(priority, Mapping):
        failures.append("action_priority metrics are missing")
        return failures
    priority_labeled = int(priority.get("labeled") or 0)
    if priority_labeled < min_priority_labeled:
        failures.append(
            "action_priority labeled rows "
            f"{priority_labeled} < required {min_priority_labeled}"
        )
    for field, boundary in (
        ("ndcg_at_k", min_priority_ndcg_at_k),
        ("precision_at_k", min_priority_precision_at_k),
    ):
        value = priority.get(field)
        if value is None or float(value) < boundary:
            failures.append(f"action_priority {field} {value} < minimum {boundary}")
    return failures
