## Identity

- Project and public domain: QAZ.FUND — https://qaz.fund
- Canonical checkout: `/Users/belilovsky/Documents/Codex/2026-05-21/grant-radar-public` (audit worktree: `/tmp/qazfund-edpol-20260823`)
- Branch and source revision: detached `origin/main` at `71f756d085e18d088cf17b3da963006c93644cb1`
- Audit timestamp and timezone: 2026-08-23, Asia/Almaty
- Mode: rewrite (local candidate only; deployment not authorized by this request)
- Lifecycle surface: deployed public inspected; edits are a local candidate
- Content owner: QAZ.FUND product team
- Reviewer or decision owner: Codex under user-authorized EdPol rewrite

## Authority

- Editorial language policy: `1.1.0`, https://edpol.pro/rules/editorial-language-policy.json, SHA-256 `3d2c66102da7f3066b6609581067a838035d7813a73366587a1437f55d2bdb76`
- Typography policy: https://edpol.pro/rules/typography-policy.json, SHA-256 `7d0324ba83f5c5d7ec704963637fd7b1e4c10dcfe3371e48ea929d3fdf81db2d`
- Anti-generative signal catalogue: `edpol-anti-generative-signals-v1`, skill reference, SHA-256 `aec821a7bf57c33f3ad3bed7f10eba00fcebb67cf5d4babbfc399df9de05d33d`
- AI-origin policy and evidence schema: out of scope. This audit makes no authorship claim.

## Enumerated scope

| Unit | Route or file | Locale | State or viewport | Included | Reason if excluded |
|---|---|---|---|---|---|
| `unit-001` | `api/**/*.py` public SSR copy | RU/KK/EN | normal, empty and fallback strings | yes | — |
| `unit-002` | `/` | RU | 1440×960 and 393×852 | yes | deployed runtime inspected |
| `unit-003` | `/?lang=kk` | KK | responsive route | yes | deployed runtime inspected |
| `unit-004` | `/?lang=en` | EN | responsive route | yes | deployed runtime inspected |
| `unit-005` | binary branding assets | all | n/a | no | no editorial text |

## Automated candidate scan

- Report schema and gate state: `edpol-editorial-candidate-scan-v2`; exact scan after rewrite has no publishable exact match outside `api/edpol_language.py`, which is the policy matcher catalogue, not rendered product copy.
- Files considered / scanned / skipped: 51 / 46 / 5. Skipped: favicon and ornamental image binaries; reviewed as non-text.
- Before review: 78 exact-policy, 136 structural candidates, 1 editorial-risk candidate. Most structural matches are explicit `unknown`/`not published` states or source-code identifiers and require contextual review; they are not silently normalized.
- Excerpt mode: raw, retained only in the repository-local audit scan outputs.

## Confirmed findings

| ID | Unit | Locale | Lifecycle | Exact excerpt | Class | Severity | Rule or rationale | Evidence dependency | Proposed replacement | Owner | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `EDPOL-001` | `api/qpost_feed.py` | RU/KK/EN | public export | generic instruction to check eligibility at the official page | policy-exact | block | `empty-source-disclaimer`: instruction concealed that criteria were absent | existing card data | state that criteria are not published in available data | product | rewritten |
| `EDPOL-002` | `api/application_prep_page.py` | KK/EN | public preparation state | `Бұл бағдарлама`; `This programme` | policy-exact | rewrite | generic programme framing in closed/deadline notices | none | name the acceptance/deadline state directly | product | rewritten |
| `EDPOL-003` | `api/dashboard_copy.py` | KK/EN | public dashboard/detail | generic `this opportunity` and `бұл мүмкіндік` labels | policy-exact | rewrite | referent can be the selected or saved card | none | use `selected/saved card` and direct card wording | product | rewritten |

## Manual verification

- Factual grounding and source boundary: replacements do not add criteria, deadlines, amounts or certainty; they expose missing published data plainly.
- RU/KK/EN semantic parity: `EDPOL-001` has equivalent “not published in available data” states in all three locales; other rewrites remove generic framing without changing workflow meaning.
- Typography and protected technical contexts: source URLs, IDs, legal policy titles, quotations and machine states were not rewritten.
- Desktop routes and states: deployed RU home captured at 1440×960: `output/playwright/edpol-audit-home-ru-1440.png`.
- Mobile routes and states: deployed homes captured at 393×852 in RU (`output/playwright/edpol-audit-home-ru-393.png`), KK (`output/playwright/edpol-audit-home-kk-393.png`) and EN (`output/playwright/edpol-audit-home-en-393.png`); header, filter controls and bottom navigation remain visible and tappable.
- Accessibility or truncation observations: no text clipping observed in the captured RU mobile surface. Public runtime recorded console errors and loading skeleton during capture; this is a runtime observation, not evidence that the local copy edits are deployed.
- Native tests/content/build gates: 34 focused localization, dashboard and QPost tests passed. Exact EdPol scan rerun after rewrite; remaining exact matches are confined to `api/edpol_language.py`, the non-rendered EdPol matcher catalogue.

## Verdict

- Verdict: `pass` for the audited local public-copy candidate.
- Remaining exceptions and approver: structural unknown-value candidates are retained where the product honestly signals missing published data; no exception is used to mask a policy-exact rendered phrase.
- Local candidate evidence: focused tests passed; policy scan after rewrite has no rendered exact-policy candidate.
- Deployed runtime identity: not updated by this editorial request.
- Public browser evidence: current deployed RU home captured for desktop and mobile; KK/EN mobile captures confirm localized public surfaces. The local rewrites require a separately authorized release before public acceptance.
