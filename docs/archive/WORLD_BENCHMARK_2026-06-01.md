# QAZ.FUND benchmark vs world-class funding platforms

Date: 2026-06-01

## Why this doc

This benchmark compares `qaz.fund` with mature global platforms in adjacent
categories:

- grant prospecting for nonprofits;
- research funding discovery;
- global development tender and grant intelligence;
- funder and recipient intelligence.

The goal is not to copy their full product scope. The goal is to identify the
smallest set of additions that would materially improve `qaz.fund` for
Kazakhstan-based users.

## Current QAZ.FUND baseline

As of 2026-06-01, the live product already has several strengths:

- Kazakhstan-first ranking with Central Asia context.
- Public Russian-first interface plus English variant.
- Local detail pages with structured metadata, source excerpts, preparation
  checklist and application path.
- Transparent source coverage via `/coverage`.
- Verified production smoke and content audit flow.
- A mixed source base across grants, subsidies, startup programs, procurement,
  development banks and cloud-credit programs.

What it does not yet do deeply:

- user-level personalization;
- saved searches and alerts;
- funder intelligence pages;
- historical awards and peer funding analysis;
- lifecycle tracking from forecast to award;
- workflow and pipeline management.

## Benchmark set

### 1. Instrumentl

Official sources:

- [Discover Plan](https://help.instrumentl.com/en/articles/14794007-discover-plan)
- [Filtering Matches](https://help.instrumentl.com/en/articles/3827937-sorting-and-filtering-your-opportunity-matches)

Notable strengths:

- project-based matching instead of one flat catalog;
- funder matches beyond open calls;
- foundation profiles with funding history and 990 insights;
- reverse lookup through recipient profiles and peer prospecting;
- tracker with owners, tasks, calendar, cycles, reminders and notes;
- import of historic grants into the pipeline.

What matters for us:

- Instrumentl is strongest on moving from discovery to execution.
- The big lesson is not "build a giant CRM now".
- The real lesson is to connect search results to lightweight pipeline actions.

### 2. GrantForward

Official sources:

- [About GrantForward](https://www.grantforward.com/about)
- [Researcher Support](https://www.grantforward.com/support/researcher)

Notable strengths:

- large continuously updated sponsor database;
- researcher profiles that drive recommendations;
- saved searches across grants, awards and pre-solicitations;
- collaborator discovery;
- sponsor search and awarded-project intelligence.

What matters for us:

- GrantForward is strong on profile-based matching and strategic discovery.
- The key takeaway is that users want more than "find open calls now". They
  also want pre-solicitations, awards and sponsor intelligence.

### 3. Pivot-RP

Official sources:

- [Pivot-RP product page](https://clarivate.com/academia-government/scientific-and-academic-research/research-funding-analytics/pivot-rp-funding/)
- [Pivot-RP overview page](https://clarivate.com/academia-government/lp/pivot-rp/)

Notable strengths:

- expert-curated global funding database;
- AI matching via researcher profiles;
- awarded-grants intelligence at large scale;
- collaborator discovery through scholarly profiles;
- institution-level communication and workflow tools;
- AI-generated summaries for faster evaluation.

What matters for us:

- Pivot-RP shows the value of combining opportunities with historical outcomes.
- For `qaz.fund`, the closest equivalent is not researcher profiles first. It
  is likely organization or project profiles for matching and alerts.

### 4. Candid

Official sources:

- [Candid dashboard](https://candid.org/candid-search/features/dashboard/)
- [Candid grants data](https://candid.org/candid-search/features/grants-data/)
- [Candid search launch](https://candid.org/press/launch-of-candid-search-unifies-nonprofit-and-funder-data-in-one-place-enabling-faster-and-more-meaningful-connections/)

Notable strengths:

- organization-centric grant intelligence;
- grants given vs grants received;
- auto-generated collections like "my funders" and peer cohorts;
- saved searches and prospect lists;
- filtering by year, amount, subject, geography and population served;
- APIs and data-layer orientation.

What matters for us:

- Candid is the clearest proof that funder and recipient graphs are product
  features, not just back-office data.
- The most transferable idea for `qaz.fund` is "who funded organizations like
  me" and "which funders keep supporting this topic in my region".

### 5. Devex Pro Funding

Official sources:

- [Devex Pro Funding](https://pgs.devex.com/devex-pro-funding/)
- [Search for funding](https://support.devex.com/hc/en-us/articles/360036503613-Search-for-funding)

Notable strengths:

- full funding lifecycle: early activity, program reports, open calls, awards;
- strong filter model by country, funder, topic, status and size;
- shortlist and award intelligence;
- full-text preview without leaving the search page;
- market-level intelligence and trend analysis.

What matters for us:

- Devex is the best reference for procurement and development-finance
  intelligence.
- The most important lesson is lifecycle depth: forecast -> program ->
  solicitation -> award.

### 6. GrantStation

Official sources:

- [Member benefits](https://grantstation.com/why-join/member-benefits-old)

Notable strengths:

- narrative funder profiles written by researchers;
- targeted search across open/approachable funders;
- saved results on a personalized dashboard;
- email alerts when profiles change;
- planning tools such as a grants calendar and decision matrix;
- practical educational resources for applicants.

What matters for us:

- GrantStation is a reminder that curated, readable funder summaries still
  matter even when the raw database is strong.
- This is especially relevant for Kazakhstan users who often need operator-grade
  plain-language guidance, not just a link dump.

## Head-to-head summary

| Capability | QAZ.FUND now | Instrumentl | GrantForward | Pivot-RP | Candid | Devex | GrantStation |
|---|---|---|---|---|---|---|---|
| Public discovery catalog | yes | yes | yes | yes | yes | yes | yes |
| Kazakhstan-first relevance | strong | no | no | no | no | partial | no |
| Public Russian UX | strong | no | no | no | no | no | no |
| Source transparency | strong | partial | partial | partial | partial | partial | partial |
| Saved searches | no | yes | yes | yes | yes | yes | yes |
| Alerts / reminders | partial | strong | strong | strong | partial | strong | strong |
| Funder profiles | weak | strong | medium | medium | strong | medium | strong |
| Historical awards | weak | medium | strong | strong | strong | strong | weak |
| Peer / cohort intelligence | weak | strong | medium | medium | strong | medium | weak |
| Forecast / pre-solicitation | weak | weak | medium | medium | weak | strong | weak |
| Workflow / tracker | weak | strong | medium | strong | weak | medium | weak |
| Collaborator / partner discovery | weak | weak | strong | strong | weak | medium | weak |
| Local application guidance | medium | medium | weak | weak | medium | weak | medium |

## What QAZ.FUND has not yet captured well

### P0: highest-value additions

1. Saved searches, watchlists and alerts

Why it matters:

- Every benchmark leader lets users save search intent, not just browse.
- For `qaz.fund`, this should become the core retention loop.

Recommended scope:

- save query + filters + language + regions + themes;
- email and Telegram alerts;
- weekly digest and immediate "new high-fit item" alerts;
- shareable watchlist URLs.

2. Funder pages

Why it matters:

- Right now we are opportunity-centric.
- Top systems also let users learn a funder and decide whether it is worth
  building toward that source.

Recommended scope:

- `/funder/{slug}` page;
- current open opportunities from that source;
- historical items from that funder;
- typical themes, geography, applicant types, amount bands, deadline patterns;
- plain-language "what this funder usually supports".

3. Historical awards and peer funding routes

Why it matters:

- Candid, GrantForward, Pivot-RP and Devex all make historical outcomes part of
  the discovery process.
- This is one of the biggest current product gaps.

Recommended scope:

- awarded / closed / archived records visible as a separate mode;
- "organizations like yours also received from...";
- "similar projects in Kazakhstan / Central Asia were funded by...";
- per-funder recent award examples where legally and technically available.

4. Funding lifecycle model

Why it matters:

- Devex proves users care about what is coming, not only what is open.
- For public procurement and MDB funding this is especially important.

Recommended scope:

- `forecast`, `pipeline`, `open`, `closed`, `awarded` states;
- filter and badge model in UI;
- early-stage signals from project pipelines and donor program pages.

5. Collections instead of one flat feed

Why it matters:

- Candid's collections and Instrumentl's projects reduce cognitive overload.
- `qaz.fund` needs lightweight organization, even before full accounts/workflow.

Recommended scope:

- curated collections like `AI for schools`, `Agrotech`, `NGO/media`,
  `State support for SMEs`, `Multilateral procurement`;
- user-saved collections later;
- shareable collection pages for teams.

### P1: very good additions after P0

6. Applicant or project profile matching

Best benchmark analogs:

- Instrumentl projects;
- GrantForward researcher profiles;
- Pivot-RP Funding Advisor.

Recommended scope:

- organization type;
- geography;
- project stage;
- sector;
- funding need;
- procurement readiness.

This would improve alerts, ranking and explanation quality.

7. Lightweight pipeline tracker

Best benchmark analog:

- Instrumentl Tracker.

Recommended scope:

- statuses like `watching`, `qualified`, `preparing`, `submitted`, `won`,
  `not a fit`;
- owner, notes, next step, due date;
- no need for a giant CRM in v1.

8. Trend and market intelligence layer

Best benchmark analogs:

- Devex analysis;
- Candid funding landscape;
- Pivot-RP strategic intelligence.

Recommended scope:

- top active funders this month;
- sectors heating up in Kazakhstan;
- average time-to-deadline by source type;
- open vs forecast vs awarded distribution.

9. Partner / implementer intelligence

Best benchmark analogs:

- Devex shortlist and awards;
- GrantForward collaborator discovery;
- Pivot-RP collaborator discovery.

Recommended scope:

- organizations frequently winning MDB / UN / donor work in Kazakhstan;
- recurring implementers and local partners;
- shortlist and award trail where public.

10. Better operator-grade summaries

Best benchmark analog:

- GrantStation narrative profiles.

Recommended scope:

- "why this matters";
- "who exactly can apply";
- "what is missing or uncertain";
- "what documents are usually needed";
- "what to verify on the source page".

### Later, not now

11. AI proposal drafting inside the platform

World leaders are adding it, but it should not be a near-term priority.

Reason:

- our current bottleneck is still discovery quality, structure and monitoring.
- proposal generation before strong funder history, saved pipeline and guidance
  will add surface area before the core product compounds.

12. Heavy institution workflow

Examples:

- deep SSO;
- branded institutional newsletters;
- multi-admin research office controls.

Useful later for enterprise or university sales, but not a near-term public-site
priority.

## Recommended product roadmap for QAZ.FUND

### Next 3 product passes

#### Pass 1

- saved searches;
- Telegram and email alerts;
- collections;
- `forecast/open/closed/awarded` lifecycle model.

#### Pass 2

- funder pages;
- historical award pages;
- peer-funding and "similar recipients" logic;
- trend cards and funder statistics.

#### Pass 3

- applicant/project profile matching;
- lightweight tracker;
- partner and implementer intelligence;
- richer summary templates.

## What not to copy blindly

- Instrumentl's full grant-work CRM.
- Pivot-RP's institution-heavy admin surface.
- broad U.S.-specific 990 mechanics as a product centerpiece.
- oversized academic collaborator graph before we have a strong Kazakhstan
  organization graph.

## My recommendation

If we want `qaz.fund` to feel clearly more serious than "a nice catalog", the
single best sequence is:

1. saved intent;
2. lifecycle depth;
3. funder intelligence;
4. historical outcomes;
5. lightweight workflow.

That would move the product from "public opportunity board" toward "funding
operating system for Kazakhstan teams" without overbuilding the wrong layers too
early.
