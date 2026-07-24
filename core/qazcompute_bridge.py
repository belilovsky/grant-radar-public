"""QazCompute-compatible task envelopes for public QAZ.FUND records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from core.models import Opportunity

EVIDENCE_READINESS_SCHEMA_VERSION = "evidence_readiness.v1"
EVIDENCE_READINESS_MODEL = "evidence-readiness-deterministic-v1"

ReadinessTier = Literal["ready", "watch", "blocked"]


@dataclass(frozen=True, slots=True)
class EvidenceReadinessFeatures:
    """Normalized public-safe features sent to the QazCompute task profile."""

    evidence_count: int
    direct_evidence_count: int
    source_count: int
    required_evidence_count: int
    required_source_count: int
    direct_evidence_ratio: float
    evidence_ratio: float
    source_ratio: float
    nlp_coverage_pct: float | None
    require_direct_evidence: bool
    privacy_flag_count: int
    review_blocker_count: int


@dataclass(frozen=True, slots=True)
class EvidenceReadinessEnvelope:
    """Read-only QazCompute evidence-readiness result envelope."""

    schema_version: str
    provider: str
    model: str
    quality_tier: str
    decision_ready: bool
    id: str
    score: float
    tier: ReadinessTier
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    features: EvidenceReadinessFeatures

    def to_json(self) -> dict[str, Any]:
        """Return the JSON-safe public API representation."""

        return {
            "schema_version": self.schema_version,
            "provider": self.provider,
            "model": self.model,
            "quality_tier": self.quality_tier,
            "decision_ready": self.decision_ready,
            "id": self.id,
            "score": self.score,
            "tier": self.tier,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "features": {
                "evidence_count": self.features.evidence_count,
                "direct_evidence_count": self.features.direct_evidence_count,
                "source_count": self.features.source_count,
                "required_evidence_count": self.features.required_evidence_count,
                "required_source_count": self.features.required_source_count,
                "direct_evidence_ratio": self.features.direct_evidence_ratio,
                "evidence_ratio": self.features.evidence_ratio,
                "source_ratio": self.features.source_ratio,
                "nlp_coverage_pct": self.features.nlp_coverage_pct,
                "require_direct_evidence": self.features.require_direct_evidence,
                "privacy_flag_count": self.features.privacy_flag_count,
                "review_blocker_count": self.features.review_blocker_count,
            },
        }


def opportunity_evidence_readiness(item: Opportunity) -> dict[str, Any]:
    """Return a QazCompute-compatible evidence-readiness envelope.

    QAZ.FUND keeps this local fallback deterministic until the private
    QazCompute task endpoint is wired into the server-side sync path. The public
    API shape matches `evidence_readiness.v1`, so consumers do not need a second
    contract when remote execution is enabled.
    """

    raw = item.raw if isinstance(item.raw, dict) else {}
    present = {
        "deadline": bool(item.deadline or raw.get("deadline_policy") == "rolling"),
        "amount": bool(
            item.amount_min is not None
            or item.amount_max is not None
            or raw.get("amount_raw")
        ),
        "eligibility": bool(item.eligibility or raw.get("eligibility")),
        "application": bool(item.source_url or raw.get("application_url")),
    }
    missing_fields = tuple(name for name, available in present.items() if not available)
    evidence_count = sum(present.values())
    direct_evidence_count = evidence_count if item.source_url else 0
    source_count = 1 if item.source else 0
    required_evidence_count = len(present)
    required_source_count = 1
    direct_ratio = _ratio(direct_evidence_count, max(evidence_count, 1))
    evidence_ratio = min(1.0, _ratio(evidence_count, required_evidence_count))
    source_ratio = min(1.0, _ratio(source_count, required_source_count))

    weighted_features = (
        (0.42, evidence_ratio),
        (0.28, source_ratio),
        (0.30, direct_ratio),
    )
    total_weight = sum(weight for weight, _value in weighted_features)
    score = round(
        100.0
        * sum(weight * value for weight, value in weighted_features)
        / total_weight,
        1,
    )

    blockers: list[str] = []
    warnings = [f"missing_{field}" for field in missing_fields]
    if direct_evidence_count == 0:
        blockers.append("missing_direct_evidence")
    if source_count < required_source_count:
        blockers.append("insufficient_source_count")

    tier: ReadinessTier
    if blockers:
        tier = "blocked"
    elif score >= 85:
        tier = "ready"
    else:
        tier = "watch"

    return EvidenceReadinessEnvelope(
        schema_version=EVIDENCE_READINESS_SCHEMA_VERSION,
        provider="qazfund-local-fallback",
        model=EVIDENCE_READINESS_MODEL,
        quality_tier="deterministic",
        decision_ready=False,
        id=str(item.id),
        score=score,
        tier=tier,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        features=EvidenceReadinessFeatures(
            evidence_count=evidence_count,
            direct_evidence_count=direct_evidence_count,
            source_count=source_count,
            required_evidence_count=required_evidence_count,
            required_source_count=required_source_count,
            direct_evidence_ratio=round(direct_ratio, 4),
            evidence_ratio=round(evidence_ratio, 4),
            source_ratio=round(source_ratio, 4),
            nlp_coverage_pct=None,
            require_direct_evidence=True,
            privacy_flag_count=0,
            review_blocker_count=0,
        ),
    ).to_json()


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0
