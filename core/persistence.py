"""In-memory persistence layer with dedup for M2 ingestion.

This module provides a lightweight, dependency-free repository abstraction
that the `PipelineRunner` can use to deduplicate and persist incoming
`GrantRecord` / `Opportunity` items. It is intentionally backend-agnostic:
  * `InMemoryRepository` is the default and used by tests.
  * A future SQLAlchemy-backed implementation will conform to the same
    `Repository` protocol and be selectable via configuration.

Deduplication is keyed on a stable fingerprint derived from `(source,
external_id)` (or `url` as a fallback). Records returning a fingerprint
that already exists in the repo are reported as duplicates, but still refresh
the stored payload so parser fixes and changed deadlines propagate to prod.
"""

from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, Dict, Iterable, Optional, Protocol

from qazstack.source import canonicalize_source_url


def compute_fingerprint(record: Any) -> str:
    """Compute a stable fingerprint for any record-like object/dict.

    Order of preference:
      1. Explicit `fingerprint()` method on the record.
      2. `(source, external_id)` tuple (attribute or dict).
      3. `url` field.
      4. SHA256 of `repr(record)` as a last-resort fallback.
    """
    # 1) explicit method
    fp_attr = getattr(record, "fingerprint", None)
    if callable(fp_attr):
        fp: Any = None
        try:
            fp = fp_attr()
        except (AttributeError, TypeError, ValueError):
            fp = None
        if fp:
            return str(fp)

    def _get(key: str) -> Optional[Any]:
        if isinstance(record, dict):
            return record.get(key)
        return getattr(record, key, None)

    source = _get("source")
    external_id = _get("external_id") or _get("id")
    if source and external_id:
        return f"{source}:{external_id}"

    url = _get("url")
    if url:
        canonical_url = canonicalize_source_url(url)
        return f"url:{canonical_url or url}"

    return "sha256:" + hashlib.sha256(repr(record).encode("utf-8")).hexdigest()


def _current_score(record: Any) -> Any:
    if isinstance(record, dict):
        return record.get("score")
    return getattr(record, "score", None)


def _set_score(record: Any, value: float) -> None:
    if isinstance(record, dict):
        record["score"] = value
        return
    try:
        setattr(record, "score", value)
    except (AttributeError, TypeError):
        return


def _scoring_subject(record: Any) -> Any:
    if not isinstance(record, dict):
        return record
    return SimpleNamespace(
        source=record.get("source") or "",
        title=record.get("title") or "",
        summary=record.get("summary") or record.get("description") or "",
        funder=record.get("funder") or "",
        eligibility=record.get("eligibility") or [],
        tags=record.get("tags") or [],
        languages=record.get("languages") or [],
        deadline=record.get("deadline"),
        raw=record.get("raw") or {},
    )


def _score_if_missing(record: Any) -> None:
    current_score = _current_score(record)
    if current_score not in (None, 0, 0.0):
        return
    try:
        from core.scoring import score as score_opportunity

        _set_score(record, float(score_opportunity(_scoring_subject(record))))
    except Exception:
        return


class Repository(Protocol):
    def exists(self, fingerprint: str) -> bool: ...
    def upsert(self, record: Any) -> bool: ...  # returns True if newly inserted
    def all(self) -> Iterable[Any]: ...
    def size(self) -> int: ...


@dataclass
class InMemoryRepository:
    """Thread-safe in-memory repository keyed by fingerprint."""

    _store: Dict[str, Any] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def exists(self, fingerprint: str) -> bool:
        with self._lock:
            return fingerprint in self._store

    def upsert(self, record: Any) -> bool:
        fp = compute_fingerprint(record)
        with self._lock:
            is_new = fp not in self._store
            self._store[fp] = record
            return is_new

    def all(self) -> Iterable[Any]:
        with self._lock:
            return list(self._store.values())

    def size(self) -> int:
        with self._lock:
            return len(self._store)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


class DedupProcessor:
    """Adapter that wraps an inner async processor with dedup + persistence.

    Usage:
        repo = InMemoryRepository()
        processor = DedupProcessor(repo, inner=my_async_processor)
        runner = PipelineRunner(queue, processor=processor)
    """

    def __init__(self, repo: Repository, inner=None):
        self.repo = repo
        self.inner = inner
        self.duplicates = 0
        self.persisted = 0

    async def __call__(self, record: Any) -> None:
        _score_if_missing(record)
        inserted = self.repo.upsert(record)
        if not inserted:
            self.duplicates += 1
            return
        self.persisted += 1
        if self.inner is not None:
            await self.inner(record)
