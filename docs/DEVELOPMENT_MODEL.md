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

## Working rule

Treat `grant-radar-public` as the product source of truth. Do not maintain a
parallel code history in the ops repository.
