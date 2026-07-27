# QazStack reuse boundary - 2026-07-28

QAZ.FUND adopts QazStack as a packaged Python dependency through the pinned
wheel in `requirements-prod.txt`. The active shared modules are:

- `qazstack.opportunities` for parser/source contract validation;
- `qazstack.source` for canonical source URL fingerprints;
- `qazstack.content` for text normalization and source-diverse digest ordering;
- `qazstack.evidence` for public evidence-state semantics;
- `qazstack.export` for NDJSON machine export.

Grant relevance, Kazakhstan-fit policy, source suitability and scoring remain
product-owned. No local primitive exception is currently approved; future shared
collector, export, observability or AI-discovery work should first extend
QazStack and only remain local with a dated exception in `qazstack-reuse.json`.
