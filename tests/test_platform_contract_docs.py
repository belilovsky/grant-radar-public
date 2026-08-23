"""Keep public integration documentation aligned with executable contracts."""

from pathlib import Path

from api.ecosystem import ecosystem_manifest
from api.integration_versions import (
    AVDS_PATTERN_SOURCE_REVISION,
    AVDS_VERSION,
    QAZSTACK_VERSION,
)

ROOT = Path(__file__).resolve().parents[1]


def test_current_integration_documents_match_the_version_contract() -> None:
    ecosystem = (ROOT / "docs" / "ECOSYSTEM_INTEGRATION.md").read_text()
    avds_integration = (ROOT / "docs" / "AVDS_INTEGRATION.md").read_text()
    avds_exchange = (ROOT / "docs" / "AVDS_EXCHANGE_2026-07-26.md").read_text()
    benchmark = (ROOT / "docs" / "WORLD_BENCHMARK_2026-07-27.md").read_text()

    for document in (ecosystem, avds_integration, avds_exchange, benchmark):
        assert "AV DS 4.6.0" not in document
        assert f"AV DS {AVDS_VERSION}" in document

    assert f"QazStack {QAZSTACK_VERSION}" in ecosystem
    assert AVDS_PATTERN_SOURCE_REVISION in avds_exchange


def test_deferred_qazgeo_contract_has_a_product_owner_and_review_trigger() -> None:
    qazgeo = ecosystem_manifest("https://qaz.fund")["integrations"]["qazgeo"]

    assert qazgeo["status"] == "deferred-no-geometry"
    assert qazgeo["product_owner"] == "qaz-fund"
    assert "Verified coordinates" in qazgeo["review_trigger"]
