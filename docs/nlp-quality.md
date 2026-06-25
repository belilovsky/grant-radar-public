# NLP / NER quality workflow

Grant Radar uses two layers for text quality:

1. deterministic QA helpers in `core/nlp.py`;
2. optional DeepSeek enrichment through `scripts/deepseek_enrich_content.py`.

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

## DeepSeek dry-run

Use this when `DEEPSEEK_API_KEY` is available in the runtime environment:

```bash
PYTHONPATH=. ./.venv/bin/python -m scripts.deepseek_enrich_content \
  --limit 20
```

Without provider credentials, verify DB access and rule-based enrichment only:

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

To replace Russian summaries from DeepSeek output, add `--apply-summary`:

```bash
PYTHONPATH=. ./.venv/bin/python -m scripts.deepseek_enrich_content \
  --limit 50 \
  --apply \
  --apply-summary
```

Use `--apply-summary` in small batches and rerun `scripts/nlp_quality_audit.py`
after each batch.

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

The next safe step is optional, not a release blocker: run DeepSeek enrichment
in small batches once the `DEEPSEEK_API_KEY` is present in the production
environment, then rerun the audit before applying summaries publicly.
