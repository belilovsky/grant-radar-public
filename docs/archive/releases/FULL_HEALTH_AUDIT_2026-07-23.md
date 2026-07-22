# Full Health Audit 2026-07-23

## Scope

- Repository: `grant-radar-public` (main branch)
- Related local repositories in scope: `grant-radar`, `grant-radar-ops`
- Production endpoint: `https://qaz.fund`

## Verification results for `grant-radar-public`

- Branch: `main`
- Working tree: clean
- Local HEAD: `ddf1dda0d93de93301350f8a73cbfc1958be3e41`
- Remote HEAD (`origin/main`): `ddf1dda0d93de93301350f8a73cbfc1958be3e41`
- GitHub CLI availability: not installed in environment (`gh` command missing)

### Static checks

- `make lint` passed
- `make ci-fast` passed (`449 passed in 6.97s`)
- `pip check` passed

### Production checks

- `scripts.production_smoke --base-url https://qaz.fund` passed
- Release marker: `/.well-known/release.json` revision `ddf1dda0d93de93301350f8a73cbfc1958be3e41`
- `.well-known/avds-ui-contract.json`, `.well-known/qazstack-consumer.json`, `.well-known/qdev-ecosystem.json` present

### Documentation and workflow hygiene

- `README.md`, `DEPLOYMENT.md`, `docs/PRODUCTION_CHECKLIST.md` align with current production entry points and contract artifacts
- CI workflow exists at `.github/workflows/verify.yml` and runs `make lint` + `pytest`

### Related local repository hygiene notes

- `grant-radar` is not clean:
  - Dirty files: `.env.example`, `DEPLOYMENT.md`, `api/main.py`, `core/db.py`, `tests/test_api_repository.py`
  - It is on feature branch `codex/grant-radar-robots-head-2026-06-14`
- `grant-radar-ops` is not clean:
  - Untracked file: `.mcp.json`
  - It is on `main` with clean branch status otherwise

## Open risk and action items

1. Close the local repo hygiene drift in `grant-radar` and `grant-radar-ops` before claiming a global multi-repository finish.
2. Keep `main` on all repos clean before any further cross-repo release decisions.
3. Continue periodic production proof after each content or UI pass.
