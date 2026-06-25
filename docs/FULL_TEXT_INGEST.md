# Full-text opportunity pages

## Goal

Grant Radar should let an operator evaluate grants, subsidies and state programs
inside our product without opening every fund website first. The source link
must remain available, but the dashboard should show a local, attributable,
sanitized detail snapshot whenever the source policy allows it.

## Product contract

- Each opportunity card can open a local detail view with source, deadline,
  eligibility, amount, application steps, contacts and extracted source text.
- The original source URL remains visible as attribution and as the canonical
  application route.
- If a page cannot be mirrored in full, store structured fields plus a short
  excerpt and explain that the operator should open the source for the official
  text.
- Russian/Kazakh/English text should be preserved as collected; machine
  translation can be a separate derived field, not a replacement for source text.
- Kazakhstan domestic support pages, subsidies, tax benefits and state-program
  routes are priority sources because operators need them during qualification.

## Storage contract

The first implementation uses `Opportunity.raw` to avoid a risky schema
migration. Use these keys consistently:

- `detail_text`: sanitized plain text collected from the canonical detail page.
- `detail_sections`: optional list of `{heading, text}` objects extracted from
  official page structure.
- `detail_html_sha256`: checksum of the sanitized source HTML before text
  extraction.
- `detail_fetched_at`: UTC ISO timestamp of the detail fetch.
- `detail_language`: detected or source-declared language code.
- `detail_fetch_status`: `ok`, `not_allowed`, `blocked`, `too_large`,
  `unsupported_media`, or `parse_error`.
- `detail_excerpt_only`: boolean marker for sources where full mirroring is not
  appropriate.
- `application_url`: direct apply URL when separate from `source_url`.

Current production behavior:

- `kazakhstan_domestic_support` attempts to store sanitized local snapshots for
  official Kazakhstan grant, subsidy, reimbursement and state-program pages.
- Russian official pages set `detail_language=ru`, so the Russian dashboard can
  show the extracted source text directly without waiting for machine
  translation.
- QazIndustry pages use a scoped TLS fallback for their missing intermediate
  certificate: the adapter appends the official GoGetSSL intermediate CA from
  the certificate AIA path to the certifi bundle and still verifies TLS.
- Numeric amounts are stored only when the source gives a stable currency value,
  for example KZT. MRP-based amounts remain in `amount_raw` until the current
  MRP value is normalized by a dedicated rule.
- `scripts.content_audit` verifies that domestic-support records have either a
  local detail snapshot or an explicit non-ok detail status.

If detail pages become a core workflow, promote the snapshot into a separate
table with `opportunity_id`, source URL, fetched timestamp, checksum, language,
status, sanitized text, sections and parser version.

## Fetching and safety

- Fetch detail pages only through source adapters or an allowlisted detail
  fetcher; do not crawl arbitrary links from public input.
- Respect robots, rate limits and source-specific usage rules.
- Enforce size and content-type limits before parsing.
- Strip scripts, styles, tracking pixels, inline event handlers and unsafe URLs.
- Normalize whitespace, preserve headings/lists/tables where useful, and avoid
  injecting source HTML into the dashboard.
- Keep fetch failures as metadata, not as public card text.

## Copyright and official-text policy

- Public official notices, procurement pages and government program descriptions
  can usually be represented more fully, with attribution and source link.
- Donor/fund websites should default to structured extraction and short excerpts
  unless their terms clearly allow fuller reproduction.
- Never present extracted text as our own wording; show source attribution and
  fetched timestamp near the detail content.

## UI requirements

- Add a compact detail drawer/page from the card, not another large dashboard
  section.
- Keep "Open source" as a secondary action; the primary reading path should be
  local when `detail_fetch_status=ok`.
- Show empty/error states for blocked, not allowed and parse-error snapshots.
- The detail view must be mobile friendly: no nested cards, no horizontal
  overflow, sticky action bar only if it does not fight browser scrolling.

## Test plan

- Unit tests for each detail extractor with mocked HTML/PDF responses.
- Sanitizer tests for scripts, inline handlers, unsafe links and very large
  pages.
- API tests that detail fields are returned only as sanitized text/sections.
- Browser smoke for mobile detail drawer/page, long headings and long URLs.
- Content audit checks for important Kazakhstan domestic records without either
  `detail_text` or an explicit non-ok `detail_fetch_status`.
