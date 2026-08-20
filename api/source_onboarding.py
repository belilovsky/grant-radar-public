"""Public source-admission contract for the QAZ.FUND data plane.

The manifest keeps prospective integrations explicit without turning a blocked
or licensed source into an unverified scraper.  It is intentionally metadata
only: credentials, private responses and operator notes never enter the
public payload.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

SOURCE_ONBOARDING_SCHEMA_VERSION = "source-onboarding.v1"


def _candidate(
    slug: str,
    *,
    name: str,
    status: str,
    role: str,
    official_surface: str,
    access: str,
    next_action: str,
    checks: list[str],
) -> dict[str, Any]:
    return {
        "slug": slug,
        "name": name,
        "status": status,
        "role": role,
        "official_surface": official_surface,
        "access": access,
        "next_action": next_action,
        "admission_checks": checks,
    }


def source_onboarding_contract(
    origin: str,
    active_source_slugs: Iterable[str],
) -> dict[str, Any]:
    """Return the machine-readable source admission boundary.

    ``active_source_slugs`` is derived from the runtime parser registry so the
    manifest cannot claim an enabled adapter that is absent from production.
    """

    active = sorted(
        {str(slug).strip() for slug in active_source_slugs if str(slug).strip()}
    )
    return {
        "schema_version": SOURCE_ONBOARDING_SCHEMA_VERSION,
        "product": "qaz-fund",
        "policy": {
            "scope": "public opportunity and secondary context sources",
            "default_role": "read_only",
            "unverified_source_promotion": False,
            "raw_private_payloads": False,
            "credentials_in_public_contract": False,
            "required_evidence": [
                "official stable listing or API",
                "item-level source URL",
                "deterministic deduplication",
                "deadline and lifecycle handling",
                "mocked parser tests",
                "count-only production smoke",
            ],
        },
        "active": {
            "count": len(active),
            "slugs": active,
        },
        "candidates": [
            _candidate(
                "openalex_context",
                name="OpenAlex research context",
                status="candidate",
                role="secondary_context",
                official_surface="https://openalex.org/",
                access="public API; polite-pool and rate limits required",
                next_action=(
                    "Build a separate enrichment adapter for institutions, topics "
                    "and works; do not mix research records with open grants."
                ),
                checks=[
                    "retain OpenAlex IDs and source links",
                    "separate enrichment records from opportunity cards",
                    "cache responses and respect the API rate policy",
                ],
            ),
            _candidate(
                "data_egov_kz",
                name="data.egov.kz open datasets",
                status="gated",
                role="secondary_context",
                official_surface="https://data.egov.kz/pages/samples",
                access="official API key required for dataset reads",
                next_action=(
                    "Select grant-relevant datasets, approve the key and storage "
                    "terms, then add fixtures for metadata and freshness."
                ),
                checks=[
                    "approved API key and quota",
                    "dataset-level license and attribution",
                    "Kazakhstan relevance and update cadence",
                    "no personal-data replication",
                ],
            ),
            _candidate(
                "ungm_notices",
                name="UNGM procurement notices",
                status="gated",
                role="opportunity_source",
                official_surface="https://developer.ungm.org/",
                access="official OAuth/API authorization required",
                next_action=(
                    "Obtain an approved integration path and confirm permitted "
                    "field storage before implementing the adapter."
                ),
                checks=[
                    "authorized API client",
                    "reuse and public-display terms",
                    "notice, deadline and award-result fixtures",
                    "Central Asia relevance filter",
                ],
            ),
            _candidate(
                "us_embassy_central_asia",
                name="U.S. Embassy small-grants pages",
                status="deferred",
                role="opportunity_source",
                official_surface="https://kz.usembassy.gov/",
                access="public pages; stable item feed not yet confirmed",
                next_action=(
                    "Confirm a stable Kazakhstan or regional listing with current "
                    "deadlines before adding a parser."
                ),
                checks=[
                    "stable item-level official URL",
                    "current call status",
                    "deadline parser fixture",
                    "duplicate and archive policy",
                ],
            ),
        ],
        "links": {
            "source_registry": f"{origin.rstrip('/')}/.well-known/source-onboarding.json",
            "coverage": f"{origin.rstrip('/')}/coverage",
            "status": f"{origin.rstrip('/')}/status",
        },
    }
