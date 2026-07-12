# QAZ.FUND final launch plan – 2026-07-12

## Goal

Bring QAZ.FUND to a public-demo-ready state without overloading the working
interface. The product should stay catalog-first, readable, and operational:
users must quickly find relevant opportunities, inspect a source, and understand
why the item is shown.

## Current state

- Public site: `https://qaz.fund/`
- Runtime: database-backed API, worker, Redis and Postgres on VPS.
- Current production smoke baseline:
  - `health_items`: 770
  - `coverage_sources`: 23
  - `coverage_relevant_open_items`: 121
  - public discovery surfaces: `/llms.txt`, `/site-discovery.json`, `/docs`
- UI direction: compact working tool, not a marketing landing. The catalog and
  source trust controls stay first-class; discovery blocks remain secondary.

## Completed launch blockers

| Area | Status | Notes |
|---|---|---|
| First-screen workflow | Done | Catalog-first IA, compact hero, source/data status visible. |
| Visual quality | Done | Calmer palette, cleaner cards, restored useful panels, reduced decorative borders. |
| Loading states | Done | Sources and async grids now show explicit loading states before fallback messages. |
| Mobile/Fold usability | Done | Checked 390px and fold-like widths for horizontal overflow. |
| Data relevance | Done | Low-confidence and out-of-region sources are filtered or pushed out of default feed. |
| QazStack bridge | Done | Shared opportunity/geofit primitives vendored through a deploy-safe snapshot. |
| AI/readability surfaces | Done | `llms.txt`, sitemap, OpenAPI, source coverage and canonical public pages are exposed. |
| Public-safe repo hygiene | Done | Operator-only details moved out of public-facing docs/scripts. |

## Final non-blockers

These are not release blockers, but they are the next highest-value cleanup
items after public launch.

| Priority | Item | Action |
|---|---|---|
| P1 | Source freshness variance | Monitor sources that occasionally fetch 0 records and add source-specific fallbacks only when repeated. |
| P1 | Opportunity Desk bridge depth | Keep main/category RSS feeds enabled; review first production refresh after deploy. |
| P1 | Long official text on detail pages | Add collapsible official-text sections if users report excessive scrolling. |
| P2 | Operator workflow | Add saved collections/account state only after real operator feedback. |
| P2 | Source confidence explanation | Add a short tooltip or help row for exact/strong/basic relevance labels if users ask. |
| P2 | API docs localization | Keep Swagger developer-facing; localize only if API becomes a public product surface. |

## Safe final pass order

1. Data-source pass:
   - run parser smoke for all active sources;
   - fix repeated source failures only when reproducible;
   - avoid broad scraping rewrites.
2. UI pass:
   - inspect home, opportunity page, funder page and docs at desktop, tablet and 390px;
   - fix only overflow, unreadable contrast, bad truncation and repetitive blocks.
3. Content pass:
   - remove placeholders and generic summaries from public cards;
   - keep official source excerpts intact but avoid duplicating titles.
4. Contract pass:
   - run lint, full pytest, production smoke and live route checks;
   - deploy only from a clean tree.
5. Closeout:
   - update this plan or production closeout with deployed commit and live counts.

## Acceptance

QAZ.FUND can be considered public-demo-ready when:

- `/`, `/docs`, `/llms.txt`, `/site-discovery.json`, representative
  `/opportunity/*` and `/funder/*` routes return 200/expected redirects;
- the home page loads catalog data without permanent loading or empty states;
- mobile width has no horizontal overflow;
- tests and lint pass locally;
- production smoke reports non-zero source coverage and opportunities;
- production containers are healthy after deploy.
