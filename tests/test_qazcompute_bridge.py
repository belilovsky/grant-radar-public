from __future__ import annotations

from datetime import date

from core.models import Opportunity, OpportunityType
from core.qazcompute_bridge import opportunity_evidence_readiness


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
