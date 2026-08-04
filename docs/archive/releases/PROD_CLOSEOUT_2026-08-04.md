# QAZ.FUND production closeout – 2026-08-04

## Release

- Canonical checkout: `/Users/belilovsky/Documents/Codex/2026-05-21/grant-radar-public`
- Branch: `codex/qaz-fund-reuse-boundary-20260728`
- Application revision audited by the checks below: `a698bb073d8388986eb9368c29ab91fb802f26f3`
- Runtime: `root@148.230.117.131:/opt/grant-radar`
- Public surface: `https://qaz.fund`
- The final deployed revision is always the exact value returned by
  `/.well-known/release.json`; this closeout is itself included in that
  release, so the document intentionally does not duplicate its own commit
  hash.

## Scope

- Completed the curated Kazakh interface for the public insights page.
- Added Kazakh section headings to opportunity pages without rewriting source
  descriptions or excerpts.
- Made source-language fallback explicit in the dashboard, opportunity and
  funder pages; it is not presented as an approved translation.
- Documented the language-surface and translation holdout boundary.

## Verification

- `./.venv/bin/python -m pytest -q`: 471 passed.
- `make lint`: Black, isort, flake8, mypy and vulture passed.
- `git diff --check`: passed; working tree clean and branch matches origin.
- Production smoke: passed; 26 sources, 393 open relevant opportunities, 0
  stale sources, 5 digest items, all discovery/AVDS4/QazStack markers present.
- Public content audit: passed with no issues, including no missing summaries,
  deadlines, detail statuses, or forbidden text.
- RU and EN NLP audits: 150 records per locale, zero issues.
- `/ready`: database backend healthy, 1280 records.
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
