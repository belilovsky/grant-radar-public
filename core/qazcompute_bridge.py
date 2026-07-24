"""QazCompute-compatible task envelopes for public QAZ.FUND records."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Literal
from urllib.parse import urlsplit

from core.models import Opportunity

EVIDENCE_READINESS_SCHEMA_VERSION = "evidence_readiness.v1"
EVIDENCE_READINESS_MODEL = "evidence-readiness-deterministic-v1"
DEADLINE_ANOMALY_SCHEMA_VERSION = "deadline_anomaly.v1"
DEADLINE_ANOMALY_MODEL = "deadline-anomaly-deterministic-v1"
SOURCE_FRESHNESS_SCHEMA_VERSION = "source_freshness.v1"
SOURCE_FRESHNESS_MODEL = "source-freshness-deterministic-v1"
DUPLICATE_CLUSTER_SCHEMA_VERSION = "duplicate_cluster.v1"
DUPLICATE_CLUSTER_MODEL = "duplicate-cluster-deterministic-v1"

ReadinessTier = Literal["ready", "watch", "blocked"]
DeadlineTier = Literal["clean", "watch", "blocked"]
FreshnessTier = Literal["fresh", "watch", "stale", "unknown"]

_WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)
_STOPWORDS = {
    "and",
    "для",
    "және",
    "the",
    "with",
    "for",
    "of",
    "in",
    "on",
    "to",
    "по",
}


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


@dataclass(frozen=True, slots=True)
class DeadlineAnomalyEnvelope:
    """Read-only QazCompute deadline anomaly result envelope."""

    schema_version: str
    provider: str
    model: str
    quality_tier: str
    decision_ready: bool
    id: str
    tier: DeadlineTier
    anomalies: tuple[str, ...]
    warnings: tuple[str, ...]
    features: dict[str, float | int | bool | str | None]

    def to_json(self) -> dict[str, Any]:
        """Return the JSON-safe public API representation."""

        return {
            "schema_version": self.schema_version,
            "provider": self.provider,
            "model": self.model,
            "quality_tier": self.quality_tier,
            "decision_ready": self.decision_ready,
            "id": self.id,
            "tier": self.tier,
            "anomalies": list(self.anomalies),
            "warnings": list(self.warnings),
            "features": self.features,
        }


@dataclass(frozen=True, slots=True)
class SourceFreshnessEnvelope:
    """Read-only QazCompute source freshness result envelope."""

    schema_version: str
    provider: str
    model: str
    quality_tier: str
    decision_ready: bool
    id: str
    score: float
    tier: FreshnessTier
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    features: dict[str, float | int | bool | None]

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
            "features": self.features,
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


def opportunity_deadline_anomaly(
    item: Opportunity, *, checked_at: datetime | None = None
) -> dict[str, Any]:
    """Return a QazCompute-compatible deadline anomaly envelope."""

    now = _aware(checked_at or datetime.now(UTC))
    raw = item.raw if isinstance(item.raw, dict) else {}
    deadline_at = _date_to_datetime(item.deadline)
    published_at = (
        _aware(item.discovered_at) if isinstance(item.discovered_at, datetime) else None
    )
    status = str(
        item.opportunity_status
        or item.lifecycle
        or raw.get("opportunity_status")
        or raw.get("status")
        or "open"
    )
    is_rolling = raw.get("deadline_policy") == "rolling"

    anomalies: list[str] = []
    warnings: list[str] = []
    is_open = status.strip().casefold() not in {
        "closed",
        "ended",
        "archived",
        "cancelled",
        "закрыт",
        "завершен",
    }

    if deadline_at and published_at and deadline_at < published_at:
        anomalies.append("deadline_before_publication")
    if is_open and deadline_at and deadline_at < now:
        anomalies.append("open_after_deadline")
    if is_open and not is_rolling and deadline_at is None:
        anomalies.append("missing_deadline")
    if is_rolling and deadline_at is not None:
        warnings.append("rolling_call_has_deadline")

    runway_days: float | None = None
    if deadline_at:
        runway_days = (deadline_at - now).total_seconds() / 86_400
        if is_open and 0 <= runway_days < 3:
            warnings.append("short_runway")

    tier: DeadlineTier = "blocked" if anomalies else "watch" if warnings else "clean"
    return DeadlineAnomalyEnvelope(
        schema_version=DEADLINE_ANOMALY_SCHEMA_VERSION,
        provider="qazfund-local-fallback",
        model=DEADLINE_ANOMALY_MODEL,
        quality_tier="deterministic",
        decision_ready=False,
        id=str(item.id),
        tier=tier,
        anomalies=tuple(_unique(anomalies)),
        warnings=tuple(_unique(warnings)),
        features={
            "status": status.strip().casefold() or "unknown",
            "is_open": is_open,
            "is_rolling": bool(is_rolling),
            "runway_days": round(runway_days, 2) if runway_days is not None else None,
            "minimum_runway_days": 3,
        },
    ).to_json()


def source_freshness_envelope(
    *,
    source_id: str,
    last_success_at: datetime | None,
    checked_at: datetime | None = None,
    expected_interval_hours: float = 72.0,
    item_count_24h: int | None = None,
) -> dict[str, Any]:
    """Return a QazCompute-compatible source freshness envelope."""

    now = _aware(checked_at or datetime.now(UTC))
    last_success = _aware(last_success_at) if last_success_at else None
    expected_interval_hours = max(0.25, float(expected_interval_hours))
    blockers: list[str] = []
    warnings: list[str] = []

    age_hours: float | None = None
    overdue_ratio: float | None = None
    if last_success is None:
        blockers.append("missing_last_success")
        score = 0.0
        tier: FreshnessTier = "unknown"
    else:
        age_hours = max(0.0, (now - last_success).total_seconds() / 3600)
        overdue_ratio = age_hours / expected_interval_hours
        score = max(0.0, min(100.0, 100.0 - max(0.0, overdue_ratio - 1.0) * 45.0))
        if overdue_ratio <= 1.0:
            tier = "fresh"
        elif overdue_ratio <= 2.0:
            tier = "watch"
            warnings.append("source_lagging")
        else:
            tier = "stale"
            blockers.append("source_stale")
    if item_count_24h == 0:
        warnings.append("no_items_last_24h")

    return SourceFreshnessEnvelope(
        schema_version=SOURCE_FRESHNESS_SCHEMA_VERSION,
        provider="qazfund-local-fallback",
        model=SOURCE_FRESHNESS_MODEL,
        quality_tier="deterministic",
        decision_ready=False,
        id=source_id,
        score=round(score, 1),
        tier=tier,
        blockers=tuple(_unique(blockers)),
        warnings=tuple(_unique(warnings)),
        features={
            "age_hours": round(age_hours, 2) if age_hours is not None else None,
            "expected_interval_hours": round(expected_interval_hours, 2),
            "overdue_ratio": (
                round(overdue_ratio, 4) if overdue_ratio is not None else None
            ),
            "failure_count": 0,
            "item_count_24h": item_count_24h,
        },
    ).to_json()


def duplicate_cluster_envelope(
    items: list[Opportunity],
    *,
    duplicate_threshold: float = 0.82,
    related_threshold: float = 0.62,
    max_pairs: int = 100,
) -> dict[str, Any]:
    """Return QazCompute-compatible duplicate candidates for public records."""

    if not 0.0 <= related_threshold <= duplicate_threshold <= 1.0:
        raise ValueError("Thresholds must satisfy 0 <= related <= duplicate <= 1.")
    if max_pairs < 1:
        raise ValueError("max_pairs must be at least 1.")

    ordered = sorted(items, key=lambda item: str(item.id))
    pairs: list[dict[str, Any]] = []
    duplicate_edges: list[tuple[str, str]] = []

    for left_index, left in enumerate(ordered[:-1]):
        for right in ordered[left_index + 1 :]:
            score, reasons = _duplicate_pair_score(left, right)
            if score < related_threshold:
                continue
            left_id = str(left.id)
            right_id = str(right.id)
            tier = (
                "duplicate_candidate"
                if score >= duplicate_threshold
                else "related_candidate"
            )
            pairs.append(
                {
                    "left_id": left_id,
                    "right_id": right_id,
                    "score": round(score, 4),
                    "tier": tier,
                    "reasons": reasons,
                }
            )
            if tier == "duplicate_candidate":
                duplicate_edges.append((left_id, right_id))

    pairs.sort(key=lambda row: (-float(row["score"]), row["left_id"], row["right_id"]))
    pairs = pairs[:max_pairs]
    pair_ids = {(row["left_id"], row["right_id"]) for row in pairs}
    duplicate_edges = [edge for edge in duplicate_edges if edge in pair_ids]
    clusters = _duplicate_clusters(
        [str(item.id) for item in ordered], duplicate_edges, pairs
    )

    return {
        "schema_version": DUPLICATE_CLUSTER_SCHEMA_VERSION,
        "provider": "qazfund-local-fallback",
        "model": DUPLICATE_CLUSTER_MODEL,
        "quality_tier": "deterministic",
        "decision_ready": False,
        "item_count": len(ordered),
        "pair_count": len(pairs),
        "cluster_count": len(clusters),
        "pairs": pairs,
        "clusters": clusters,
    }


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _date_to_datetime(value: date | datetime | None) -> datetime | None:
    if isinstance(value, datetime):
        return _aware(value)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=UTC)
    return None


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _duplicate_pair_score(
    left: Opportunity, right: Opportunity
) -> tuple[float, list[str]]:
    left_tokens = _tokens(left.title)
    right_tokens = _tokens(right.title)
    title_similarity = _jaccard(left_tokens, right_tokens)
    summary_similarity = _jaccard(_tokens(left.summary), _tokens(right.summary))
    same_source = left.source.strip().casefold() == right.source.strip().casefold()
    left_url = str(left.source_url)
    right_url = str(right.source_url)
    same_host = _host(left_url) == _host(right_url)

    score = title_similarity * 0.78 + summary_similarity * 0.12
    reasons: list[str] = []
    if title_similarity >= 0.8:
        reasons.append("title_overlap")
    if summary_similarity >= 0.7:
        reasons.append("summary_overlap")
    if same_host:
        score += 0.06
        reasons.append("same_host")
    if same_source:
        score += 0.04
        reasons.append("same_source")
    if _canonical_url(left_url) == _canonical_url(right_url):
        score = 1.0
        reasons.append("same_canonical_url")

    return min(1.0, score), _unique(reasons or ["lexical_overlap"])


def _duplicate_clusters(
    ids: list[str],
    edges: list[tuple[str, str]],
    pairs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    parent = {item_id: item_id for item_id in ids}

    def find(item_id: str) -> str:
        while parent[item_id] != item_id:
            parent[item_id] = parent[parent[item_id]]
            item_id = parent[item_id]
        return item_id

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[max(left_root, right_root)] = min(left_root, right_root)

    for left, right in edges:
        union(left, right)

    groups: dict[str, list[str]] = {}
    for item_id in ids:
        groups.setdefault(find(item_id), []).append(item_id)

    pair_by_items = {
        frozenset((str(pair["left_id"]), str(pair["right_id"]))): pair for pair in pairs
    }
    clusters: list[dict[str, Any]] = []
    for members in groups.values():
        if len(members) < 2:
            continue
        member_pairs = [
            pair_by_items[frozenset((left, right))]
            for index, left in enumerate(members[:-1])
            for right in members[index + 1 :]
            if frozenset((left, right)) in pair_by_items
        ]
        reasons = _unique(
            [str(reason) for pair in member_pairs for reason in pair.get("reasons", [])]
        )
        score = min((float(pair["score"]) for pair in member_pairs), default=0.0)
        sorted_members = sorted(members)
        clusters.append(
            {
                "id": "dup-" + "-".join(sorted_members),
                "item_ids": sorted_members,
                "score": round(score, 4),
                "reasons": reasons,
            }
        )
    clusters.sort(key=lambda cluster: (-float(cluster["score"]), str(cluster["id"])))
    return clusters


def _tokens(text: str | None) -> set[str]:
    return {
        normalized
        for token in _WORD_RE.findall(text or "")
        if len(normalized := token.casefold()) >= 3 and normalized not in _STOPWORDS
    }


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def _host(url: str) -> str:
    return urlsplit(url).netloc.casefold().removeprefix("www.")


def _canonical_url(url: str) -> str:
    parsed = urlsplit(url)
    return f"{parsed.netloc.casefold().removeprefix('www.')}{parsed.path.rstrip('/')}"
