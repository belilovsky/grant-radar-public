# QAZ.FUND Platform integration closeout — 2026-08-25

This is a delta review of the open rows from the 2026-08-23 Platform audit. It
does not repeat unchanged infrastructure, security, delivery, or route checks.
Source, candidate, Platform registry, runtime, and public evidence remain
separate.

## Identity

- Product/runtime ID: `qaz-fund`, as published by
  `/.well-known/qdev-ecosystem.json` and the root `qdev-project.json`.
- Stable Platform catalog key: `grant-radar`. It remains an explicit
  compatibility alias because Webmaster, catalog URLs, generated contracts,
  and historical runtime evidence already use it.
- Canonical repository: `https://github.com/belilovsky/grant-radar-public`,
  default branch `main`; public entrypoint: `https://qaz.fund`.

The alias is deliberate. A fleet-wide key rename is not required to describe
the product accurately and would break existing Platform consumers.

## Changed contract rows

| Capability | Decision | Current evidence |
| --- | --- | --- |
| Root project manifest | required / covered | `qdev-project.json` validates against `qdev-project-manifest-v1`; repository tests verify identity, routes, versions, capability modes, and local contract paths. |
| QazStack | required / covered | Runtime package and bilateral public contract remain pinned to 1.41.2 and source revision `986cfca3779f74c0f734ed174e7a28c944fd30f7`. |
| AVDS | required / covered | SSR adapter remains the runtime boundary; the canonical AVDS release and `@sgeo/ui-kit` contract are 4.7.0 at source revision `aa91d2ec56c64d56df3270b805f7d0d18ed84246`, verified 2026-08-25. |
| QazPipe / QazLake | optional / not activated | QAZ.FUND publishes a read-only pull source and provenance contract. It does not push directly to QazLake and no private dataset or shared ingestion activation is claimed. |
| QazCompute | optional / not activated | Product-local deterministic ranking and semantic service remain owned by QAZ.FUND. No remote QazCompute execution receipt is claimed. |
| QazGeo | not applicable | The public opportunity contract has no verified geometry; region labels are not promoted to coordinates. |
| Identity / notifications | not applicable / time-bounded exception | The product is anonymous and read-only; browser drafts and saved selections remain local, and there are no accounts, uploads, profiles, personal notifications, or submission endpoints. The root manifest records owner `QDev` and review expiry `2026-12-31` for the Platform `identity` gate. |

## Candidate evidence

- `make lint`: pass.
- `make ci-fast`: 669/669 tests pass; typography findings: 0.
- QazData integrity ledger: valid; the one partial source state remains visible
  rather than being promoted to success.
- KZ compliance bundle: valid, with no open legal question after all
  third-party analytics were removed.
- EdPol receipt: pass; 28/28 files scanned and five heuristic candidates
  context-reviewed as false positives.
- AVDS validators: anti-generative and visual-craft pass.
- Chromium acceptance: 119/119 route/viewport cells and 9/9 targeted checks
  pass at 320, 390, 768, 1024, 1440, 1920, and 2560 px.

## Promotion boundary

The product commit is promoted first so Platform can bind an immutable SHA.
The Platform source card, public catalog projection, surface contract, and
tracker-free Webmaster declaration are then regenerated and released from the
canonical Platform repository. Final closure requires the exact product SHA to
match GitHub CI, `/.well-known/release.json`, `/ready`, the worker heartbeat,
the public browser pass, and the deployed Platform registry record.

## Verdict

The product-side Platform contract is complete and contains no fabricated
activation. Public registry and runtime/public proof are release-phase checks,
not missing product declarations.
