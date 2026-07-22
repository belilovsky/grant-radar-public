"""Regression coverage for the two-way QAZ.FUND and AV DS exchange."""

from pathlib import Path

from api.ecosystem import avds_ui_contract

ROOT = Path(__file__).resolve().parents[1]


def test_avds_contract_declares_runtime_neutral_catalog_patterns() -> None:
    contract = avds_ui_contract()

    assert contract["runtime_neutral_patterns"]["adopted"] == [
        "evidence-summary",
        "filter-state-summary",
        "decision-summary",
    ]
    families = {
        family["id"]: family["components"] for family in contract["component_families"]
    }
    assert "EvidenceSummary" in families["evidence"]
    assert "FilterStateSummary" in families["navigation-filtering"]
    assert "DecisionSummary" in families["explainable-results"]


def test_avds_exchange_document_keeps_business_logic_local() -> None:
    document = (ROOT / "docs" / "AVDS_EXCHANGE_2026-07-22.md").read_text()

    assert "`EvidenceSummary`" in document
    assert "`FilterStateSummary`" in document
    assert "`DecisionSummary`" in document
    assert "stay in QAZ.FUND" in document
