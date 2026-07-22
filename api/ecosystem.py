"""Machine-readable QDev ecosystem contracts for QAZ.FUND."""

from __future__ import annotations

from typing import Any

from qazstack import __version__ as qazstack_version
from qazstack.contracts import validate_consumer_contract

QAZSTACK_SOURCE_REVISION = "a0a4bfc6ea6b2fce205afe24fbf732fb3de3bc68"
QAZSTACK_SCHEMA_DIGEST = (
    "sha256:6ca8e38c09315d02993e3600b7a05dc23d695cd152545f8a970566e303fc158c"
)
QAZSTACK_VERIFIED_AT = "2026-07-22T20:06:40Z"
AVDS_PACKAGE = "@sgeo/ui-kit"
AVDS_VERSION = "4.3.2"
AVDS_PATTERN_PACKAGE = "@av/patterns"
AVDS_PATTERN_VERSION = "0.1.0"


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
        "qazstack_version": qazstack_version,
        "source_revision": QAZSTACK_SOURCE_REVISION,
        "primitives": [
            "collectors-and-entity-pipeline",
            "content-api",
            "core-foundation",
            "reports-and-export",
        ],
        "evidence": {
            "source_files": [
                "core/qazstack_bridge.py",
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


def avds_ui_contract() -> dict[str, Any]:
    """Return the AV DS 4 compatibility boundary for the server-rendered UI."""

    return {
        "schema_version": "avds-ui-contract-v1",
        "contract_id": "avds-ui-contract",
        "avds_source": {
            "site": "https://ui.qdev.run",
            "package": AVDS_PACKAGE,
            "version": AVDS_VERSION,
        },
        "component_families": [
            {
                "id": "navigation-filtering",
                "components": [
                    "PillTabs",
                    "FilterChipRow",
                    "SearchField",
                    "FilterStateSummary",
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
                    "ProvenanceCard",
                    "ProvenanceTable",
                    "SourceCard",
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
                "id": "metrics",
                "components": ["MiniMetric", "PublicSummaryStrip"],
                "qazstack_relationship": (
                    "Catalog and operator summaries expose compact, comparable counts."
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
            "adopted": [
                "evidence-summary",
                "filter-state-summary",
                "decision-summary",
            ],
            "rendering": "server-rendered-local-adapter",
            "calculation_ownership": "qaz-fund",
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
            "observability-and-ui",
            "pagination-and-listing",
        ],
    }


def ecosystem_manifest(origin: str) -> dict[str, Any]:
    """Describe implemented and deliberately deferred ecosystem boundaries."""

    opportunities = _url(origin, "/opportunities")
    opportunities_ndjson = _url(origin, "/opportunities.ndjson")
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
            "openapi": _url(origin, "/openapi.json"),
            "discovery": _url(origin, "/site-discovery.json"),
        },
        "data_plane": {
            "read_only_feed": opportunities,
            "machine_export": opportunities_ndjson,
            "format": "application/json",
            "formats": ["application/json", "application/x-ndjson"],
            "pagination": {"limit": "1..5000", "offset": "integer >= 0"},
            "provenance_fields": ["source", "source_url", "discovered_at"],
            "machine_export_fields": [
                "source",
                "source_url",
                "discovered_at",
                "evidence_state",
            ],
            "write_api": False,
        },
        "integrations": {
            "qazstack": {
                "status": "runtime-proven",
                "mode": "python-package",
                "version": qazstack_version,
            },
            "avds4": {
                "status": "adapter-aligned",
                "mode": "server-rendered-local-adapter",
                "target_package": AVDS_PACKAGE,
                "target_version": AVDS_VERSION,
                "direct_package_import": False,
            },
            "qazpipe": {
                "status": "interface-ready",
                "mode": "pull",
                "source": opportunities,
                "activation": "consumer-controlled",
            },
            "qazlake": {
                "status": "brokered-via-qazpipe",
                "direct_write": False,
                "allowed_data": "public opportunity records and source provenance",
            },
            "qazgeo": {
                "status": "deferred-no-geometry",
                "reason": (
                    "Current records expose region classes but not verified coordinates. "
                    "A decorative or inferred map is intentionally not published."
                ),
            },
            "qazcompute": {
                "status": "candidate-not-enabled",
                "candidate_jobs": [
                    "cross-source duplicate clustering",
                    "deadline anomaly detection",
                    "source freshness scoring",
                ],
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
