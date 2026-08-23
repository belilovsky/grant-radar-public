# EdPol editorial rewrite — QAZ.FUND — 2026-08-23

## Identity

- Project and public domain: QAZ.FUND — `https://qaz.fund`
- Canonical checkout: `/Users/belilovsky/Documents/Codex/2026-05-21/grant-radar-public`
- Base revision: `9906676dd9355e9079987ccc36db2d88e7d8808e`; final audited state is a
  **dirty local candidate** containing the narrow absence-label rewrite. It has
  not been committed or deployed under this audit scope.
- Audit timestamp and timezone: 2026-08-23, Asia/Almaty.
- Mode: rewrite; lifecycle surface: local public-candidate fixture.
- Content owner: QAZ.FUND product team. Reviewer: Codex under the authorised
  EdPol rewrite scope.

## Authority

- Editorial language policy: `1.1.0`,
  `https://edpol.pro/rules/editorial-language-policy.json`, SHA-256
  `3d2c66102da7f3066b6609581067a838035d7813a73366587a1437f55d2bdb76`.
- Typography policy: `1.1.1`, `https://edpol.pro/rules/typography-policy.json`,
  SHA-256 `7d0324ba83f5c5d7ec704963637fd7b1e4c10dcfe3371e48ea929d3fdf81db2d`.
- Anti-generative signals: `edpol-anti-generative-signals-v1`, SHA-256
  `aec821a7bf57c33f3ad3bed7f10eba00fcebb67cf5d4babbfc399df9de05d33d`.
- AI-origin policy was not invoked: wording style is not evidence of authorship.

## Enumerated scope

| Unit | Route or source | Locale | State / viewport | Included |
|---|---|---|---|---|
| `copy-01` | Dashboard and catalogue SSR copy | RU/KK/EN | loaded | yes |
| `copy-02` | Opportunity, preparation, funder, media, status, insight and embed SSR copy | RU/KK/EN | loaded, empty and degraded strings | yes |
| `copy-03` | Public information, comparison, QPost and notification boundary copy | RU/KK/EN | public / contract states | yes |
| `ui-01` | `/?lang=ru` | RU | 1440×960, 393×852 | yes |
| `ui-02` | `/?lang=kk`, `/?lang=en` | KK/EN | 393/768/1440/320/1920 px | yes |

## Automated candidate scan

- Scan: `edpol-editorial-candidate-scan-v2`; 16 files considered, scanned and
  skipped: 16 / 16 / 0. Excerpts were redacted.
- Exact publication gate: `--no-heuristics --fail-on-policy-match` exited 0.
- The final exact scan reports 79 `unknown-value-placeholder` structural
  candidates. They occur only where the UI explicitly identifies missing source
  data as unpublished; none is an exact policy match or a claim of AI origin.

## Confirmed findings and closure

| ID | Unit | Locale | Class | Severity | Finding and replacement | Owner | Status |
|---|---|---|---|---|---|---|---|
| `EDPOL-001` | dashboard quick filters | RU/KK/EN | editorial-risk | rewrite | Generic labels implied checks or support while activating a specific filter. They now name the actual action: startups, name search, deadline, Kazakhstan programs and tenders. | product | rewritten + verified |
| `EDPOL-002` | dashboard heading | RU/KK/EN | editorial-risk | rewrite | Generic “where to start” framing obscured the job. It now asks the visitor to refine the task. | product | rewritten + verified |
| `EDPOL-003` | topic filter | RU/KK/EN | structural-candidate | review | Topic is a real taxonomy filter, not a decorative label. It is now disclosed on demand, preserving its accessible group name. | product | verified |
| `EDPOL-004` | absent amount and deadline labels | RU/KK/EN | editorial-risk | rewrite | Ambiguous “not stated” labels could obscure that the source field is absent. They now say that the amount or deadline is not published. QPost keeps those factual labels in its review card but omits them from the short Threads fact block. | product | rewritten + focused tests |

## Manual verification

- Factual grounding: no deadline, amount, eligibility, source or success claim
  was added. Every changed label maps to the existing `data-hero-*` action.
- RU/KK/EN parity: the three locale dictionaries were updated together; 54
  focused public/media/QPost/comparison/preparation/localization tests pass
  after the final rewrite; the full current-candidate suite also passes
  660/660.
- Typography: the repository typography gate passes; URLs, source titles, IDs,
  legal text and machine contract values were not rewritten.
- Desktop and mobile: local browser evidence records no console errors,
  critical/serious axe findings or horizontal overflow for the home surface at
  RU/KK/EN × 393/768/1440/320/1920 (15 checks).
- The browser fixture is production-like only for layout/content behaviour; it
  is not proof that the local candidate is deployed.

## Verdict

`pass` for the enumerated local candidate.

No confirmed policy-exact finding remains in the audited public-copy scope.
Public runtime remains SHA `4d7e078f7bee69656b6b4d39644eb58288ede641`, so this
rewrite has no live-public acceptance claim.
