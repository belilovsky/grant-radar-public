# QAZ.FUND production closeout - 2026-07-14

## Scope

Dense visual and product-experience pass across the public catalog, opportunity
detail, funder profile, source status and operator shell. The release changes
presentation and rendered content hierarchy without changing source contracts,
database schema or ingestion behavior.

## Release

- Release PR: `#1` (`codex/qazfund-visual-density-20260714`).
- Deployed code revision: `1220545b280098ceb4b406c1f01c799e9c722178`.
- Public URL: `https://qaz.fund/`.
- Runtime: API, PostgreSQL and Redis healthy; worker running.

## Visual verification

Browser checks covered the Russian and English home pages, a live opportunity,
the Astana Hub funder profile, public source status, operator shell and branded
404. Desktop used `1440 x 1000`; mobile used `390 x 844`.

- every checked page has one visible `h1`;
- horizontal overflow is zero on every checked viewport;
- desktop headings do not exceed 48 px;
- mobile headings stay within 24-28 px;
- mobile filters start collapsed and expose the catalog before advanced fields;
- the only browser console error was the expected response for the deliberate
  404 route check.

## Quality gates

- Full tests: `401 passed`.
- Black, isort, Flake8 and mypy: passed.
- GitHub Actions `Verify` run `#30`: passed.
- Production smoke: `status=ok`.
- Indexed records: `818`.
- Relevant open opportunities: `149`.
- Enabled sources: `26`.
- Stale sources: `0`.
- Sources without a freshness timestamp: `1`.
- Content audit: no issues, empty sources or missing public summaries.
- RU NLP audit: 200 records checked, 0 issues.
- EN NLP audit: 200 records checked, 0 issues.

## Remaining non-blocker

One source does not expose a reliable freshness timestamp. It remains visible in
the public status page as unknown rather than being presented as fresh. This is
an honest data-quality state and does not block the release.
