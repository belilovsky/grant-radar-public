# QAZ.FUND production readiness – 2026-07-27

## Scope

This release finishes the AVDS and QazStack exchange pass, adds a world
benchmark for comparable grant and opportunity systems, and introduces the
first public “decision check” block on opportunity pages.

The product boundary is unchanged: QAZ.FUND helps users find a relevant
program, inspect source evidence and prepare the next step. It does not accept
applications, confirm legal eligibility or predict approval.

## Release candidate

- Repository: `grant-radar-public`
- Branch: `codex/qazfund-completion-2026-07-26`
- Application candidate revision: `be1decd8e6d206e2f965d05581270234b8944bee`
- Release evidence revision: docs-only commits after the application candidate
  do not change runtime code; use `git rev-parse HEAD` immediately before
  production deploy as the exact revision for public verification.
- Public URL expected after deploy: `https://qaz.fund`
- Host path expected by deploy helper: `/opt/grant-radar`

## Delivered changes

- AVDS exchange documented in `docs/AVDS_EXCHANGE_2026-07-22.md`.
- QazStack exchange documented in `docs/QAZSTACK_EXCHANGE_2026-07-27.md`.
- Global benchmark and product extension priorities documented in
  `docs/WORLD_BENCHMARK_2026-07-27.md`.
- Opportunity pages now show “Проверка перед решением” / “Decision check”
  before the preparation route.
- The new block keeps the legal boundary explicit: it lists what QAZ.FUND can
  check and what the user must verify at the official source.

## Verification

Local checks passed on the candidate revision:

```text
make lint
.venv/bin/python -m pytest -q
```

Result:

```text
460 passed
```

Repository hygiene:

```text
git status --short
```

Result: clean working tree before production handoff.

Editorial hygiene checked for the touched product layer:

Result: no em dash hits in the checked QAZ.FUND application, docs and tests
scope.

## Production deployment status

The production helper is ready and intentionally refuses unsafe releases:

```bash
DEPLOY_HOST=<private-ssh-target> \
PUBLIC_URL=https://qaz.fund \
bash scripts/deploy_qaz_fund.sh
```

The helper requires both the private SSH target and public revision verification
through `/.well-known/release.json?revision=<git-sha>`. In the current Codex
environment `DEPLOY_HOST` is not configured in the repository or process
environment, and the shell cannot resolve external hosts. Because the SSH target
is not present, the QAZ.FUND production deploy was not executed from this
session.

Do not mark this release as publicly deployed until the command above verifies
the exact candidate revision on `https://qaz.fund`.
