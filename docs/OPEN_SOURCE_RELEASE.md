# Open Source Release Notes

This repository can be published safely only after separating the public source
tree from private deployment history.

## Current audit result

- The current working tree is public-safe after the June 2026 cleanup pass.
- The private git history is not automatically public-safe.
- Historical commits included tracked `.env.dev`, `.env.staging`, and
  `.env.prod` files.
- Historical commits also included operator-oriented deployment details such as
  live hosts, cutover notes, and private infrastructure references.

## Safe publication options

### Option A: create a fresh public repository

Recommended default.

1. Start a new repository from the current cleaned working tree.
2. Keep only the current public-safe files and a fresh commit history.
3. Reconnect CI, issue tracker, and contributor docs there.
4. Keep the old private repository as the operator/source-of-truth archive.

This is the lowest-risk path when older private history may contain secrets or
host inventory.

### Option B: rewrite the existing private repository history

Use this only if preserving issue links, stars, or the exact repository URL is
important.

1. Remove `.env.dev`, `.env.staging`, `.env.prod`, and any private runbook
   material from all commits.
2. Purge host/IP references and operator-only backup paths from history.
3. Force-push the rewritten history.
4. Rotate any credential that may have appeared in old commits before making
   the repository public.

This path is riskier because mistakes in history rewriting are easy to miss.

## Publication checklist

- `make lint`
- `make ci-fast`
- confirm `.env*` files are ignored and untracked
- review deployment docs for placeholders only
- review GitHub Actions for public execution
- rotate any credential that ever appeared in private history

## Recommendation

Prefer a new public repository created from the current cleaned tree, then keep
operator inventory, production host details, and incident history in a
separate private repository or private docs store.
