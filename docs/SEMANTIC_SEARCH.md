# Semantic search boundary

QAZ.FUND can enrich the existing deterministic catalog search with an
internal-only semantic service. It uses `BAAI/bge-m3` for multilingual dense
retrieval, `BAAI/bge-reranker-v2-m3` to reorder the strongest candidates, and
Qdrant for vector storage.

## What is indexed

The sidecar fetches only the already-public compact NDJSON catalog from the API.
For each record it keeps the stable public UUID and a normalized text built from
the title, summary, funder, type, tags, eligibility and source slug. It does
not receive parser `raw` payloads, source snapshots, credentials or private
operator data. It is not exposed through an edge port.

The public API applies its normal lifecycle, region, source, relevance and
deadline filters before sending an ID allowlist to the sidecar. Returned IDs are
intersected with that allowlist again. A stale vector point therefore cannot
resurrect an inactive, irrelevant or excluded record.

For a query, the API fuses the existing lexical result ranks and semantic ranks
with Reciprocal Rank Fusion (RRF). Exact field matches therefore remain useful,
while BGE-M3 can surface semantically related RU/KZ/EN records that do not share
the same words.

## Runtime behavior

`docker-compose.prod.yml` starts two internal services:

- `qdrant`, with the durable `qdrantdata` volume;
- `semantic`, with a separate `semantic-models` model-cache volume.

The public API talks to `http://semantic:8010` only when
`GRANT_RADAR_SEMANTIC_SEARCH_ENABLED=1`. If the sidecar is warming, unavailable
or returns an invalid response, the API uses the pre-existing lexical search;
there is no public error or broadened result set.

The semantic service reindexes from the public catalog on startup and every
`GRANT_RADAR_SEMANTIC_REINDEX_INTERVAL_SECONDS` (default: six hours). It does
not trigger source crawls. Internal catalog requests retain the canonical
public Host header (`GRANT_RADAR_SEMANTIC_CATALOG_HOST`, default: `qaz.fund`),
so the API's trusted-host boundary stays enabled. A failed initial index is
retried every `GRANT_RADAR_SEMANTIC_STARTUP_RETRY_SECONDS` (default: 15 seconds).
The deploy helper waits for `/health` after the API is ready, unless semantic
search is explicitly disabled in `.env.prod`.

Model snapshots explicitly omit ONNX and OpenVINO exports because this service
loads both models through the PyTorch-only FlagEmbedding runtime. This keeps the
durable model volume from downloading several gigabytes of unused weights.

## Capacity and evaluation gate

BGE-M3's local runtime and reranker need a dedicated model cache and materially
more RAM than the API. The semantic image is deliberately separate from
`Dockerfile.prod`; API workers never load these models.

Before changing ranking policy, assemble a manually judged RU/KZ/EN query set
and compare lexical versus semantic results with Recall@20 and nDCG@10. Keep
the lexical path as fallback until the judged set demonstrates a benefit and
the server has sustained headroom under concurrent API and worker load.

## Document review lane

The optional Docling lane is local and review-only. Install
`requirements-document-review.txt`, then run:

```bash
python -m scripts.extract_document_review \
  --input /path/to/official-notice.pdf \
  --source-url https://official.example.org/notice.pdf \
  --output output/document-review/notice.json
```

It outputs a draft with an HTTPS source URL, document hash and candidate title,
date and amount mentions. It stores no extracted document text, contact details
or images and cannot create a public opportunity. A reviewed source adapter and
the normal publication checks remain required.
