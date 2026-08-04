# QAZ.FUND production closeout – source onboarding.v1

## Release identity

- Checkout: `/Users/belilovsky/Documents/Codex/2026-05-21/grant-radar-public`
- Branch: `codex/qaz-fund-reuse-boundary-20260728`
- Runtime: `root@148.230.117.131:/opt/grant-radar`
- Public domain: `https://qaz.fund`
- Deployed revision: `d06f0f64a5e67986d484f5447705abb259b574e3`

## Delivered slice

`/.well-known/source-onboarding.json` (`source-onboarding.v1`) now publishes a
machine-readable boundary for source expansion. It reports the 26 active
runtime adapters and keeps four future surfaces explicit:

- OpenAlex – candidate secondary research context;
- data.egov.kz – gated until API key, license and dataset selection are
  approved;
- UNGM – gated until official OAuth/API access and reuse terms are approved;
- U.S. Embassy Central Asia pages – deferred until a stable item-level listing
  is confirmed.

The contract contains no keys, tokens, private responses or operator notes. It
does not promote a candidate into the public opportunity feed. The admission
checks and ownership boundary are documented in
[`SOURCE_ONBOARDING_CONTRACT.md`](../../SOURCE_ONBOARDING_CONTRACT.md).

The endpoint is linked from `site-discovery.json`, `llms.txt`, the QDev
ecosystem manifest and the production smoke gate.

## Verification

- `PYTHONPATH=. .venv/bin/pytest -q`: **486 passed**.
- `make lint`: passed (Black, isort, flake8, mypy, vulture).
- `git diff --check`: passed before release.
- `make smoke-prod`: passed on the second run after the container warm-up;
  26 sources, 393 relevant open cards, 0 stale sources, 0 unknown-freshness
  sources, 5 digest items, all discovery and ecosystem markers green.
- `make content-audit`: passed with no issues.
- Public release marker: `d06f0f64a5e67986d484f5447705abb259b574e3`.
- Public onboarding payload: `active.count=26`, no public credentials, and
  expected `candidate`, `gated` and `deferred` statuses.

## Next gate

The next implementation may build an OpenAlex enrichment adapter only as a
separate context layer. UNGM and data.egov.kz require explicit access and
reuse approval first; no page scraping workaround is authorized.
