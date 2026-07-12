# QAZ.FUND production closeout – 2026-07-11

## Scope

Final production pass after the QazStack primitive bridge, operator UI cleanup
and public launch hardening work.

## Deployed revision

- Branch: `codex/qazfund-audit-pass-2026-07-07`
- Deployed commit: `cc6ce1cc7b15dca467afcd3a0cd89e0c8cf4136b`
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
PYTHONPATH=. .venv/bin/pytest -q  -> 367 passed
make lint                         -> black/isort/flake8/mypy passed
```

## Remaining non-blockers

- The opportunity detail page can still be improved editorially by shortening
  very long official source text, but it is readable and not a runtime blocker.
- Source/funder lists intentionally show a limited first slice on the public
  page; full API/data access remains available through the public endpoints.
