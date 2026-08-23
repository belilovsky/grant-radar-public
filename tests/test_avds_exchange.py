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
        "package_version": "4.5.1",
        "version": "4.7.0",
        "source_revision": "79342b07b061938c14101a213d1dd0c7a412d689",
    }
    assert contract["runtime_neutral_patterns"]["source_revision"] == (
        "ea32d93aa05fa6faa4278ccc030c1d3567c1de35"
    )
    assert contract["runtime_neutral_patterns"]["version"] == "0.2.0"
    families = {
        family["id"]: family["components"] for family in contract["component_families"]
    }
    assert "EvidenceSummary" in families["evidence"]
    assert "EvidenceDisclosure" in families["evidence"]
    assert "TrustStrip" in families["evidence"]
    assert "FilterStateSummary" in families["navigation-filtering"]
    assert "QuickLinksRail" in families["navigation-filtering"]
    assert "DecisionSummary" in families["explainable-results"]
    assert "ActionPath" in families["guidance"]
    assert "TrustFactsPanel" in families["guidance"]
    assert "EditorialLeadRail" in families["guidance"]
    assert "LiteReadingSurface" in families["guidance"]
    assert "PublicSummaryStrip" in families["metrics"]
    assert "DataQualityScorecard" in families["metrics"]
    assert "FormField" in families["foundation"]
    assert "Progress" in families["application-preparation"]
    assert contract["verification"]["public_site_status"] == "live"
    assert contract["verification"]["reference_release"] == "4.7.0"
    assert contract["local_recipes"]["package_claim"] is False
    assert "application-workspace" in contract["local_recipes"]["recipes"]
    assert "machine-entrypoints" in contract["local_recipes"]["recipes"]
    assert contract["pattern_exchange"]["adopted_existing"] == [
        "PublicSummaryStrip",
        "QuickLinksRail",
        "TrustStrip",
        "TrustFactsPanel",
        "DocumentCard",
        "EditorialLeadRail",
        "LiteReadingSurface",
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
