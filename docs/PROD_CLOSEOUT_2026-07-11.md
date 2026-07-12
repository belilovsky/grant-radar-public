# QAZ.FUND production closeout – 2026-07-11 / 2026-07-12 update

## Scope

Final production pass after the QazStack primitive bridge, operator UI cleanup
and public launch hardening work.

## Deployed revision

- Branch: `codex/qazfund-audit-pass-2026-07-07`
- Current deployed commit: `848372a0507c87527df20d6c2faa0f16b9d6a78a`
- Host path: `/opt/grant-radar`
- Public URL: `https://qaz.fund/`

## Runtime proof

Production smoke:

```text
status: ok
base_url: https://qaz.fund
health_items: 770
ready_backend: database
coverage_sources: 23
coverage_relevant_open_items: 121
coverage_stale_sources: 1
coverage_unknown_freshness_sources: 0
opportunities: 121
digest_items: 5
forbidden_hits: []
```

QazStack bridge proof inside the production API container:

```text
1.6.1 GeoFitResult True True True
```

Container state after deploy:

```text
grant-radar-api-1      Up (healthy)
grant-radar-db-1       Up (healthy)
grant-radar-redis-1    Up (healthy)
grant-radar-worker-1   Up
```

## Live route checks

```text
https://qaz.fund/                                             200
https://qaz.fund/?lang=en                                     200
https://qaz.fund/docs                                         200
https://qaz.fund/ready                                        200
https://qaz.fund/llms.txt                                     200
https://qaz.fund/site-discovery.json                          200
https://qaz.fund/opportunity/3f53feca-a953-5c0a-9648-77967cafbc48 200
https://qaz.fund/funder/dod-amraa                             302 -> /?lang=ru&q=DOD-AMRAA
```

## Browser/UI checks

Checked live with Playwright:

- desktop home: opportunities, funders, sources and data status render after JS load;
- mobile home at 390px: no horizontal overflow, 8 opportunity cards rendered;
- fold-like width at 674px: no horizontal overflow, 8 opportunity cards rendered;
- opportunity detail page: no horizontal overflow, no editorial placeholder markers;
- funder profile page: no horizontal overflow, no editorial placeholder markers;
- browser console: no errors or warnings on checked pages.

## QazStack integration state

QAZ.FUND now uses the shared opportunity contract through a deployment-safe
vendored snapshot:

- `qazstack/opportunities/models.py`
- `qazstack/opportunities/geofit.py`
- `core/qazstack_bridge.py`
- `core/geofit.py`

The vendored snapshot is intentionally small and dependency-free. Production
Docker builds do not require private GitHub credentials.

## Local gates

```text
PYTHONPATH=. .venv/bin/pytest -q  -> 375 passed
make lint                         -> black/isort/flake8/mypy passed
```

## Remaining non-blockers

- The opportunity detail page can still be improved editorially by shortening
  very long official source text, but it is readable and not a runtime blocker.
- Source/funder lists intentionally show a limited first slice on the public
  page; full API/data access remains available through the public endpoints.

## 2026-07-12 follow-up

- UI loading states were hardened so source blocks do not show an unavailable
  message before `/coverage` finishes.
- Opportunity Desk was expanded from the main RSS feed to main, grants,
  fellowships and competitions feeds, while preserving link-level dedupe.
- Opportunity Desk roundup posts such as monthly lists of scholarships and
  fellowships are now filtered out before they reach the applicant-facing feed.
- Final launch plan added: `docs/FINAL_LAUNCH_PLAN_2026-07-12.md`.

## 2026-07-13 product-workbench follow-up

- Search now tolerates common Russian/English synonyms and one-character
  typing errors without calling an external model.
- Saved opportunities have a local work stage: review, fit, preparation,
  submitted and result. `Моя работа` isolates those cards without requiring an
  account or sending applicant data to the server.
- Mobile filters collapse into one disclosure below 760px; desktop keeps the
  full workbench visible.
- `/coverage` exposes explicit source freshness counts. The token-protected
  `/operator/health` route combines stale-source evidence with recent run
  failures for operators.
- A production-only admin token is configured on the VPS; its value is not
  stored in Git or printed in the closeout. The protected route reports 22
  fresh sources and one source requiring attention at closeout time.
- PostgreSQL no longer receives the full `.env.prod` payload. Its production
  container gets only the explicitly declared `POSTGRES_*` variables, so an
  unrelated API secret change no longer forces a database recreation.
- Opportunity JSON exposes `raw.decision_readiness`, listing which deadline,
  amount, eligibility and application fields are known or missing.
- The hero's catalog metric remains the global relevant-open count when the
  user searches or filters; the match count changes only inside the catalog.
- Live Playwright verification passed at 1440px and 390px: no horizontal
  overflow, mobile filter disclosure closed by default, saved workflow stage
  persisted, typo search returned results, and the console had no errors.

### Deliberate boundaries

- Server accounts, shared pipelines and email notifications are not simulated;
  they require an approved authentication/privacy/retention design.
- Kazakh UI is not published partially. It requires a complete translation and
  native-language review; no configured DeepSeek key was available for this
  pass.

## 2026-07-13 top-product follow-up

- Large responses now use standard gzip negotiation. The full compact catalog
  transferred at roughly 65 KB instead of 480 KB in the production check.
- `Экспорт` groups CSV, deadline calendar and workspace backup tools, leaving
  only the three primary work actions visible on mobile.
- A versioned workspace backup exports and restores saved views, saved cards
  and application stages. Import validates shape, limits record counts and
  ignores unknown workflow states before writing local storage.
- The detail drawer now explains data completeness from
  `raw.decision_readiness`, for example `3 of 4` with the exact field that still
  needs verification at the official source.
- The drawer has dialog semantics, keyboard focus containment, background
  inertness, Escape close and focus restoration. A closed drawer is no longer
  exposed in the accessibility tree.
- Live browser proof covered backup download/upload round-trip, detail focus,
  completeness text and a 390px layout with zero horizontal overflow and no
  console errors.
