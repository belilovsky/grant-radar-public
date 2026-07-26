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
        "evidence-disclosure",
        "action-path",
    ]
    assert contract["avds_source"] == {
        "site": "https://avds.digital",
        "package": "@sgeo/ui-kit",
        "version": "4.2.0",
    }
    assert contract["runtime_neutral_patterns"]["source_revision"] == (
        "3d482e1c7592e2f8ae359c3e3b2d10c5c1118c37"
    )
    families = {
        family["id"]: family["components"] for family in contract["component_families"]
    }
    assert "EvidenceSummary" in families["evidence"]
    assert "EvidenceDisclosure" in families["evidence"]
    assert "FilterStateSummary" in families["navigation-filtering"]
    assert "QuickLinksRail" in families["navigation-filtering"]
    assert "DecisionSummary" in families["explainable-results"]
    assert "ActionPath" in families["guidance"]
    assert "TrustFactsPanel" in families["guidance"]
    assert "PublicSummaryStrip" in families["metrics"]
    assert contract["pattern_exchange"]["adopted_existing"] == [
        "PublicSummaryStrip",
        "QuickLinksRail",
        "TrustFactsPanel",
        "DocumentCard",
    ]
    assert [
        item["component"]
        for item in contract["pattern_exchange"]["absorbed_from_qaz_fund"]
    ] == ["EvidenceDisclosure", "ActionPath"]


def test_avds_exchange_document_keeps_business_logic_local() -> None:
    document = (ROOT / "docs" / "AVDS_EXCHANGE_2026-07-26.md").read_text()

    assert "`EvidenceSummary`" in document
    assert "`FilterStateSummary`" in document
    assert "`DecisionSummary`" in document
    assert "`EvidenceDisclosure`" in document
    assert "`ActionPath`" in document
    assert "остаются в QAZ.FUND" in document
