"""Machine-readable QDev ecosystem contracts for QAZ.FUND."""

from __future__ import annotations

from typing import Any

from qazstack import __version__ as qazstack_version
from qazstack.contracts import validate_consumer_contract

from api.integration_versions import (
    AVDS_PACKAGE,
    AVDS_PATTERN_PACKAGE,
    AVDS_PATTERN_SOURCE_REVISION,
    AVDS_PATTERN_VERSION,
    AVDS_SOURCE_REVISION,
    AVDS_VERIFIED_AT,
    AVDS_VERSION,
    QAZSTACK_VERSION,
)
from core.public_contract import DATASET_SCHEMA_VERSION, SCHEMA_VERSION
from core.qazcompute_bridge import (
    DEADLINE_ANOMALY_MODEL,
    DEADLINE_ANOMALY_SCHEMA_VERSION,
    DUPLICATE_CLUSTER_MODEL,
    DUPLICATE_CLUSTER_SCHEMA_VERSION,
    EVIDENCE_READINESS_MODEL,
    EVIDENCE_READINESS_SCHEMA_VERSION,
    SOURCE_FRESHNESS_MODEL,
    SOURCE_FRESHNESS_SCHEMA_VERSION,
)

QAZSTACK_SOURCE_REVISION = "986cfca3779f74c0f734ed174e7a28c944fd30f7"
QAZSTACK_SCHEMA_DIGEST = (
    "sha256:6ca8e38c09315d02993e3600b7a05dc23d695cd152545f8a970566e303fc158c"
)
QAZSTACK_VERIFIED_AT = "2026-08-04T00:47:27Z"


def _verified_qazstack_version() -> str:
    if qazstack_version != QAZSTACK_VERSION:
        raise RuntimeError(
            "QazStack runtime mismatch: "
            f"loaded {qazstack_version}, expected {QAZSTACK_VERSION}"
        )
    return qazstack_version


def _url(origin: str, path: str) -> str:
    return f"{origin.rstrip('/')}/{path.lstrip('/')}"


def qazstack_consumer_contract(origin: str) -> dict[str, Any]:
    """Return the strict QazStack production-consumer contract."""

    payload: dict[str, Any] = {
        "schema_version": "qazstack-consumer-v1",
        "project_id": "qaz-fund",
        "product_name": "QAZ.FUND",
        "lifecycle": "production",
        "integration_mode": "python-package",
        "qazstack_version": _verified_qazstack_version(),
        "source_revision": QAZSTACK_SOURCE_REVISION,
        "primitives": [
            "collectors-and-entity-pipeline",
            "content-api",
            "core-foundation",
            "opportunity-public-contract",
            "opportunity-ranking-evaluation",
            "reports-and-export",
        ],
        "owns": [
            "grant-opportunity-ranking",
            "kazakhstan-fit-policy",
            "source-suitability-gate",
        ],
        "depends_on": ["qazstack", "postgres"],
        "forbidden_capabilities": [
            "fake-application-submission",
            "unverified-source-promotion",
            "secret-export",
        ],
        "evidence": {
            "source_files": [
                "core/qazstack_bridge.py",
                "core/public_contract.py",
                "core/ranking_evaluation.py",
                "core/source_text.py",
                "requirements-prod.txt",
                "tests/test_qazstack_adoption.py",
                "tests/test_qazstack_bridge.py",
            ],
            "test_commands": [
                ".venv/bin/python -m pytest -q",
                "python -m scripts.production_smoke --base-url https://qaz.fund",
            ],
            "runtime_urls": [
                _url(origin, "/.well-known/qazstack-consumer.json"),
                _url(origin, "/ready"),
            ],
            "verified_at": QAZSTACK_VERIFIED_AT,
            "environment": "production",
            "source_revision": QAZSTACK_SOURCE_REVISION,
            "schema_digest": QAZSTACK_SCHEMA_DIGEST,
            "checked_by": "qazfund-release-gate",
        },
        "owner": "qdev-platform",
        "notes": (
            "QAZ.FUND imports the immutable QazStack release wheel. Product-specific "
            "Kazakhstan relevance rules remain owned by QAZ.FUND."
        ),
    }
    validate_consumer_contract(payload, strict=True)
    return payload


def avds_ui_contract(*, coverage: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the AV DS 4 compatibility boundary for the server-rendered UI."""

    return {
        "schema_version": "avds-ui-contract-v1",
        "contract_id": "avds-ui-contract",
        "avds_source": {
            "site": "https://avds.digital",
            "package": AVDS_PACKAGE,
            "version": AVDS_VERSION,
            "source_revision": AVDS_SOURCE_REVISION,
        },
        "verification": {
            "checked_at": AVDS_VERIFIED_AT,
            "public_site_status": "live",
            "reference_release": AVDS_VERSION,
            "note": (
                f"The official AV DS release contract identifies release {AVDS_VERSION}. "
                "QAZ.FUND composes its server-rendered adapter from documented "
                "tokens and component semantics; it does not import the React package."
            ),
        },
        "coverage": coverage
        or {
            "basis": "route-registry-unavailable",
            "route_count": 0,
            "covered": 0,
            "total": 0,
            "percent": 0.0,
            "gaps": ["runtime route registry was not supplied"],
        },
        "component_families": [
            {
                "id": "foundation",
                "components": [
                    "Alert",
                    "Breadcrumbs",
                    "Button",
                    "Card",
                    "Checkbox",
                    "FormField",
                    "Progress",
                    "Table",
                    "TextInput",
                    "Textarea",
                ],
                "qazstack_relationship": (
                    "Stable AV DS primitives provide interaction and accessibility "
                    "semantics. QAZ.FUND renders equivalent server-side markup."
                ),
            },
            {
                "id": "navigation-filtering",
                "components": [
                    "PillTabs",
                    "FilterChipRow",
                    "SearchField",
                    "FilterStateSummary",
                    "QuickLinksRail",
                ],
                "qazstack_relationship": (
                    "QAZ.FUND keeps filtering behavior local and follows AV DS 4 "
                    "navigation and input semantics through its SSR adapter. "
                    "The visible active-query summary follows the runtime-neutral "
                    "@av/patterns contract."
                ),
            },
            {
                "id": "data-listing",
                "components": ["DataTable", "PaginatedList", "ScrollArea"],
                "qazstack_relationship": (
                    "Opportunity and source lists use stable ids, bounded result sets, "
                    "and explicit loading or empty states."
                ),
            },
            {
                "id": "evidence",
                "components": [
                    "EvidenceSummary",
                    "EvidenceDisclosure",
                    "ProvenanceCard",
                    "ProvenanceTable",
                    "SourceCard",
                    "TrustStrip",
                ],
                "qazstack_relationship": (
                    "Official source, freshness, coverage, and limitations remain "
                    "visible beside public opportunity data through the "
                    "@av/patterns evidence contract."
                ),
            },
            {
                "id": "explainable-results",
                "components": ["DecisionSummary", "FitPill", "OpportunityCard"],
                "qazstack_relationship": (
                    "QAZ.FUND owns relevance and action-priority calculation. "
                    "AV DS only standardizes how the resulting reasons and limits "
                    "are presented."
                ),
            },
            {
                "id": "guidance",
                "components": [
                    "ActionPath",
                    "DocumentCard",
                    "EditorialLeadRail",
                    "LiteReadingSurface",
                    "TrustFactsPanel",
                ],
                "qazstack_relationship": (
                    "AV DS standardizes ordered guidance, related documents, and "
                    "compact trust facts. QAZ.FUND owns the wording, applicability, "
                    "routes, and submission state."
                ),
            },
            {
                "id": "metrics",
                "components": [
                    "DataQualityScorecard",
                    "MiniMetric",
                    "PublicSummaryStrip",
                ],
                "qazstack_relationship": (
                    "Catalog, quality, and operator summaries expose compact, "
                    "comparable counts with named measures."
                ),
            },
            {
                "id": "application-preparation",
                "components": [
                    "Alert",
                    "Button",
                    "Card",
                    "Checkbox",
                    "FormField",
                    "Progress",
                    "TextInput",
                    "Textarea",
                ],
                "qazstack_relationship": (
                    "The application workspace stores draft content only in the "
                    "browser. It does not submit forms or infer eligibility."
                ),
            },
            {
                "id": "ops-status",
                "components": ["StatusBadge", "StatePanel", "ServiceStatusCard"],
                "qazstack_relationship": (
                    "Readiness and source freshness use semantic status labels, not "
                    "color alone."
                ),
            },
        ],
        "runtime_neutral_patterns": {
            "package": AVDS_PATTERN_PACKAGE,
            "version": AVDS_PATTERN_VERSION,
            "source_revision": AVDS_PATTERN_SOURCE_REVISION,
            "source": (
                "https://github.com/belilovsky/av-platform-core/tree/"
                f"{AVDS_PATTERN_SOURCE_REVISION}/packages/patterns"
            ),
            "adopted": [
                "evidence-summary",
                "filter-state-summary",
                "decision-summary",
                "evidence-disclosure",
                "action-path",
            ],
            "rendering": "server-rendered-local-adapter",
            "calculation_ownership": "qaz-fund",
        },
        "pattern_exchange": {
            "direction": "two-way",
            "published_at": "2026-07-26",
            "adopted_existing": [
                "PublicSummaryStrip",
                "QuickLinksRail",
                "TrustStrip",
                "TrustFactsPanel",
                "DocumentCard",
                "EditorialLeadRail",
                "LiteReadingSurface",
            ],
            "absorbed_from_qaz_fund": [
                {
                    "component": "EvidenceDisclosure",
                    "pattern": "evidence-disclosure",
                    "source_surface": "public opportunity source excerpts",
                },
                {
                    "component": "ActionPath",
                    "pattern": "action-path",
                    "source_surface": "preparation and application guidance",
                },
            ],
            "ownership_boundary": (
                "QAZ.FUND owns source selection, eligibility, ranking, deadlines, "
                "routes, localization, and submission state. AV DS owns reusable "
                "presentation contracts and component semantics."
            ),
        },
        "local_recipes": {
            "lifecycle": "product-owned",
            "package_claim": False,
            "recipes": [
                "application-workspace",
                "catalogue-composition",
                "change-ledger",
                "deadline-distribution",
                "machine-entrypoints",
                "source-coverage",
            ],
            "boundary": (
                "Charts, analytics composition, change semantics, and application "
                "draft behavior remain QAZ.FUND recipes. AV DS supplies the tokens "
                "and stable primitive contracts used to render them."
            ),
        },
        "do_not_duplicate": [
            "alert",
            "badge",
            "button",
            "card",
            "kpi-card",
            "progress",
            "table",
            "toast",
        ],
        "qazstack_behavior_sources": [
            "collectors-and-entity-pipeline",
            "opportunity-public-contract",
            "opportunity-ranking-evaluation",
            "observability-and-ui",
            "pagination-and-listing",
        ],
    }


def qazpipe_source_contract(origin: str) -> dict[str, Any]:
    """Describe the stable read-only handoff from QAZ.FUND to QazPipe."""

    api_index = _url(origin, "/api/v1/opportunities")
    bulk_export = _url(origin, "/api/v1/opportunities.ndjson")
    return {
        "schema_version": "qazpipe-pull-source-v1",
        "source_id": "qazfund-opportunities",
        "producer": {
            "project_id": "qaz-fund",
            "service": "QAZ.FUND",
            "lifecycle": "production",
        },
        "mode": "pull",
        "direction": "outbound-read-only",
        "data_classification": "public",
        "record_contract": {
            "dataset": DATASET_SCHEMA_VERSION,
            "opportunity": SCHEMA_VERSION,
            "schema": _url(origin, "/api/v1/schema"),
        },
        "endpoints": {
            "index": api_index,
            "bulk_ndjson": bulk_export,
            "detail_template": _url(origin, "/api/v1/opportunities/{id}"),
            "coverage": _url(origin, "/coverage"),
            "readiness": _url(origin, "/ready"),
        },
        "pull": {
            "default_language": "ru",
            "limit": {"default": 500, "maximum": 5000},
            "offset_parameter": "offset",
            "limit_parameter": "limit",
            "conditional_requests": ["ETag", "Last-Modified"],
            "recommended_interval_minutes": 60,
        },
        "checkpoint": {
            "strategy": "dataset-revision-and-offset",
            "dataset_revision_field": "dataset_revision",
            "stable_record_id_field": "id",
            "content_revision_field": "provenance.content_hash",
        },
        "idempotency": {
            "entity_key": "id",
            "content_key": "provenance.content_hash",
            "source_key": "source.url",
        },
        "required_provenance": [
            "source.id",
            "source.url",
            "timestamps.discovered_at",
            "provenance.evidence_state",
            "provenance.verification_method",
            "provenance.content_hash",
        ],
        "qazlake_handoff": {
            "status": "brokered-activation-gated",
            "direct_write": False,
            "allowed_records": "public opportunity contract only",
            "forbidden_fields": [
                "raw",
                "private credentials",
                "saved selections",
                "operator notes",
            ],
            "activation_requires": [
                "approved target table",
                "retention policy",
                "dry-run artifact",
                "idempotency proof",
                "rollback procedure",
            ],
        },
    }


def qazcompute_profile_contract(origin: str) -> dict[str, Any]:
    """Publish the deterministic QazCompute-compatible runtime profiles."""

    return {
        "schema_version": "qazcompute-profile-contract-v1",
        "project_id": "qaz-fund",
        "execution": {
            "mode": "local-deterministic-fallback",
            "runtime_status": "proven",
            "remote_execution_active": False,
            "decision_ready": False,
        },
        "profiles": [
            {
                "schema_version": EVIDENCE_READINESS_SCHEMA_VERSION,
                "model": EVIDENCE_READINESS_MODEL,
                "projection": "opportunities[].raw.qazcompute_evidence_readiness",
                "endpoint": _url(origin, "/opportunities?compact=false"),
            },
            {
                "schema_version": DEADLINE_ANOMALY_SCHEMA_VERSION,
                "model": DEADLINE_ANOMALY_MODEL,
                "projection": "opportunities[].raw.qazcompute_deadline_anomaly",
                "endpoint": _url(origin, "/opportunities?compact=false"),
            },
            {
                "schema_version": SOURCE_FRESHNESS_SCHEMA_VERSION,
                "model": SOURCE_FRESHNESS_MODEL,
                "projection": "sources[].qazcompute_source_freshness",
                "endpoint": _url(origin, "/coverage"),
            },
            {
                "schema_version": DUPLICATE_CLUSTER_SCHEMA_VERSION,
                "model": DUPLICATE_CLUSTER_MODEL,
                "projection": "duplicate candidates",
                "endpoint": _url(origin, "/opportunities/duplicate-candidates"),
            },
        ],
        "safety": {
            "public_safe_features_only": True,
            "publication_authority": False,
            "eligibility_authority": False,
            "funding_decision_authority": False,
        },
    }


def ecosystem_manifest(origin: str) -> dict[str, Any]:
    """Describe implemented and deliberately deferred ecosystem boundaries."""

    opportunities = _url(origin, "/opportunities")
    opportunities_ndjson = _url(origin, "/opportunities.ndjson")
    opportunity_history = _url(origin, "/opportunities/{id}/history.json")
    return {
        "schema_version": "qdev-ecosystem-integration-v1",
        "project": {
            "id": "qaz-fund",
            "name": "QAZ.FUND",
            "lifecycle": "production",
            "role": "public-opportunity-navigator",
        },
        "contracts": {
            "qazstack": _url(origin, "/.well-known/qazstack-consumer.json"),
            "avds4": _url(origin, "/.well-known/avds-ui-contract.json"),
            "notifications": _url(origin, "/.well-known/notification-contract.json"),
            "source_onboarding": _url(origin, "/.well-known/source-onboarding.json"),
            "openapi": _url(origin, "/openapi.json"),
            "discovery": _url(origin, "/site-discovery.json"),
        },
        "data_plane": {
            "read_only_feed": opportunities,
            "machine_export": opportunities_ndjson,
            "history_read_model": opportunity_history,
            "history_schema": "history.v1",
            "format": "application/json",
            "formats": ["application/json", "application/x-ndjson"],
            "pagination": {"limit": "1..5000", "offset": "integer >= 0"},
            "provenance_fields": [
                "source",
                "source_url",
                "discovered_at",
                "raw.provenance",
            ],
            "machine_export_fields": [
                "source",
                "source_url",
                "discovered_at",
                "evidence_state",
                "raw.provenance",
            ],
            "write_api": False,
        },
        "integrations": {
            "qazstack": {
                "status": "runtime-proven",
                "mode": "python-package",
                "version": qazstack_version,
                "source_revision": QAZSTACK_SOURCE_REVISION,
                "adopted_primitives": [
                    "opportunity-public-contract",
                    "opportunity-ranking-evaluation",
                ],
            },
            "avds4": {
                "status": "adapter-aligned",
                "mode": "server-rendered-local-adapter",
                "target_package": AVDS_PACKAGE,
                "target_version": AVDS_VERSION,
                "direct_package_import": False,
            },
            "qazpipe": {
                "status": "producer-ready",
                "mode": "pull",
                "source": _url(origin, "/api/v1/opportunities.ndjson"),
                "contract": _url(origin, "/.well-known/qazpipe-source.json"),
                "activation": "consumer-controlled",
            },
            "qazlake": {
                "status": "brokered-via-qazpipe",
                "direct_write": False,
                "allowed_data": "public opportunity records and source provenance",
                "handoff_contract": _url(origin, "/.well-known/qazpipe-source.json"),
                "activation": "schema-retention-and-dry-run-gated",
            },
            "qazgeo": {
                "status": "deferred-no-geometry",
                "product_owner": "qaz-fund",
                "reason": (
                    "Current records expose region classes but not verified coordinates. "
                    "A decorative or inferred map is intentionally not published."
                ),
                "review_trigger": (
                    "Verified coordinates or an authoritative region geometry reference "
                    "becomes available for published records."
                ),
            },
            "qazcompute": {
                "status": "local-runtime-proven",
                "contract": _url(origin, "/.well-known/qazcompute-profiles.json"),
                "execution_mode": "local-deterministic-fallback",
                "remote_execution_active": False,
                "enabled_profiles": [
                    "evidence_readiness.v1",
                    "deadline_anomaly.v1",
                    "source_freshness.v1",
                    "duplicate_cluster.v1",
                ],
                "public_fields": [
                    "raw.qazcompute_evidence_readiness",
                    "raw.qazcompute_deadline_anomaly",
                    "coverage.sources[].qazcompute_source_freshness",
                ],
                "public_endpoints": [
                    _url(origin, "/opportunities/duplicate-candidates"),
                ],
                "decision_ready": False,
                "candidate_jobs": [],
            },
            "notifications": {
                "status": "not-enabled",
                "mode": "contract-only",
                "delivery_enabled": False,
                "reason": (
                    "Identity, explicit opt-in, delivery receipts, unsubscribe, "
                    "deletion and retention rules are not enabled yet."
                ),
            },
            "edpol": {
                "status": "query-ready",
                "mode": "read-only",
                "education_feed": (f"{opportunities}?lang=ru&limit=100&tag=education"),
            },
        },
        "ownership": {
            "product_rules": "qaz-fund",
            "shared_contracts": "qazstack",
            "visual_system": "avds4",
            "ingestion_orchestration": "qazpipe",
            "evidence_archive": "qazlake",
            "geospatial_truth": "qazgeo",
            "batch_compute": "qazcompute",
        },
    }
