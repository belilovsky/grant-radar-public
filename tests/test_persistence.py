"""Tests for core/persistence: fingerprints, repository, dedup processor."""

from __future__ import annotations

import asyncio

from core.persistence import DedupProcessor, InMemoryRepository, compute_fingerprint
from sources.base import GrantRecord


def test_fingerprint_prefers_explicit_method():
    class Rec:
        def fingerprint(self):
            return "explicit"

    assert compute_fingerprint(Rec()) == "explicit"


def test_fingerprint_uses_source_and_external_id_for_object():
    class Rec:
        source = "grants_gov"
        external_id = "abc-123"

    assert compute_fingerprint(Rec()) == "grants_gov:abc-123"


def test_fingerprint_uses_source_and_id_for_dict():
    rec = {"source": "astana_hub", "id": "prog-1"}
    assert compute_fingerprint(rec) == "astana_hub:prog-1"


def test_fingerprint_falls_back_to_url():
    rec = {"url": "https://internews.org/opportunity/x/"}
    assert compute_fingerprint(rec).startswith("url:")


def test_fingerprint_last_resort_sha256():
    rec = {"foo": "bar"}
    fp = compute_fingerprint(rec)
    assert fp.startswith("sha256:")
    assert len(fp) > len("sha256:")


def test_inmemory_repo_upsert_is_idempotent():
    repo = InMemoryRepository()
    rec = {"source": "s", "id": "1"}
    assert repo.upsert(rec) is True
    assert repo.upsert(rec) is False
    assert repo.size() == 1


def test_inmemory_repo_distinguishes_records():
    repo = InMemoryRepository()
    repo.upsert({"source": "s", "id": "1"})
    repo.upsert({"source": "s", "id": "2"})
    repo.upsert({"source": "s", "id": "1"})  # duplicate
    assert repo.size() == 2


def test_inmemory_repo_clear_resets_state():
    repo = InMemoryRepository()
    repo.upsert({"source": "s", "id": "1"})
    repo.clear()
    assert repo.size() == 0
    assert list(repo.all()) == []


def test_dedup_processor_refreshes_duplicates_and_calls_inner_only_for_new():
    repo = InMemoryRepository()
    seen = []

    async def inner(record):
        seen.append(record)

    proc = DedupProcessor(repo, inner=inner)
    r1 = {"source": "s", "id": "1", "title": "A"}
    r1_dup = {"source": "s", "id": "1", "title": "A (dup)"}
    r2 = {"source": "s", "id": "2", "title": "B"}

    asyncio.run(proc(r1))
    asyncio.run(proc(r1_dup))
    asyncio.run(proc(r2))

    assert proc.persisted == 2
    assert proc.duplicates == 1
    assert repo.size() == 2
    assert [r["id"] for r in seen] == ["1", "2"]
    stored = {r["id"]: r for r in repo.all()}
    assert stored["1"]["title"] == "A (dup)"


def test_dedup_processor_works_without_inner():
    repo = InMemoryRepository()
    proc = DedupProcessor(repo)
    asyncio.run(proc({"source": "s", "id": "x"}))
    asyncio.run(proc({"source": "s", "id": "x", "title": "refreshed"}))
    assert proc.persisted == 1
    assert proc.duplicates == 1
    assert list(repo.all())[0]["title"] == "refreshed"


def test_dedup_processor_scores_records_before_persisting():
    repo = InMemoryRepository()
    proc = DedupProcessor(repo)
    rec = GrantRecord(
        source="internews",
        external_id="score-1",
        title="AI journalism fellowship for Central Asia",
        url="https://example.org/score-1",
        tags=["media"],
    )

    asyncio.run(proc(rec))

    stored = list(repo.all())[0]
    assert stored.score is not None
    assert stored.score > 0


def test_dedup_processor_treats_zero_score_as_missing():
    repo = InMemoryRepository()
    proc = DedupProcessor(repo)
    rec = {
        "source": "grants_gov",
        "external_id": "score-2",
        "title": "Artificial intelligence education grant for Central Asia",
        "url": "https://example.org/score-2",
        "tags": ["education"],
        "score": 0.0,
    }

    asyncio.run(proc(rec))

    stored = list(repo.all())[0]
    assert stored["score"] > 0
