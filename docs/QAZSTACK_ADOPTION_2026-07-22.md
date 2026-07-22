# QazStack 1.40 adoption - 2026-07-22

## Change

QAZ.FUND now consumes the checksum-pinned `qazstack-1.40.0-py3-none-any.whl`
built from the published `v1.40.0` tag at
`a0a4bfc6ea6b2fce205afe24fbf732fb3de3bc68`.

The product removes its duplicate `core/opportunity_intelligence.py` module
and imports these deterministic, product-neutral lifecycle helpers directly
from `qazstack.opportunities`:

- `is_rolling_item` for priority scoring;
- `normalized_opportunity_status` for the API projection;
- `public_lifecycle` for catalog, funder and filter views.

## Boundaries

This release changes implementation ownership, not QAZ.FUND policy. Relevance
and priority weights, Kazakhstan and Central Asia fit rules, source behavior,
localization and publication decisions remain product-owned.

## Verification

The QazStack `v1.40.0` source suite completed with `1600 passed, 19 skipped`.
QAZ.FUND verifies the wheel checksum, imports the package from `site-packages`
and asserts that no local lifecycle copy remains. Public smoke continues to
require the runtime consumer contract to expose `qazstack_version: 1.40.0`.
