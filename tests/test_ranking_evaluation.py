from __future__ import annotations

import json

import pytest

from core.ranking_evaluation import (
    REVIEW_SCHEMA_VERSION,
    RankingEvaluationError,
    RankingJudgment,
    evaluate_judgments,
    gate_failures,
    judgment_from_mapping,
)
from scripts import ranking_evaluation


def _judgment(
    item_id: str,
    *,
    relevance: float,
    priority: float,
    relevance_label: int | None,
    priority_label: int | None,
    source: str = "source-a",
) -> RankingJudgment:
    return RankingJudgment(
        item_id=item_id,
        model_version="qazfund-relevance-v2",
        source=source,
        opportunity_type="grant",
        geography="kazakhstan",
        confidence="supported",
        matched_themes=("ai",),
        predicted_relevance=relevance,
        predicted_priority=priority,
        relevance_label=relevance_label,
        action_priority_label=priority_label,
    )


def _api_item(
    item_id: str,
    *,
    source: str,
    relevance: float,
    confidence: str = "supported",
) -> dict:
    return {
        "id": item_id,
        "title": f"Opportunity {item_id}",
        "summary": "Reviewed public opportunity.",
        "source": source,
        "source_url": f"https://example.org/{item_id}",
        "type": "grant",
        "deadline": "2026-09-01",
        "raw": {
            "ranking": {
                "model_version": "qazfund-relevance-v2",
                "relevance": relevance,
                "priority": relevance,
                "geography": "kazakhstan",
                "confidence": confidence,
            }
        },
    }


def test_judgment_contract_rejects_wrong_schema_and_non_integer_label():
    row = ranking_evaluation.review_row(
        _api_item("one", source="source-a", relevance=0.8)
    )
    row["schema_version"] = "other"

    with pytest.raises(RankingEvaluationError, match="schema_version"):
        judgment_from_mapping(row)

    row["schema_version"] = REVIEW_SCHEMA_VERSION
    row["relevance_label"] = 2.0
    with pytest.raises(RankingEvaluationError, match="integer"):
        judgment_from_mapping(row)


def test_labeled_row_requires_reviewer_and_timezone():
    row = ranking_evaluation.review_row(
        _api_item("one", source="source-a", relevance=0.8)
    )
    row["relevance_label"] = 3

    with pytest.raises(RankingEvaluationError, match="reviewer"):
        judgment_from_mapping(row)

    row["reviewer"] = "editor@example.org"
    row["reviewed_at"] = "2026-07-16T18:00:00"
    with pytest.raises(RankingEvaluationError, match="timezone"):
        judgment_from_mapping(row)

    row["reviewed_at"] = "2026-07-16T18:00:00+05:00"
    assert judgment_from_mapping(row).relevance_label == 3


def test_evaluation_reports_perfect_order_and_separate_priority_metrics():
    rows = [
        _judgment(
            "high", relevance=0.9, priority=0.6, relevance_label=3, priority_label=1
        ),
        _judgment(
            "medium",
            relevance=0.6,
            priority=0.9,
            relevance_label=2,
            priority_label=3,
        ),
        _judgment(
            "low", relevance=0.1, priority=0.1, relevance_label=0, priority_label=0
        ),
    ]

    report = evaluate_judgments(rows, precision_k=2, recall_k=2, ndcg_k=2)

    assert report["relevance"]["precision_k"] == 2
    assert report["relevance"]["recall_k"] == 2
    assert report["relevance"]["ndcg_k"] == 2
    assert report["relevance"]["unique_sources_at_k"] == 1
    assert report["relevance"]["source_diversity_at_k"] == 0.5
    assert report["relevance"]["precision_at_k"] == 1.0
    assert report["relevance"]["recall_at_k"] == 1.0
    assert report["relevance"]["ndcg_at_k"] == 1.0
    assert report["action_priority"]["ndcg_at_k"] == 1.0
    assert report["slices"]["geography"]["kazakhstan"]["rows"] == 3
    assert report["slices"]["opportunity_type"]["grant"]["rows"] == 3
    assert report["slices"]["matched_theme"]["ai"]["rows"] == 3


def test_evaluation_exposes_false_positive_and_false_negative_rates():
    rows = [
        _judgment(
            "false-positive",
            relevance=0.8,
            priority=0.8,
            relevance_label=0,
            priority_label=None,
        ),
        _judgment(
            "false-negative",
            relevance=0.1,
            priority=0.1,
            relevance_label=3,
            priority_label=None,
        ),
    ]

    report = evaluate_judgments(
        rows, precision_k=2, recall_k=2, ndcg_k=2, threshold=0.3
    )

    assert report["relevance"]["false_positive_rate"] == 1.0
    assert report["relevance"]["false_negative_rate"] == 1.0


def test_evaluation_rejects_duplicate_item_ids():
    row = _judgment(
        "duplicate",
        relevance=0.8,
        priority=0.8,
        relevance_label=3,
        priority_label=3,
    )

    with pytest.raises(RankingEvaluationError, match="unique"):
        evaluate_judgments([row, row])


def test_gate_cannot_pass_without_required_adjudicated_rows():
    report = evaluate_judgments(
        [
            _judgment(
                "one",
                relevance=0.8,
                priority=0.8,
                relevance_label=3,
                priority_label=3,
            )
        ],
        precision_k=1,
        recall_k=1,
        ndcg_k=1,
    )

    failures = gate_failures(
        report,
        min_labeled=200,
        min_ndcg_at_k=0.75,
        min_precision_at_k=0.75,
        max_false_positive_rate=0.2,
        min_priority_labeled=200,
        min_priority_ndcg_at_k=0.7,
        min_priority_precision_at_k=0.7,
    )

    assert any("labeled rows 1 < required 200" in failure for failure in failures)


def test_gate_passes_for_well_ordered_positive_and_negative_judgments():
    report = evaluate_judgments(
        [
            _judgment(
                "positive",
                relevance=0.9,
                priority=0.9,
                relevance_label=3,
                priority_label=3,
            ),
            _judgment(
                "negative",
                relevance=0.1,
                priority=0.1,
                relevance_label=0,
                priority_label=0,
            ),
        ],
        precision_k=1,
        recall_k=2,
        ndcg_k=2,
    )

    assert (
        gate_failures(
            report,
            min_labeled=2,
            min_ndcg_at_k=0.75,
            min_precision_at_k=0.75,
            max_false_positive_rate=0.2,
            min_priority_labeled=2,
            min_priority_ndcg_at_k=0.7,
            min_priority_precision_at_k=0.7,
        )
        == []
    )


def test_stratified_sample_is_deterministic_and_source_diverse():
    items = [
        _api_item("a-2", source="source-a", relevance=0.8),
        _api_item("a-1", source="source-a", relevance=0.8),
        _api_item("b-1", source="source-b", relevance=0.8),
        _api_item(
            "c-1", source="source-c", relevance=0.2, confidence="review_required"
        ),
    ]

    first = ranking_evaluation.stratified_sample(items, size=3)
    second = ranking_evaluation.stratified_sample(reversed(items), size=3)

    assert [item["id"] for item in first] == [item["id"] for item in second]
    assert len({item["source"] for item in first}) == 3


def test_review_rows_have_blank_labels_and_evaluate_cli_fails_closed(tmp_path, capsys):
    queue = tmp_path / "review.jsonl"
    queue.write_text(
        json.dumps(
            ranking_evaluation.review_row(
                _api_item("one", source="source-a", relevance=0.8)
            )
        )
        + "\n",
        encoding="utf-8",
    )

    result = ranking_evaluation.main(
        ["evaluate", "--input", str(queue), "--min-labeled", "1"]
    )
    payload = json.loads(capsys.readouterr().out)

    assert result == 1
    assert payload["relevance"]["labeled"] == 0
    assert payload["gate"]["status"] == "failed"
