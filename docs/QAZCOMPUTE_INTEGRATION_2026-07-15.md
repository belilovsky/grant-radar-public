# QazCompute opportunity enrichment integration

QAZ.FUND uses `opportunity_enrich.v1` as an optional, operator-controlled
shadow profile. Provider credentials stay in QazCompute; QAZ.FUND receives only
the versioned result contract through a service credential.

Profile source: `belilovsky/qazcompute` commit `08f5eb1` on branch
`codex/qazfund-compute-profile-20260715` (PR #30).

The implementation passes the full local QazCompute suite (141 tests), lint and
format gates. GitHub Actions did not start because of the repository owner's
billing/spending-limit gate. Until hosted CI succeeds and PR #30 is merged,
QAZ.FUND must keep this integration disabled in production.

## Runtime boundary

- QAZ.FUND sends one opportunity at a time to
  `/api/v1/tasks/opportunity-enrich` with `X-Caller: qaz-fund`.
- The response schema, returned opportunity id, runtime status, quality tier,
  provenance and decision-readiness type are validated before metadata is
  accepted.
- Runtime status, provider, model, quality tier, fallback reason, omitted
  capabilities, bounded source evidence and decision readiness are persisted
  with the enrichment.
- Degraded local-rule output may enrich internal audit metadata but does not
  fabricate summaries or semantic entities.
- Public Russian copy can change only when the response contains a non-empty
  summary, bounded source evidence, `available` runtime status, `estimated`
  quality and explicit `decision_ready=true`.

The current QazCompute candidate always reports `decision_ready=false`,
including when an LLM provider is available. Therefore this integration cannot
alter public summaries before its release.

## Operator use

Configure `QAZCOMPUTE_URL` and `QAZCOMPUTE_API_KEY` through the service
environment; the command line intentionally does not accept credentials. Do
not put provider keys in the QAZ.FUND environment. Start with a dry run:

```bash
PYTHONPATH=. ./.venv/bin/python -m scripts.deepseek_enrich_content --limit 20
```

The historical module name remains for runbook compatibility. Use
`--no-provider` to exercise deterministic local metadata without a service
credential. `--apply` persists metadata; `--apply-summary` is still blocked by
the decision gate.

## Promotion checklist

1. Freeze a multilingual benchmark and expected evidence labels.
2. Measure unsupported claims, entity precision and evidence coverage.
3. Record an approved quality threshold and model/version pair.
4. Change the QazCompute quality contract and both repositories' tests.
5. Run a small shadow batch and the QAZ.FUND NLP quality audit.

HTTP success, provider availability or a plausible summary is not promotion
evidence.
