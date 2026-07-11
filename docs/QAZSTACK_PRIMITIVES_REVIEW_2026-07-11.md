# QazStack primitives review - 2026-07-11

Scope: QAZ.FUND (`grant-radar-public`) against the current platform/QazStack
surface in `platform-portal-git` and the QazStack registry.

This is an inventory and adoption plan, not a rewrite plan. QAZ.FUND is a small
FastAPI service with a production-safe local AV DS adapter; broad framework
replacement would add deployment risk. Use this file to decide what to upstream
to QazStack and what to pull back into QAZ.FUND later.

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

## Pass 1 - QAZ.FUND primitives to upstream into QazStack

| Candidate | Local evidence | Why it belongs in QazStack | Status | Recommended action |
|---|---|---|---|---|
| Kazakhstan/Central Asia geo-fit rules | `core/geofit.py`, `tests/test_scoring.py` | Several products need Kazakhstan/Central Asia relevance gating, not only grants. The exclusion rules are already practical and test-backed. | Candidate | Extract as `qazstack/geo/fit.py` or `qazstack/analytics/relevance.py` after stabilizing public API. Keep QAZ.FUND local until QazStack package import is deploy-safe. |
| Opportunity relevance scoring | `core/scoring.py`, `tests/test_scoring.py` | The weighted keyword + geography + deadline scoring is a reusable operator-ranking primitive. | Candidate | Upstream as a domain-neutral `relevance_score()` engine with product-supplied weights. Do not hard-code grant tags in the shared primitive. |
| Source parser contract | `sources/base.py`, `sources/*`, `tests/test_parsers_async.py` | QAZ.FUND has a mature pattern for async source adapters, curated fallback, blocked-source retention and source-specific tests. | Partly covered | Align with `qazstack/collectors/source_contracts.py`. Upstream the contract shape and test fixtures, not every product source. |
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

## Pass 2 - QazStack/platform primitives QAZ.FUND should adopt

| QazStack primitive | Platform evidence | Fit for QAZ.FUND | Risk | Recommended action |
|---|---|---|---|---|
| `collectors-and-entity-pipeline` | `qazstack/primitives-registry.json` maps `grant-radar` | High. QAZ.FUND already behaves like a collector pipeline. | Medium | Start with contract alignment: make `sources/base.py` fields match QazStack collector contract names where possible. Avoid importing the package in prod until packaging/auth is stable. |
| `tasking-and-resilience` | Registry maps `grant-radar`; local worker already uses queue/scheduler | High. Retry/circuit-breaker primitives would reduce local drift. | Medium | Adopt only after a package import smoke in Docker. First target: shared retry/backoff policy for source fetches. |
| `observability-and-ui` | Includes `qazstack/observability/middleware.py`, `qazstack/ui/jinja_helpers.py`, `qazstack/seo/meta.py` | Medium/high. QAZ.FUND has local meta/analytics/AVDS helpers that could align. | Medium | Pull concepts, not direct code, unless dependency packaging is available. Candidate first step: shared SEO/discovery helper. |
| `reports-and-export` | `qazstack/reports/*`, `qazstack/export/*` | Medium. QAZ.FUND has CSV/calendar links and could later export funder/opportunity packs. | Low/medium | Add later as an operator feature: export saved collection to CSV/XLSX/report. No immediate code change. |
| `analytics-and-kznlp` | `qazstack/kznlp/*`, `qazstack/analytics/*` | Medium. Useful for KZ/RU/EN normalization and lightweight NER. | Medium | Replace local deterministic NLP only after behavior parity tests. Current local helpers are simple and well tested. |
| `geo-and-location` | `qazstack/geo/*`, QazGeo/QazStack registry | Medium. Useful if QAZ.FUND adds maps or regional program routing. | Low/medium | Use for future region filters, source maps and Kazakhstan oblast aliases. No current map UI should be added unless it serves operator workflow. |
| `pagination-and-listing` | `qazstack/pagination/page.py` | Low/medium. QAZ.FUND already has API pagination and client list logic. | Low | Consider for API response normalization only if public API grows. |
| `auth-and-admin` | `qazstack/auth/*`, `qazstack/admin/setup.py` | Low now. QAZ.FUND is public/read-only plus deploy scripts. | Medium | Defer until there is a real admin/operator write surface. |
| `governance-and-audit` | `qazstack/governance/*`, `qazstack/audit/*` | Medium. Useful for source trust, run evidence and public claims. | Low/medium | Add docs-level evidence model first: source, checked_at, status, limitation. |
| `databus-and-bus` | `qazstack/bus/*`, `qazstack/databus/*` | Low now. QAZ.FUND does not need event fanout yet. | Medium/high | Defer. Use only when QAZ.FUND becomes a data provider for QazLake/QazPipe. |

## Immediate safe actions

These can be done without changing runtime architecture:

1. Keep `docs/AVDS_INTEGRATION.md` as the active UI contract and update it when
   QAZ.FUND adopts new AV DS/QazStack operator primitives.
2. Add this review to repo docs and test that it stays present.
3. Open a platform-side follow-up to add QAZ.FUND's `geo-fit`,
   `public-discovery` and `operator-passport-card` candidates to the QazStack
   registry.
4. Before any direct QazStack import in QAZ.FUND, require:
   - Docker build proof;
   - `pytest -q`;
   - `scripts.production_smoke --base-url https://qaz.fund`;
   - rollback path to local implementation.

## Decision

Current recommendation:

- Keep QAZ.FUND runtime local and stable for production.
- Upstream QAZ.FUND's mature algorithms and UI patterns as documented QazStack
  candidates first.
- Pull QazStack primitives back only through small, test-backed slices, starting
  with discovery/SEO helpers and collector contract alignment rather than broad
  framework imports.

