"""Focused contracts for the Central Asia source expansion."""

from __future__ import annotations

import asyncio
from datetime import date, timedelta

import httpx

from sources.canada_cfli import CanadaCfliCentralAsiaParser
from sources.eu_funding_tenders import EuFundingTendersCentralAsiaParser
from sources.world_bank_procurement import WorldBankCentralAsiaProcurementParser


def _collect(parser):
    async def drain():
        return [item async for item in parser.fetch()]

    return asyncio.run(drain())


def test_world_bank_procurement_keeps_only_current_actionable_notices():
    future = (date.today() + timedelta(days=20)).isoformat()
    expired = (date.today() - timedelta(days=2)).isoformat()
    payload = {
        "procnotices": [
            {
                "id": "WB-KG-001",
                "bid_description": "Digital public services implementation",
                "project_name": "Digital Central Asia",
                "project_ctry_name": "Kyrgyz Republic",
                "notice_type": "Request for Expression of Interest",
                "submission_deadline_date": future,
                "noticedate": "01-Jul-2026",
                "project_id": "P000001",
            },
            {
                "id": "WB-KZ-OLD",
                "bid_description": "Expired consultancy",
                "project_ctry_name": "Kazakhstan",
                "notice_type": "Invitation for Bids",
                "submission_deadline_date": expired,
            },
            {
                "id": "WB-UZ-AWARD",
                "bid_description": "Award notice",
                "project_ctry_name": "Uzbekistan",
                "notice_type": "Contract Award",
                "submission_deadline_date": future,
            },
        ]
    }
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=payload, request=request)
    )
    parser = WorldBankCentralAsiaProcurementParser(
        client=httpx.AsyncClient(transport=transport)
    )

    items = _collect(parser)

    assert len(items) == 1
    assert items[0].raw["external_id"] == "WB-KG-001"
    assert items[0].deadline == date.fromisoformat(future)
    assert "kyrgyzstan" in items[0].tags
    assert str(items[0].source_url).endswith("/WB-KG-001")


def test_eu_funding_tenders_deduplicates_search_terms_and_warns_on_eligibility():
    future = (date.today() + timedelta(days=30)).isoformat()
    payload = {
        "results": [
            {
                "metadata": {
                    "language": ["en"],
                    "identifier": ["HORIZON-CA-2026-01"],
                    "callIdentifier": ["HORIZON-CALL-2026"],
                    "title": ["Trusted AI data spaces"],
                    "deadlineDate": [future],
                    "keywords": ["Artificial intelligence", "Central Asia"],
                    "frameworkProgramme": ["HORIZON"],
                }
            }
        ]
    }
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=payload, request=request)
    )
    parser = EuFundingTendersCentralAsiaParser(
        client=httpx.AsyncClient(transport=transport)
    )

    items = _collect(parser)

    assert len(items) == 1
    assert items[0].raw["external_id"] == "HORIZON-CA-2026-01"
    assert "eligibility_check_required" in items[0].tags
    assert "not proof" in items[0].raw["eligibility_note"]
    assert items[0].raw["i18n"]["ru"]["title"] == ("Конкурс ЕС – HORIZON-CA-2026-01")
    assert "topic-details/HORIZON-CA-2026-01" in str(items[0].source_url)


def test_canada_cfli_combines_open_central_asia_country_rows():
    future = (date.today() + timedelta(days=40)).isoformat()
    html = f"""
    <table id="dataset-filter1"><tbody>
      <tr><td><a href="/cfli/kazakhstan.aspx">Kazakhstan</a></td><td>Open</td><td>{future}</td></tr>
      <tr><td><a href="/cfli/kazakhstan.aspx">Kyrgyzstan</a></td><td>Open</td><td>{future}</td></tr>
      <tr><td><a href="/cfli/uzbekistan.aspx">Uzbekistan</a></td>
          <td>Closed</td><td>{future}</td></tr>
    </tbody></table>
    """
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, text=html, request=request)
    )
    parser = CanadaCfliCentralAsiaParser(client=httpx.AsyncClient(transport=transport))

    items = _collect(parser)

    assert len(items) == 1
    assert items[0].deadline == date.fromisoformat(future)
    assert items[0].raw["countries"] == ["Kazakhstan", "Kyrgyzstan"]
    assert items[0].currency == "CAD"
    assert items[0].raw["i18n"]["ru"]["title"].startswith("Канадский фонд")


def test_canada_cfli_does_not_publish_closed_calls():
    future = (date.today() + timedelta(days=40)).isoformat()
    html = f"""
    <table id="dataset-filter1"><tbody>
      <tr><td><a href="/cfli/kazakhstan.aspx">Kazakhstan</a></td>
          <td>Closed</td><td>{future}</td></tr>
    </tbody></table>
    """
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, text=html, request=request)
    )
    parser = CanadaCfliCentralAsiaParser(client=httpx.AsyncClient(transport=transport))

    assert _collect(parser) == []
