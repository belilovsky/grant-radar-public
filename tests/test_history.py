from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from api import main as api_main
from core.db import SqlRepository
from core.history import changed_fields, public_snapshot, snapshot_hash
from core.models import Opportunity, OpportunityType
from core.persistence import InMemoryRepository


def _item(**changes) -> Opportunity:
    values = {
        "source": "history_source",
        "source_url": "https://example.org/history",
        "type": OpportunityType.GRANT,
        "title": "History grant",
        "summary": "Support for Kazakhstan teams.",
        "funder": "History funder",
        "amount_min": 1000,
        "currency": "USD",
        "deadline": date(2027, 1, 1),
        "eligibility": ["Kazakhstan teams"],
        "tags": ["kazakhstan", "innovation"],
        "opportunity_status": "open",
        "lifecycle": "open",
        "discovered_at": datetime(2026, 8, 4, 12, 0, tzinfo=timezone.utc),
        "raw": {
            "external_id": "HISTORY-1",
            "application_url": "https://example.org/apply",
        },
    }
    values.update(changes)
    return Opportunity(**values)


def test_public_snapshot_is_stable_and_lists_only_public_fields() -> None:
    first = public_snapshot(_item())
    second = public_snapshot(_item(discovered_at=datetime(2026, 8, 4, 13, 0)))

    assert first == second
    assert "raw" not in first
    assert "discovered_at" not in first
    assert snapshot_hash(first) == snapshot_hash(second)
    assert changed_fields(first, public_snapshot(_item(title="Changed title"))) == [
        "title"
    ]


def test_in_memory_history_appends_only_when_public_fields_change() -> None:
    repo = InMemoryRepository()
    first = _item()
    assert repo.upsert(first) is True
    assert repo.upsert(_item(discovered_at=datetime(2026, 8, 4, 13, 0))) is False
    assert repo.upsert(_item(title="Changed title")) is False

    entries = repo.history_for(first.fingerprint())
    assert len(entries) == 2
    assert entries[0]["changed_fields"] == ["initial"]
    assert entries[1]["version"] == 2
    assert entries[1]["changed_fields"] == ["title"]
    assert entries[1]["fields"]["title"] == "Changed title"


def test_sql_history_is_versioned_and_cleared_with_records() -> None:
    repo = SqlRepository("sqlite:///:memory:")
    first = _item()
    assert repo.upsert(first) is True
    assert repo.upsert(_item(deadline=date(2027, 2, 1))) is False

    entries = repo.history_for(first.fingerprint())
    assert len(entries) == 2
    assert entries[0]["changed_fields"] == ["initial"]
    assert entries[1]["changed_fields"] == ["deadline"]
    assert entries[1]["fields"]["deadline"] == "2027-02-01"

    repo.clear()
    assert repo.history_for(first.fingerprint()) == []


def test_public_history_endpoint_returns_source_grounded_versions(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("GRANT_RADAR_DB_URL", f"sqlite:///{tmp_path / 'history.sqlite'}")
    api_main._repository_for_url.cache_clear()
    api_main._cache.clear()
    api_main._clear_public_items_cache()

    repository = SqlRepository(f"sqlite:///{tmp_path / 'history.sqlite'}")
    repository.upsert(_item())
    repository.upsert(_item(summary="Updated public summary."))
    api_main._clear_public_items_cache()
    item = api_main._cached_public_items("en")[0]

    response = TestClient(api_main.app).get(
        f"/opportunities/{item.id}/history.json",
        params={"lang": "ru"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "history.v1"
    assert payload["status"] == "ready"
    assert payload["version_count"] == 2
    assert payload["items"][1]["changed_fields"] == ["summary"]
    assert payload["links"]["current"].endswith(f"/opportunities/{item.id}?lang=ru")
    assert response.headers["cache-control"].startswith("public, max-age=60")
