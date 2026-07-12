# Source expansion review - 2026-07-13

## Shipped adapters

| Adapter | Official surface | Runtime rule | Live check on 2026-07-13 |
|---|---|---|---|
| `world_bank_procurement_ca` | World Bank Procurement Notices API | Central Asia country filter; active notice types; future deadlines; recent general notices only | 24 current notices |
| `eu_funding_tenders_ca` | EU Funding & Tenders Search API | Active English calls matched against Kazakhstan and Central Asia terms; deduplicated by topic ID | 7 current calls, all marked `eligibility_check_required` |
| `canada_cfli_ca` | Canada Fund for Local Initiatives country table | Emit only when an official Central Asia row is `Open` and its deadline is current | 0 current calls because the annual round is closed |

The source registry now contains 26 enabled adapters. A registered source may
legitimately contribute zero current opportunities; coverage and freshness are
reported separately from item count.

## Reviewed but not enabled

| Candidate | Decision | Exact blocker / next artifact |
|---|---|---|
| UNGM notices | Gated | Public API requires OAuth and the reuse terms need an approved integration path. Add only with credentials, permitted field storage and mocked contract tests. |
| UNDP country announcements beyond procurement | Gated | Direct automated requests currently return `403`. A future adapter needs a stable official feed or explicit access, not a browser-scraping workaround. |
| KOICA procurement and country programs | Gated | Current official listings are dynamic and primarily Korean-language. Require a stable item URL, deadline parser and English/Russian normalization fixture. |
| GIZ, UNOPS and UNHCR procurement | Gated | Much of the actionable inventory is routed through UNGM. Prefer the approved UNGM API path instead of parallel scraping. |
| UN Partner Portal | Gated | Requires account/session workflow. Integrate only through an authorized API/export with documented storage terms. |
| TED | Deferred | Official API is available, but broad EU-buyer procurement adds high volume with weak Central Asia applicant value. Enable only with a demonstrated regional eligibility filter. |
| NIH | Not duplicated | Relevant federal notices are already available through Grants.gov; a second adapter would create duplicate inventory without better regional evidence. |

## Admission contract for future sources

Every additional adapter must have:

1. an official, stable listing or API and permitted automated access;
2. item-level official URLs, titles and current deadline/status evidence;
3. explicit Kazakhstan/Central Asia eligibility or an honest verification flag;
4. deterministic deduplication and expiry behavior;
5. mocked parser tests plus a live count-only smoke test;
6. source-registry, content-coverage and production-smoke updates;
7. no fabricated opportunity when the official source has no open call.
