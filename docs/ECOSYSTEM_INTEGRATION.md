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
| QazStack 1.37.2 | `runtime-proven` | QAZ.FUND uses neutral contracts, source/content normalization, evidence states, diversified listing and machine-export helpers. Product relevance policy stays local. |
| AV DS 4.3.2 | `adapter-aligned` | FastAPI pages use a local SSR adapter mapped to AV DS component families. No React package import is claimed. |
| QazPipe | `interface-ready` | QazPipe can pull the public `/opportunities` API with stable pagination and provenance. Activation remains consumer-controlled. |
| QazLake | `brokered-via-qazpipe` | Public records may be archived through QazPipe. QAZ.FUND never writes directly into QazLake tables. |
| EdPol | `query-ready` | Education opportunities are available through the public tag-filtered API. EdPol decides whether and how to consume them. |
| QazGeo | `deferred-no-geometry` | Region classes exist, but verified coordinates do not. No inferred or decorative map is published. |
| QazCompute | `candidate-not-enabled` | Suitable batch jobs are identified, but no remote compute is claimed until parity and fallback tests exist. |

## Machine entry points

- `/.well-known/qazstack-consumer.json` – strict QazStack production contract.
- `/.well-known/avds-ui-contract.json` – AV DS 4 component-family boundary.
- `/.well-known/qdev-ecosystem.json` – implemented and deferred integrations.
- `/site-discovery.json` – public routes, query templates and contracts.
- `/llms.txt` – compact discovery guidance for AI systems.
- `/openapi.json` – executable API contract.
- `/opportunities` - read-only, paginated public JSON data plane.
- `/opportunities.ndjson` - filtered, cache-aware stream for AI and data consumers.

## Data ownership

QAZ.FUND owns source adapters, schedules, product taxonomy, Kazakhstan fit,
editorial summaries and publication decisions. QazStack owns reusable neutral
contracts. QazPipe owns cross-product transport and ingestion orchestration.
QazLake owns archived evidence and analytical persistence. QazGeo owns verified
geometry and region identifiers. QazCompute owns heavy or scheduled reusable
computations. AV DS owns visual primitives and semantic UI roles.

Private operator credentials, saved user selections and internal refresh tokens
must never enter the public feed. Public records sent downstream retain at least
`source`, `source_url` and `discovered_at`.

## Development pipeline

1. A source adapter is implemented and tested in QAZ.FUND.
2. The parser output is validated against the released QazStack source contract.
3. Product-specific scoring and localization remain local; neutral URL
   canonicalization and text cleanup come from the pinned QazStack release.
4. Public API, discovery contracts and production smoke are updated together.
5. QazPipe ingestion is enabled only with a dry run, idempotency proof and a
   named QazLake record contract.
6. Reusable computation moves to QazCompute only after fixture parity proves
   that local fallback and remote execution produce equivalent results.
7. New visual patterns use AV DS 4 component families; a local SSR exception is
   documented instead of forking React source.

## Next safe integrations

### QazPipe and QazLake

Create a QazPipe pull connector against `/opportunities` with checkpointed
`offset`, source URL idempotency and dry-run output. The first archive should
contain only public records and provenance. Do not enable a production write
until the target QazLake schema and retention policy have owner approval.

### QazCompute

The first candidates are cross-source duplicate clustering, deadline anomaly
detection and source-freshness scoring. Keep request/response fixtures in both
repositories. QAZ.FUND must degrade to its local deterministic implementation
when QazCompute is unavailable.

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
- Production smoke verifies all three `/.well-known/` documents.
- QazStack registry probes are added only after the public endpoints are live.
- Platform catalog status changes only from runtime evidence, never from this
  document alone.
