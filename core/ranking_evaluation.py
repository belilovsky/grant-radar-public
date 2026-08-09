"""QAZ.FUND schema adapter for shared opportunity-ranking evaluation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from qazstack.opportunities import MetricSet, RankingEvaluationError, RankingJudgment
from qazstack.opportunities import evaluate_judgments as _evaluate_judgments
from qazstack.opportunities import gate_failures
from qazstack.opportunities import judgment_from_mapping as _judgment_from_mapping

REVIEW_SCHEMA_VERSION = "qazfund-ranking-review-v1"
EVALUATION_SCHEMA_VERSION = "qazfund-ranking-evaluation-v1"


def judgment_from_mapping(row: Mapping[str, Any]) -> RankingJudgment:
    """Validate one review row while preserving the QAZ.FUND schema identifier."""

    return _judgment_from_mapping(
        row,
        review_schema_version=REVIEW_SCHEMA_VERSION,
    )


def evaluate_judgments(
    judgments: Sequence[RankingJudgment],
    *,
    precision_k: int = 10,
    recall_k: int = 50,
    ndcg_k: int = 10,
    threshold: float = 0.3,
) -> dict[str, Any]:
    """Evaluate rows with the established QAZ.FUND public schema identifiers."""

    return _evaluate_judgments(
        judgments,
        precision_k=precision_k,
        recall_k=recall_k,
        ndcg_k=ndcg_k,
        threshold=threshold,
        review_schema_version=REVIEW_SCHEMA_VERSION,
        evaluation_schema_version=EVALUATION_SCHEMA_VERSION,
    )


__all__ = [
    "EVALUATION_SCHEMA_VERSION",
    "MetricSet",
    "REVIEW_SCHEMA_VERSION",
    "RankingEvaluationError",
    "RankingJudgment",
    "evaluate_judgments",
    "gate_failures",
    "judgment_from_mapping",
]
