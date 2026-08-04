# QAZ.FUND production closeout – 2026-08-04

## Release

- Canonical checkout: `/Users/belilovsky/Documents/Codex/2026-05-21/grant-radar-public`
- Branch: `codex/qaz-fund-reuse-boundary-20260728`
- The application and integration-contract revisions are audited by the
  checks below; the final deployed revision is always the exact value returned
  by `/.well-known/release.json`.
- Runtime: `root@148.230.117.131:/opt/grant-radar`
- Public surface: `https://qaz.fund`
- This closeout is itself included in the release, so the document intentionally
  does not duplicate its own commit hash.

## Scope

- Completed the curated Kazakh interface for the public insights page.
- Added Kazakh section headings to opportunity pages without rewriting source
  descriptions or excerpts.
- Made source-language fallback explicit in the dashboard, opportunity and
  funder pages; it is not presented as an approved translation.
- Refreshed the QazStack contract evidence and made the checked-in contract
  fail tests when it drifts from the runtime contract.
- Documented the language-surface and translation holdout boundary.
- Added the public `provenance.v1` profile to opportunity JSON, compact
  dashboard payloads, NDJSON and detail responses. It keeps parser observation,
  explicit verification, source language and field confidence separate.
- Added the benchmark and upgrade plan for the next discovery, workflow,
  funder-graph and visualization slices.
- Added mobile-friendly system sharing for filtered catalog links and individual
  opportunity cards, with clipboard and prompt fallbacks.
- Added the reproducible `insights.v1` read model at `/insights.json`, wired it
  into site discovery and `llms.txt`, and added an AVDS4 upcoming-deadlines
  block to the public insights page.
- Gave each inline chart a meaningful accessible label and named the relevance
  block consistently in all three public languages.
- Corrected the wide-screen analytics grid so the shorter quality card no longer
  stretches to the height of the deadline list and creates an empty panel.

## Verification

- `PYTHONPATH=. .venv/bin/pytest -q`: 476 passed.
- `make lint`: Black, isort, flake8, mypy and vulture passed.
- `git diff --check`: passed; working tree clean and branch matches origin.
- Production smoke: passed; 26 sources, 393 open relevant opportunities, 0
  stale sources, 5 digest items, all discovery/AVDS4/QazStack markers present.
- Public content audit: passed with no issues, including no missing summaries,
  deadlines, detail statuses, or forbidden text.
- RU and EN NLP audits: 150 records per locale, zero issues.
- `/ready`: database backend healthy, 1280 records.
- Translation readiness remains intentionally held: `kk_content_coverage_rate`
  is `0.0`; source-language metadata is present for 45 of 616 records, while
  reviewer, quality and approval metadata are not present.
- Public provenance sample verified on `/opportunities`: `schema_version`
  `provenance.v1`, `evidence_state=sourced`, separate `observed_at` and
  `last_verified_at` fields.
- `/insights.json?lang=ru` verified with `schema_version=insights.v1`, explicit
  deadline buckets, an upcoming-card list and links back to the human page;
  `/insights` exposes the same values with no horizontal overflow at 390px and
  2560px viewports.
- Browser proof for `/insights?lang=kk` and a live opportunity detail:
  `lang=kk`, Kazakh headings, transparent source fallback, and no horizontal
  overflow at 390px and 2560px viewports.

## Translation boundary

The public translation-readiness guard remains `decision=hold`:
`kk_content_coverage_rate=0.0`, with no reviewer, quality-score or approval
metadata. Dynamic opportunity and source descriptions therefore remain in their
published source language until a native-language editorial pass approves
`raw.i18n.kk`. Automatic translation publishing and remote writes remain
disabled.

## Rollback

Redeploy the previous verified revision from the canonical checkout with the
same deployment script and target. The server keeps the deployed revision in
`/opt/grant-radar/.deployed-revision`; database migrations were unchanged.
