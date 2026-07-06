# Contributing

## Local setup

```bash
make bootstrap BOOTSTRAP_PYTHON=python3.12
cp .env.example .env.dev
make dev
```

If your local `python3` still resolves to 3.9 or 3.10, bootstrap will now stop
early with a clear error. Use Python 3.12 explicitly or stay on the Docker
workflow.

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
- Keep deployment inventory, hostnames, backups, and maintainer-only notes out
  of the public repository.

## Scope

Good public contributions usually fit one of these lanes:

- source adapters and parsers
- ranking, dedupe, and normalization
- API and dashboard usability
- tests, fixtures, docs, and local developer experience
