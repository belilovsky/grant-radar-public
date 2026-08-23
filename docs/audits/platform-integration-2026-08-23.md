# Platform integration audit — QAZ.FUND — 2026-08-23

## Scope and identity

- Project/site: QAZ.FUND — `https://qaz.fund`
- Canonical source authority: `/Users/belilovsky/Documents/Codex/2026-05-21/grant-radar-public`
- Source repository: `https://github.com/belilovsky/grant-radar-public.git`
- Baseline source SHA: `2421deb52c34995c1c1213148f15d4a7320f6e1c`
- Default branch: `main`; the baseline was three commits ahead of `origin/main`.
- Public/runtime address: `https://qaz.fund` (declared by `deploy/nginx/qaz.fund.conf` and project contracts).
- Evidence cut-off: `2026-08-23T07:50:08Z`.
- Working-tree boundary: only this checkout was inspected. The authorized
  follow-up is committed locally as candidate
  `7f2484ca7f25f33925386bd622ad6e6bb6dd29ec`; local `node_modules/` and
  `output/` artifacts were preserved and are now ignored without deletion. No
  accepted production release SHA exists yet.

The public health and release endpoints were read once, without changing
state. The public runtime answered `/ready` with HTTP 200 and
`{"status":"ok","backend":"database","items":1424}` at
`2026-08-23T07:50:03Z`. The public release contract answered HTTP 200 at
`2026-08-23T07:50:03Z`, but identifies deployed SHA
`4d7e078f7bee69656b6b4d39644eb58288ede641`, not the observed canonical SHA.
Its internal receipt is coherent (`sourceDirty=false`) with image digest
`sha256:11fbcb8f5c1aa3ef3062bd5cef6874ae3653d44980dbdc8d5d8a960e470db8b2`,
artifact digest
`sha256:420eb8e9720a029e0866714905aa5803f0ec2c222039a63e537f021f804b6be6`,
and `deployedAt=2026-08-22T11:14:27Z`, but it is not the current source
release.

## Verdict

`blocked`

- Applicable rows: **12**
- Covered: **0**
- Documented: **5**
- Missing: **1**
- Stale: **0**
- Conflicting: **1**
- Not applicable: **0**
- Unverifiable: **5**
- Coverage: **0/12 = 0%**

`covered` is reserved for a fresh two-sided source plus operational proof. Local
tests, a local browser fixture, an old receipt, and a public 200 without the
current source identity do not qualify. The blocking conditions are the missing
root manifest and the source/runtime SHA conflict; Platform registry evidence
is also not observable in this project-only scope.

## Root `qdev-project.json` and manifest migration

Status: **missing**.

The canonical source checkout was observed at the pinned SHA above and has no
root-level `qdev-project.json`. No nested file, `.well-known` response,
QazStack contract, or documentation was substituted for it. The Platform Portal
checkout, `qdev-project-manifest-v1` schema, and authoritative Platform registry
were not provided or available inside this project scope, so manifest schema
validation and catalogue reconciliation are **unverifiable**, not inferred.

This is a required governance gap. Owner role: **Qdev Platform catalogue owner**
(the responsible individual is not identified by this repository). Closure
requires an approved manifest at the repository root, validation against the
canonical `qdev-project-manifest-v1` schema, and a matching Platform catalogue
record. The project is production, not archived; no deprecated lifecycle
exception applies.

## Coverage matrix

| Area | Requirement / boundary | State | Project evidence | Missing or closure evidence |
|---|---|---|---|---|
| Identity and registry | One project ID, repo, owner, lifecycle, catalogue entry, public route and release SHA | **missing** | Local contracts consistently use `project_id=qaz-fund`; root manifest is absent; public route is `https://qaz.fund`. | Root manifest plus Platform catalogue record and runtime release all agree on ID, repo, owner, lifecycle and accepted SHA. |
| QazStack | Consumer contract, primitives, version, verification and runtime receipt | **unverifiable** | `qazstack-reuse.json`, `docs/qazstack/consumer-contract.json`, `api/ecosystem.py`, checksum-pinned `vendor/qazstack-1.41.2.sha256`; local QazStack tests pass. | Current public QazStack contract and Platform/QazStack registry observation at the accepted release SHA. |
| AV DS | Shipped adapter/version, tokens/components, accessibility and responsive proof | **unverifiable** | `api/integration_versions.py` pins `@sgeo/ui-kit` 4.7.0 and `@av/patterns` 0.2.0; `api/avds.py`, `api/ecosystem.py`, AV DS tests and local browser evidence exist. | Current public AV DS contract and browser evidence for the deployed SHA; Platform-side agreement is not observed. |
| QazPipe | Read-only producer boundary, provenance, pagination and degradation | **unverifiable** | `api/ecosystem.py` and `/.well-known/qazpipe-source.json` contract implementation; NDJSON/checkpoint/idempotency tests. | Consumer/Platform handshake or an authoritative inactive record; current endpoint was not queried during the infrastructure safety window. |
| QazLake | Archive handoff, retention and no-direct-write boundary | **unverifiable** | QazPipe contract sets `direct_write=false` and requires target schema, retention, dry run, idempotency and rollback. | Named QazLake owner, approved target schema/retention, dry-run artifact and registry evidence. |
| QazCompute | Safe compute profiles, non-mutation and graceful local fallback | **unverifiable** | Four deterministic public-safe profiles; `remote_execution_active=false`, `decision_ready=false`; `core/qazcompute_bridge.py` and tests. | Current runtime receipt/fixture parity and authorised private server-side wiring if activation is required. |
| QazGeo | Geographic contract or explicit deferred boundary | **documented** | `api/ecosystem.py` declares `deferred-no-geometry`, `product_owner=qaz-fund`, rationale and review trigger; no inferred map is published. | A dated review exception is absent, and QazGeo registry evidence is unavailable. Add verified geometry only after QazGeo validation. |
| Identity capability | Accounts, consent, sync and notifications | **documented** | `api/notification_contract.py` explicitly keeps anonymous read-only access, server profiles, sync and delivery disabled; browser-only storage is tested. | If activation is proposed: identity provider, recovery, consent, deletion, retention and delivery receipts. |
| Data and privacy | Source, provenance, public/private projection and retention | **documented** | `core/provenance.py`, `docs/DATA_PROVENANCE_CONTRACT.md`, `docs/qazstack/language-surface.json`; public projections exclude operator data, credentials and raw protected payloads. | Fresh deployed projection check and owner-approved retention record; no current-SHA public projection was observed. |
| Routes and UI | Canonical routes, 404/error/empty states, keyboard/focus, RU/KK/EN and responsive proof | **documented** | `api/route_registry.py`, route/CJM tests, `scripts/browser_matrix.py`; local evidence file records 50 checks at 320/393/768/1440/1920 px with zero failures. | Browser evidence against the public runtime at the accepted SHA; the local fixture is not runtime proof. |
| Delivery and operations | CI, build, health/readiness, release identity, backup and rollback | **conflicting** | `.github/workflows/verify.yml`, `Dockerfile.prod`, deploy/rollback scripts and passing local gates; production Compose now defaults to `https://qaz.fund`, but `/ready` is healthy while public release is SHA `4d7e078…` and the local candidate is dirty after remediation. | Guarded release of an exact accepted SHA, exact public release match, health/readiness, worker/semantic and rollback evidence. |
| Security | Auth, mutations, CSRF boundary, audit trail, allowlist and secrets | **documented** | Bearer-token/operator tests in `api/runtime_config.py` and `tests/test_api_repository.py`; public writes disabled; `.dockerignore`, non-root Docker runtime and `pip-audit` show no known vulnerabilities. | Deployed-SHA security/route proof and retained CI security artifact; no authenticated runtime session was used. |

## Cross-system consistency

| Claim / edge | Project-side evidence | Platform/runtime-side evidence | Result |
|---|---|---|---|
| `qaz-fund` identity | Local contracts and code use `qaz-fund`; source SHA `2421deb…` | Public release says service `qaz-fund` but SHA `4d7e078…`; Platform catalogue not observed | **conflicting** |
| QAZ.FUND → QazStack | Consumer contract, pinned 1.41.2 wheel, local tests | Platform/QazStack registry and current public consumer contract not observed | **unverifiable** |
| QAZ.FUND → AV DS | 4.7.0 adapter, tokens, component markers, local browser matrix | Current public AV DS contract and Platform record not observed | **unverifiable** |
| QAZ.FUND → QazPipe/QazLake | Read-only producer and gated archive boundary | Consumer handshake/registry/receipt not observed | **unverifiable** |
| QAZ.FUND → QazCompute/QazGeo | Local deterministic fallback and deferred geometry boundary | Current runtime/owner registry not observed | **unverifiable / documented boundary** |
| QAZ.FUND → public route | Nginx product config declares `qaz.fund` | `HEAD /` returned HTTP 200; release identity differs from source | **conflicting** |

## Data, privacy and security boundary

The source contracts preserve public source URLs, discovery timestamps and
provenance while excluding operator credentials, saved selections, private
notes and raw protected payloads. Application preparation is browser-only and
does not submit data. Public mutation routes remain protected by bearer/admin
checks; no authenticated page or secret was opened during this audit. The
production Dockerfile uses a non-root runtime, the deployment path pins the
QazStack wheel hash, and the local `pip-audit` run reported `No known
vulnerabilities found`.

These are source and candidate checks. They do not prove that the currently
deployed SHA exposes exactly the same projection, auth boundary or asset set.

## Gates run

| Gate | Result | Evidence / limitation |
|---|---|---|
| Source authority | pass | Canonical checkout, SHA, `main`, remote and dirty boundary recorded above. |
| Root manifest | **missing** | `test -f qdev-project.json` failed because the root manifest is absent; no schema/registry substitute used. |
| Product lint/types | pass | `make lint`: Black, isort, flake8, mypy (121 files), vulture. |
| Product tests/typography | pass | `make ci-fast`: 657 passed; typography `finding_count=0`. |
| Dependency consistency | pass | `pip check`: no broken requirements. |
| Dependency vulnerability scan | pass | `pip-audit --strict` on production requirements: no known vulnerabilities. |
| Local browser/accessibility matrix | pass, local only | 50 surface/viewport checks from `output/browser-matrix/platform-local-2026-08-23.json`, observed `2026-08-23T06:16:53Z`; zero console, serious/critical axe, interaction and overflow findings. |
| Public readiness | pass for observed runtime | `GET https://qaz.fund/ready` → 200, database backend, 1424 items at `2026-08-23T07:50:03Z`. |
| Public release identity | **conflicting** | `GET /.well-known/release.json` → 200, `sourceDirty=false`, digests present, but deployed SHA `4d7e078…` ≠ source SHA `2421deb…`. |
| Public root route | pass for observed runtime | `HEAD https://qaz.fund/` → 200 at `2026-08-23T07:50:08Z`; this does not prove current-SHA content. |
| Production smoke | not run | Full smoke was not run during the active infrastructure safety window; no result was fabricated. |
| Production image build/SBOM | not run | CI workflow declares the gate, but this audit did not start a local build or alter Docker state. |
| Production public-origin default | pass locally | `docker-compose.prod.yml` defaults API and worker `PUBLIC_BASE_URL` to `https://qaz.fund`; `tests/test_deploy_contract.py` asserts both substitutions. |
| Platform Portal gates | unverifiable | No Platform Portal checkout, manifest schema or authoritative registry was in this project-only scope. |

## Follow-up remediation and re-audit

The authorized follow-up fixed the confirmed local deployment-contract drift:

- production API and worker now default `PUBLIC_BASE_URL` to the canonical
  `https://qaz.fund` origin;
- the deploy contract test prevents the old `example.org` default returning;
- generated `node_modules/` and browser-audit output are ignored so they do not
  become accidental release inputs, while existing files remain untouched.

The follow-up gates are green: the focused deploy/platform/numbering tests are
20/20, `make lint` passes, `make ci-fast` passes with 657 tests, `pip check`
reports no broken requirements, and `pip-audit --strict` reports no known
vulnerabilities after excluding the locally vendored QazStack wheel from the
PyPI-only audit. The change is not closed in production: the root manifest is
still missing, the public release still identifies `4d7e078…`, and no build,
backup or deploy was attempted during the VPS emergency pause. The candidate
commit is local only and has not been pushed or promoted.

## Remediation queue

| Priority | Owner role | Finding | Concrete next action | Closure proof |
|---|---|---|---|---|
| P0 | Qdev Platform catalogue owner | Root `qdev-project.json` missing | Supply the approved `qdev-project-manifest-v1` root manifest and register the project. | Schema validation, catalogue record and source ID/repo/owner/lifecycle agree. |
| P0 | QAZ.FUND release owner | Public runtime is `4d7e078…`; the post-remediation candidate is local-only and has no accepted release SHA. | After the infrastructure pause is lifted and separately authorised, push the candidate and run the guarded immutable release path. | Public release JSON source SHA exactly equals the accepted commit SHA; image/artifact digests, timestamps and `sourceDirty=false` agree. |
| P1 | Qdev Platform integration owners | Bidirectional QazStack/AV DS/QazPipe/QazLake/QazCompute/QazGeo evidence unavailable. | Reconcile each public contract with the authoritative Platform/consumer registry. | Dated registry/handshake evidence for every edge at the same release SHA. |
| P1 | QAZ.FUND product/release owner | Local browser proof is not deployed browser proof. | Run the browser matrix and public smoke after the accepted release is live. | RU/KK/EN, 404/empty/error, desktop/mobile, focus, axe, console and overflow results tied to release SHA. |
| P2 | QAZ.FUND + QazGeo owner | Deferred QazGeo boundary has a trigger but no dated review exception. | Record a dated review decision or keep it explicitly optional in the approved manifest. | Owner, rationale, boundary and review date in the manifest/registry; no geometry before validation. |

## Boundary notes

- The initial audit was read-only. The authorized follow-up changed only local
  `docker-compose.prod.yml`, `.gitignore`, the deploy-contract test and this
  report. No registry, Platform catalogue, PR, database, Docker object, VPS
  configuration or deployment was changed.
- The public health/release/root reads were limited to safe GET/HEAD evidence.
- A public 200 is not treated as proof of the current source release.
- No Platform registry or schema was guessed, cloned, or reconstructed.
- The local browser JSON is fixture-based evidence and is explicitly not a
  production browser proof.
- The verdict is blocked by missing governance and conflicting release identity;
  it is not upgraded by the passing local gates.
