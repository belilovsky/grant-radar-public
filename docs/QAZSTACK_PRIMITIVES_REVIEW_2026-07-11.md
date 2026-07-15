# QazStack primitives review – 2026-07-11

## Update - 2026-07-15 (QazStack 1.37.2)

The second adoption pass is documented in
`docs/QAZSTACK_ADOPTION_2026-07-15.md`. QAZ.FUND now consumes stable shared
source/content normalization, evidence-state, result-diversification and
cache-aware NDJSON export helpers. Product scoring, geo-fit, localization and
source fallback policy remain local. Earlier snapshot-based integration notes
are preserved only in dated closeout evidence and are not the current runtime
contract.

The former source snapshot was removed from this repository. QAZ.FUND installs
the immutable `qazstack-1.37.2-py3-none-any.whl` release dependency from
`vendor/`; its SHA-256 is verified in the repository and the production
Dockerfiles install the same wheel. Kazakhstan/Central Asia relevance rules
remain product-owned in `core/geofit.py`.

The wheel is intentionally carried with the product while QazStack remains a
private repository and the production host has no package-registry credential.
It is a reproducible release dependency, not a source checkout. A future
internal package registry may replace this delivery mechanism without changing
the QAZ.FUND contract boundary.

Scope: QAZ.FUND (`grant-radar-public`) against the current platform/QazStack
surface in `platform-portal-git` and the QazStack registry.

This started as an inventory and adoption plan, then advanced into a small
runtime integration. QAZ.FUND is still a small FastAPI service with a
production-safe local AV DS adapter; broad framework replacement would add
deployment risk. The implemented integration is intentionally narrow:
QAZ.FUND imports released contracts from the installed 1.37.2 wheel while
preserving product-owned policy.

## Staged follow-ups - 2026-07-15

- QazStack PR #33 merged the neutral lifecycle helper after release 1.37.2.
  QAZ.FUND can consume it after the next compatible package release and keeps
  its tested local implementation until then.
- QazCompute PR #30, head `08f5eb1`, provides `opportunity_enrich.v1`; its
  hosted CI is blocked by the GitHub account billing gate, so the profile is
  code-ready but not runtime-enabled or release-proven.
- QAZ.FUND accepts optional lifecycle and compute integration only through
  explicit fallback and decision-readiness gates.
- Direct provider credentials were removed from the QAZ.FUND enrichment path.

## Implemented runtime bridge

- QazStack release source commit:
  `b401122feb0ab7fd7e4b1d84b9b6ea8ded20071b`
- QazStack package: `qazstack==1.37.2`
- Shared module: `qazstack.opportunities`
- QAZ.FUND bridge: `core/qazstack_bridge.py`
- Active integration point: source-contract validation in the parser layer
- Runtime contract: `/.well-known/qazstack-consumer.json`

The first deploy attempt used a direct private GitHub package dependency. That
is not acceptable for the production Docker build because the VPS build context
does not have GitHub credentials and should not require them. The production
implementation therefore installs a checksum-pinned release wheel from
`vendor/`; it does not carry or import a QazStack source snapshot.

Runtime behavior:

- QAZ.FUND validates parser metadata with
  `qazstack.opportunities.SourceContract`;
- `tests/test_qazstack_bridge.py` proves the module is imported from
  `site-packages`, not a repository source copy;
- local QAZ.FUND rules remain authoritative for Kazakhstan/Central Asia fit and
  product-specific exclusions.
- the lifecycle bridge returns no shared result until a compatible package is
  released, so the local implementation remains authoritative;
- QazCompute enrichment is operator-controlled and may write auditable metadata
  only while `decision_ready=false`; see
  `docs/QAZCOMPUTE_INTEGRATION_2026-07-15.md`.

## Current QazStack registry evidence

The platform registry already maps `grant-radar` as a consumer of:

- `collectors-and-entity-pipeline`
  - registry paths: `qazstack/collectors/__init__.py`,
    `qazstack/collectors/registry.py`, `qazstack/collectors/pipeline.py`,
    `qazstack/collectors/extractor.py`
  - local equivalents: `sources/*`, `core/pipeline.py`,
    `core/pipeline_runner.py`, `core/fetch_queue.py`
- `tasking-and-resilience`
  - registry paths: `qazstack/tasks/worker.py`,
    `qazstack/redis/client.py`, `qazstack/resilience/breaker.py`,
    `qazstack/resilience/retry.py`
  - local equivalents: `core/scheduler.py`, `core/fetch_queue.py`,
    `core/runner_factory.py`, `scripts/production_smoke.py`

The current QAZ.FUND dashboard also uses a local AV DS-compatible adapter:
`api/avds.py` plus `data-avds-component` markers validated by
`scripts/production_smoke.py`.

## Pass 1 – QAZ.FUND primitives to upstream into QazStack

| Candidate | Local evidence | Why it belongs in QazStack | Status | Recommended action |
|---|---|---|---|---|
| Kazakhstan/Central Asia geo-fit rules | `core/geofit.py`, `tests/test_scoring.py`, `tests/test_qazstack_bridge.py` | The rules contain product-specific inclusion and exclusion policy. | Keep product-owned | Reuse only a future configurable evidence contract; do not move QAZ.FUND's source and geography decisions into QazStack. |
| Opportunity relevance scoring | `core/scoring.py`, `tests/test_scoring.py` | The weighted keyword + geography + deadline scoring is a reusable operator-ranking primitive. | Candidate | Upstream as a domain-neutral `relevance_score()` engine with product-supplied weights. Do not hard-code grant tags in the shared primitive. |
| Source parser contract | `sources/base.py`, `sources/*`, `tests/test_sources.py` | QAZ.FUND has a mature pattern for async source adapters, curated fallback, blocked-source retention and source-specific tests. | Partly implemented | `qazstack.opportunities.SourceContract` now validates shared parser metadata. QAZ.FUND exposes optional validation through `core/qazstack_bridge.validate_shared_source_contract()`. |
| Curated fallback and retention policy | `sources/kazakhstan_watch.py`, `sources/kazakhstan_domestic.py`, parser tests | This is a reusable pattern for official sources that block automation or return temporary errors while the public route remains important. | Candidate | Add a QazStack collector policy primitive: `retain_on_fetch_error`, `detail_fetch_status`, `status_note`. |
| Public AI/discovery surface contract | `api/main.py`, `api/public_meta.py`, `scripts/production_smoke.py`, tests for `llms.txt`, `site-discovery.json`, `/docs`, `/openapi.json` | Multiple public products need AI-readable entrypoints and smoke gates. QAZ.FUND has a compact, production-proven contract. | Candidate | Upstream a small `qazstack/seo/discovery.py` helper for `llms.txt`, `site-discovery.json`, OpenAPI/docs links and smoke markers. |
| Operator list card anatomy | `api/dashboard.py`, `docs/AVDS_INTEGRATION.md`, `tests/test_api_repository.py` | The latest QAZ.FUND card pattern is a good AV DS operator surface: meaning left, service passport right, few actions. | Candidate | Add to AV DS/QazStack UI docs as `document-row` / `operator-passport-card`; do not move server-rendered HTML into a shared package yet. |
| Content cleanup and localized fallback | `core/nlp.py`, `core/localization.py`, `core/russian_summary.py`, `tests/test_nlp_quality.py`, `tests/test_localization.py` | The cleanup rules remove duplicated titles, source UI noise and mixed-language fragments; this is useful beyond grants. | Candidate | Upstream deterministic text-cleanup helpers as KZ/RU content hygiene utilities. Keep DeepSeek/LLM enrichment outside shared core. |
| Production smoke profile | `scripts/production_smoke.py`, `tests/test_production_smoke.py` | It checks readiness, public discovery, dashboard markers and forbidden content. This shape is reusable across public QDev surfaces. | Candidate | Turn into a parameterized smoke helper in platform ops/QazStack, with per-product marker config. |
| Source registry documentation pattern | `docs/SOURCE_REGISTRY.md`, `docs/CONTENT_COVERAGE.md` | Clear source inventory improves trust and operator handoff. | Candidate | Upstream as a docs template plus optional JSON schema for source coverage. |

Do not upstream now:

- Product-specific source adapters such as `sources/unesco_iite.py` or
  `sources/kazakhstan_domestic.py` as shared QazStack code. Their lessons should
  be upstreamed as contracts/policies; the adapters should remain product code.
- QAZ.FUND's exact public copy, filters and selection presets. These are product
  logic, not platform primitives.
- The current local `api/avds.py` token adapter as a canonical AV DS package.
  It is a safe deployment bridge, not the source of truth for AV DS.

## Pass 2 – QazStack/platform primitives QAZ.FUND should adopt

| QazStack primitive | Platform evidence | Fit for QAZ.FUND | Risk | Recommended action |
|---|---|---|---|---|
| `collectors-and-entity-pipeline` | `qazstack/primitives-registry.json` maps `grant-radar`; `qazstack.opportunities.SourceContract` is installed in QAZ.FUND | High. QAZ.FUND already behaves like a collector pipeline. | Medium | Keep runtime parser implementations local; use shared contract validation and fixtures before moving any source adapter. |
| `tasking-and-resilience` | Registry maps `grant-radar`; local worker already uses queue/scheduler | High. Retry/circuit-breaker primitives would reduce local drift. | Medium | Still defer shared retry/backoff runtime import until per-source smoke tests exist. |
| `observability-and-ui` | Includes `qazstack/observability/middleware.py`, `qazstack/ui/jinja_helpers.py`, `qazstack/seo/meta.py` | Medium/high. QAZ.FUND has local meta/analytics/AVDS helpers that could align. | Medium | Pull concepts, not direct code, unless dependency packaging is available. Candidate first step: shared SEO/discovery helper. |
| `reports-and-export` | `qazstack/reports/*`, `qazstack/export/*` | Medium. QAZ.FUND has CSV/calendar links and could later export funder/opportunity packs. | Low/medium | Add later as an operator feature: export saved collection to CSV/XLSX/report. No immediate code change. |
| `analytics-and-kznlp` | `qazstack/kznlp/*`, `qazstack/analytics/*` | Medium. Useful for KZ/RU/EN normalization and lightweight NER. | Medium | Replace local deterministic NLP only after behavior parity tests. Current local helpers are simple and well tested. |
| `geo-and-location` | `qazstack/geo/*`, QazGeo/QazStack registry | Medium. Useful if QAZ.FUND adds maps or regional program routing. | Low/medium | Use for future region filters, source maps and Kazakhstan oblast aliases. No current map UI should be added unless it serves operator workflow. |
| `pagination-and-listing` | `qazstack/pagination/page.py` | Low/medium. QAZ.FUND already has API pagination and client list logic. | Low | Consider for API response normalization only if public API grows. |
| `auth-and-admin` | `qazstack/auth/*`, `qazstack/admin/setup.py` | Low now. QAZ.FUND is public/read-only plus deploy scripts. | Medium | Defer until there is a real admin/operator write surface. |
| `governance-and-audit` | `qazstack/governance/*`, `qazstack/audit/*` | Medium. Useful for source trust, run evidence and public claims. | Low/medium | Add docs-level evidence model first: source, checked_at, status, limitation. |
| `databus-and-bus` | `qazstack/bus/*`, `qazstack/databus/*` | Low now. QAZ.FUND does not need event fanout yet. | Medium/high | Defer. Use only when QAZ.FUND becomes a data provider for QazLake/QazPipe. |

## Completed safe actions

Completed in the QAZ.FUND / QazStack integration pass:

1. Keep `docs/AVDS_INTEGRATION.md` as the active UI contract and update it when
   QAZ.FUND adopts new AV DS/QazStack operator primitives.
2. Add this review to repo docs and test that it stays present.
3. Add QAZ.FUND primitives to the platform-side QazStack registry.
4. Install checksum-pinned QazStack 1.37.2 from the vendored release wheel.
5. Use `qazstack.opportunities.SourceContract` as the dependency-free parser
   metadata contract.
6. Keep lifecycle adoption optional with a deterministic local fallback until
   the shared helper reaches a package release.
7. Exclude repository source snapshots so production cannot shadow the wheel.
8. Stage optional enrichment through the versioned QazCompute profile without
   copying provider keys into QAZ.FUND; do not enable it before upstream CI and
   runtime smoke are green.

## Decision

Current recommendation:

- Keep QAZ.FUND runtime local and stable where product-specific rules are richer
  than the shared primitive.
- Use QazStack for narrow, tested shared contracts first.
- Continue extraction only through parity fixtures and per-source smoke checks.
- Do not replace source adapters or scoring wholesale until the shared package
  proves exact behavior parity.
