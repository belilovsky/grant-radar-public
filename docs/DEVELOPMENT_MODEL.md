# Development Model

`grant-radar-public` is the primary development repository for the project.

Use this repository for:

- feature work
- bug fixes
- tests and migrations
- contributor-facing documentation
- public-safe deployment contracts

The separate private repository `grant-radar-ops` exists only for maintainer
context that should not live in the public codebase, such as internal cleanup
history, non-public release notes, and private operational reference material.

If you still have an older local checkout named `grant-radar`, treat it as a
legacy transition repository only. Do not continue feature work there.

## Working rule

Treat `grant-radar-public` as the product source of truth. Do not maintain a
parallel code history in the ops repository.
