# QAZ.FUND production closeout – 2026-08-03

## Release

- Canonical checkout: `/Users/belilovsky/Documents/Codex/2026-05-21/grant-radar-public`
- Branch: `codex/qaz-fund-reuse-boundary-20260728`
- Revision: `1f4d88a42aa2eeb0c485e664d1420468749c1cd9`
- Runtime: `root@148.230.117.131:/opt/grant-radar`
- Public surface: `https://qaz.fund`
- Release time: `2026-08-03T07:05:29Z`

## What changed

- Restored the crawler-safe raster social preview at `/og-image.png`.
- Kept `/og-image.svg` available for existing integrations.
- Switched public Open Graph and Twitter image metadata to the PNG preview.
- Added GET/HEAD contract coverage and documented the public route.

## Verification

- `tests/test_api_repository.py -k 'og_image_route or opportunity_page_prefers_public_base_url or funder_page or root_renders'`: 6 passed.
- `python -m compileall -q api`: passed.
- Production smoke with database backend and current thresholds: passed.
- `/.well-known/release.json`: reports the exact revision above and remained stable after deployment.
- `/ready`: `status=ok`, `backend=database`.
- `/og-image.png`: `200 image/png`, valid PNG signature, GET and HEAD verified.
- Homepage and opportunity detail pages expose `og:image=https://qaz.fund/og-image.png`.

## Remaining data-quality work

The live content audit is intentionally recorded as `needs_attention`, not hidden:

- one source (`unicef_kazakhstan`) is stale;
- 20 records have no explicit deadline policy;
- public tag labels still need broader RU/EN localization;
- one source URL is a root-level tender index and should be narrowed to the exact announcement when possible.

These are content/source-review tasks, not deployment failures. Do not lower the
production smoke thresholds to silence them.

## Rollback

Redeploy the previous verified revision from the canonical checkout using the
same deployment script and target. The server keeps the release marker in
`/opt/grant-radar/.deployed-revision`; database migrations were unchanged in
this release.
