# NLP / NER quality workflow

Grant Radar uses two layers for text quality:

1. deterministic QA helpers in `core/nlp.py`;
2. optional QazCompute enrichment through `scripts/deepseek_enrich_content.py`.

The deterministic layer is intentionally conservative. It extracts coarse
entities for audit and routing:

- support types;
- sectors;
- regions;
- audiences;
- funders.

It also flags visible text problems:

- missing or short summaries;
- English-heavy text on Russian views;
- repeated machine-translation phrases;
- source UI fragments such as `Read more` / `Читать далее`.

## Audit visible public text

```bash
PYTHONPATH=. ./.venv/bin/python -m scripts.nlp_quality_audit \
  --base-url https://qaz.fund \
  --lang ru \
  --limit 250
```

The command exits with code `1` when issues are found. That is expected for QA
runs; inspect the JSON report and treat `latin_heavy_ru_text`,
`missing_cyrillic_ru_text`, `repeated_phrase`, and `short_summary` as content
backlog candidates.

## QazCompute dry-run

Set `QAZCOMPUTE_URL` and the service credential `QAZCOMPUTE_API_KEY`. Provider
credentials remain inside QazCompute and must not be copied into QAZ.FUND.

```bash
PYTHONPATH=. ./.venv/bin/python -m scripts.deepseek_enrich_content \
  --limit 20
```

Without the service credential, verify DB access and rule-based enrichment only:

```bash
PYTHONPATH=. ./.venv/bin/python -m scripts.deepseek_enrich_content \
  --no-provider \
  --limit 20
```

Both commands are dry-runs unless `--apply` is passed.

## Apply enrichment

```bash
PYTHONPATH=. ./.venv/bin/python -m scripts.deepseek_enrich_content \
  --limit 50 \
  --apply
```

This writes `raw.i18n.*.nlp` metadata only. It does not overwrite public Russian
summaries by default.

`--apply-summary` only accepts a response with `decision_ready=true`. Current
model and local-rule profiles are deliberately shadow-only, so public summaries
remain unchanged until a product benchmark promotes the contract.

```bash
PYTHONPATH=. ./.venv/bin/python -m scripts.deepseek_enrich_content \
  --limit 50 \
  --apply \
  --apply-summary
```

Run the audit after each applied batch. Never treat HTTP 200 as proof that the
result is publication-ready; persist and inspect `runtime.quality_tier` and
`runtime.decision_ready`.

## Current production state

The final 2026-06-08 production audit on `https://qaz.fund` is clean:

- `scripts.nlp_quality_audit --base-url https://qaz.fund --lang ru --limit 150`
  checked 145 public Russian cards;
- `issue_count=0`;
- `missing_entity_count=0`;
- no `latin_heavy_ru_text`, repeated phrase, missing summary, or missing entity
  flags were reported;
- a separate source-link/content pass also reported no rootish source URLs and
  no forbidden content hits.

The next safe step is a shadow QazCompute batch. It may enrich internal metadata,
but it cannot replace public summaries until the benchmark gate is recorded.
