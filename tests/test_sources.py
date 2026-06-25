"""Smoke tests for M2 source parser skeletons."""

import asyncio

import httpx
import pytest

from sources import PARSERS, BaseSourceParser, GrantRecord
from sources.adb_kazakhstan import AdbKazakhstanParser
from sources.astana_hub import AstanaHubParser
from sources.ebrd_ecepp import EbrdEceppProcurementParser
from sources.eeas_kazakhstan import EeasKazakhstanParser
from sources.erasmus_kazakhstan import ErasmusKazakhstanParser
from sources.google_org import GoogleOrgAiOpportunityParser
from sources.grants_gov import GrantsGovParser
from sources.internews import InternewsParser
from sources.isdb_procurement import IsdbProjectProcurementParser
from sources.kazakhstan_domestic import KazakhstanDomesticSupportParser
from sources.kazakhstan_watch import KazakhstanWatchParser
from sources.rss_feeds import FundsForNgosParser, OpportunityDeskParser
from sources.startup_programs import (
    AwsActivateParser,
    CloudflareStartupsParser,
    GoogleCloudStartupParser,
    MicrosoftFoundersHubParser,
    MongoDbStartupsParser,
    NvidiaInceptionParser,
)
from sources.undp_procurement import UndpProcurementParser
from sources.unesco_iite import UnescoIiteParser
from sources.unicef_kazakhstan import UnicefKazakhstanParser
from sources.world_bank import WorldBankKazakhstanParser

PARSER_CLASSES = [
    GrantsGovParser,
    AstanaHubParser,
    InternewsParser,
    IsdbProjectProcurementParser,
    EbrdEceppProcurementParser,
    ErasmusKazakhstanParser,
    OpportunityDeskParser,
    FundsForNgosParser,
    KazakhstanDomesticSupportParser,
    KazakhstanWatchParser,
    EeasKazakhstanParser,
    WorldBankKazakhstanParser,
    AdbKazakhstanParser,
    GoogleCloudStartupParser,
    MicrosoftFoundersHubParser,
    AwsActivateParser,
    NvidiaInceptionParser,
    CloudflareStartupsParser,
    MongoDbStartupsParser,
    UnicefKazakhstanParser,
    GoogleOrgAiOpportunityParser,
    UnescoIiteParser,
    UndpProcurementParser,
]


def test_registry_contains_all_parsers():
    assert set(PARSERS.keys()) == {
        "grants_gov",
        "astana_hub",
        "internews",
        "isdb_project_procurement",
        "ebrd_ecepp_procurement",
        "erasmus_kazakhstan",
        "opportunity_desk",
        "fundsforngos",
        "kazakhstan_domestic_support",
        "kazakhstan_watch",
        "eeas_kazakhstan",
        "world_bank_kazakhstan",
        "adb_kazakhstan",
        "google_cloud_startup",
        "microsoft_founders_hub",
        "aws_activate",
        "nvidia_inception",
        "cloudflare_startups",
        "mongodb_startups",
        "unicef_kazakhstan",
        "google_org_ai_opportunity",
        "unesco_iite",
        "undp_procurement",
    }
    for cls in PARSERS.values():
        assert issubclass(cls, BaseSourceParser)


@pytest.mark.parametrize("cls", PARSER_CLASSES)
def test_parser_basic_attrs(cls):
    parser = cls()
    assert parser.name
    assert parser.base_url.startswith("http")
    assert parser.request_delay >= 0


@pytest.mark.parametrize("cls", PARSER_CLASSES)
def test_fetch_returns_async_iterator(cls):
    transport = httpx.MockTransport(lambda request: httpx.Response(503))
    parser = cls(client=httpx.AsyncClient(transport=transport))

    async def _drain():
        items = []
        async for rec in parser.fetch():
            items.append(rec)
        return items

    items = asyncio.run(_drain())
    assert items == []  # skeletons yield nothing yet


@pytest.mark.parametrize("cls", PARSER_CLASSES)
def test_healthcheck(cls):
    transport = httpx.MockTransport(lambda request: httpx.Response(200))
    parser = cls(client=httpx.AsyncClient(transport=transport))
    assert asyncio.run(parser.healthcheck()) is True


def test_grant_record_defaults():
    rec = GrantRecord(source="x", external_id="1", title="t", url="https://x")
    assert rec.description == ""
    assert rec.deadline is None
    assert rec.raw == {}
