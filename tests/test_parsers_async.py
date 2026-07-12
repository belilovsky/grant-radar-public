"""Async HTTP-mocked tests for M2 source parsers.

Uses `respx` to mock the httpx AsyncClient so that `fetch()` can be exercised
without real network access. These tests verify that:
  * On success, parsers yield Opportunity-like records with normalized fields.
  * On 5xx / network errors, parsers swallow exceptions and yield nothing.
  * Healthchecks return False on transport failure.
"""

from __future__ import annotations

from datetime import date

import certifi
import httpx
import pytest

respx = pytest.importorskip("respx")

from core.models import OpportunityType  # noqa: E402
from sources import kazakhstan_domestic as domestic_source  # noqa: E402
from sources.adb_kazakhstan import ADB_KAZAKHSTAN_IATI_URL  # noqa: E402
from sources.adb_kazakhstan import AdbKazakhstanSource  # noqa: E402
from sources.astana_hub import FALLBACK_PROGRAM_URLS  # noqa: E402
from sources.astana_hub import AstanaHubSource  # noqa: E402
from sources.astana_hub import LISTING_URL as AH_URL  # noqa: E402
from sources.ebrd_ecepp import ECEPP_SEARCH_URL  # noqa: E402
from sources.ebrd_ecepp import EbrdEceppProcurementSource  # noqa: E402
from sources.eeas_kazakhstan import LISTING_URL as EEAS_LISTING_URL  # noqa: E402
from sources.eeas_kazakhstan import EeasKazakhstanSource  # noqa: E402
from sources.erasmus_kazakhstan import ERASMUS_ARCHIVE_URL  # noqa: E402
from sources.erasmus_kazakhstan import ERASMUS_NEWS_URL  # noqa: E402
from sources.erasmus_kazakhstan import ErasmusKazakhstanSource  # noqa: E402
from sources.erasmus_kazakhstan import _extract_actions  # noqa: E402
from sources.google_org import GOOGLE_ORG_KNOWLEDGE_URL  # noqa: E402
from sources.google_org import GoogleOrgAiOpportunitySource  # noqa: E402
from sources.grants_gov import SEARCH_URL as GG_SEARCH_URL  # noqa: E402
from sources.grants_gov import GrantsGovSource  # noqa: E402
from sources.internews import FEED_URL as IW_FEED_URL  # noqa: E402
from sources.internews import LISTING_URL as IW_URL  # noqa: E402
from sources.internews import InternewsSource  # noqa: E402
from sources.isdb_procurement import TENDER_URLS as ISDB_TENDER_URLS  # noqa: E402
from sources.isdb_procurement import IsdbProjectProcurementSource  # noqa: E402
from sources.kazakhstan_domestic import DOMESTIC_PROGRAMS  # noqa: E402
from sources.kazakhstan_domestic import DomesticProgram  # noqa: E402
from sources.kazakhstan_domestic import KazakhstanDomesticSupportSource  # noqa: E402
from sources.kazakhstan_watch import WATCH_PAGES  # noqa: E402
from sources.kazakhstan_watch import KazakhstanWatchSource  # noqa: E402
from sources.kazakhstan_watch import WatchPage  # noqa: E402
from sources.rss_feeds import FUNDSFORNGOS_FEED_URLS  # noqa: E402
from sources.rss_feeds import OPPORTUNITY_DESK_FEED_URL  # noqa: E402
from sources.rss_feeds import FundsForNgosSource  # noqa: E402
from sources.rss_feeds import OpportunityDeskSource  # noqa: E402
from sources.startup_programs import PROGRAM_SPECS  # noqa: E402
from sources.startup_programs import (  # noqa: E402
    AwsActivateSource,
    CloudflareStartupsSource,
    GoogleCloudStartupSource,
    MicrosoftFoundersHubSource,
    MongoDbStartupsSource,
    NvidiaInceptionSource,
)
from sources.undp_procurement import LISTING_URL as UNDP_LISTING_URL  # noqa: E402
from sources.undp_procurement import UndpProcurementSource  # noqa: E402
from sources.unesco_iite import UNESCO_IITE_ANNOUNCEMENTS_URL  # noqa: E402
from sources.unesco_iite import UnescoIiteSource  # noqa: E402
from sources.unicef_kazakhstan import UnicefKazakhstanSource  # noqa: E402
from sources.unicef_kazakhstan import (  # noqa: E402
    UNICEF_KAZAKHSTAN_TENDERS_READER_URL,
    UNICEF_KAZAKHSTAN_TENDERS_URL,
)
from sources.world_bank import WORLD_BANK_PROJECTS_API  # noqa: E402
from sources.world_bank import WorldBankKazakhstanSource  # noqa: E402

ASTANA_HTML = (
    "<html><body>"
    '<a href="/ru/service/programs/tech-orda/" class="card"><h3>Tech Orda</h3></a>'
    "<p>до 15.06.2026</p>"
    '<a href="/ru/service/programs/silkway/" class="card"><h3>Silkway</h3></a>'
    "<p>deadline: 01.09.2026</p>"
    "</body></html>"
)

INTERNEWS_HTML = (
    "<html><body>"
    '<a href="https://internews.org/opportunity/media-grant-2026/">Media Grant 2026</a>'
    "<p>Deadline: 30 Jun 2026</p>"
    '<a href="https://internews.org/resource/journalism-fellowship/">Journalism Fellowship</a>'
    "<p>Apply by 12 Sep 2026</p>"
    "</body></html>"
)

RSS_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>AI Education Fellowship for Emerging Leaders</title>
      <link>https://example.org/ai-education-fellowship</link>
      <guid>ai-education-fellowship</guid>
      <description>Deadline: 30 Jun 2026. Funding for digital skills.</description>
      <category>Education</category>
      <category>AI</category>
    </item>
    <item>
      <title>Media Grant for Civil Society</title>
      <link>https://example.org/media-grant</link>
      <guid>media-grant</guid>
      <description>Apply by July 15, 2026.</description>
      <category>Media</category>
    </item>
  </channel>
</rss>
"""

EEAS_DETAIL_PATH = (
    "/delegations/kazakhstan/"
    "call-proposals-%E2%80%9Csupport-civil-society-kazakhstan%E2%80%9D-2_en"
)
EEAS_DETAIL_URL = f"https://www.eeas.europa.eu{EEAS_DETAIL_PATH}"
EEAS_LISTING_HTML = f"""
<html><body>
<div class="card">
  <h3 class="h2 card-title">
    <a href="{EEAS_DETAIL_PATH}">
      Call for Proposals “Support to Civil Society in Kazakhstan”
    </a>
  </h3>
  <time datetime="2026-05-12T12:00:00Z" class="datetime">12.05.2026</time>
</div>
</body></html>
"""

EEAS_EMPTY_LISTING_HTML = """
<html><body>
<div class="card">
  <h3 class="h2 card-title">No current calls are listed.</h3>
</div>
</body></html>
"""

EEAS_LISTING_WITH_CONTRACTS_HTML = f"""
<html><body>
<div class="card">
  <h3 class="h2 card-title">
    <a href="{EEAS_DETAIL_PATH}">
      Call for Proposals “Support to Civil Society in Kazakhstan”
    </a>
  </h3>
  <time datetime="2026-05-12T12:00:00Z" class="datetime">12.05.2026</time>
</div>
<div class="card">
  <h3 class="h2 card-title">
    <a href="/delegations/kazakhstan/list-contracts-were-concluded-framework-
call-proposals-europeaid176-656ddactkz_en?s=222">
      List of contracts were concluded under the framework of call for
      proposals EuropeAid/176-656/DD/ACT/KZ
    </a>
  </h3>
  <time datetime="2026-05-12T12:00:00Z" class="datetime">12.05.2026</time>
</div>
</body></html>
"""
EEAS_DETAIL_HTML = """
<html><head>
  <meta
    property="og:title"
    content="Call for Proposals “Support to Civil Society in Kazakhstan”"
  />
  <meta
    name="description"
    content="Publication reference: EuropeAid/186114/DD/ACT/KZ
      The European Commission is seeking proposals for actions in Kazakhstan."
  />
</head><body>
  <h1>Call for Proposals “Support to Civil Society in Kazakhstan”</h1>
  <p>
    The deadline for submission of proposals is 12 May 2026
    at 14:00 Brussels time.
  </p>
</body></html>
"""

WORLD_BANK_PAYLOAD = {
    "rows": 1,
    "total": "1",
    "projects": {
        "P513072": {
            "id": "P513072",
            "project_name": (
                "Advancing Learning, Entrepreneurship, and Markets for "
                "Artificial Intelligence"
            ),
            "countryshortname": "Kazakhstan",
            "countrycode": ["KZ"],
            "boardapprovaldate": "2026-07-14T00:00:00Z",
            "closingdate": "2031-04-21",
            "totalamt": "75000000",
            "grantamt": "0",
            "borrower": "Ministry of Finance of Republic of Kazakhstan",
            "regionname": "Europe and Central Asia",
            "pdo": (
                "To enable the creation, commercialization and scale-up of "
                "technology startups for productivity-driven growth in Kazakhstan."
            ),
            "project_abstract": (
                "The project aims to strengthen Kazakhstan's AI startup ecosystem."
            ),
        }
    },
}
WORLD_BANK_FALSE_AI_PAYLOAD = {
    "rows": 1,
    "total": "1",
    "projects": {
        "P508695": {
            "id": "P508695",
            "project_name": "Second Inclusive & Sustainable Economic Growth",
            "countryshortname": "Kazakhstan",
            "countrycode": ["KZ"],
            "closingdate": "2027-08-31",
            "totalamt": "600000000",
            "grantamt": "0",
            "borrower": "Republic of Kazakhstan",
            "regionname": "Europe and Central Asia",
            "pdo": "To support the Government of Kazakhstan's greener and inclusive transition.",
            "project_abstract": "The project aims to support reforms.",
        }
    },
}

ADB_IATI_XML = """<?xml version="1.0" encoding="UTF-8"?>
<iati-activities generated-datetime="2026-04-27T10:32:35+08:00" version="2.03">
  <iati-activity default-currency="USD" last-updated-datetime="2026-04-27T10:32:35+08:00">
    <iati-identifier>XM-DAC-46004-58135-001-LN4763</iati-identifier>
    <title><narrative>Promoting Inclusive and Green Housing Finance Project</narrative></title>
    <description>
      <narrative>
        The project will promote affordable residential mortgage loans to women
        and support green housing finance in Kazakhstan.
      </narrative>
    </description>
    <participating-org role="4"><narrative>Housing Finance Company</narrative></participating-org>
    <activity-status code="2"/>
    <activity-date iso-date="2025-03-28" type="1"/>
    <activity-date iso-date="2030-08-31" type="3"/>
    <recipient-country code="KZ"/>
    <transaction>
      <transaction-type code="2"/>
      <value value-date="2025-03-28">173588000</value>
    </transaction>
    <document-link url="https://www.adb.org/projects/58135-001/main#project-documents">
      <title><narrative>URL to project documents</narrative></title>
    </document-link>
  </iati-activity>
  <iati-activity default-currency="USD">
    <iati-identifier>XM-DAC-46004-55039-001-LN4405</iati-identifier>
    <title><narrative>Closed Fiscal Governance Program</narrative></title>
    <description><narrative>Closed item.</narrative></description>
    <activity-status code="3"/>
    <activity-date iso-date="2024-12-31" type="3"/>
  </iati-activity>
</iati-activities>
"""

ISDB_TENDERS_HTML = """
<html><body>
<article role="article" about="/project-procurement/tenders/2025/gpn/smart-ed">
  <div class="field-title mt-4">
    <h2>
      <a href="/project-procurement/tenders/2025/gpn/smart-ed">
        Joint IsDB/ GPE Smart-ED Project for Improving Access and Quality of
        Inclusive Learning Opportunities for all Children in the Kyrgyz Republic - GPN
      </a>
    </h2>
  </div>
  <div class="tender-badges">
    <div class="field field--name-field-tender-status field--item">
      <div class="taxonomy-term slug-active">Active</div>
    </div>
    <div class="field field--name-field-tender-type field--item">
      <div class="taxonomy-term slug-gpn">General Procurement Notice</div>
    </div>
    <div class="field field--name-field-world-country field--item">Kyrgyz</div>
    <div class="field field--name-field-close-date field--item">
      <time datetime="00Z">7 November 2099</time>
    </div>
  </div>
</article>
<article role="article" about="/project-procurement/tenders/2025/gpn/azerbaijan">
  <div class="field-title mt-4">
    <h2><a href="/project-procurement/tenders/2025/gpn/azerbaijan">Other region</a></h2>
  </div>
  <div class="field field--name-field-tender-status field--item">
    <div class="taxonomy-term slug-active">Active</div>
  </div>
  <div class="field field--name-field-tender-type field--item">
    <div class="taxonomy-term slug-gpn">General Procurement Notice</div>
  </div>
  <div class="field field--name-field-world-country field--item">Azerbaijan</div>
</article>
<article role="article" about="/project-procurement/tenders/2024/gpn/kazakhstan-closed">
  <div class="field-title mt-4">
    <h2>
      <a href="/project-procurement/tenders/2024/gpn/kazakhstan-closed">
        Closed Kazakhstan tender
      </a>
    </h2>
  </div>
  <div class="field field--name-field-tender-status field--item">
    <div class="taxonomy-term slug-closed">Closed</div>
  </div>
  <div class="field field--name-field-tender-type field--item">
    <div class="taxonomy-term slug-gpn">General Procurement Notice</div>
  </div>
  <div class="field field--name-field-world-country field--item">Kazakhstan</div>
</article>
</body></html>
"""

ECEPP_NOTICE_RESULTS_HTML = """
<html><body>
<table id="noticeResultsTable">
<tbody>
  <tr>
    <td>
      <a href="viewNotice.html?displayNoticeId=42107171">
        Kazakhstan: Technical Supervision of Construction and reconstruction
      </a>
    </td>
    <td>Invitation For Tenders Single</td>
    <td>Technical Supervision and Project Implementation Support Services</td>
    <td>12/05/2099 08:00</td>
    <td>05/06/2099 15:00</td>
    <td>Open</td>
    <td>12/05/2099</td>
    <td>209905120800</td>
    <td>209906051500</td>
    <td>
      [Aktobe Ulgaisyn Roads, 55068, Kazakhstan, Technical Supervision of
      Construction, 42107044, Consultancy, Open Tender Single - Two Envelope,
      JSC KazAvtoZhol, Transport, Invitation For Tenders Single]
    </td>
  </tr>
  <tr>
    <td>
      <a href="viewNotice.html?displayNoticeId=42771525">
        Kyrgyz Republic: Rehabilitation of Water Supply Systems
      </a>
    </td>
    <td>Invitation For Tenders Single</td>
    <td>Rehabilitation and Extension of Water Supply Systems</td>
    <td>20/05/2099 08:49</td>
    <td>30/06/2099 15:00</td>
    <td>Open</td>
    <td>20/05/2099</td>
    <td>209905200849</td>
    <td>209906301500</td>
    <td>
      [Kyrgyz Water Resilience Framework, 52283, Kyrgyz Republic,
      Works, Water Utilities, Municipal and Environmental Infrastructure,
      Invitation For Tenders Single]
    </td>
  </tr>
  <tr>
    <td><a href="viewNotice.html?displayNoticeId=100">Ukraine: Closed Item</a></td>
    <td>Invitation For Tenders Single</td>
    <td>Closed item</td>
    <td>20/05/2099 08:49</td>
    <td>30/06/2099 15:00</td>
    <td>Closed</td>
    <td>20/05/2099</td>
    <td>209905200849</td>
    <td>209906301500</td>
    <td>[Ukraine, Works, Invitation For Tenders Single]</td>
  </tr>
  <tr>
    <td><a href="viewNotice.html?displayNoticeId=101">Georgia: Other Region</a></td>
    <td>Invitation For Tenders Single</td>
    <td>Other region</td>
    <td>20/05/2099 08:49</td>
    <td>30/06/2099 15:00</td>
    <td>Open</td>
    <td>20/05/2099</td>
    <td>209905200849</td>
    <td>209906301500</td>
    <td>[Georgia, Works, Invitation For Tenders Single]</td>
  </tr>
</tbody>
</table>
</body></html>
"""

ERASMUS_CURRENT_NEWS_HTML = """
<html><body>
  <a
    href="https://erasmus.kz/en/novost/information-sessions-newcomers-partner-search"
    class="item-news"
  >
    <div class="item-news__date 1">20.03.2026</div>
    <div class="item-news__title">Information Sessions - From Newcomers to Partner Search</div>
    <div class="item-news__text">Informative sessions for universities.</div>
  </a>
</body></html>
"""

ERASMUS_ARCHIVE_NEWS_HTML = """
<html><body>
  <a
    href="https://erasmus.kz/en/novost/erasmus-2026-call-now-open-opportunities-kazakhstani-universities-and-organizations"
    class="item-news"
  >
    <div class="item-news__date 1">19.12.2025</div>
    <div class="item-news__title">
      Erasmus+ 2026 Call Is Now Open: Opportunities for Kazakhstani
      Universities and Organizations
    </div>
    <div class="item-news__text">
      The Erasmus+ 2026 Call is officially open. All interested higher
      education institutions can now submit project proposals under the
      various programme actions.
    </div>
  </a>
  <a
    href="https://erasmus.kz/en/novost/erasmus-cbhe-2025-call-results"
    class="item-news"
  >
    <div class="item-news__date 1">01.08.2025</div>
    <div class="item-news__title">Erasmus+ CBHE 2025 Call results featuring Kazakhstan</div>
    <div class="item-news__text">Selected projects were announced.</div>
  </a>
</body></html>
"""

ERASMUS_CALL_ARTICLE_HTML = """
<html><body>
<section class="news-single">
  <h1 class="news-single__title title">
    Erasmus+ 2026 Call Is Now Open: Opportunities for Kazakhstani
    Universities and Organizations
  </h1>
  <div class="news-single__text">
    <p>
      The National Erasmus+ Office in Kazakhstan (NEO KZ) is pleased to
      announce that the Erasmus+ 2026 Call is officially open.
    </p>
    <p><strong>Programme Actions and Deadlines for 2026</strong></p>
    <p>
      <a href="https://erasmus.kz/en/dlya-vuzov/informaciya-o-zhan-mone">
        <strong>Jean Monnet</strong>
      </a>
      - contributes to spreading knowledge about the European Union
      integration matters - <strong>3 February 2099</strong>
    </p>
    <p>
      <a href="https://erasmus.kz/en/dlya-vuzov/informaciya-o-ppvo">
        <strong>Capacity Building in Higher Education (CBHE)</strong>
      </a>
      - projects aimed at strengthening the capacity of universities and
      modernizing educational programmes - <strong>10 February 2099</strong>
    </p>
    <p>
      <a href="https://erasmus.kz/en/dlya-vuzov/erasmus-mundus">
        <strong>
          Erasmus Mundus Joint Master Degrees (EMJM) and Erasmus Mundus
          Design Measure (EMDM)
        </strong>
      </a>
      - development and implementation of joint master's programmes -
      <strong>12 February 2099</strong>
    </p>
    <p>
      <a href="https://erasmus.kz/en/dlya-vuzov/informaciya-o-mkm">
        <strong>International Credit Mobility (ICM)</strong>
      </a>
      - supports short-term academic mobility of students and staff between
      Kazakhstan and EU Member States - <strong>19 February 2099</strong>
    </p>
  </div>
</section>
</body></html>
"""

UNICEF_TENDERS_HTML = """
<html><body>
  <p>
    <strong>UNITED NATIONS CHILDREN'S FUND (UNICEF)</strong>
    would like to invite you to submit a proposal for
    <strong>RFP/KAZA/2099/001 - International consultancy for a digital
    learning platform in Kazakhstan.</strong>
  </p>
  <p>
    The bid form must be used when replying to this request for proposal.
    Please send your
    <a href="https://drive.google.com/drive/folders/example">proposals</a>.
  </p>
  <p>
    <strong>
      The Proposals MUST be received by latest 6-00 p.m. (Astana time UTC+5:00)
      on 02 February 2099.
    </strong>
  </p>
  <hr>
  <p>
    <strong>
      RFQ/KAZA/2099/002 - Hotel accommodation and conference hall services
      in Astana.
    </strong>
  </p>
  <p>
    The quotation MUST be received by latest 6-00 p.m. on 02 February 2099.
  </p>
  <hr>
  <p>
    <strong>RFP/KAZA/2024/001 - Expired consultancy in Kazakhstan.</strong>
  </p>
  <p>
    <strong>
      The Proposals MUST be received by latest 6-00 p.m. (Astana time UTC+5:00)
      on 02 February 2024.
    </strong>
  </p>
</body></html>
"""

UNICEF_TENDERS_MARKDOWN = """
Title: Tenders

URL Source: https://www.unicef.org/kazakhstan/en/tenders

**UNITED NATIONS CHILDREN'S FUND (UNICEF)** would like to invite you to submit
a proposal for **RFP/KAZA/2099/001 - International consultancy for a digital
learning platform in Kazakhstan.**

The bid form must be used when replying to this request for proposal. Please
send your [**proposals**](https://drive.google.com/drive/folders/example).

**The Proposals MUST be received by latest 6-00 p.m. (Astana time UTC+5:00)
on 02 February 2099.**
"""

UNICEF_TENDERS_WITH_DETAIL_LINK_HTML = """
<html><body>
  <p>
    <a href="/kazakhstan/en/tenders/rfp-kaza-2099-001">
      Tender page
    </a>
  </p>
  <p>
    <strong>
      RFP/KAZA/2099/001 - International consultancy for a digital
      learning platform in Kazakhstan.
    </strong>
  </p>
  <p>
    The bid form must be used when replying to this request for proposal.
    Please send your
    <a href="https://drive.google.com/drive/folders/example">proposals</a>.
  </p>
  <p>
    The Proposals MUST be received by latest 6-00 p.m. on 02 February 2099.
  </p>
</body></html>
"""

GOOGLE_ORG_HTML = """
<html>
  <head><title>Knowledge, Skills & Learning - Google.org</title></head>
  <body>
    <h1>AI Opportunity Fund</h1>
    <p>Global AI skills and education support for nonprofits.</p>
  </body>
</html>
"""

UNESCO_MONTH_FIRST_URL = (
    "https://iite.unesco.org/announcements/global-education-data-challenge-2099/"
)
UNESCO_OPEN_URL = (
    "https://iite.unesco.org/announcements/join-the-ai-for-education-awards-2099/"
)
UNESCO_GENERIC_URL = (
    "https://iite.unesco.org/announcements/"
    "call-for-proposals-publication-editing-and-proofreading-2099/"
)
UNESCO_EXPIRED_URL = (
    "https://iite.unesco.org/announcements/expired-digital-education-call/"
)
UNESCO_LISTING_HTML = f"""
<html><body>
  <a href="{UNESCO_IITE_ANNOUNCEMENTS_URL}">Who we are</a>
  <a href="{UNESCO_OPEN_URL}">
    Call for Entries: The AI for Education Awards 2099
  </a>
  <a href="{UNESCO_GENERIC_URL}">
    Call for Proposals: Publication Editing and Proofreading
  </a>
  <a href="{UNESCO_MONTH_FIRST_URL}">
    Global Education Data Challenge 2099
  </a>
  <a href="{UNESCO_EXPIRED_URL}">
    Call for Proposals: Old Digital Education Project
  </a>
</body></html>
"""
UNESCO_OPEN_HTML = """
<html><head>
  <title>Call for Entries: The AI for Education Awards 2099 – UNESCO IITE</title>
  <meta name="description" content="Global award for responsible AI in K-12 education." />
</head><body>
  <h1>Call for Entries: The AI for Education Awards 2099</h1>
  <p>Artificial Intelligence can transform teaching and learning.</p>
  <p>Application deadline: 31 May 2099</p>
</body></html>
"""
UNESCO_GENERIC_HTML = """
<html><head>
  <title>Call for Proposals: Publication Editing and Proofreading – UNESCO IITE</title>
</head><body>
  <h1>Call for Proposals: Publication Editing and Proofreading</h1>
  <p>Publication 1: AI policy and practices report for education systems.</p>
  <p>Submission Deadline: 25 May 2099</p>
</body></html>
"""
UNESCO_MONTH_FIRST_HTML = """
<html><head>
  <title>Global Education Data Challenge 2099 – UNESCO IITE</title>
</head><body>
  <article>
    <h1>Global Education Data Challenge 2099</h1>
    <p>Application deadline is May 31st, 2099.</p>
    <p>Focus on AI, education data, and digital learning systems.</p>
  </article>
</body></html>
"""
UNESCO_EXPIRED_HTML = """
<html><head>
  <title>Call for Proposals: Old Digital Education Project – UNESCO IITE</title>
</head><body>
  <h1>Call for Proposals: Old Digital Education Project</h1>
  <p>Digital education project.</p>
  <p>Submission Deadline: 25 May 2024</p>
</body></html>
"""

UNDP_LISTING_HTML = """
<html><body>
  <div class="vacanciesTable">
    <a href="view_negotiation.cfm?nego_id=901234">
      <div class="vacanciesTable__name">Procurement of digital classroom equipment</div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">Title</div>
        <span>Procurement of digital classroom equipment</span>
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">UNDP Office/Country</div>
        <span>UNDP-KAZ / Kazakhstan Office, Astana</span>
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">Ref No</div>
        <span>UNDP-KAZ-2099-TECH-001</span>
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">Process</div>
        <span>Open Tender</span>
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">Deadline</div>
        <span>03-Jun-2099</span>
      </div>
    </a>
    <a href="view_negotiation.cfm?nego_id=901235">
      <div class="vacanciesTable__name">Procurement in Georgia for smart meters</div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">Title</div>
        <span>Procurement in Georgia for smart meters</span>
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">UNDP Office/Country</div>
        <span>UNDP-GE / Georgia Office</span>
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">Ref No</div>
        <span>UNDP-GE-2099-GRID-002</span>
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">Process</div>
        <span>Open Tender</span>
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">Deadline</div>
        <span>03-Jun-2099</span>
      </div>
    </a>
    <a href="view_negotiation.cfm?nego_id=901236">
      <div class="vacanciesTable__name">Closed Kazakhstan contract</div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">Title</div>
        <span>Closed Kazakhstan contract</span>
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">UNDP Office/Country</div>
        <span>UNDP-KAZ Office</span>
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">Ref No</div>
        <span>UNDP-KAZ-2024-CLOSED</span>
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">Deadline</div>
        <span>01-Jan-2024</span>
      </div>
    </a>
    <a href="view_negotiation.cfm?nego_id=901237">
      <div class="vacanciesTable__name">
        Long Term Agreements for Hotel Accommodation and Conference Package Services
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">Title</div>
        <span>Long Term Agreements for Hotel Accommodation and Conference Package Services</span>
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">UNDP Office/Country</div>
        <span>UNDP-KAZ / Kazakhstan Office, Astana</span>
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">Ref No</div>
        <span>UNDP-KAZ-2099-HOTEL-003</span>
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">Process</div>
        <span>Request for Quotation</span>
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">Deadline</div>
        <span>03-Jun-2099</span>
      </div>
    </a>
  </div>
</body></html>
"""

UNDP_LISTING_RU_OPERATIONAL_HTML = """
<html><body>
  <div class="vacanciesTable">
    <a href="view_negotiation.cfm?nego_id=901238">
      <div class="vacanciesTable__name">
        Долгосрочные соглашения на оказание услуг проживания в отеле и конференц-пакета
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">Title</div>
        <span>Долгосрочные соглашения на оказание услуг проживания в отеле и конференц-пакета</span>
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">UNDP Office/Country</div>
        <span>UNDP-KAZ / Kazakhstan Office, Astana</span>
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">Ref No</div>
        <span>UNDP-KAZ-2099-HOTEL-RU-004</span>
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">Process</div>
        <span>Request for Quotation</span>
      </div>
      <div class="vacanciesTable__cell">
        <div class="vacanciesTable__cell__label">Deadline</div>
        <span>03-Jun-2099</span>
      </div>
    </a>
  </div>
</body></html>
"""

STARTUP_PROGRAM_CLASSES = [
    GoogleCloudStartupSource,
    MicrosoftFoundersHubSource,
    AwsActivateSource,
    NvidiaInceptionSource,
    CloudflareStartupsSource,
    MongoDbStartupsSource,
]


async def _collect(source) -> list:
    out = []
    async with source:
        async for item in source.fetch():
            out.append(item)
    return out


@pytest.mark.asyncio
@respx.mock
async def test_grants_gov_skips_us_tribal_only_opportunities():
    payload = {
        "data": {
            "oppHits": [
                {
                    "id": "362270",
                    "number": "HHS-2026-ACF-ANA-NAI-0035",
                    "title": (
                        "AI3 Action Institute - Artificial Intelligence "
                        "for American Indians"
                    ),
                    "agencyCode": "HHS-ACF-ANA",
                    "agency": "Administration for Native Americans",
                },
                {
                    "id": "362271",
                    "title": "AI education grant for Uzbekistan&rsquo;s partners",
                    "agencyCode": "EXAMPLE",
                    "agency": "Example Agency",
                    "closeDate": "07/30/2026",
                },
            ]
        }
    }
    respx.post(GG_SEARCH_URL).mock(return_value=httpx.Response(200, json=payload))

    items = await _collect(GrantsGovSource())

    assert "AI3 Action Institute" not in {item.title for item in items}
    assert any(
        item.title == "AI education grant for Uzbekistan’s partners" for item in items
    )
    central_asia_item = next(
        item
        for item in items
        if item.title == "AI education grant for Uzbekistan’s partners"
    )
    assert central_asia_item.summary


@pytest.mark.asyncio
@respx.mock
async def test_kazakhstan_watch_yields_curated_relevant_pages():
    for page in WATCH_PAGES:
        respx.get(page.url).mock(
            return_value=httpx.Response(200, text=f"<title>{page.title}</title>")
        )

    items = await _collect(KazakhstanWatchSource())

    assert len(items) == len(WATCH_PAGES)
    assert {item.source for item in items} == {"kazakhstan_watch"}
    assert all("kazakhstan" in item.tags for item in items)
    assert all(item.raw["page_title"] for item in items)
    assert all("rolling" in item.tags for item in items)
    assert all(item.raw["deadline_policy"] == "rolling" for item in items)


@pytest.mark.asyncio
@respx.mock
async def test_kazakhstan_domestic_support_yields_official_programs():
    for program in DOMESTIC_PROGRAMS:
        respx.get(program.url).mock(
            return_value=httpx.Response(200, text=f"<title>{program.title}</title>")
        )

    items = await _collect(KazakhstanDomesticSupportSource())

    assert len(items) == len(DOMESTIC_PROGRAMS)
    assert {item.source for item in items} == {"kazakhstan_domestic_support"}
    assert all("kazakhstan" in item.tags for item in items)
    assert all("domestic_support" in item.tags for item in items)
    assert all("state_program" in item.tags for item in items)
    assert all(item.raw["page_title"] for item in items)
    assert all("rolling" in item.tags for item in items)
    assert all(item.raw["deadline_policy"] == "rolling" for item in items)
    by_title = {item.title: item for item in items}
    assert "State grant for startup business development" in by_title
    assert "How to get a state grant to start a business" in by_title
    assert "Interest-rate subsidy service for entrepreneurs" in by_title
    assert "Road Map of Business support programme" in by_title
    assert "State grants for social entrepreneurship" in by_title
    assert "Subsidies for crop production" in by_title
    assert "Bgov.kz unified financial support platform" in by_title
    assert "KazAgroFinance Own Feed and Preferential Leasing" in by_title
    assert "Agrarian Credit Corporation Ken Dala financing" in by_title
    assert "Development Bank of Kazakhstan investment-project financing" in by_title
    assert "Astana Hub participant tax benefits" in by_title
    assert "Business Enbek entrepreneur-support portal" not in by_title
    assert "Gosagro subsidy portal" not in by_title
    assert "Science Fund commercialization support" not in by_title
    assert "Qazaqstan Investment Corporation private equity funds" not in by_title
    assert "tax_benefit" in by_title["Astana Hub participant tax benefits"].tags
    assert (
        "preferential_financing"
        in by_title["Bgov.kz unified financial support platform"].tags
    )
    assert (
        "leasing" in by_title["KazAgroFinance Own Feed and Preferential Leasing"].tags
    )
    assert (
        by_title["State grants for social entrepreneurship"].raw["amount_raw"]
        == "up to 5,000,000 KZT according to current service conditions"
    )
    assert (
        by_title["State grants for social entrepreneurship"].raw["amount_max"]
        == "5000000"
    )
    assert by_title["State grants for social entrepreneurship"].currency == "KZT"
    assert str(by_title["State grants for social entrepreneurship"].amount_max) == (
        "5000000"
    )
    assert (
        by_title["State grant for startup business development"].raw["amount_raw"]
        == "up to 400 MRP"
    )
    assert by_title["State grant for startup business development"].amount_max is None
    assert (
        "social_entrepreneurship"
        in by_title["State grants for social entrepreneurship"].tags
    )


@pytest.mark.asyncio
@respx.mock
async def test_kazakhstan_domestic_support_extracts_detail_snapshot():
    program = DomesticProgram(
        url="https://egov.kz/cms/ru/services/state_support_measures/260_pass",
        title="State grants for social entrepreneurship",
        summary="Official eGov service for social entrepreneurship grants.",
        tags=("grant", "social_entrepreneurship", "egov"),
        eligibility=("Social-entrepreneurship SMEs in Kazakhstan",),
        amount_raw="up to 5,000,000 KZT",
    )
    respx.get(program.url).mock(
        return_value=httpx.Response(
            200,
            text="""
            <html lang="ru">
              <body>
                <main>
                  <h1>Предоставление государственных грантов</h1>
                  <p>Грант предоставляется субъектам социального предпринимательства.</p>
                  <h2>Как получить услугу онлайн</h2>
                  <ul><li>Авторизоваться на портале и заполнить заявку.</li></ul>
                </main>
              </body>
            </html>
            """,
        )
    )
    source = KazakhstanDomesticSupportSource()
    source.programs = (program,)

    items = await _collect(source)

    assert len(items) == 1
    item = items[0]
    assert item.raw["detail_fetch_status"] == "ok"
    assert item.raw["detail_language"] == "ru"
    assert item.raw["detail_html_sha256"]
    assert "Как получить услугу онлайн" in item.raw["detail_text"]
    assert item.raw["detail_sections"][0]["heading"] == (
        "Предоставление государственных грантов"
    )
    assert item.eligibility == ["Social-entrepreneurship SMEs in Kazakhstan"]


@pytest.mark.asyncio
@respx.mock
async def test_kazakhstan_domestic_support_skips_navigation_noise_in_detail_snapshot():
    program = DomesticProgram(
        url="https://example.org/domestic-animal-husbandry",
        title="Agrarian Credit Corporation animal husbandry loans",
        summary="Official concessional lending route for animal husbandry.",
        tags=("loan", "agriculture", "livestock"),
    )
    respx.get(program.url).mock(
        return_value=httpx.Response(
            200,
            text="""
            <html lang="ru">
              <body>
                <main>
                  <p>
                    1408 Call Center About the company Strategy, mission, vision
                    Corporate governance Financial and annual reports Loan program
                    Open an account online at Halyk Bank Opening an online account
                    at the CenterCredit Bank Open an account online at ForteBank
                    Settlement of problem debts Press center Media about us
                  </p>
                  <h1>Аграрная кредитная корпорация запускает новую программу кредитования</h1>
                  <p>Новая программа направлена на поддержку развития животноводства.</p>
                  <h2>Другие новости по теме</h2>
                  <p>Получите консультацию!</p>
                </main>
              </body>
            </html>
            """,
        )
    )
    source = KazakhstanDomesticSupportSource()
    source.programs = (program,)

    items = await _collect(source)

    assert len(items) == 1
    detail_sections = items[0].raw["detail_sections"]
    assert all(
        "Open an account online" not in section["text"] for section in detail_sections
    )
    assert all(
        section["heading"] != "Другие новости по теме" for section in detail_sections
    )
    assert "животноводства" in detail_sections[0]["text"]


@pytest.mark.asyncio
@respx.mock
async def test_kazakhstan_domestic_support_retries_govkz_seo_shell():
    url = "https://www.gov.kz/situations/501/1169?lang=ru"
    program = DomesticProgram(
        url=url,
        title="How to get a state grant to start a business",
        summary="Official gov.kz guidance for state startup grants.",
        tags=("grant", "startup", "govkz"),
        amount_raw="up to 400 MRP",
    )
    shell = """
    <html lang="kk">
      <head>
        <title>GOV.KZ - Единая платформа интернет-ресурсов государственных органов</title>
      </head>
      <body><div id="root"></div></body>
    </html>
    """
    seo_html = """
    <html lang="ru">
      <head><title>Условия по получению гранта на открытие бизнеса.</title></head>
      <body>
        <h1>Условия по получению гранта на открытие бизнеса.</h1>
        <p>Гранты предоставляются на конкурсной основе.</p>
        <p>Размер гранта составляет до 400-кратного МРП.</p>
      </body>
    </html>
    """
    route = respx.get(url).mock(
        side_effect=[
            httpx.Response(200, text=shell),
            httpx.Response(200, text=seo_html),
        ]
    )
    source = KazakhstanDomesticSupportSource()
    source.programs = (program,)

    items = await _collect(source)

    assert route.call_count == 2
    assert len(items) == 1
    assert items[0].raw["detail_fetch_status"] == "ok"
    assert items[0].raw["detail_language"] == "ru"
    assert "400-кратного МРП" in items[0].raw["detail_text"]


@pytest.mark.asyncio
@respx.mock
async def test_kazakhstan_domestic_support_retries_qazindustry_ca_bundle(monkeypatch):
    url = "https://qazindustry.gov.kz/ru/business_reimbursement"
    program = DomesticProgram(
        url=url,
        title="QazIndustry productivity reimbursement measures",
        summary="Official QazIndustry reimbursement route.",
        tags=("reimbursement", "industry", "qazindustry"),
    )
    request = httpx.Request("GET", url)
    route = respx.get(url).mock(
        side_effect=[
            httpx.ConnectError(
                "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: "
                "unable to get local issuer certificate",
                request=request,
            ),
            httpx.Response(
                200,
                text="""
                <html lang="ru"><body><main>
                  <h1>Меры государственного стимулирования</h1>
                  <p>Возмещение части затрат субъектов промышленности.</p>
                </main></body></html>
                """,
            ),
        ]
    )

    async def fake_ca_bundle_path() -> str:
        return certifi.where()

    monkeypatch.setattr(
        domestic_source,
        "_qazindustry_ca_bundle_path",
        fake_ca_bundle_path,
    )
    source = KazakhstanDomesticSupportSource()
    source.programs = (program,)

    items = await _collect(source)

    assert route.call_count == 2
    assert len(items) == 1
    assert items[0].raw["detail_fetch_status"] == "ok"
    assert "Возмещение части затрат" in items[0].raw["detail_text"]


@pytest.mark.asyncio
@respx.mock
async def test_eeas_kazakhstan_fetch_yields_grant_page():
    respx.get(EEAS_LISTING_URL).mock(
        return_value=httpx.Response(200, text=EEAS_LISTING_HTML)
    )
    respx.get(EEAS_DETAIL_URL).mock(
        return_value=httpx.Response(200, text=EEAS_DETAIL_HTML)
    )

    items = await _collect(EeasKazakhstanSource())

    assert len(items) == 1
    item = items[0]
    assert item.source == "eeas_kazakhstan"
    assert item.deadline.isoformat() == "2026-05-12"
    assert item.funder == "European External Action Service"
    assert "central_asia" in item.tags
    assert "civil_society" in item.tags
    assert (
        item.title == "Call for Proposals “Support to Civil Society in Kazakhstan” "
        "(EuropeAid/186114/DD/ACT/KZ)"
    )
    assert item.raw["reference"] == "EuropeAid/186114/DD/ACT/KZ"


@pytest.mark.asyncio
@respx.mock
async def test_eeas_kazakhstan_uses_curated_fallback_when_listing_is_empty(
    monkeypatch: pytest.MonkeyPatch,
):
    fallback_url = (
        "https://www.eeas.europa.eu/delegations/kazakhstan/fallback-call_en?s=222"
    )
    monkeypatch.setattr(
        "sources.eeas_kazakhstan.FALLBACK_DETAIL_URLS",
        (fallback_url,),
    )
    respx.get(EEAS_LISTING_URL).mock(
        return_value=httpx.Response(200, text=EEAS_EMPTY_LISTING_HTML)
    )
    respx.get(fallback_url).mock(
        return_value=httpx.Response(200, text=EEAS_DETAIL_HTML)
    )

    items = await _collect(EeasKazakhstanSource())

    assert len(items) == 1
    item = items[0]
    assert str(item.source_url) == fallback_url
    assert item.deadline.isoformat() == "2026-05-12"
    assert item.raw["listing_url"] == EEAS_LISTING_URL
    assert item.title.endswith("(EuropeAid/186114/DD/ACT/KZ)")


@pytest.mark.asyncio
@respx.mock
async def test_eeas_kazakhstan_skips_contracts_concluded_pages():
    respx.get(EEAS_LISTING_URL).mock(
        return_value=httpx.Response(200, text=EEAS_LISTING_WITH_CONTRACTS_HTML)
    )
    respx.get(EEAS_DETAIL_URL).mock(
        return_value=httpx.Response(200, text=EEAS_DETAIL_HTML)
    )

    items = await _collect(EeasKazakhstanSource())

    assert len(items) == 1
    assert (
        items[0].title == "Call for Proposals “Support to Civil Society in Kazakhstan” "
        "(EuropeAid/186114/DD/ACT/KZ)"
    )


@pytest.mark.asyncio
@respx.mock
async def test_world_bank_kazakhstan_fetch_yields_project_pipeline_item():
    respx.get(WORLD_BANK_PROJECTS_API).mock(
        return_value=httpx.Response(200, json=WORLD_BANK_PAYLOAD)
    )

    items = await _collect(WorldBankKazakhstanSource())

    assert len(items) == 1
    item = items[0]
    assert item.source == "world_bank_kazakhstan"
    assert item.type == "tender"
    assert item.deadline.isoformat() == "2031-04-21"
    assert item.amount_max == 75000000
    assert "central_asia" in item.tags
    assert "ai" in item.tags
    assert "startup" in item.tags
    assert item.raw["project_id"] == "P513072"


@pytest.mark.asyncio
@respx.mock
async def test_world_bank_kazakhstan_does_not_tag_ai_inside_words():
    respx.get(WORLD_BANK_PROJECTS_API).mock(
        return_value=httpx.Response(200, json=WORLD_BANK_FALSE_AI_PAYLOAD)
    )

    items = await _collect(WorldBankKazakhstanSource())

    assert len(items) == 1
    assert "ai" not in items[0].tags


@pytest.mark.asyncio
@respx.mock
async def test_adb_kazakhstan_fetch_yields_active_project_pipeline_items():
    respx.get(ADB_KAZAKHSTAN_IATI_URL).mock(
        return_value=httpx.Response(200, text=ADB_IATI_XML)
    )

    items = await _collect(AdbKazakhstanSource())

    assert len(items) == 1
    item = items[0]
    assert item.source == "adb_kazakhstan"
    assert item.type == "tender"
    assert item.deadline.isoformat() == "2030-08-31"
    assert item.amount_max == 173588000
    assert "central_asia" in item.tags
    assert "green_transition" in item.tags
    assert "finance" in item.tags
    assert "ai" not in item.tags
    assert item.raw["project_id"] == "58135-001"


@pytest.mark.asyncio
@respx.mock
async def test_adb_kazakhstan_marks_deadline_less_projects_as_rolling():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <iati-activities>
      <iati-activity default-currency="USD">
        <iati-identifier>XM-DAC-46004-58135-002-LN4764</iati-identifier>
        <title><narrative>Kazakhstan Digital Skills Platform</narrative></title>
        <description><narrative>National digital skills capacity building.</narrative></description>
        <activity-status code="2"/>
        <recipient-country code="KZ"/>
        <document-link url="https://www.adb.org/projects/58135-002/main#project-documents">
          <title><narrative>Project documents</narrative></title>
        </document-link>
      </iati-activity>
    </iati-activities>
    """
    respx.get(ADB_KAZAKHSTAN_IATI_URL).mock(return_value=httpx.Response(200, text=xml))

    items = await _collect(AdbKazakhstanSource())

    assert len(items) == 1
    item = items[0]
    assert item.deadline is None
    assert "rolling" in item.tags
    assert item.raw["deadline_policy"] == "rolling"


@pytest.mark.asyncio
@respx.mock
async def test_isdb_project_procurement_fetch_yields_central_asia_active_tenders():
    respx.get(ISDB_TENDER_URLS[0]).mock(
        return_value=httpx.Response(200, text=ISDB_TENDERS_HTML)
    )
    for url in ISDB_TENDER_URLS[1:]:
        respx.get(url).mock(return_value=httpx.Response(200, text="<html></html>"))

    items = await _collect(IsdbProjectProcurementSource())

    assert len(items) == 1
    item = items[0]
    assert item.source == "isdb_project_procurement"
    assert item.type == "tender"
    assert item.deadline.isoformat() == "2099-11-07"
    assert "central_asia" in item.tags
    assert "kyrgyz" in item.tags
    assert "education" in item.tags
    assert item.funder == "Islamic Development Bank"
    assert item.raw["country"] == "Kyrgyz"


@pytest.mark.asyncio
@respx.mock
async def test_ebrd_ecepp_procurement_fetch_yields_open_central_asia_tenders():
    respx.get(ECEPP_SEARCH_URL).mock(
        return_value=httpx.Response(200, text=ECEPP_NOTICE_RESULTS_HTML)
    )

    items = await _collect(EbrdEceppProcurementSource())

    assert len(items) == 2
    by_title = {item.title: item for item in items}
    kazakhstan = by_title[
        "Kazakhstan: Technical Supervision of Construction and reconstruction"
    ]
    assert kazakhstan.source == "ebrd_ecepp_procurement"
    assert kazakhstan.type == "tender"
    assert kazakhstan.deadline.isoformat() == "2099-06-05"
    assert kazakhstan.funder == "European Bank for Reconstruction and Development"
    assert "kazakhstan" in kazakhstan.tags
    assert "transport" in kazakhstan.tags
    assert "consultancy" in kazakhstan.tags
    assert kazakhstan.raw["current_state"] == "Open"
    assert kazakhstan.raw["notice_type"] == "Invitation For Tenders Single"

    kyrgyz = by_title["Kyrgyz Republic: Rehabilitation of Water Supply Systems"]
    assert "kyrgyzstan" in kyrgyz.tags
    assert "water" in kyrgyz.tags


@pytest.mark.asyncio
@respx.mock
async def test_erasmus_kazakhstan_fetch_yields_open_call_actions():
    respx.get(ERASMUS_NEWS_URL).mock(
        return_value=httpx.Response(200, text=ERASMUS_CURRENT_NEWS_HTML)
    )
    respx.get(ERASMUS_ARCHIVE_URL.format(year=2025)).mock(
        return_value=httpx.Response(200, text=ERASMUS_ARCHIVE_NEWS_HTML)
    )
    respx.get(
        (
            "https://erasmus.kz/en/novost/"
            "erasmus-2026-call-now-open-opportunities-kazakhstani-"
            "universities-and-organizations"
        )
    ).mock(return_value=httpx.Response(200, text=ERASMUS_CALL_ARTICLE_HTML))

    items = await _collect(ErasmusKazakhstanSource())

    assert len(items) == 4
    by_title = {item.title: item for item in items}

    jean_monnet = by_title["Jean Monnet – Erasmus+ Kazakhstan"]
    assert jean_monnet.deadline.isoformat() == "2099-02-03"
    assert jean_monnet.funder == "European Union / Erasmus+"
    assert "jean_monnet" in jean_monnet.tags
    assert "policy" in jean_monnet.tags
    assert jean_monnet.raw["article_title"].startswith("Erasmus+ 2026 Call Is Now Open")

    cbhe = by_title[
        "Capacity Building in Higher Education (CBHE) – Erasmus+ Kazakhstan"
    ]
    assert "capacity_building" in cbhe.tags
    assert "higher_education" in cbhe.tags

    emjm = by_title[
        "Erasmus Mundus Joint Master Degrees (EMJM) and Erasmus Mundus Design "
        "Measure (EMDM) – Erasmus+ Kazakhstan"
    ]
    assert "erasmus_mundus" in emjm.tags
    assert "joint_degrees" in emjm.tags

    icm = by_title["International Credit Mobility (ICM) – Erasmus+ Kazakhstan"]
    assert "mobility" in icm.tags
    assert "student_exchange" in icm.tags


@pytest.mark.asyncio
@respx.mock
async def test_erasmus_kazakhstan_fetch_parses_neighbor_deadline_actions():
    article = """
    <html><body>
    <section class="news-single">
      <h1 class="news-single__title title">Erasmus+ 2026 Call Is Now Open</h1>
      <div class="news-single__text">
        <p>
          <a href="https://erasmus.kz/en/dlya-vuzov/informaciya-o-zhan-mone">
            Jean Monnet
          </a>
          - EU studies action for universities.
        </p>
        <p>Application deadline: 15 March 2099</p>
      </div>
    </section>
    </body></html>
    """
    respx.get(ERASMUS_NEWS_URL).mock(
        return_value=httpx.Response(200, text=ERASMUS_CURRENT_NEWS_HTML)
    )
    respx.get(ERASMUS_ARCHIVE_URL.format(year=2025)).mock(
        return_value=httpx.Response(200, text=ERASMUS_ARCHIVE_NEWS_HTML)
    )
    respx.get(
        (
            "https://erasmus.kz/en/novost/"
            "erasmus-2026-call-now-open-opportunities-kazakhstani-"
            "universities-and-organizations"
        )
    ).mock(return_value=httpx.Response(200, text=article))

    items = await _collect(ErasmusKazakhstanSource())

    assert len(items) == 1
    assert items[0].title == "Jean Monnet – Erasmus+ Kazakhstan"
    assert items[0].deadline.isoformat() == "2099-03-15"
    assert "jean_monnet" in items[0].tags


def test_erasmus_kazakhstan_retains_closed_call_actions():
    article = """
    <html><body>
    <div class="news-single__text">
      <p>
        <a href="https://erasmus.kz/en/dlya-vuzov/informaciya-o-zhan-mone">
          Jean Monnet
        </a>
        - EU studies action for universities - <strong>3</strong>
        <strong>February 2026</strong>
      </p>
    </div>
    </body></html>
    """

    actions = _extract_actions(
        article,
        article_url="https://erasmus.kz/en/novost/erasmus-2026-call",
        today=date(2026, 6, 1),
    )

    assert len(actions) == 1
    assert actions[0].title == "Jean Monnet"
    assert actions[0].deadline == date(2026, 2, 3)
    assert actions[0].rolling is False


@pytest.mark.asyncio
@respx.mock
async def test_startup_program_sources_yield_evergreen_cloud_credit_items():
    for spec in PROGRAM_SPECS.values():
        respx.get(spec.url).mock(
            return_value=httpx.Response(
                200,
                text=f"<html><head><title>{spec.name}</title></head></html>",
            )
        )

    for source_cls in STARTUP_PROGRAM_CLASSES:
        items = await _collect(source_cls())

        assert len(items) == 1
        item = items[0]
        assert item.type == "cloud_credit"
        assert item.source == source_cls.slug
        assert "global" in item.eligibility
        assert "startup" in item.tags
        assert "rolling" in item.tags
        assert "central_asia_eligible" in item.tags
        assert item.raw["external_id"] == source_cls.slug
        assert item.raw["deadline_policy"] == "rolling"


@pytest.mark.asyncio
@respx.mock
async def test_google_org_fetch_yields_ai_opportunity_watch():
    respx.get(GOOGLE_ORG_KNOWLEDGE_URL).mock(
        return_value=httpx.Response(200, text=GOOGLE_ORG_HTML)
    )

    items = await _collect(GoogleOrgAiOpportunitySource())

    assert len(items) == 1
    item = items[0]
    assert item.source == "google_org_ai_opportunity"
    assert item.type == "grant"
    assert "global" in item.eligibility
    assert "ai" in item.tags
    assert "central_asia_eligible" in item.tags
    assert "rolling" in item.tags
    assert item.raw["external_id"] == "google_org_ai_opportunity"
    assert item.raw["deadline_policy"] == "rolling"


@pytest.mark.asyncio
@respx.mock
async def test_unesco_iite_fetch_yields_open_relevant_announcements():
    respx.get(UNESCO_IITE_ANNOUNCEMENTS_URL).mock(
        return_value=httpx.Response(200, text=UNESCO_LISTING_HTML)
    )
    respx.get(UNESCO_OPEN_URL).mock(
        return_value=httpx.Response(200, text=UNESCO_OPEN_HTML)
    )
    respx.get(UNESCO_GENERIC_URL).mock(
        return_value=httpx.Response(200, text=UNESCO_GENERIC_HTML)
    )
    respx.get(UNESCO_MONTH_FIRST_URL).mock(
        return_value=httpx.Response(200, text=UNESCO_MONTH_FIRST_HTML)
    )
    respx.get(UNESCO_EXPIRED_URL).mock(
        return_value=httpx.Response(200, text=UNESCO_EXPIRED_HTML)
    )

    items = await _collect(UnescoIiteSource())

    assert [item.source for item in items] == [
        "unesco_iite",
        "unesco_iite",
        "unesco_iite",
    ]
    assert {item.title for item in items} == {
        "Call for Entries: The AI for Education Awards 2099",
        "Call for Proposals: Publication Editing and Proofreading",
        "Global Education Data Challenge 2099",
    }
    assert "Announcements" not in {item.title for item in items}
    assert {item.deadline.isoformat() for item in items if item.deadline} == {
        "2099-05-31",
        "2099-05-25",
    }
    assert all("education" in item.tags for item in items)
    assert any("ai" in item.tags for item in items)


@pytest.mark.asyncio
@respx.mock
async def test_undp_procurement_fetch_yields_central_asia_active_notices():
    respx.get(UNDP_LISTING_URL).mock(
        return_value=httpx.Response(200, text=UNDP_LISTING_HTML)
    )

    items = await _collect(UndpProcurementSource())

    assert len(items) == 1
    item = items[0]
    assert item.source == "undp_procurement"
    assert item.type == "tender"
    assert item.deadline.isoformat() == "2099-06-03"
    assert "central_asia" in item.tags
    assert item.raw["external_id"] == "UNDP-KAZ-2099-TECH-001"
    assert item.raw["reference"] == "UNDP-KAZ-2099-TECH-001"
    assert "hotel" not in item.title.lower()
    assert (
        item.summary
        == "UNDP procurement opportunity in UNDP-KAZ / Kazakhstan Office, Astana. "
        "Reference number: UNDP-KAZ-2099-TECH-001."
    )


@pytest.mark.asyncio
@respx.mock
async def test_undp_procurement_skips_russian_operational_service_notice():
    respx.get(UNDP_LISTING_URL).mock(
        return_value=httpx.Response(200, text=UNDP_LISTING_RU_OPERATIONAL_HTML)
    )

    items = await _collect(UndpProcurementSource())

    assert items == []


def test_grants_gov_does_not_publish_query_keyword_without_content_signal():
    item = GrantsGovSource()._to_opportunity(
        {
            "id": "DOD-AMRAA-26-001",
            "title": "Epilepsy Research Program Award",
            "description": "Clinical research opportunity from USAMRAA.",
            "agencyName": "USAMRAA",
            "closeDate": "08/17/2026",
        },
        "artificial intelligence",
    )

    assert "artificial intelligence" not in item.tags


def test_grants_gov_keeps_query_keyword_when_public_copy_supports_it():
    item = GrantsGovSource()._to_opportunity(
        {
            "id": "AI-KZ-001",
            "title": "Artificial intelligence education program for Kazakhstan",
            "description": "Supports responsible AI training in Kazakhstan.",
            "agencyName": "International Programs Office",
        },
        "artificial intelligence",
    )

    assert "artificial intelligence" in item.tags


@pytest.mark.asyncio
@respx.mock
async def test_kazakhstan_watch_skips_technical_difficulties_page():
    url = "https://kz.usembassy.gov/education-culture/grants/"
    respx.get(url).mock(
        return_value=httpx.Response(
            200,
            text=(
                "<html><head><title>Technical Difficulties</title></head>"
                "<body>We’re sorry, this site is currently experiencing "
                "technical difficulties. Please try again.</body></html>"
            ),
        )
    )
    source = KazakhstanWatchSource()
    source.pages = (
        WatchPage(
            url=url,
            title="U.S. Embassy Kazakhstan grants",
            summary="Small grants and public diplomacy opportunities.",
            tags=("grant", "education"),
            type=OpportunityType.GRANT,
        ),
    )

    items = await _collect(source)

    assert items == []


@pytest.mark.asyncio
@respx.mock
async def test_kazakhstan_watch_keeps_curated_blocked_page_without_access_denied_title():
    url = "https://kazakhstan.britishcouncil.org/programmes/arts/connections-through-culture"
    respx.get(url).mock(
        return_value=httpx.Response(
            403,
            text=(
                "<html><head><title>Access Denied</title></head>"
                "<body>Access Denied</body></html>"
            ),
        )
    )
    source = KazakhstanWatchSource()
    source.pages = (
        WatchPage(
            url=url,
            title="British Council Connections Through Culture Grants Kazakhstan",
            summary="Creative collaboration grants that include Kazakhstan.",
            tags=("grant", "culture"),
            type=OpportunityType.GRANT,
            rolling=True,
        ),
    )

    items = await _collect(source)

    assert len(items) == 1
    assert (
        items[0].title
        == "British Council Connections Through Culture Grants Kazakhstan"
    )
    assert items[0].raw["page_title"] == items[0].title
    assert items[0].raw["status_code"] == 403
    assert "blocked or rate limited" in items[0].raw["status_note"]
    assert "Access Denied" not in items[0].raw.values()


def test_kazakhstan_watch_keeps_curated_russian_copy_with_source_record():
    page = WatchPage(
        url="https://example.org/embassy-grants",
        title="U.S. Embassy Kazakhstan grants",
        summary="Small grants and public diplomacy opportunities for Kazakhstan.",
        tags=("grant", "education"),
        type=OpportunityType.GRANT,
        title_ru="Гранты Посольства США в Казахстане",
        summary_ru="Актуальные условия и сроки подачи доступны на странице Посольства.",
    )

    item = KazakhstanWatchSource()._opportunity(page, raw={"external_id": page.url})

    assert item.raw["i18n"]["ru"] == {
        "title": "Гранты Посольства США в Казахстане",
        "summary": "Актуальные условия и сроки подачи доступны на странице Посольства.",
    }


@pytest.mark.asyncio
@respx.mock
async def test_kazakhstan_watch_can_retain_official_page_on_fetch_error():
    url = "https://egov.kz/cms/ru/mobile-services/pass455_mir"
    respx.get(url).mock(side_effect=httpx.ConnectError("tls failed"))
    source = KazakhstanWatchSource()
    source.pages = (
        WatchPage(
            url=url,
            title="Innovation grants for commercialization of technologies",
            summary="Official Kazakhstan eGov service page for innovation grants.",
            tags=("grant", "innovation", "commercialization"),
            type=OpportunityType.GRANT,
            rolling=True,
            retain_on_fetch_error=True,
        ),
    )

    items = await _collect(source)

    assert len(items) == 1
    assert items[0].title == "Innovation grants for commercialization of technologies"
    assert items[0].raw["page_title"] == items[0].title
    assert items[0].raw["status_code"] is None
    assert "fetch failed" in items[0].raw["status_note"]
    assert "rolling" in items[0].tags


@pytest.mark.asyncio
@respx.mock
async def test_kazakhstan_domestic_support_retains_transport_error():
    url = "https://qazinn.kz/en/granty-qazinnovations"
    respx.get(url).mock(side_effect=httpx.ConnectError("tls failed"))
    source = KazakhstanDomesticSupportSource()
    source.programs = (
        DomesticProgram(
            url=url,
            title="QazInnovations grants",
            summary="Official Kazakhstan innovation grant route.",
            tags=("grant", "innovation", "qazinnovations"),
        ),
    )

    items = await _collect(source)

    assert len(items) == 1
    assert items[0].source == "kazakhstan_domestic_support"
    assert items[0].title == "QazInnovations grants"
    assert items[0].raw["page_title"] == items[0].title
    assert items[0].raw["status_code"] is None
    assert "fetch failed" in items[0].raw["status_note"]
    assert items[0].raw["detail_fetch_status"] == "parse_error"
    assert items[0].raw["detail_sections"][0]["heading"] == "Overview"
    assert "innovation grant route" in items[0].raw["detail_text"]
    assert "domestic_support" in items[0].tags


@pytest.mark.asyncio
@respx.mock
async def test_unicef_kazakhstan_fetch_yields_only_open_tenders():
    respx.get(UNICEF_KAZAKHSTAN_TENDERS_URL).mock(
        return_value=httpx.Response(200, text=UNICEF_TENDERS_HTML)
    )

    items = await _collect(UnicefKazakhstanSource())

    assert len(items) == 1
    item = items[0]
    assert item.source == "unicef_kazakhstan"
    assert item.type == "tender"
    assert item.deadline.isoformat() == "2099-02-02"
    assert "central_asia" in item.tags
    assert "digital" in item.tags
    assert item.raw["reference"] == "RFP/KAZA/2099/001"
    assert "hotel" not in item.title.lower()
    assert (
        item.raw["application_url"] == "https://drive.google.com/drive/folders/example"
    )


@pytest.mark.asyncio
async def test_unicef_kazakhstan_retries_cloudflare_blocked_response():
    responses = iter(
        [
            httpx.Response(403, text="<title>Just a moment...</title>"),
            httpx.Response(200, text=UNICEF_TENDERS_HTML),
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return next(responses)

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        follow_redirects=True,
    )
    items = await _collect(UnicefKazakhstanSource(client=client))

    assert len(items) == 1
    assert items[0].raw["reference"] == "RFP/KAZA/2099/001"


@pytest.mark.asyncio
@respx.mock
async def test_unicef_kazakhstan_prefers_item_detail_link_for_source_url():
    respx.get(UNICEF_KAZAKHSTAN_TENDERS_URL).mock(
        return_value=httpx.Response(200, text=UNICEF_TENDERS_WITH_DETAIL_LINK_HTML)
    )

    items = await _collect(UnicefKazakhstanSource())

    assert len(items) == 1
    assert (
        str(items[0].source_url)
        == "https://www.unicef.org/kazakhstan/en/tenders/rfp-kaza-2099-001"
    )
    assert (
        items[0].raw["application_url"]
        == "https://drive.google.com/drive/folders/example"
    )


@pytest.mark.asyncio
@respx.mock
async def test_unicef_kazakhstan_uses_reader_fallback_when_vps_is_blocked():
    respx.get(UNICEF_KAZAKHSTAN_TENDERS_URL).mock(
        return_value=httpx.Response(403, text="<title>Just a moment...</title>")
    )
    respx.get(UNICEF_KAZAKHSTAN_TENDERS_READER_URL).mock(
        return_value=httpx.Response(200, text=UNICEF_TENDERS_MARKDOWN)
    )

    items = await _collect(UnicefKazakhstanSource())

    assert len(items) == 1
    assert items[0].raw["reference"] == "RFP/KAZA/2099/001"
    assert (
        items[0].raw["application_url"]
        == "https://drive.google.com/drive/folders/example"
    )


@pytest.mark.asyncio
@respx.mock
async def test_unicef_kazakhstan_keeps_recently_closed_tender_for_coverage():
    html = """
    <html><body>
      <p>
        <strong>
          RFP/KAZA/2026/001 - Institutional consultancy for mental health
          evaluation in Kazakhstan.
        </strong>
      </p>
      <p>
        The Proposals MUST be received by latest 6-00 p.m. on 02 February 2026.
      </p>
    </body></html>
    """
    respx.get(UNICEF_KAZAKHSTAN_TENDERS_URL).mock(
        return_value=httpx.Response(200, text=html)
    )

    items = await _collect(UnicefKazakhstanSource())

    assert len(items) == 1
    assert items[0].deadline.isoformat() == "2026-02-02"
    assert "closed" in items[0].tags
    assert items[0].raw["deadline_policy"] == "closed"


@pytest.mark.asyncio
@respx.mock
async def test_astana_hub_fetch_success_yields_opportunities():
    respx.get(AH_URL).mock(return_value=httpx.Response(200, text=ASTANA_HTML))
    items = await _collect(AstanaHubSource())
    assert len(items) >= 2
    titles = {it.title for it in items}
    assert "Tech Orda" in titles
    assert "Silkway" in titles
    for it in items:
        assert it.source == "astana_hub"
        assert it.url.startswith("https://astanahub.com")


@pytest.mark.asyncio
@respx.mock
async def test_astana_hub_fetch_swallows_5xx():
    respx.get(AH_URL).mock(return_value=httpx.Response(503))
    items = await _collect(AstanaHubSource())
    assert items == []


@pytest.mark.asyncio
@respx.mock
async def test_astana_hub_fetch_swallows_transport_error():
    respx.get(AH_URL).mock(side_effect=httpx.ConnectError("boom"))
    items = await _collect(AstanaHubSource())
    assert items == []


@pytest.mark.asyncio
@respx.mock
async def test_astana_hub_fetch_uses_curated_pages_on_404():
    respx.get(AH_URL).mock(return_value=httpx.Response(404))
    fallback_html = {
        "https://astanahub.com/ru/l/TechOrda2025": (
            "<title>Tech Orda 2025</title>"
            "<p>Прием заявок открыт по 29 мая 2026 года.</p>"
        ),
        "https://astanahub.com/ru/l/silkwayaccelerator2025": (
            "<title>Silkway Accelerator 2025</title>"
            '<script>const deadline = new Date("June 6, 2026 23:59:00");</script>'
        ),
        "https://astanahub.com/en/l/regional/develop": (
            "<title>Regional IT Hub</title>"
            "<p>Regional program for IT ecosystem development.</p>"
        ),
    }
    for url in FALLBACK_PROGRAM_URLS:
        respx.get(url).mock(return_value=httpx.Response(200, text=fallback_html[url]))

    items = await _collect(AstanaHubSource())
    assert len(items) == len(FALLBACK_PROGRAM_URLS)
    assert {it.source for it in items} == {"astana_hub"}
    assert all(it.url.startswith("https://astanahub.com") for it in items)
    by_title = {item.title: item for item in items}
    assert by_title["Tech Orda 2025"].deadline.isoformat() == "2026-05-29"
    assert by_title["Silkway Accelerator 2025"].deadline.isoformat() == "2026-06-06"
    assert len(by_title["Tech Orda 2025"].summary) > 120
    assert "digital-skills" in by_title["Tech Orda 2025"].summary
    assert "central_asia_eligible" in by_title["Silkway Accelerator 2025"].tags
    assert "rolling" in by_title["Regional IT Hub"].tags
    assert by_title["Regional IT Hub"].raw["deadline_policy"] == "rolling"
    assert (
        by_title["Regional IT Hub"].raw["country_scope"] == "Kazakhstan / Central Asia"
    )


@pytest.mark.asyncio
@respx.mock
async def test_internews_fetch_success_yields_opportunities():
    respx.get(IW_URL).mock(return_value=httpx.Response(200, text=INTERNEWS_HTML))
    items = await _collect(InternewsSource())
    assert len(items) == 2
    by_url = {str(item.source_url): item for item in items}
    assert "https://internews.org/opportunity/media-grant-2026/" in by_url
    assert "https://internews.org/resource/journalism-fellowship/" in by_url
    for it in items:
        assert it.source == "internews"
    assert (
        by_url[
            "https://internews.org/opportunity/media-grant-2026/"
        ].deadline.isoformat()
        == "2026-06-30"
    )
    assert by_url["https://internews.org/opportunity/media-grant-2026/"].type == "grant"
    assert (
        by_url[
            "https://internews.org/resource/journalism-fellowship/"
        ].deadline.isoformat()
        == "2026-09-12"
    )
    assert (
        by_url["https://internews.org/resource/journalism-fellowship/"].type
        == "fellowship"
    )


@pytest.mark.asyncio
@respx.mock
async def test_internews_fetch_swallows_5xx():
    respx.get(IW_URL).mock(return_value=httpx.Response(500))
    items = await _collect(InternewsSource())
    assert items == []


@pytest.mark.asyncio
@respx.mock
async def test_internews_fetch_uses_feed_on_cloudflare_403():
    feed = """<?xml version="1.0" encoding="UTF-8"?>
    <rss><channel>
      <item>
        <title>GRANT COMPETITION: Media Support</title>
        <link>https://internews.org/grant-competition-media-support/</link>
        <description>Deadline: 30 Jun 2026</description>
        <category>Call for Proposals</category>
      </item>
      <item>
        <title>Regular program update</title>
        <link>https://internews.org/regular-update/</link>
        <description>News only</description>
      </item>
    </channel></rss>
    """
    respx.get(IW_URL).mock(return_value=httpx.Response(403))
    respx.get(IW_FEED_URL).mock(return_value=httpx.Response(200, text=feed))

    items = await _collect(InternewsSource())
    assert len(items) == 1
    assert items[0].title == "GRANT COMPETITION: Media Support"
    assert (
        str(items[0].source_url)
        == "https://internews.org/grant-competition-media-support/"
    )


@pytest.mark.asyncio
@respx.mock
async def test_internews_fetch_parses_dotted_deadline_and_tender_type():
    html = """
    <html><body>
      <a href="https://internews.org/opportunity/media-grant-2026/">Media Grant 2026</a>
      <p>Deadline: 17.04.2026</p>
      <a href="https://internews.org/resource/terms-of-reference-audit/">
        Terms of Reference for Independent Audit
      </a>
      <p>Closes: 20.04.2026</p>
    </body></html>
    """
    respx.get(IW_URL).mock(return_value=httpx.Response(200, text=html))

    items = await _collect(InternewsSource())

    by_title = {item.title: item for item in items}
    assert by_title["Media Grant 2026"].deadline.isoformat() == "2026-04-17"
    assert by_title["Media Grant 2026"].type == "grant"
    assert (
        by_title["Terms of Reference for Independent Audit"].deadline.isoformat()
        == "2026-04-20"
    )
    assert by_title["Terms of Reference for Independent Audit"].type == "tender"


@pytest.mark.asyncio
@respx.mock
async def test_internews_marks_terms_without_deadline_as_rolling():
    html = """
    <html><body>
      <a href="https://internews.org/resource/learning-visibility-events/">
        Terms of Reference: Learning and Visibility events in Brussels, Belgium
      </a>
      <p>Open call for qualified event teams.</p>
    </body></html>
    """
    respx.get(IW_URL).mock(return_value=httpx.Response(200, text=html))

    items = await _collect(InternewsSource())

    assert len(items) == 1
    assert items[0].deadline is None
    assert "rolling" in items[0].tags
    assert items[0].raw["deadline_policy"] == "rolling"


@pytest.mark.asyncio
@respx.mock
async def test_internews_healthcheck_false_on_error():
    src = InternewsSource()
    respx.get(src.base_url).mock(side_effect=httpx.ConnectError("down"))
    async with src:
        ok = await src.healthcheck()
    assert ok is False


@pytest.mark.asyncio
@respx.mock
async def test_opportunity_desk_rss_fetch_yields_opportunities():
    respx.get(OPPORTUNITY_DESK_FEED_URL).mock(
        return_value=httpx.Response(200, text=RSS_FEED)
    )

    items = await _collect(OpportunityDeskSource())

    assert len(items) == 2
    assert items[0].source == "opportunity_desk"
    assert items[0].deadline.isoformat() == "2026-06-30"
    assert "ai" in items[0].tags
    assert "edtech" in items[0].tags


@pytest.mark.asyncio
@respx.mock
async def test_opportunity_desk_rss_skips_roundup_posts():
    feed = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <item>
          <title>15 Opportunities for Professionals Aged 30 and Above Currently Open</title>
          <link>https://example.org/roundup</link>
          <guid>roundup</guid>
          <description>Here are some opportunities for professionals this month.</description>
          <category>Our Blog</category>
        </item>
        <item>
          <title>AI Fellowship for Journalists</title>
          <link>https://example.org/fellowship</link>
          <guid>fellowship</guid>
          <description>Deadline: 10 Jul 2026. Media and AI opportunity.</description>
          <category>Fellowships</category>
        </item>
      </channel>
    </rss>
    """
    respx.get(OPPORTUNITY_DESK_FEED_URL).mock(
        return_value=httpx.Response(200, text=feed)
    )

    items = await _collect(OpportunityDeskSource())

    assert len(items) == 1
    assert items[0].title == "AI Fellowship for Journalists"


@pytest.mark.asyncio
@respx.mock
async def test_fundsforngos_rss_fetch_combines_feeds():
    for url in FUNDSFORNGOS_FEED_URLS:
        respx.get(url).mock(return_value=httpx.Response(200, text=RSS_FEED))

    items = await _collect(FundsForNgosSource())

    assert len(items) == 2
    assert {item.source for item in items} == {"fundsforngos"}
    assert all("grant" in item.tags for item in items)
    assert any("media" in item.tags for item in items)


@pytest.mark.asyncio
@respx.mock
async def test_rss_inference_does_not_tag_ai_inside_other_words():
    feed = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"><channel><item>
      <title>Savings Fellowship for Working Professionals</title>
      <link>https://example.org/savings</link>
      <description>Practical finance advice for applicants.</description>
    </item></channel></rss>
    """
    respx.get(OPPORTUNITY_DESK_FEED_URL).mock(
        return_value=httpx.Response(200, text=feed)
    )

    items = await _collect(OpportunityDeskSource())

    assert len(items) == 1
    assert "ai" not in items[0].tags


@pytest.mark.asyncio
@respx.mock
async def test_rss_deadline_parses_hyphenated_month_name():
    feed = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"><channel><item>
      <title>Creative Fellowship Program</title>
      <link>https://example.org/creative-fellowship</link>
      <description>
        Deadline: 30-Mar-2026.
        The post Creative Fellowship first appeared on fundsforNGOs.
      </description>
    </item></channel></rss>
    """
    respx.get(FUNDSFORNGOS_FEED_URLS[0]).mock(
        return_value=httpx.Response(200, text=feed)
    )
    for url in FUNDSFORNGOS_FEED_URLS[1:]:
        respx.get(url).mock(return_value=httpx.Response(503))

    items = await _collect(FundsForNgosSource())

    assert len(items) == 1
    assert items[0].deadline.isoformat() == "2026-03-30"
    assert "first appeared" not in items[0].summary


@pytest.mark.asyncio
@respx.mock
async def test_opportunity_desk_skips_blog_posts_without_opportunity_terms():
    feed = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"><channel><item>
      <title>How to Build Savings While Working a Job</title>
      <link>https://example.org/blog-savings</link>
      <description>Practical finance advice for applicants.</description>
    </item></channel></rss>
    """
    respx.get(OPPORTUNITY_DESK_FEED_URL).mock(
        return_value=httpx.Response(200, text=feed)
    )

    items = await _collect(OpportunityDeskSource())

    assert items == []
