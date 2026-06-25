"""Tests for SQLAlchemy-backed SqlRepository and repository_factory.

These tests use sqlite:///:memory: so they don't require external services.
If SQLAlchemy is not installed, the SqlRepository tests are skipped.
"""

from __future__ import annotations

import os
from datetime import datetime

import pytest

pytest.importorskip("sqlalchemy", reason="SQLAlchemy is optional for in-memory tests")

from core.db import OpportunityRow, SqlRepository  # noqa: E402
from core.models import Opportunity, OpportunityType  # noqa: E402
from core.persistence import InMemoryRepository  # noqa: E402
from core.repository_factory import make_repository  # noqa: E402
from sources.base import GrantRecord  # noqa: E402


def _record(
    source="grants_gov",
    external_id="OPP-1",
    title="Title",
    url="https://example.org/1",
    score=8.0,
):
    return {
        "source": source,
        "external_id": external_id,
        "title": title,
        "url": url,
        "score": score,
        "summary": "sum",
    }


def test_sql_repository_insert_and_exists():
    repo = SqlRepository("sqlite:///:memory:")
    rec = _record()
    assert repo.size() == 0
    inserted = repo.upsert(rec)
    assert inserted is True
    assert repo.size() == 1
    # exists() works by fingerprint
    from core.persistence import compute_fingerprint

    fp = compute_fingerprint(rec)
    assert repo.exists(fp) is True
    assert repo.exists("unknown-fingerprint") is False


def test_sql_repository_upsert_updates_fields():
    repo = SqlRepository("sqlite:///:memory:")
    rec = _record(title="Old", url="https://example.org/old", score=1.0)
    assert repo.upsert(rec) is True

    updated = _record(title="New", url="https://example.org/new", score=9.5)
    assert repo.upsert(updated) is False  # not new, but updated
    assert repo.size() == 1

    rows = list(repo.all())
    assert len(rows) == 1
    row = rows[0]
    assert row.title == "New"
    assert str(row.url) == "https://example.org/new"
    assert row.score == 9.5


def test_sql_repository_upsert_refreshes_discovered_at():
    repo = SqlRepository("sqlite:///:memory:")
    assert repo.upsert(_record(title="Old")) is True
    first_seen = list(repo.all())[0].discovered_at

    with repo._Session() as session:  # noqa: SLF001 - verifies persisted timestamp.
        row = session.get(OpportunityRow, "grants_gov:OPP-1")
        row.discovered_at = datetime(2024, 1, 1)
        session.commit()

    assert repo.upsert(_record(title="Still active")) is False
    refreshed = list(repo.all())[0]
    assert refreshed.title == "Still active"
    assert refreshed.discovered_at > datetime(2024, 1, 1)
    assert refreshed.discovered_at >= first_seen


def test_sql_repository_upsert_preserves_i18n_payload():
    repo = SqlRepository("sqlite:///:memory:")
    repo.upsert(
        Opportunity(
            source="grants_gov",
            source_url="https://example.org/i18n",
            type=OpportunityType.GRANT,
            title="English title",
            summary="English summary",
            score=0.7,
            raw={
                "external_id": "I18N-1",
                "i18n": {
                    "ru": {
                        "title": "Русский заголовок",
                        "summary": "Русское описание",
                    }
                },
            },
        )
    )

    repo.upsert(
        Opportunity(
            source="grants_gov",
            source_url="https://example.org/i18n",
            type=OpportunityType.GRANT,
            title="English title refreshed",
            summary="English summary refreshed",
            score=0.8,
            raw={"external_id": "I18N-1", "agency": "Example Agency"},
        )
    )

    row = list(repo.all())[0]
    assert row.title == "English title refreshed"
    assert row.summary == "English summary refreshed"
    assert row.raw["raw"]["agency"] == "Example Agency"
    assert row.raw["raw"]["i18n"]["ru"]["title"] == "Русский заголовок"
    assert row.raw["raw"]["i18n"]["ru"]["summary"] == "Русское описание"


def test_sql_repository_clear():
    repo = SqlRepository("sqlite:///:memory:")
    for i in range(3):
        repo.upsert(_record(external_id=f"OPP-{i}"))
    assert repo.size() == 3
    repo.clear()
    assert repo.size() == 0


def test_sql_repository_serializes_dataclass_payload():
    repo = SqlRepository("sqlite:///:memory:")
    repo.upsert(
        GrantRecord(
            source="grants_gov",
            external_id="DATACLASS-1",
            title="Dataclass",
            url="https://example.org/dataclass",
            description="Stored payload",
            tags=["ai", "education"],
        )
    )

    row = list(repo.all())[0]
    assert row.raw["external_id"] == "DATACLASS-1"
    assert row.raw["description"] == "Stored payload"
    assert row.raw["tags"] == ["ai", "education"]


def test_sql_repository_serializes_opportunity_source_raw_without_full_model():
    repo = SqlRepository("sqlite:///:memory:")
    repo.upsert(
        Opportunity(
            source="grants_gov",
            source_url="https://example.org/opportunity",
            type=OpportunityType.GRANT,
            title="Opportunity",
            tags=["ai", "grant"],
            score=0.7,
            raw={"external_id": "SOURCE-1", "agency": "Example Agency"},
        )
    )

    row = list(repo.all())[0]
    assert row.raw["type"] == "grant"
    assert row.raw["tags"] == ["ai", "grant"]
    assert row.raw["raw"] == {
        "external_id": "SOURCE-1",
        "agency": "Example Agency",
    }
    assert "source_url" not in row.raw


def test_sql_repository_upserts_opportunity_by_raw_external_id():
    repo = SqlRepository("sqlite:///:memory:")
    assert repo.upsert(
        Opportunity(
            source="unicef_kazakhstan",
            source_url="https://example.org/tenders",
            type=OpportunityType.TENDER,
            title="English tender",
            score=0.7,
            raw={"external_id": "RFP/KAZA/2026/001"},
        )
    )

    assert (
        repo.upsert(
            Opportunity(
                source="unicef_kazakhstan",
                source_url="https://example.org/tender-results",
                type=OpportunityType.TENDER,
                title="Russian tender",
                score=0.8,
                raw={"external_id": "RFP/KAZA/2026/001"},
            )
        )
        is False
    )

    rows = list(repo.all())
    assert len(rows) == 1
    assert rows[0].title == "Russian tender"
    assert str(rows[0].url) == "https://example.org/tender-results"


def test_make_repository_default_is_in_memory(monkeypatch):
    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    repo = make_repository()
    assert isinstance(repo, InMemoryRepository)


def test_make_repository_memory_keyword(monkeypatch):
    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    assert isinstance(make_repository("memory"), InMemoryRepository)
    assert isinstance(make_repository(":memory:"), InMemoryRepository)
    assert isinstance(make_repository(""), InMemoryRepository)


def test_make_repository_sqlite_url(monkeypatch):
    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    repo = make_repository("sqlite:///:memory:")
    assert isinstance(repo, SqlRepository)
    assert repo.size() == 0


def test_make_repository_env_variable(monkeypatch):
    monkeypatch.setenv("GRANT_RADAR_DB_URL", "sqlite:///:memory:")
    repo = make_repository()
    assert isinstance(repo, SqlRepository)


def test_make_repository_database_url_fallback(monkeypatch):
    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    repo = make_repository()
    assert isinstance(repo, SqlRepository)


def test_sql_repository_works_after_alembic_head(tmp_path, monkeypatch):
    pytest.importorskip("alembic")

    from alembic import command
    from alembic.config import Config

    repo_root = os.path.dirname(os.path.dirname(__file__))
    db_path = tmp_path / "migrated.sqlite"
    url = f"sqlite:///{db_path}"
    monkeypatch.setenv("GRANT_RADAR_DB_URL", url)

    cfg = Config(os.path.join(repo_root, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(repo_root, "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    repo = SqlRepository(url)
    assert repo.upsert(_record(external_id="MIG-1", title="Migrated")) is True
    assert repo.upsert(_record(external_id="MIG-1", title="Migrated updated")) is False
    rows = list(repo.all())
    assert len(rows) == 1
    assert rows[0].title == "Migrated updated"
    assert rows[0].dedup_key == "grants_gov:MIG-1"
