# QazStack adoption review - 2026-07-15

## Purpose

This pass reduces duplicated infrastructure in QAZ.FUND without moving its
editorial policy, Kazakhstan relevance rules or public product model into the
platform package. The adopted release is the immutable QazStack `1.37.2` tag.

## Adopted now

| Primitive | QAZ.FUND use | Product effect |
| --- | --- | --- |
| `qazstack.source.canonicalize_source_url` | Stable fingerprints remove tracking parameters and fragments. | Fewer duplicate records caused by campaign URLs. |
| `qazstack.content.strip_html` and `normalize_text` | One source-text helper replaces 16 collector-local implementations. | Consistent HTML decoding and whitespace cleanup. |
| `qazstack.content.diversify_ranked_items` | The short digest promotes source variety, then fills remaining slots in rank order. | A single source cannot crowd out the useful overview. |
| `qazstack.evidence.resolve_public_evidence_state` | Coverage exposes aggregate evidence states; NDJSON rows expose their state. | A source link is labelled `sourced`, never falsely promoted to `verified`. |
| `qazstack.export.ndjson_response` | `/opportunities.ndjson` mirrors public filters with ETag and `304` support. | AI systems and data consumers can stream compact records with lower transfer cost. |

The vendored wheel is built from tag `v1.37.2` at commit
`b401122feb0ab7fd7e4b1d84b9b6ea8ded20071b`. Its SHA-256 is recorded beside
the artifact in `vendor/`.

## Kept product-owned

- `core/geofit.py`: Kazakhstan and Central Asia inclusion and exclusion policy.
- `core/scoring.py`: opportunity value, deadline urgency and audience weights.
- `core/localization.py`: RU/EN product copy and deterministic fallback policy.
- `core/opportunity_intelligence.py`: public lifecycle and decision readiness.
- `sources/*`: source-specific extraction, fallback and retention decisions.
- `api/dashboard.py`: QAZ.FUND workflows and AV DS 4 SSR adapter.

These modules encode product judgement. Replacing them with generic platform
helpers would remove useful behaviour rather than reduce duplication.

## Deferred after review

| Primitive | Decision | Reason |
| --- | --- | --- |
| `RequestIDMiddleware` | Defer | Version 1.37.2 accepts and logs an unbounded caller-supplied request ID. Adopt after the shared middleware validates length and character set. |
| `PublicCacheMiddleware` | Defer | QAZ.FUND already owns route-specific caching and content invalidation. A broad middleware migration needs exact ETag parity tests first. |
| Shared pagination response | Defer | Changing the current list response from a JSON array would break public consumers. |
| QazStack retry/circuit breaker | Defer | Source adapters have different retention and fallback semantics. Migrate one adapter only after fixture parity and live source smoke. |
| Generic KZ NLP | Defer | Current product rules are deterministic and covered; optional NLP dependencies would enlarge the runtime. |
| QazGeo map primitives | Defer | Opportunities do not yet carry verified coordinates or authoritative geometry references. |
| QazCompute | Defer | Duplicate clustering and anomaly detection remain candidates until local/remote parity and fallback are proven. |

## Public contracts

- JSON catalog: `/opportunities`
- Streaming export: `/opportunities.ndjson`
- Source and evidence coverage: `/coverage`
- Short diversified feed: `/digest`
- Discovery: `/llms.txt`, `/site-discovery.json`, `/openapi.json`
- Runtime boundary: `/.well-known/qazstack-consumer.json`

The NDJSON route accepts the same public filters as the JSON catalog. Each row
adds `evidence_state`; plain official links are `sourced`. Reviewed evidence can
become `verified` only when QAZ.FUND stores a separate reviewed-source record.

## Verification

Required before merge and deploy:

```text
shasum -a 256 -c vendor/qazstack-1.37.2.sha256
.venv/bin/python -m pytest -q
make lint
docker build -f Dockerfile.prod -t qazfund:qazstack-1.37.2 .
```

Production completion still requires the documented deploy, `/ready`, NDJSON
ETag smoke and the full `scripts.production_smoke` run. Local green does not
prove production rollout.

Local result for this change set:

- QazStack wheel checksum: passed;
- full test suite: `409 passed`;
- Black, isort, Flake8 and mypy: passed;
- local HTTP check: NDJSON, `llms.txt` and evidence counters responded;
- production Docker build: not run locally because the Docker CLI is not
  installed on this workstation; CI/deploy must keep this as a blocking gate.
