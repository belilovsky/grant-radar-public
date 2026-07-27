# QAZ.FUND production closeout – 2026-07-27

## Scope

This release closes the AVDS, QazStack, editorial and source-expansion pass for
QAZ.FUND. It adds the opportunity decision-check block and seven strategic
official watch sources for higher-quality grant, procurement, scholarship and
partner-call discovery.

## Public topology

- Public URL: `https://qaz.fund`
- Edge nginx host: `root@148.230.117.131`
- Runtime backend: `root@187.55.228.239:/opt/grant-radar`
- Backend service: Docker Compose project `grant-radar`
- Public release endpoint:
  `https://qaz.fund/.well-known/release.json`

The edge nginx host proxies `qaz.fund` to the backend host. Deploying only to
`148.230.117.131:/opt/grant-radar` updates a healthy local copy, but it does
not update the public route. The production deploy target for this release is
`root@187.55.228.239:/opt/grant-radar`.

## Delivered product changes

- AVDS exchange completed and documented.
- QazStack exchange completed on QazStack `1.41.2`.
- Opportunity detail pages include “Проверка перед решением” / “Decision
  check”.
- World benchmark added for comparable grant, procurement and opportunity
  systems.
- Seven strategic official watch sources added:
  - `ungm_opportunities`
  - `osce_procurement`
  - `iom_kazakhstan_procurement`
  - `edb_procurement`
  - `daad_central_asia`
  - `gef_sgp_kazakhstan`
  - `global_innovation_fund`

## Verification before production deploy

Local verification passed:

```text
make lint
.venv/bin/python -m pytest -q
```

Results:

```text
463 passed
```

Targeted source checks passed:

```text
tests/test_source_expansion.py
tests/test_sources.py
tests/test_integration_m2.py
```

Result:

```text
92 passed
```

## Production deploy proof

Initial app deploy target:

```text
root@148.230.117.131:/opt/grant-radar
```

That host built and ran the new containers, but public revision verification
failed because nginx proxies `qaz.fund` to `187.55.228.239:18610`.

Final production deploy target:

```text
root@187.55.228.239:/opt/grant-radar
```

The public release endpoint verified the deployed revision:

```text
Public revision verified at https://qaz.fund:
5b7b504e2cae49a209768943ff09dd00f4167049
```

Runtime state after deploy:

```text
grant-radar-api-1      Up (healthy)   127.0.0.1:18611->8000/tcp
grant-radar-db-1       Up (healthy)   127.0.0.1:5432->5432/tcp
grant-radar-worker-1   Up             8000/tcp
```

Public readiness:

```json
{"status":"ok","backend":"database","items":916}
```

Production smoke:

```text
status: ok
release_revision: 5b7b504e2cae49a209768943ff09dd00f4167049
health_items: 916
ready_backend: database
coverage_sources: 33
coverage_relevant_open_items: 115
coverage_stale_sources: 0
coverage_unknown_freshness_sources: 0
opportunities: 119
ndjson_items: 20
digest_items: 5
forbidden_hits: []
```

All seven new source slugs are present in public `/sources`.

## Remaining watch items

- UNGM and OSCE are currently official watch sources. The next useful step is
  item-level parsing by official API or stable form-backed extraction.
- `gef_sgp_kazakhstan` can return CDN-level `403` from automated fetches. The
  adapter keeps the official source visible and records `blocked_fetch`.
- `global_innovation_fund` is intentionally marked as `future_watch`, not an
  open call, until the official source publishes a new application window.
