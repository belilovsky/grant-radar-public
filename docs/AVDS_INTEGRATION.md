# AV Design System integration

Grant Radar has a server-rendered FastAPI dashboard, so it does not depend on
private `@av-ds/*` packages at runtime. The production-safe contract is a local
adapter in `api/avds.py`.

## Contract

- The root document declares `data-avds="grant-radar"` and
  `data-av-theme="light"`.
- `api/avds.py` exposes the local AV DS token subset used by this dashboard:
  color, spacing, radius, shadow, motion and typography variables.
- The local token subset also includes product-density primitives for this
  operational surface: dashboard container width, compact/regular control
  heights, card padding, section gap and a shared focus ring.
- The adapter follows the AV DS 3.7 token names used in the shared UI kit where
  this static FastAPI surface needs them: `--font-sans`, `--font-serif`,
  `--font-mono`, `--button-outline`, `--badge-outline`, `--shadow-*`,
  `--radius`, `--motion-*`, and semantic border aliases.
- Dashboard CSS maps the local AV DS variables into the shared semantic names
  used by the rest of the QDev ecosystem: `--color-bg`, `--color-surface`,
  `--color-text`, `--color-border`, `--color-accent`, `--color-success`,
  `--color-warning`, and `--color-danger`.
- The dashboard keeps AV DS as a restrained admin surface: `TabsList` /
  `TabsTrigger` tab anatomy, `avds-field`-style inputs, `StatKpiCard`-style
  metric typography, `SourceCard` source rows with the real
  `avds-source-card__icon/body/name/meta/arrow` anatomy, compact document rows,
  visible keyboard focus and a reduced-motion fallback.
- Rendered controls expose `data-avds-component` markers for smoke tests and
  future migration: `admin-shell`, `toolbar`, `button`, `panel`, `metric-card`,
  `field`, `source-card`, `source-icon`, `source-main`, `source-meta`,
  `source-url`, `source-count`, `opportunity-card`, `badge`, `tag`, `score`,
  `health-card`, `sticky-shell`, and `filter-summary`.
- `scripts/production_smoke.py` treats the AV DS shell markers as part of the
  live release gate, so production deploys fail smoke if the rendered page
  loses `data-avds="grant-radar"`, `data-av-theme="light"`, the default
  Russian shell markers, or the current AV DS component markers.

## Why local adapter

This project deploys as a small Python/Docker service on VPS. Pulling private
frontend packages during production deploy would make the service dependent on
registry credentials. The adapter keeps the visual contract aligned with AV DS
while preserving a simple, reproducible Docker build.

If the shared AV DS package becomes available in this deploy environment, the
adapter can be replaced by importing the packaged tokens while keeping the same
semantic variables and `data-avds-component` markers.
