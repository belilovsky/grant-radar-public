# Contributing

## Local setup

```bash
make bootstrap
cp .env.example .env.dev
make dev
```

Main local surfaces:

- API: `http://localhost:8000`
- PostgreSQL: `localhost:5434`
- Redis: `localhost:6380`

## Before opening a PR

Run:

```bash
make lint
make ci-fast
```

Use `make ci` if you want the docker-based validation pass too.

## Environment rules

- Never commit `.env`, `.env.dev`, `.env.staging`, or `.env.prod`.
- Use `.env.example` as the tracked template.
- Keep deployment inventory, hostnames, backups, and operator-only notes out of
  the public repository.

## Scope

Good public contributions usually fit one of these lanes:

- source adapters and parsers
- ranking, dedupe, and normalization
- API and dashboard usability
- tests, fixtures, docs, and local developer experience
