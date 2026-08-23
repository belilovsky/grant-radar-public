# QAZ.FUND — Qdev Platform integration audit

Date: 2026-08-23  
Scope: this repository only (`qaz-fund`). No Platform registry, adjacent product,
VPS, deployment, database, or public-runtime mutation was performed.

## Verdict after remediation: blocked

The product has a strong, locally verified integration boundary, but it is not
eligible for the Platform **ready** status. The repository has no required
`qdev-project.json`, so there is no project-governance declaration to reconcile
with the authoritative Platform catalogue. Fresh public/runtime evidence was
also deliberately not collected: the production VPS is under an active
infrastructure pause and is outside this audit's safe execution scope.

This is a fail-closed verdict. It does not mean that QAZ.FUND is unavailable;
it means that Platform acceptance cannot be honestly asserted from this
repository alone.

## Coverage

| Measure | Result |
| --- | --- |
| Applicable Platform dimensions | 12 |
| Locally source-verified after remediation | 10 / 12 (83.3%) |
| Documented but without fresh runtime/platform proof | 1 / 12 (8.3%) |
| Missing required governance evidence | 1 / 12 (8.3%) |
| Fresh cross-system Platform/runtime proofs collected | 0 / 12 |

`Locally source-verified` means executable code, pinned contract and/or tests
were checked in this worktree. It is intentionally not presented as a live
Platform or public-production proof.

## Evidence matrix

| Dimension | Applicability | Status | Project evidence | Acceptance evidence still required |
| --- | --- | --- | --- | --- |
| Project declaration and Platform catalogue | Required | **missing** | No `qdev-project.json` exists in the repository. | Authoritative project declaration plus matching Platform catalogue record. |
| QazStack | Required | locally verified | `qazstack-reuse.json`, `docs/qazstack/consumer-contract.json`, checksum-pinned `qazstack` 1.41.2 wheel, strict contract code and tests. | Fresh public consumer contract and Platform registry reconciliation. |
| AV DS | Required | locally verified | `api/integration_versions.py` pins 4.7.0; `api/ecosystem.py` publishes the SSR boundary; AV DS tests and component markers are covered. | Fresh endpoint/browser proof against the declared release contract. |
| QazPipe | Applicable producer | locally verified | Read-only pull contract at `/.well-known/qazpipe-source.json`, NDJSON export, checkpoint/idempotency/provenance boundaries and route tests. | Consumer-side handshake or an explicit approved inactive record in Platform. |
| QazLake | Applicable, activation-gated | locally verified | QazPipe contract forbids direct write and names schema, retention, dry-run, idempotency and rollback gates. | Approved target schema, retention decision, dry-run artifact and named QazLake owner before activation. |
| QazCompute | Applicable local fallback | locally verified | Four deterministic public-safe envelopes, `decision_ready=false`, remote execution disabled, contract and unit tests. | Fixture parity and authorised private server-side wiring before remote execution. |
| QazGeo | Applicable but deferred | locally verified | No inferred geometry; ecosystem contract now names `product_owner=qaz-fund` and a review trigger. | Verified coordinates or authoritative geometry reference, then QazGeo validation before a map or geometry claim. |
| Identity | Applicable boundary | locally verified | Anonymous read-only contract; no accounts, profiles, cross-device sync, server subscriptions or enabled delivery. | Identity provider, recovery, consent, deletion and retention controls before activation. |
| Data and privacy | Required | locally verified | Browser-only application drafts; QazPipe excludes raw/operator/private fields; provenance is public-safe; notification contract has collection disabled. | Data-owner approval only if a new personal-data flow is proposed. |
| Routes and UI | Required | locally verified | Generated FastAPI route registry, RU/KK/EN language surface, GET/HEAD and operator boundaries; browser matrix is defined in CI. | Fresh browser/axe/console evidence from the accepted runtime. |
| CI and supply chain | Required | locally verified | PR/main/release workflow, pinned actions, `pip check`, audit, immutable image scan, CycloneDX SBOM and QDev artifact upload. | Green CI run tied to the accepted SHA and retained artifacts. |
| Release and runtime evidence | Required | documented, not freshly verified | Immutable release fields, deploy lock/capacity/backup/rollback gates, non-root image and release smoke checks are implemented and tested. | A release contract with exact SHA, digests, timestamps and `sourceDirty=false`, plus public smoke on the same SHA after the infrastructure pause ends. |

## Confirmed findings and remediation

| Finding before remediation | Change made | Closure evidence |
| --- | --- | --- |
| Four active documents still stated AV DS 4.6.0 while the executable contract uses 4.7.0. | Updated `ECOSYSTEM_INTEGRATION.md`, `AVDS_INTEGRATION.md`, `AVDS_EXCHANGE_2026-07-26.md` and `WORLD_BENCHMARK_2026-07-27.md`; corrected the `@av/patterns` revision in the exchange note. | `tests/test_platform_contract_docs.py` prevents those documents drifting from `api/integration_versions.py`. |
| `api/main.py` could not compile because an f-string expression contained an escaped quote. | Rewrote the API-documentation language-link composition without an invalid f-string expression. | `compileall`, API documentation route tests and the complete test suite pass. |
| `api/application_prep_page.py` was not Black-formatted, so `make lint` failed. | Applied Black to that one file. | `make lint` passes. |
| Deferred QazGeo had rationale but no project owner or explicit reconsideration condition. | Added `product_owner` and `review_trigger` to the executable ecosystem contract and matching documentation. | Contract test asserts both fields. |

No `qdev-project.json` was invented. The Platform Integration Audit requires
that declaration to come from the authoritative governance contract, not from
a product-local guess.

## Open links and closure plan

| Priority | Unclosed link | Owner | Concrete action | Proof that closes it |
| --- | --- | --- | --- | --- |
| P0 | Required project declaration / Platform catalogue presence | Qdev Platform catalogue owner | Supply the approved `qdev-project.json` contract and register or reconcile the QAZ.FUND catalogue entry. | Manifest validates; product id, owner, lifecycle, repository and public URLs agree with the authoritative catalogue. |
| P1 | Fresh runtime and release identity | QAZ.FUND release owner | After the infrastructure pause is formally lifted, run the existing guarded release/verification path; do not bypass its capacity, backup or rollback gates. | Public `/.well-known/release.json` shows accepted SHA, image/artifact digests, timestamps and `sourceDirty=false`; smoke and browser evidence reference that SHA. |
| P1 | Cross-system consumer acceptance | Qdev Platform integration owners | Reconcile the public QazStack, AV DS, QazPipe, QazLake and QazCompute contracts with their owner registries. | Dated registry/handshake records identify the same contract URLs and the approved integration states. |
| P2 | QazPipe → QazLake activation | QazPipe and QazLake owners | Keep producer mode until a target table, retention policy, dry run, idempotency proof and rollback are approved. | Approved handoff record and dry-run artifact; no direct QAZ.FUND write. |
| P2 | QazCompute remote execution | QazCompute owner with QAZ.FUND owner | Keep local deterministic profiles until fixtures prove parity and private server-side wiring is authorised. | Versioned fixtures, parity result and a runtime receipt; `decision_ready` remains false unless policy changes. |
| P2 | QazGeo activation | QAZ.FUND product owner and QazGeo owner | Re-open only when published records gain verified coordinates or authoritative geometry references. | QazGeo validation record and source-backed geometry fields; otherwise retain `deferred-no-geometry`. |

## Re-audit result

The post-remediation source inspection found no active 4.6.0 AV DS claim in
the corrected documentation, the Python package compiles, all local integration
and release-contract tests pass, and the full fast CI suite passes. The verdict
remains **blocked** solely because the required Platform declaration/catalogue
proof and fresh runtime proof are not available within this repository and
must not be fabricated.

## Commands and results

```text
make lint PYTHON=/Users/belilovsky/Documents/Codex/2026-05-21/grant-radar-public/.venv/bin/python
PASS: Black, isort, flake8, mypy (121 files), vulture

python -m pip check
PASS: No broken requirements found.

make ci-fast PYTHON=/Users/belilovsky/Documents/Codex/2026-05-21/grant-radar-public/.venv/bin/python
PASS: 654 passed in 13.43s; typography finding_count=0
```

The interpreter is the existing project virtual environment; the isolated audit
worktree did not receive a new environment or dependency installation.
