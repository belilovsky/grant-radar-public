# Platform integration audit + remediation — QAZ.FUND — 2026-08-23

## Scope, authority and cut-off

- Project/site: QAZ.FUND — `https://qaz.fund`.
- Canonical source authority:
  `/Users/belilovsky/Documents/Codex/2026-05-21/grant-radar-public`.
- Repository: `https://github.com/belilovsky/grant-radar-public.git`; default
  branch: `main`.
- Base SHA: `c3cb85629bb70342cbbd6f080933f513b5e62eb7`, six commits ahead of
  `origin/main`. The final audited candidate also contains uncommitted local
  remediation; it has no release SHA and must not be confused with the base.
- Runtime/public URL: `https://qaz.fund`. Evidence cut-off: 2026-08-23
  Asia/Almaty. No VPS, deployment, backup, restart, PR, commit or push was run.
- Fresh public observation: `/ready` returned 200; `/well-known/release.json`
  returned runtime SHA `4d7e078f7bee69656b6b4d39644eb58288ede641`,
  `sourceDirty=false` and image/artifact digests. It is a healthy **older
  runtime**, not evidence for the local candidate.

## Verdict and coverage

`blocked`

- Applicable connections: **15**; covered **0**, documented **7**, missing
  **1**, stale **2**, conflicting **3**, not_applicable **1**, unverifiable
  **1**.
- Two-sided current-candidate coverage: **0/15 = 0%**. `covered` requires a
  fresh source and runtime/registry observation of the same immutable SHA;
  local tests, fixtures, an old receipt and a public 200 do not qualify.
- `documented` means the product boundary is implemented and testable locally;
  `stale` means observed runtime evidence belongs to another SHA; `conflicting`
  means the observed parties disagree; `missing` means the source file is
  absent; `unverifiable` means the authoritative schema or external receipt is
  not accessible in scope; `not_applicable` is an explicit supported boundary.

## Root `qdev-project.json`

**Status: missing.** The pinned source is available and has no root-level
`qdev-project.json`; no `.well-known` response, documentation or catalogue
record was substituted. The canonical `qdev-project-manifest-v1` schema is not
publicly retrievable in this project-only scope: public Platform URLs return an
authenticated workspace, and the referenced Platform source repository is not
available anonymously. Therefore schema validation is **unverifiable** and a
manifest must not be guessed.

External owner: Qdev Platform catalogue owner. Required external change:
publish/provide the approved `qdev-project-manifest-v1` schema and add the
validated root manifest; reconcile the registry record at
`catalog/projects/grant-radar.md`. Closure proof: schema-validation output plus
a registry observation agreeing on `qaz-fund`, repository, owner, lifecycle,
public route and the accepted release SHA.

## Evidence matrix

| Connection / requirement | State | Product-side evidence | Other-side evidence and closure action |
|---|---|---|---|
| Root manifest | **missing** | Root file absent at base SHA and local candidate. | Platform catalogue owner supplies schema and approved manifest; validation output is closure proof. |
| Identity/catalogue | **conflicting** | `project_id=qaz-fund`, repo and production route are consistent in executable contracts. | Public `https://avds.digital/platform/ecosystem.generated.json` (generated 2026-08-20) records `id=grant-radar`, `source_path=catalog/projects/grant-radar.md`, QazStack 1.35 and AV DS 4.6. Registry owner must update it to the approved manifest. |
| Release identity | **conflicting** | Candidate is `c3cb856…` plus uncommitted fixes. | Public release is `4d7e078…`; guarded immutable release and matching public receipt are required. |
| QazStack | **stale** | `qazstack-consumer-v1`, checksum-pinned 1.41.2 wheel, strict validation and tests. | Public consumer contract currently reports 1.41.2 but belongs to `4d7e078…`; re-observe it at the candidate SHA and obtain registry receipt. |
| AV DS | **conflicting** | SSR adapter now separates release 4.7.0 from source package `@sgeo/ui-kit` 4.5.1 and pins live AVDS SHA `79342b…`; local visual/a11y evidence passes. | Public QAZ.FUND contract still reports old AVDS SHA `5411…`; public registry reports AV DS 4.6. Registry and deployed contract must adopt the candidate contract. |
| QazPipe | **documented** | Versioned public pull source with NDJSON, pagination, checkpoint, idempotency and provenance. | Consumer owner must record a pull receipt or explicit inactive registration at the candidate SHA. |
| QazLake | **documented** | Brokered-only handoff, `direct_write=false`; target schema, retention, dry run, idempotency and rollback are activation gates. | QazLake owner must approve target/retention and preserve dry-run and rollback evidence before activation. |
| QazCompute | **documented** | Four public-safe deterministic profiles; remote execution disabled and no publication/eligibility authority. | QazCompute owner must publish a candidate-SHA runtime receipt if remote activation is requested. |
| QazGeo | **documented** | `deferred-no-geometry` records owner, reason and review trigger; no inferred map is emitted. | QazGeo owner needs a dated review exception or verified geometry reference before activation. |
| Identity / notifications | **not_applicable** | Anonymous read-only public access; accounts, server profiles, consent sync and delivery are disabled by contract. | No integration is due. Activation would require identity, consent, deletion, retention and delivery receipts. |
| Data and privacy | **documented** | Public provenance contracts exclude credentials, operator notes, saved selections and protected raw fields; preparation is browser-only. | Data owner must attach retention approval and deployed projection check to the accepted SHA. |
| Routes / UI / locales | **documented** | Route registry plus local six-surface RU browser matrix (30/30, 393/768/1440/320/1920), RU/KK/EN home matrix (15/15), focused tests and a verified 44 px compact filter-disclosure target. | Run full public route/browser matrix at the accepted SHA; fixture evidence is not runtime proof. |
| CI / build / delivery | **stale** | CI defines lint, tests, image, Trivy and SBOM gates; deployment scripts contain capacity/backup/rollback gates. | Green CI and immutable image/SBOM must be retained for the accepted SHA; no build was started in this audit. |
| Health / readiness / rollback | **unverifiable** | Source has health/readiness and guarded rollback contracts. | Candidate runtime readiness, worker/semantic receipt and rollback snapshot require an authorised guarded release; VPS safety pause remains respected. |
| Security | **documented** | Public writes disabled; operator auth/authorization tests, non-root image, secret boundaries and dependency audit are present. | Retain CI security artifact and re-check public allowlist/auth boundary at candidate SHA. |

## Remediation performed in this checkout

1. Corrected the AVDS contract ambiguity: `4.7.0` remains the public release;
   package provenance is explicitly `@sgeo/ui-kit` `4.5.1`, and the current
   upstream revision is `79342b07b061938c14101a213d1dd0c7a412d689`.
2. Added tests and documentation for that split, preserving legacy public
   `version` fields for compatibility.
3. Rewrote misleading dashboard filter labels, shortened/rebalanced the hero,
   and disclosed optional topic filters progressively. See the AVDS and EdPol
   audits beside this file.

No external registry, Platform checkout, service, database or production
configuration was changed.

## Checks run

| Check | Result | Evidence boundary |
|---|---|---|
| Root manifest presence | fail as expected | root `qdev-project.json` absent; no replacement invented |
| AVDS upstream contracts | pass | release 4.7.0, SHA `79342b…`; source package 4.5.1 |
| Source tests | pass | 657/657 tests, including 140 dashboard/localization/AVDS/platform regressions, on the final local candidate |
| AVDS browser acceptance | pass | local fixture, desktop visual-craft cell, no H1/asset/console/overflow failure |
| Browser matrix | pass | local six-surface RU matrix: 30/30; RU/KK/EN home × five widths: 15/15; zero serious/critical axe, console and overflow findings |
| EdPol exact gate | pass | 15 public-copy files, no failing exact policy candidate |
| Dependency health | pass | `pip check` and strict no-dependency-resolution `pip-audit` report no broken requirements or known vulnerabilities |
| Public release/consumer read | pass, stale | safe GETs only; observes deployed SHA `4d7e078…`, not candidate |
| Platform catalogue read | conflicting | stale `grant-radar` public record at the URL above |

## Unclosed connections

| Priority | Owner | Action | Closure proof |
|---|---|---|---|
| P0 | Qdev Platform catalogue owner | Provide the manifest schema, add root `qdev-project.json`, and replace stale `catalog/projects/grant-radar.md` identity/version claims. | Validated manifest and public registry record match `qaz-fund` and accepted SHA. |
| P0 | QAZ.FUND release owner | After the separate VPS safety pause and release authorization, promote one immutable candidate SHA through guarded CI/release. | Public release receipt, health/readiness, rollback artifact and browser proof match exactly. |
| P1 | AVDS + Platform registry owner | Reconcile AVDS 4.7.0/package provenance in registry and deployment receipt. | Public QAZ.FUND UI contract and registry carry current AVDS revision at candidate SHA. |
| P1 | QazPipe/QazLake/QazCompute/QazGeo owners | Attach consumer/activation receipts or owned deferred review records. | Dated record for each edge, with data boundary and candidate SHA where applicable. |

## Audit boundary

This report is an evidence-based local-candidate audit. It deliberately does
not assert Platform-ready or release-ready while schema/catalogue access and
same-SHA runtime evidence are absent. The public site was read but not changed;
the VPS was not contacted.
