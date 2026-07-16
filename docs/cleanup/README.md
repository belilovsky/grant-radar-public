# Repository cleanup

Current cleanup evidence and deferred legacy decisions live here:

- [`cleanup-audit-2026-07-16.md`](cleanup-audit-2026-07-16.md)
- [`legacy-candidates-2026-07-16.md`](legacy-candidates-2026-07-16.md)

The cleanup policy is conservative: generated caches and proven-unused runtime
components may be removed, while compatibility routes, source-specific parser
rules, migrations, release artifacts and vendored contract packages stay until
their replacement is independently verified.
