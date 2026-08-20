# QAZ.FUND ecosystem integration

## Purpose

QAZ.FUND is the public discovery and decision-support surface for grants,
subsidies, accelerators, tenders and institutional support programs. It should
participate in the QDev ecosystem without becoming a second data lake, workflow
bus, geospatial registry or design system.

The runtime source of truth for this boundary is
`/.well-known/qdev-ecosystem.json`. Documentation may explain the contract but
must not claim an integration that the endpoint and production smoke cannot
prove.

## Implemented now

| System | Runtime status | Boundary |
| --- | --- | --- |
| QazStack 1.41.2 | `runtime-proven` | QAZ.FUND uses neutral contracts, source and text normalization, lifecycle rules, evidence states, diversified listing, machine exports, the public opportunity schema and expert-reviewed ranking metrics. Product relevance and publication policy stay local. |
| AV DS 4.6.0 | `adapter-aligned` | FastAPI pages use a local server-side adapter aligned with AV DS component families. No direct React package import is claimed. |
| QazPipe | `producer-ready` | QAZ.FUND publishes a versioned read-only pull contract over `/api/v1/opportunities.ndjson`, including pagination, checkpoints, idempotency and required provenance. Connector activation remains consumer-controlled. |
| QazLake | `brokered-via-qazpipe` | Public records may be archived only through QazPipe after the target schema, retention, dry run, idempotency and rollback gates pass. QAZ.FUND never writes directly into QazLake tables. |
| EdPol | `query-ready` | Education opportunities are available through the public tag-filtered API. EdPol decides whether and how to consume them. |
| QazGeo | `deferred-no-geometry` | Region classes exist, but verified coordinates do not. No inferred or decorative map is published. |
| QazCompute | `local-runtime-proven` | Four deterministic profiles run locally and publish QazCompute-compatible envelopes. Remote task execution remains disabled until fixture parity and private server-side wiring are ready. |

## Machine entry points

- `/.well-known/qazstack-consumer.json` – strict QazStack production contract.
- `/.well-known/avds-ui-contract.json` – AV DS 4 component-family boundary.
- `/.well-known/qazpipe-source.json` – versioned pull, checkpoint,
  provenance and QazLake handoff contract.
- `/.well-known/qazcompute-profiles.json` – executable local profiles and
  safety boundary.
- `/.well-known/qdev-ecosystem.json` – implemented and deferred integrations.
- `/.well-known/source-onboarding.json` – active adapters and gated source
  candidates with admission checks.
- `/site-discovery.json` – public routes, query templates and contracts.
- `/llms.txt` – compact discovery guidance for AI systems.
- `/openapi.json` – executable API contract.
- `/opportunities` - read-only, paginated public JSON data plane.
- `/opportunities.ndjson` - filtered, cache-aware full stream for data consumers.
- `/opportunities.ndjson?compact=true` - lighter bulk stream for AI discovery.
- `/api/v1/insights` – deterministic catalogue distributions and field coverage.
- `/api/v1/changes` – semantic observation history.
- `/media/v1/digest/daily.json` – daily new and changed records with an
  explicit delivery boundary.

## Data ownership

QAZ.FUND owns source adapters, schedules, product taxonomy, Kazakhstan fit,
editorial summaries and publication decisions. QazStack owns reusable neutral
contracts. QazPipe owns cross-product transport and ingestion orchestration.
QazLake owns archived evidence and analytical persistence. QazGeo owns verified
geometry and region identifiers. QazCompute owns heavy or scheduled reusable
computations. AV DS owns visual primitives and semantic UI roles.

Private operator credentials, saved user selections and internal refresh tokens
must never enter the public feed. Public records sent downstream retain at least
`source`, `source_url`, `discovered_at` and `raw.provenance`. The provenance
contract is documented in [`DATA_PROVENANCE_CONTRACT.md`](DATA_PROVENANCE_CONTRACT.md).

Application draft text stays in browser storage. It is not a QazLake record,
QazPipe payload or QazCompute task. Telegram delivery is disabled by default
and cannot create its own scheduler.

## Development pipeline

1. A source adapter is implemented and tested in QAZ.FUND.
2. The parser output is validated against the released QazStack source contract.
3. Product-specific scoring and localization remain local; neutral URL
   canonicalization and text cleanup come from the pinned QazStack release.
4. Public API, discovery contracts and production smoke are updated together.
5. QazPipe ingestion is enabled only with a dry run, idempotency proof and a
   named QazLake record contract.
6. Reusable computation moves to QazCompute only through versioned task-profile
   envelopes. `evidence_readiness.v1`, `deadline_anomaly.v1`,
   `source_freshness.v1` and `duplicate_cluster.v1` are now exposed through
   deterministic local fallbacks that match the QazCompute result shape; remote
   execution still requires fixture parity and a private server-side sync path.
7. New visual patterns use AV DS 4 component families; a local SSR exception is
   documented instead of forking React source.
8. Candidate sources remain outside the public opportunity feed until the
   source-onboarding contract is satisfied.

## Next safe integrations

### QazPipe and QazLake

The producer side is complete at `/.well-known/qazpipe-source.json`. A QazPipe
consumer should pull `/api/v1/opportunities.ndjson`, checkpoint the dataset
revision and offset, and deduplicate by record ID plus
`provenance.content_hash`. The first archive must contain only public records
and provenance. Do not enable a QazLake write until the target table, retention
policy, dry-run artifact, idempotency proof and rollback procedure have owner
approval.

### QazCompute

The enabled contracts are:

- `evidence_readiness.v1` in API responses as
  `raw.qazcompute_evidence_readiness`;
- `deadline_anomaly.v1` in API responses as
  `raw.qazcompute_deadline_anomaly`;
- `source_freshness.v1` in `/coverage` source rows as
  `qazcompute_source_freshness`.
- `duplicate_cluster.v1` at `/opportunities/duplicate-candidates` as a
  review-only candidate queue.
- `provenance.v1` in public opportunity payloads as `raw.provenance`; this
  distinguishes parser observation from explicit source verification and keeps
  field-level confidence visible to downstream consumers.

All four keep `decision_ready=false`; they are technical review signals, not
legal eligibility, publication, funding or source-control decisions.
Keep request/response fixtures in both repositories. QAZ.FUND must degrade to
its local deterministic implementation when QazCompute is unavailable.

### QazGeo

First normalize region identifiers against QazGeo. Add map UI only after records
carry verified coordinates or an authoritative region geometry reference. A map
must help users find regional programs; it must not infer locations from prose.

### EdPol and other consumers

Start with read-only query templates and record which tags each consumer uses.
If multiple products need the same audience/theme mapping, promote that mapping
to a versioned QazStack contract rather than adding product-to-product imports.

## Release gates

- Full QAZ.FUND tests, lint and type checks pass.
- Strict QazStack consumer validation passes from the installed wheel.
- Production smoke verifies the ecosystem, AVDS4, notification, QazStack and
  source-onboarding `/.well-known/` contracts.
- QazStack registry probes are added only after the public endpoints are live.
- Platform catalog status changes only from runtime evidence, never from this
  document alone.
