# QazStack consumer release – 2026-07-15

## Purpose

QAZ.FUND consumes a narrow, released QazStack primitive without making its
source collectors, product relevance policy or public site dependent on a
GitHub checkout during container builds.

## Runtime dependency

- Release: `qazstack v1.37.2`.
- Artifact: `vendor/qazstack-1.37.2-py3-none-any.whl`.
- Integrity manifest: `vendor/qazstack-1.37.2.sha256`.
- Install paths: `requirements.txt`, `requirements-prod.txt`, `Dockerfile`,
  and `Dockerfile.prod`.

`tests/test_qazstack_bridge.py` proves that the installed module is imported
from `site-packages`, not from a copied `qazstack/` source directory.

## Boundary

QazStack owns product-neutral opportunity/source contracts, source URL and
content normalization, evidence-state projection, ranking composition and
machine-export helpers. QAZ.FUND owns all collection adapters, source
schedules, editorial copy, Kazakhstan/Central Asia relevance rules, weights,
exclusions and publication decisions.

The adopted runtime surfaces and deferred primitives are recorded in
`docs/QAZSTACK_ADOPTION_2026-07-15.md`.

## Why the wheel is in the repository

The QazStack repository is private and the QAZ.FUND production host currently
has no read token, deploy key or private package registry. A checked-in,
checksum-verified release wheel makes the image reproducible without exposing
credentials or requiring network access during `docker build`.

Replace this delivery method only after a private package registry or a
read-only deploy credential is available. The replacement must preserve the
same release pin, checksum verification and integration test.
