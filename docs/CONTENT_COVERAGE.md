# Content coverage

## Active ingestion

| Source | Adapter | Signal | Current role |
|---|---|---|---|
| Grants.gov | API | US federal grants | High-volume upstream source for AI, education, media, governance, agriculture and environment themes |
| Astana Hub | HTML + curated fallback | Kazakhstan startup/program ecosystem | Local startup and accelerator coverage |
| Internews | HTML + RSS fallback | Media grants and fellowships | Media and journalism opportunities; no-date terms of reference are marked `rolling` instead of surfacing as broken deadline records |
| IsDB project procurement | HTML listing | Central Asia development procurement | Item-level active IsDB tender coverage for Kazakhstan and neighboring Central Asia countries |
| EBRD ECEPP procurement | HTML table | EBRD procurement notices | Item-level active ECEPP tenders filtered to Kazakhstan and neighboring Central Asia countries |
| Erasmus+ Kazakhstan | HTML news + detail pages | Higher-education grant calls | Item-level Erasmus+ call coverage for Kazakhstani universities and organizations with action-specific deadlines |
| Opportunity Desk | RSS | Fellowships, contests, scholarships, grants | Global bridge source with blog-post filtering |
| FundsforNGOs | RSS | NGO grants, education, media, agriculture, environment, animal welfare | Donor bridge source with expanded category coverage for AgroTech, VetTech and EcoTech signals; raw categories are still not blindly trusted for scoring |
| Kazakhstan Domestic Support | curated official page checks + local detail snapshots | Kazakhstan grants, subsidies, preferential finance, leasing, reimbursements, tax benefits and state programs | Production bridge for official domestic-support entry points with actionable detail pages: QazInnovations, Damu, Business Enbek, eGov Road Map of Business, eGov social-entrepreneurship grants, Baiterek/BGov, eGov agriculture and business-support services, gov.kz grant guidance, KazAgroFinance, Agrarian Credit Corporation, NCSTE, CISC small grants, QazIndustry, QazTrade/export.gov.kz, KazakhExport, Development Bank of Kazakhstan, Industrial Development Fund, KAZAKH INVEST, Astana Hub participant benefits and QIC fund news |
| Kazakhstan Watch | curated page checks | Kazakhstan donor/procurement entry points | Production bridge for Embassy, EBRD, Erasmus+ and British Council pages without stable item-level adapters yet |
| EEAS Kazakhstan | HTML listing + detail pages | Kazakhstan delegation grant calls | Item-level EU grant coverage with deadline/reference extraction |
| UNDP procurement notices | HTML listing | UNDP procurement and tender opportunities | Active item-level parser for Kazakhstan and Central Asia-relevant notices |
| World Bank Kazakhstan | JSON API | Kazakhstan project and procurement pipeline | Item-level multilateral project pipeline for AI, digital, education, AgroTech, EcoTech, public-sector and infrastructure signals |
| ADB Kazakhstan | IATI XML | Kazakhstan project and procurement pipeline | Item-level ADB project pipeline for infrastructure, finance, AgroTech, EcoTech, governance and public-sector signals |
| Google Cloud Startup | page monitor | Global startup cloud credits | Evergreen startup/cloud-credit opportunity for Kazakhstan-based AI/EdTech/GovTech teams |
| Microsoft Founders Hub | page monitor | Global startup cloud credits and support | Evergreen Azure/AI startup support monitor |
| AWS Activate | page monitor | Global startup cloud credits | Evergreen cloud-credit monitor for eligible startups |
| NVIDIA Inception | page monitor | Global AI startup support | AI tooling, ecosystem and investor-exposure monitor |
| Cloudflare Startups | page monitor | Global startup cloud credits | Edge/serverless/security/Workers AI credit monitor |
| MongoDB Startups | page monitor | Global startup database credits | Atlas/database startup support monitor |
| UNICEF Kazakhstan | HTML tender page | Kazakhstan procurement | Item-level UNICEF Kazakhstan tender parser with browser-like retry headers; recent closed tenders can remain as coverage-only records while expired tenders stay out of the default feed |
| Google.org AI Opportunity | page monitor | AI education philanthropy | Global AI/digital-skills grant and partner-program watch for nonprofit, government and academic routes |
| UNESCO IITE | HTML announcements | AI and education calls | Item-level UNESCO IITE parser for AI/EdTech awards, proposals and consultancy calls; expired notices are excluded |

## Quality rules now enforced

- Short keywords such as `ai` are matched on word boundaries only.
- RSS feeds infer tags from title and summary, not noisy site-wide category dumps.
- Opportunity Desk blog posts without opportunity terms are skipped.
- Opportunity Desk / FundsforNGOs bridge items without Kazakhstan/Central Asia
  signal are treated as lower confidence, and out-of-region or event-only
  items such as Africa-only accelerators and conference-only trips are excluded
  from the default feed.
- Broad bridge sources with explicit out-of-region-only signals, such as
  Ukraine-only, MENA-only or Brussels/Belgium event-service notices, are
  excluded from the default Kazakhstan/Central Asia feed unless the item also
  has a clear Kazakhstan/Central Asia eligibility signal.
- Clearly US-only domestic opportunities, including Native American / tribal-only
  grants, are excluded from the Kazakhstan/Central Asia default feed.
- Grants.gov records require an explicit Kazakhstan/Central Asia opportunity-level
  geo signal before they can enter the default feed; otherwise they remain audit-only.
- Grants.gov tourism-only/storytelling and security-only/counterterrorism notices
  are excluded from the applicant-facing feed even when they mention Central Asia.
- Grants.gov records without a synopsis receive a compact source/deadline summary
  instead of entering the UI as blank cards.
- IsDB procurement records are accepted only when the listing status is active
  and the country is Kazakhstan or a neighboring Central Asia country.
- EBRD ECEPP records are accepted only when current state is `Open`, the hidden
  notice metadata has a Central Asia country, and the closing date is not past.
- Erasmus+ Kazakhstan records are accepted only from call-specific news items,
  then expanded into action-level opportunities with future deadlines.
- World Bank theme tags use word-boundary matching so `ai` is not inferred from
  words such as `sustainable`, `rail`, or `aims`.
- World Bank state-borrower and sovereign lending records are retained only for
  audit/full-index context; they do not enter the default applicant-facing feed.
- ADB item tags use word-boundary matching and only active/proposed IATI
  activities enter ingestion; closed activities stay out of the default feed.
- Startup/cloud-credit monitors are treated as evergreen support opportunities,
  not one-off grants, and are tagged as globally accessible startup support with
  a `rolling` deadline policy.
- UNICEF Kazakhstan tenders are parsed at item level, Cloudflare-like challenge
  responses are retried with browser headers, and only recent closed tenders can
  remain as coverage-only source evidence.
- UNDP and UNICEF operational-service notices such as hotel accommodation,
  catering, venues and conference-package procurement are filtered out because
  they are not funding/support opportunities for target users.
- UNESCO IITE announcements are parsed at item level; expired calls and
  non-opportunity vacancy notices stay out of the default feed.
- Technical-difficulty placeholder pages are skipped by the Kazakhstan watch
  bridge instead of being shown as live opportunities.
- Astana Hub fallback records use curated working summaries, eligibility notes
  and country-scope metadata for Tech Orda, Silkway Accelerator and Regional IT
  Hub instead of showing a generic placeholder description.
- Official curated watch pages that block automated fetches with `403` or
  rate limits are retained with the curated title and a raw status note, so
  CDN error text such as `Access Denied` does not enter the public content.
- Selected official service pages can also be retained when the VPS cannot
  complete TLS/HTTP fetches, again using curated text plus a raw status note
  instead of surfacing transport errors to users.
- Kazakhstan Domestic Support keeps one normalized rolling record per official
  domestic program page and separates internal Kazakhstan grants, subsidies,
  cost-reimbursement, tax-benefit and state-program signals from the broader
  donor/procurement watch bridge.
- Kazakhstan Domestic Support now stores a sanitized local `detail_text`,
  `detail_sections`, `detail_language`, `detail_fetched_at` and
  `detail_html_sha256` snapshot for official pages when the page can be fetched
  and parsed. If a page blocks or fails fetch, it still records an explicit
  `detail_fetch_status` so the dashboard and audits distinguish external access
  failures from missing parser work.
- The content audit now checks that Kazakhstan domestic-support records have
  either a local detail snapshot or an explicit detail status. This prevents
  future source additions from becoming title-only cards.
- Homepage-only domestic bridge pages are excluded until a more actionable
  official detail page is available.
- `make content-audit` checks live source coverage, forbidden terms, missing
  summaries, short summaries, unmarked no-deadline records, weak homepage-like
  source URLs and leaked HTML entities.
- `/coverage` reports per-source indexed/open/relevant counts so the dashboard
  can show whether a source is only registered or actually contributing items.
- Production `GRANT_RADAR_SOURCES` must include the full source registry, not
  only the original MVP trio, otherwise active adapters will appear in coverage
  but never refresh their persisted rows.
- The public dashboard requests up to 5000 open/rolling items through the
  backend `deadline_after` filter, and the `Full index` scope explicitly asks
  the API for audit-only/low-geo-confidence rows with `include_irrelevant=true`.
- Dashboard defaults to a quality filter instead of showing every low-signal
  record first.
- Dashboard now has an explicit `Open / Full index` scope control. The default
  remains open opportunities, while `Full index` reloads the same backend feed
  without the deadline cutoff for audit and archive checks.

## Next content expansions

Priority order for the next production round:

1. U.S. Embassy small grants pages for Kazakhstan, Uzbekistan, Kyrgyzstan and Tajikistan once the pages stop returning technical-difficulty placeholders.
2. More country ministry / procurement pages for Central Asia.
3. Google.org detail-level partner/grantee pages beyond the current watch monitor.
4. British Council / KOICA / GIZ item-level sources if stable official listings are available; British Council Kazakhstan is currently covered as a curated watchlist bridge because the official pages block automated fetches.

Each new source should ship with:

- parser unit tests with mocked HTTP;
- at least one live smoke command;
- source registry entry;
- scoring/eligibility notes;
- duplicate behavior checked against existing records.
