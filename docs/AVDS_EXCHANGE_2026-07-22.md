# AV DS exchange: QAZ.FUND

Date: 2026-07-22

## Result

QAZ.FUND keeps its FastAPI/SSR runtime and adopts the platform contracts that
are safe across that boundary. The dashboard now declares the three shared
catalog patterns in both its markup and `/.well-known/avds-ui-contract.json`:

| QAZ.FUND surface | AV DS contract | Ownership boundary |
| --- | --- | --- |
| Active result chips and result count | `FilterStateSummary` | Query parsing, routing and filter behavior remain local. |
| Source rows, freshness and coverage | `EvidenceSummary` | QAZ.FUND/QazStack evidence state remains the source of truth. |
| Opportunity priority, fit and deadline cues | `DecisionSummary` | AV DS presents reasons; QAZ.FUND owns relevance, priority and eligibility limits. |

All three contracts are runtime-neutral. The public Python image does not
download unpublished JavaScript or React packages during build or deployment.

## AV DS primitives adopted or retained

- Semantic color, spacing, typography, focus, motion and density tokens remain
  in the local AV DS adapter.
- Existing shell, field, button, badge, panel, metric, source-card and status
  families remain mapped to AV DS 4 markers.
- The new catalog contracts make the existing filter, evidence and result-card
  blocks explicit platform consumers rather than undocumented local shapes.

## Not imported

| AV platform area | Decision | Reason |
| --- | --- | --- |
| `@av/search` | Not imported | Its current in-memory engine cannot replace database queries, pagination and QazStack-backed normalization. |
| `@av/jobs` | Not imported | A generic scheduler is not a replacement for persistent run records and production safety controls. |
| `@av/forms`, `@av/notify`, `@av/auth-kit` | Not imported | The public catalog has no user submission or notification workflow requiring them. |
| `@av/public-site` renderer | Not imported | QAZ.FUND already has an audited FastAPI/SSR, SEO and sitemap surface. |
| `@av/telemetry`, `@av/enrich` | Not imported | No production-equivalent transport or enrichment contract is available yet. |

## Upstream contribution

AV DS receives the reusable parts of QAZ.FUND, not its grant-specific policy:

- public evidence state with source, freshness and limitation;
- compact representation of an active filtered query;
- explainable result summary with reasons and limitation.

Scoring weights, Kazakhstan geo-fit rules, deadline policy, application
eligibility and source-specific parsing stay in QAZ.FUND. They are business
logic, not design-system primitives.

## Verification boundary

The code contract is covered by QAZ.FUND API tests and AV DS TypeScript checks.
Production proof still requires the normal QAZ.FUND release gate after merge:
the public `/.well-known/avds-ui-contract.json`, dashboard HTML and live smoke
must report the same three adopted patterns.
