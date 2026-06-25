"""Grant source parsers package.

Exposes the registered parser classes for the scheduler/ETL.
"""

from .adb_kazakhstan import AdbKazakhstanParser
from .astana_hub import AstanaHubParser
from .base import BaseSourceParser, GrantRecord
from .ebrd_ecepp import EbrdEceppProcurementParser
from .eeas_kazakhstan import EeasKazakhstanParser
from .erasmus_kazakhstan import ErasmusKazakhstanParser
from .google_org import GoogleOrgAiOpportunityParser
from .grants_gov import GrantsGovParser
from .internews import InternewsParser
from .isdb_procurement import IsdbProjectProcurementParser
from .kazakhstan_domestic import KazakhstanDomesticSupportParser
from .kazakhstan_watch import KazakhstanWatchParser
from .rss_feeds import FundsForNgosParser, OpportunityDeskParser
from .startup_programs import (
    AwsActivateParser,
    CloudflareStartupsParser,
    GoogleCloudStartupParser,
    MicrosoftFoundersHubParser,
    MongoDbStartupsParser,
    NvidiaInceptionParser,
)
from .undp_procurement import UndpProcurementParser
from .unesco_iite import UnescoIiteParser
from .unicef_kazakhstan import UnicefKazakhstanParser
from .world_bank import WorldBankKazakhstanParser

PARSERS = {
    GrantsGovParser.slug: GrantsGovParser,
    AstanaHubParser.slug: AstanaHubParser,
    InternewsParser.slug: InternewsParser,
    IsdbProjectProcurementParser.slug: IsdbProjectProcurementParser,
    EbrdEceppProcurementParser.slug: EbrdEceppProcurementParser,
    ErasmusKazakhstanParser.slug: ErasmusKazakhstanParser,
    OpportunityDeskParser.slug: OpportunityDeskParser,
    FundsForNgosParser.slug: FundsForNgosParser,
    KazakhstanDomesticSupportParser.slug: KazakhstanDomesticSupportParser,
    KazakhstanWatchParser.slug: KazakhstanWatchParser,
    EeasKazakhstanParser.slug: EeasKazakhstanParser,
    WorldBankKazakhstanParser.slug: WorldBankKazakhstanParser,
    UndpProcurementParser.slug: UndpProcurementParser,
    AdbKazakhstanParser.slug: AdbKazakhstanParser,
    GoogleCloudStartupParser.slug: GoogleCloudStartupParser,
    MicrosoftFoundersHubParser.slug: MicrosoftFoundersHubParser,
    AwsActivateParser.slug: AwsActivateParser,
    NvidiaInceptionParser.slug: NvidiaInceptionParser,
    CloudflareStartupsParser.slug: CloudflareStartupsParser,
    MongoDbStartupsParser.slug: MongoDbStartupsParser,
    UnicefKazakhstanParser.slug: UnicefKazakhstanParser,
    GoogleOrgAiOpportunityParser.slug: GoogleOrgAiOpportunityParser,
    UnescoIiteParser.slug: UnescoIiteParser,
}

__all__ = [
    "BaseSourceParser",
    "GrantRecord",
    "GrantsGovParser",
    "AstanaHubParser",
    "AdbKazakhstanParser",
    "EbrdEceppProcurementParser",
    "ErasmusKazakhstanParser",
    "InternewsParser",
    "IsdbProjectProcurementParser",
    "OpportunityDeskParser",
    "FundsForNgosParser",
    "KazakhstanDomesticSupportParser",
    "KazakhstanWatchParser",
    "EeasKazakhstanParser",
    "WorldBankKazakhstanParser",
    "GoogleCloudStartupParser",
    "MicrosoftFoundersHubParser",
    "AwsActivateParser",
    "NvidiaInceptionParser",
    "CloudflareStartupsParser",
    "MongoDbStartupsParser",
    "UnicefKazakhstanParser",
    "GoogleOrgAiOpportunityParser",
    "UnescoIiteParser",
    "UndpProcurementParser",
    "PARSERS",
]
