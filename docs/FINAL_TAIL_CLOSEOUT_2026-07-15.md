# QAZ.FUND final-tail closeout – 2026-07-15

## Scope

This release closes the remaining independent code and documentation work after
the final quality audit. It does not include QazCompute PR `#30` or QAZ.FUND
integration PR `#6`; those keep their separate CI and release gate.

## Implemented

- Per-source fetch cycles are persisted in the existing `runs` table, including
  a successful cycle that returns zero records.
- `/coverage`, `/status`, and operator health distinguish the latest successful
  check from the latest discovered record without exposing run errors publicly.
- Scheduler-owned parser clients are closed on one-shot and long-running paths;
  one close failure does not prevent the remaining clients from closing.
- Dashboard copy and static CSS are separated from render/interaction logic.
- QazStack wheel runtime dependencies are explicitly pinned.
- The complete backlog and the conditions for deferred product work are recorded
  in `REMAINING_WORK_PLAN_2026-07-15.md`.

## Render parity

The dashboard was rendered before and after decomposition with identical input:
`items=831`, `relevant_items=155`, `source_count=26`, and
`site_origin=https://qaz.fund`.

| Language | Bytes | SHA-256 before and after |
| --- | ---: | --- |
| RU | 297190 | `e3c4d59726a6fc832b06abbb51950182acc15920b9cc73e95d31348f303538c1` |
| EN | 296102 | `d3e155693986981e673593048a1cfef7edff07be6a407781721f9f6532e1275d` |

## Local verification

- Black, isort, Flake8: passed for 102 files.
- mypy: passed for 65 source files.
- pytest: `419 passed`, one upstream Starlette TestClient deprecation warning.
- `compileall`: passed.
- Clean installation from `requirements.txt`: passed.
- `pip check`: no broken requirements.
- `pip-audit`: no known vulnerabilities; private vendored QazStack is not on
  PyPI and is covered by the checked checksum and integration tests.
- QazStack 1.37.2 SHA-256: passed.
- Shell syntax, documentation links, and `git diff --check`: passed.

## Browser verification

The local app was checked in a real Chromium session at 1440x1000 and 390x844.
The RU dashboard and `/status` rendered without browser warnings or errors. The
mobile filter surface, empty state, source summary, responsive status table, and
new source-check wording remained readable without horizontal page overflow.

Screenshots are local ignored artifacts under `output/playwright/`; they are not
release inputs and are not committed.

## Release state

Pull request `#16` passed GitHub Actions and was merged as
`bcd81456bbf91ab3b82af319260cbdd4ce0cce66`.

The documented conservative deploy completed without `rsync --delete` at
`2026-07-15T17:51:42Z` on the application origin. The public TLS/edge host and
the application origin are separate infrastructure roles; their private
addresses remain outside this public repository.

Production verification through `https://qaz.fund`:

- API, PostgreSQL, and Redis: healthy; worker: running.
- Readiness backend: `database`; indexed records: 831.
- Sources: 26 fresh, 0 stale, 0 with unknown freshness.
- Relevant open opportunities: 155; NDJSON sample: 20; digest: 5.
- Content audit: 155 opportunities, 0 issues.
- NLP audit: 150 RU and 150 EN records, 0 issues.
- Dashboard, status, API/discovery, QazStack, AV DS 4, and ecosystem contracts:
  passed.
- Chromium at 1440x1000 and 390x844: no console errors or warnings.

The release exposed one operational gap: readiness on a target host did not
prove that the public reverse proxy actually used that host. The follow-up
release adds exact public revision attestation to the deploy gate.
