from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from core.models import Opportunity, OpportunityType
from core.qazcompute_bridge import (
    duplicate_cluster_envelope,
    opportunity_deadline_anomaly,
    opportunity_evidence_readiness,
    source_freshness_envelope,
)


def _opportunity(**kwargs) -> Opportunity:
    defaults = {
        "source": "astana_hub",
        "source_url": "https://example.org/program",
        "type": OpportunityType.GRANT,
        "title": "Kazakhstan startup grant",
        "summary": "Support for Kazakhstan technology projects.",
        "tags": ["kazakhstan", "startup"],
    }
    defaults.update(kwargs)
    return Opportunity(**defaults)


def test_qazcompute_evidence_readiness_envelope_is_public_safe() -> None:
    item = _opportunity(
        amount_min=1000,
        deadline=date(2027, 4, 1),
        eligibility=["Kazakhstan registered startups"],
    )

    readiness = opportunity_evidence_readiness(item)

    assert readiness["schema_version"] == "evidence_readiness.v1"
    assert readiness["provider"] == "qazfund-local-fallback"
    assert readiness["decision_ready"] is False
    assert readiness["tier"] == "ready"
    assert readiness["blockers"] == []
    assert readiness["features"] == {
        "evidence_count": 4,
        "direct_evidence_count": 4,
        "source_count": 1,
        "required_evidence_count": 4,
        "required_source_count": 1,
        "direct_evidence_ratio": 1.0,
        "evidence_ratio": 1.0,
        "source_ratio": 1.0,
        "nlp_coverage_pct": None,
        "require_direct_evidence": True,
        "privacy_flag_count": 0,
        "review_blocker_count": 0,
    }


def test_qazcompute_evidence_readiness_marks_missing_application_facts() -> None:
    readiness = opportunity_evidence_readiness(_opportunity())

    assert readiness["tier"] == "watch"
    assert readiness["score"] < 85
    assert readiness["warnings"] == [
        "missing_deadline",
        "missing_amount",
        "missing_eligibility",
    ]


def test_qazcompute_deadline_anomaly_marks_open_past_deadline() -> None:
    item = _opportunity(
        deadline=date(2026, 7, 1),
        opportunity_status="open",
        discovered_at=datetime(2026, 6, 1, tzinfo=UTC),
    )

    anomaly = opportunity_deadline_anomaly(
        item,
        checked_at=datetime(2026, 7, 24, tzinfo=UTC),
    )

    assert anomaly["schema_version"] == "deadline_anomaly.v1"
    assert anomaly["provider"] == "qazfund-local-fallback"
    assert anomaly["decision_ready"] is False
    assert anomaly["tier"] == "blocked"
    assert anomaly["anomalies"] == ["open_after_deadline"]
    assert anomaly["features"]["runway_days"] < 0


def test_qazcompute_source_freshness_envelope_reports_stale_source() -> None:
    freshness = source_freshness_envelope(
        source_id="world_bank_kazakhstan",
        last_success_at=datetime(2026, 7, 20, tzinfo=UTC),
        checked_at=datetime(2026, 7, 24, tzinfo=UTC),
        expected_interval_hours=72,
    )

    assert freshness["schema_version"] == "source_freshness.v1"
    assert freshness["provider"] == "qazfund-local-fallback"
    assert freshness["decision_ready"] is False
    assert freshness["tier"] == "watch"
    assert freshness["warnings"] == ["source_lagging"]
    assert freshness["features"]["age_hours"] == 96


def test_qazcompute_source_freshness_envelope_reports_unknown_source() -> None:
    freshness = source_freshness_envelope(
        source_id="empty_source",
        last_success_at=None,
        checked_at=datetime.now(UTC),
        expected_interval_hours=timedelta(days=3).total_seconds() / 3600,
    )

    assert freshness["tier"] == "unknown"
    assert freshness["score"] == 0
    assert freshness["blockers"] == ["missing_last_success"]


def test_qazcompute_duplicate_cluster_envelope_is_review_only() -> None:
    first = _opportunity(
        title="Kazakhstan innovation grant for startups",
        summary="Support for Kazakhstan technology startups.",
        source_url="https://example.org/program",
    )
    second = _opportunity(
        title="Kazakhstan innovation grant for startups",
        summary="Technology startup support in Kazakhstan.",
        source_url="https://www.example.org/program/",
    )
    third = _opportunity(
        title="Agritech accelerator for Central Asia",
        summary="Acceleration program for agriculture companies.",
        source_url="https://other.example.org/agri",
    )

    payload = duplicate_cluster_envelope(
        [first, second, third],
        related_threshold=0.45,
    )

    assert payload["schema_version"] == "duplicate_cluster.v1"
    assert payload["provider"] == "qazfund-local-fallback"
    assert payload["decision_ready"] is False
    assert payload["cluster_count"] == 1
    assert payload["pairs"][0]["tier"] == "duplicate_candidate"
    assert "same_canonical_url" in payload["pairs"][0]["reasons"]
