"""Internal BGE-M3 + Qdrant semantic search service.

This process is intentionally not published at the edge.  It periodically
reads QAZ.FUND's already-public compact catalog, embeds that limited projection,
and returns UUID rankings to the API.  It never fetches source pages or stores
the raw parser payloads.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import Sequence
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock
from typing import Any
from uuid import NAMESPACE_URL, uuid5

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from semantic_service.catalog import public_search_documents

logger = logging.getLogger(__name__)

COLLECTION_NAME = "qazfund-public-opportunities-v1"
EMBEDDING_MODEL = "BAAI/bge-m3"
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
VECTOR_SIZE = 1024


def _positive_int(name: str, default: int, *, maximum: int) -> int:
    try:
        return min(maximum, max(1, int(os.environ.get(name, str(default)))))
    except ValueError:
        return default


def _catalog_url() -> str:
    return os.environ.get(
        "GRANT_RADAR_SEMANTIC_CATALOG_URL",
        "http://api:8000/opportunities.ndjson?compact=true&limit=5000",
    ).strip()


def _catalog_host() -> str:
    return os.environ.get("GRANT_RADAR_SEMANTIC_CATALOG_HOST", "qaz.fund").strip()


def _qdrant_url() -> str:
    return os.environ.get("QDRANT_URL", "http://qdrant:6333").strip()


@dataclass
class ServiceState:
    backend: "BgeM3QdrantBackend | None" = None
    indexed_at: datetime | None = None
    indexed_documents: int = 0
    index_error: str = ""
    index_lock: Lock = field(default_factory=Lock)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=200)
    allowed_ids: list[str] = Field(min_length=1, max_length=5000)
    limit: int = Field(default=50, ge=1, le=5000)


class SearchItem(BaseModel):
    id: str
    score: float
    retrieval_score: float
    reranker_score: float | None = None


class SearchResponse(BaseModel):
    model: str
    reranker_model: str
    index_updated_at: datetime
    items: list[SearchItem]


class BgeM3QdrantBackend:
    """Lazy model holder; heavyweight packages load only in this sidecar."""

    def __init__(self) -> None:
        try:
            from FlagEmbedding import BGEM3FlagModel, FlagReranker
            from qdrant_client import QdrantClient, models
        except ImportError as exc:  # pragma: no cover - exercised in container
            raise RuntimeError(
                "semantic dependencies are unavailable; install requirements-semantic.txt"
            ) from exc
        self._models = models
        self._client = QdrantClient(url=_qdrant_url(), timeout=15)
        self._embedding = BGEM3FlagModel(
            EMBEDDING_MODEL,
            use_fp16=False,
        )
        self._reranker = FlagReranker(RERANKER_MODEL, use_fp16=False)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        if self._client.collection_exists(COLLECTION_NAME):
            return
        self._client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=self._models.VectorParams(
                size=VECTOR_SIZE,
                distance=self._models.Distance.COSINE,
            ),
        )

    def _vectors(self, texts: Sequence[str]) -> list[list[float]]:
        encoded = self._embedding.encode(
            list(texts),
            batch_size=8,
            max_length=2048,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False,
        )
        dense = encoded.get("dense_vecs")
        if dense is None:
            raise RuntimeError("BGE-M3 returned no dense vectors")
        return [vector.tolist() for vector in dense]

    def index(self, documents: Sequence[dict[str, str]]) -> int:
        if not documents:
            return 0
        vectors = self._vectors([document["text"] for document in documents])
        points = [
            self._models.PointStruct(
                id=_point_id(document["id"]),
                vector=vector,
                payload={"id": document["id"], "text": document["text"]},
            )
            for document, vector in zip(documents, vectors, strict=True)
        ]
        self._client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
            wait=True,
        )
        return len(points)

    def search(
        self,
        query: str,
        *,
        allowed_ids: set[str],
        limit: int,
    ) -> list[SearchItem]:
        query_vector = self._vectors([query])[0]
        candidates = self._client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=min(limit, 5000),
            with_payload=True,
        ).points
        filtered: list[tuple[str, float, str]] = []
        for point in candidates:
            payload = point.payload or {}
            item_id = str(payload.get("id") or "")
            text = str(payload.get("text") or "")
            if item_id in allowed_ids and text:
                filtered.append((item_id, float(point.score), text))
        rerank_limit = min(
            len(filtered),
            _positive_int("GRANT_RADAR_SEMANTIC_RERANK_LIMIT", 50, maximum=100),
        )
        rerank_scores: dict[str, float] = {}
        if rerank_limit:
            scores = self._reranker.compute_score(
                [[query, text] for _, _, text in filtered[:rerank_limit]],
                batch_size=rerank_limit,
                query_max_length=_positive_int(
                    "GRANT_RADAR_SEMANTIC_RERANK_QUERY_MAX_LENGTH", 64, maximum=256
                ),
                max_length=_positive_int(
                    "GRANT_RADAR_SEMANTIC_RERANK_MAX_LENGTH", 256, maximum=512
                ),
                normalize=True,
            )
            if isinstance(scores, float):
                scores = [scores]
            rerank_scores = {
                item_id: float(score)
                for (item_id, _, _), score in zip(
                    filtered[:rerank_limit], scores, strict=True
                )
            }
        ordered = sorted(
            filtered,
            key=lambda row: (
                rerank_scores.get(row[0], row[1]),
                row[1],
                row[0],
            ),
            reverse=True,
        )
        return [
            SearchItem(
                id=item_id,
                score=rerank_scores.get(item_id, retrieval_score),
                retrieval_score=retrieval_score,
                reranker_score=rerank_scores.get(item_id),
            )
            for item_id, retrieval_score, _ in ordered[:limit]
        ]


def _point_id(item_id: str) -> str:
    """Qdrant point IDs are stable without exposing source URLs in payloads."""

    return str(uuid5(NAMESPACE_URL, item_id))


async def _load_catalog() -> list[dict[str, str]]:
    url = _catalog_url()
    if not url:
        raise RuntimeError("GRANT_RADAR_SEMANTIC_CATALOG_URL is empty")
    headers = {"Host": _catalog_host()} if _catalog_host() else {}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
    rows: list[dict[str, Any]] = []
    for line in response.text.splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except ValueError:
            logger.warning("semantic_catalog_invalid_ndjson_line")
            continue
        if isinstance(value, dict):
            rows.append(value)
    return public_search_documents(rows)


async def reindex(state: ServiceState) -> None:
    """Refresh only from the public catalog; preserve last known index on error."""

    if not state.index_lock.acquire(blocking=False):
        return
    try:
        documents = await _load_catalog()
        backend = state.backend or BgeM3QdrantBackend()
        count = await asyncio.to_thread(backend.index, documents)
        state.backend = backend
        state.indexed_at = datetime.now(UTC)
        state.indexed_documents = count
        state.index_error = ""
        logger.info("semantic_indexed documents=%d", count)
    except Exception as exc:  # noqa: BLE001 - preserve lexical fallback upstream
        state.index_error = f"{type(exc).__name__}: {exc}"
        logger.exception("semantic_index_failed")
    finally:
        state.index_lock.release()


async def _index_loop(state: ServiceState) -> None:
    interval = _positive_int(
        "GRANT_RADAR_SEMANTIC_REINDEX_INTERVAL_SECONDS", 21600, maximum=86400
    )
    startup_retry_interval = _positive_int(
        "GRANT_RADAR_SEMANTIC_STARTUP_RETRY_SECONDS", 15, maximum=300
    )
    while True:
        await reindex(state)
        # A transient API/Qdrant race during Compose startup must not leave the
        # sidecar warming until the normal six-hour refresh.  Once a usable
        # index exists, preserve it and return to the regular refresh cadence.
        delay = interval if state.indexed_at is not None else startup_retry_interval
        await asyncio.sleep(delay)


def create_app() -> FastAPI:
    state = ServiceState()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        task = asyncio.create_task(_index_loop(state))
        try:
            yield
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    app = FastAPI(
        title="QAZ.FUND semantic search",
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health() -> dict[str, Any]:
        if state.indexed_at is None:
            raise HTTPException(
                status_code=503,
                detail={"status": "warming", "error": state.index_error or None},
            )
        return {
            "status": "ok",
            "model": EMBEDDING_MODEL,
            "reranker_model": RERANKER_MODEL,
            "indexed_at": state.indexed_at,
            "indexed_documents": state.indexed_documents,
        }

    @app.post("/search", response_model=SearchResponse)
    async def search(request: SearchRequest) -> SearchResponse:
        if state.backend is None or state.indexed_at is None:
            raise HTTPException(status_code=503, detail="semantic index is warming")
        items = await asyncio.to_thread(
            state.backend.search,
            request.query,
            allowed_ids=set(request.allowed_ids),
            limit=request.limit,
        )
        return SearchResponse(
            model=EMBEDDING_MODEL,
            reranker_model=RERANKER_MODEL,
            index_updated_at=state.indexed_at,
            items=items,
        )

    return app


app = create_app()
