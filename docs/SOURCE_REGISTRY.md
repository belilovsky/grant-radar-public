# Sources

Priority source map for `grant-radar`.

This document defines which sources should be monitored first for opportunities relevant to:

- AI
- EdTech
- GovTech
- AgroTech
- VetTech
- EcoTech
- digital public infrastructure
- startup support
- cloud credits
- public tenders
- donor and foundation funding

Geographic scope:

- Kazakhstan
- Uzbekistan
- Kyrgyzstan
- Tajikistan
- Turkmenistan
- Central Asia regional programs
- global programs accessible from Central Asia

## Source tiers

### Tier 1 – Must monitor continuously

These sources are high-value because they produce directly actionable opportunities or recurring programs.

| Source | Category | Why it matters | Monitoring frequency | Notes |
|---|---|---|---|---|
| Google for Startups | accelerator / startup support | Relevant for AI startups and regional founder programs | weekly | Active `google_cloud_startup` monitor covers the cloud-credit program; track MENA / MENAT cohorts next |
| Google.org | grants / philanthropy | Relevant through nonprofit or government partners | weekly | Active `google_org_ai_opportunity` watch monitor; item-level partner/grantee pages next |
| Microsoft for Startups / Founders Hub | cloud credits / startup support | High-probability infrastructure support | weekly | Active `microsoft_founders_hub` monitor |
| AWS Activate | cloud credits | Fastest non-dilutive infrastructure support | weekly | Active `aws_activate` monitor |
| Grants.gov | grants | Large upstream source for U.S.-funded opportunities | 2-3 times per week | Domestic-only notices are excluded; a search keyword becomes a public topic tag only when the visible title or summary supports it |
| Opportunity Desk | grants / fellowships / contests | Broad global opportunities with many fellowships and scholarships | daily | RSS-backed active parser; blog posts are filtered |
| FundsforNGOs | grants / NGO funding | Strong bridge source for donor grants, education, media, agriculture, environment and animal-welfare calls | daily | RSS-backed active parser; expanded category set now contributes AgroTech, VetTech and EcoTech signals |
| World Bank procurement and project pages | tenders / multilateral | Major route for education and digital transformation projects | daily | Active `world_bank_kazakhstan` project adapter plus `world_bank_procurement_ca` for current procurement notices across Central Asia |
| EU Funding & Tenders Portal | grants / R&D / partnerships | Major official surface for research, innovation, digital and consortium calls | daily | Active `eu_funding_tenders_ca` API adapter; every result is marked for eligibility verification |
| Canada Fund for Local Initiatives | local small grants | Recurring official route for locally designed civil-society projects | daily during call windows | Active `canada_cfli_ca` annual-status monitor; emits only officially open Central Asia rows |
| ADB procurement and consulting notices | tenders / multilateral | Strong relevance in education and digital public sector | weekly | Active `adb_kazakhstan` IATI adapter monitors Kazakhstan project pipeline |
| IsDB project procurement | tenders / development funding | Relevant for education, infrastructure, water, finance and digital capacity projects across member countries | weekly | Active `isdb_project_procurement` adapter filters active Kazakhstan/Central Asia notices |
| EBRD ECEPP procurement | tenders / multilateral | Relevant for digital modernization, municipal infrastructure, water, transport and energy lots | weekly | Active `ebrd_ecepp_procurement` adapter filters open Kazakhstan/Central Asia notices |
| Erasmus+ Kazakhstan | grants / education partnerships | High-fit institutional call surface for universities and academic organizations in Kazakhstan | weekly | Active `erasmus_kazakhstan` adapter expands official call posts into action-level opportunities with deadlines |
| UNICEF procurement / innovation / education | grants / tenders / partnerships | Relevant for education and child-focused digital programs | weekly | Active `unicef_kazakhstan` tender parser |
| UNESCO calls and participation programs | grants / partnerships | Good fit for education, AI literacy, teacher training | weekly | Active `unesco_iite` item-level announcements parser |
| UNDP procurement and challenges | tenders / innovation | Useful for public sector and DPI-related pilots | weekly | Active `undp_procurement` parser on country notices |

### Tier 2 – Strong strategic sources

These are highly relevant but less predictable or more partnership-dependent.

| Source | Category | Why it matters | Monitoring frequency | Notes |
|---|---|---|---|---|
| USAID-related opportunity feeds | grants / contracts | Historically important, but unstable in 2026 | weekly | Treat as opportunistic, verify active funding |
| U.S. Embassy small grants pages in Central Asia | grants | Useful for local education / STEM / civic-tech pilots | biweekly | Smaller tickets but easier entry |
| British Council | grants / partnerships | Good for education partnerships and institutional pilots | biweekly | Kazakhstan HE, creative collaboration and Newton-Al-Farabi pages are covered by the `kazakhstan_watch` bridge until stable item-level listings are available |
| Erasmus+ | grants / education partnerships | Relevant via university and consortium model | biweekly | Kazakhstan call coverage is active through `erasmus_kazakhstan`; partner-search and special actions can still expand |
| Horizon Europe partner searches | R&D / consortium funding | Relevant for research-heavy AI / education angles | biweekly | Better with EU partners |
| Islamic Development Bank country programs | development funding | Relevant in education and digital capacity building beyond tender notices | biweekly | Project procurement is covered by `isdb_project_procurement`; watch country program pages next |
| KOICA | grants / development cooperation | Good fit for digital skills and education programs | biweekly | Often enters through country programs |
| GIZ | grants / implementation programs | Practical route through local partners | biweekly | Good for digital transformation and skills |
| Astana Hub | accelerator / local ecosystem | High practical relevance for Kazakhstan-based startups | weekly | Includes competitions, acceleration, and ecosystem links |
| Kazakhstan domestic support programs | grants / subsidies / preferential finance / leasing / reimbursements / tax benefits | Direct Kazakhstan routes for innovation grants, SME subsidies, Baiterek finance, agro support, science commercialization, NGO grants, export support, industrial finance, investment support and IT tax benefits | weekly | Active `kazakhstan_domestic_support` bridge covers official QazInnovations, Damu, Business Enbek, eGov Road Map of Business, eGov social-entrepreneurship grants, Baiterek/BGov, eGov agriculture and business-support services, gov.kz grant guidance, KazAgroFinance, Agrarian Credit Corporation, NCSTE, CISC small grants, QazIndustry, QazTrade/export.gov.kz, KazakhExport, DBK, IDF, KAZAKH INVEST, Astana Hub and QIC fund news pages. Fetchable official pages store sanitized local detail snapshots; blocked pages store explicit detail status. Homepage-only entries are excluded until an actionable detail URL is available |
| NVIDIA Inception | startup / AI ecosystem | Useful for AI tooling, GPU ecosystem, technical support and investor exposure | weekly | Active `nvidia_inception` monitor |
| Cloudflare Startups | cloud credits / startup support | Useful for edge, security, serverless and Workers AI credits | weekly | Active `cloudflare_startups` monitor |
| MongoDB Startups | cloud credits / database support | Useful for Atlas credits and database-heavy AI/EdTech products | weekly | Active `mongodb_startups` monitor |
| Kazakhstan Watch | donor / procurement watchlist | High relevance entry points for Kazakhstan grants, tenders, and donor calls | daily | Curated page-level bridge for sources without stable item-level APIs/parsers; retains blocked official pages with curated titles instead of CDN error text |
| EEAS Kazakhstan | grants / EU delegation | Direct EU grant calls for Kazakhstan civil society and governance programs | daily | Active `eeas_kazakhstan` adapter extracts grant cards, deadlines, references and detail metadata |

### Tier 3 – Opportunistic / edge sources

These sources are worth tracking but should not dominate the pipeline.

| Source | Category | Why it matters | Monitoring frequency | Notes |
|---|---|---|---|---|
| OpenAI partnership announcements | partnership / ecosystem | No standard public grant track, but strategic relevance is high | monthly | Best approached through government / education rollout angle |
| NED | grants | Limited fit for core EdTech, more relevant for civic-tech overlays | monthly | Use only for narrow democracy / transparency cases |
| Corporate CSR foundations | grants / sponsorship | May support education pilots or inclusion initiatives | monthly | Highly variable, requires manual review |
| Philanthropic education foundations | grants | Useful for nonprofit wrapper strategy | monthly | Often requires NGO or academic lead |
| Regional ministry / agency sites | tenders / pilots | Can surface local procurement or pilot windows | weekly | Especially education ministries and digital ministries |
| University innovation funds | pilots / partnerships | Useful for validation and pilot co-financing | monthly | Better for research or training modules |

## Country-specific pages to track

### Kazakhstan

- Ministry of Education / Просвещения related pages
- Ministry of Digital Development / AI-related pages
- QazInnovations grants and eGov innovation-grant service pages
- Damu SME subsidy and business-support programs
- Astana Hub announcements
- national procurement portals
- quasi-government education operators

### Uzbekistan

- Ministry of Preschool and School Education
- Ministry of Digital Technologies
- Uzinfocom and related digital operators
- national procurement and donor-backed education pages

### Kyrgyzstan

- Ministry of Education and Science
- public procurement portal
- donor project pages tied to higher education and digitalization

### Tajikistan

- Ministry of Education and Science
- World Bank / ADB country program pages
- procurement pages linked to digital foundations and LEARN-type programs

### Turkmenistan

- lower signal environment; monitor multilateral and regional channels first
- watch UN agency and multilateral project pages more than local open ecosystems

## Opportunity classes

Each collected item should be tagged into one primary class and optional secondary classes.

Primary classes:

- `grant`
- `accelerator`
- `cloud_credits`
- `tender`
- `rfp`
- `challenge`
- `fellowship`
- `partnership`
- `pilot_program`

Secondary tags:

- `ai`
- `edtech`
- `govtech`
- `dpi`
- `teacher_training`
- `school_systems`
- `higher_education`
- `startup`
- `nonprofit_required`
- `government_partner_required`
- `central_asia_eligible`

## Monitoring rules

### Inclusion rules

Collect the opportunity if at least one of the following is true:

- Central Asia is explicitly eligible
- the program is global and does not exclude the region
- the call is relevant to AI, education, public sector digitization, or startup infrastructure
- the source is a major donor / multilateral / corporate platform with repeat value

### Exclusion rules

Skip or down-rank the opportunity if:

- it is clearly limited to another geography with no workaround
- it is a U.S.-domestic grant for specific local groups, for example Native American / tribal-only eligibility
- it comes from a high-volume upstream source such as Grants.gov without a clear Kazakhstan/Central Asia opportunity-level geo signal
- it is unrelated to AI, EdTech, GovTech, digital skills, public sector innovation, or startup support
- it is expired and has no archival value
- it is duplicate content syndicated from another tracked source

## Prioritization model

Each item should later receive a score across these dimensions:

- geographic fit
- sector fit
- stage fit
- application complexity
- funding value
- strategic value
- partner dependency
- deadline urgency
- confidence in eligibility

Simple early-stage scoring recommendation:

- `P1` – direct fit, open now, actionable
- `P2` – relevant but partner-dependent or less certain
- `P3` – weak fit, informational, or future watchlist

## Parser roadmap

Recommended parser order:

1. Grants.gov – active
2. Astana Hub – active
3. Internews – active
4. IsDB project procurement – active `isdb_project_procurement`
5. EBRD ECEPP procurement – active `ebrd_ecepp_procurement`
6. Erasmus+ Kazakhstan – active `erasmus_kazakhstan`
7. Opportunity Desk – active RSS bridge
8. FundsforNGOs – active RSS bridge
9. Kazakhstan domestic support – active `kazakhstan_domestic_support`
10. Kazakhstan source watch – active `kazakhstan_watch`
11. Google for Startups Cloud – active `google_cloud_startup`
12. Google.org – active `google_org_ai_opportunity` watch monitor
13. Microsoft for Startups – active `microsoft_founders_hub`
14. AWS Activate – active `aws_activate`
15. World Bank projects – active `world_bank_kazakhstan`
16. World Bank procurement – active `world_bank_procurement_ca`
17. EU Funding & Tenders – active `eu_funding_tenders_ca`
18. Canada CFLI – active `canada_cfli_ca`
19. EEAS Kazakhstan – active `eeas_kazakhstan`
20. ADB – active `adb_kazakhstan`
21. NVIDIA Inception – active `nvidia_inception`
22. Cloudflare Startups – active `cloudflare_startups`
23. MongoDB Startups – active `mongodb_startups`
24. UNICEF – active `unicef_kazakhstan`
25. UNESCO – active `unesco_iite`
26. UNDP procurement – active `undp_procurement`
27. country ministry pages

## Data capture fields

At minimum, each source adapter should try to extract:

- title
- source_name
- source_url
- country_scope
- opportunity_type
- sector_tags
- summary
- eligibility
- deadline_raw
- deadline_at
- amount_raw
- amount_min
- amount_max
- currency
- requires_partner
- nonprofit_only
- government_only
- application_url
- published_at
- scraped_at
- dedup_key

## Manual review flags

Mark for manual review if:

- eligibility is ambiguous
- the deadline cannot be parsed safely
- funding amount is unclear
- the program requires institutional lead applicant
- the source page is dynamic or incomplete
- the item looks important but classification confidence is low

## Operating notes

- Prefer official program pages over press releases.
- Keep original source links even after normalization.
- Preserve raw amount and deadline text in addition to parsed fields.
- For official Kazakhstan domestic-support pages, store sanitized local
  `detail_text` / `detail_sections` where allowed so operators can qualify
  grants and subsidies without opening every source page first.
- Store enough source metadata to reproduce collection runs and audit parser behavior.
- If a source is politically or operationally unstable, keep it in the radar but lower automation assumptions.

## Remaining source gaps

The production feed now has item-level coverage for Grants.gov, Astana Hub,
Internews, IsDB project procurement, EBRD ECEPP procurement, Erasmus+
Kazakhstan, Opportunity Desk, FundsforNGOs, EEAS Kazakhstan, World Bank
Kazakhstan, ADB Kazakhstan and UNICEF Kazakhstan, plus evergreen startup/cloud-credit
program monitors, a curated Kazakhstan watch bridge, and a dedicated Kazakhstan
domestic-support bridge for official grants, subsidies, preferential finance,
leasing, reimbursements, tax benefits and state programs.

Next useful item-level adapters:

- Google.org grant and nonprofit pages
- UNDP procurement pages remain covered by `undp_procurement`
- U.S. Embassy small grants pages across Central Asia
- country ministry and procurement pages
