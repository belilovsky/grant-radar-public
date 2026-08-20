"""Smoke tests for Alembic migrations.

Verifies that the baseline migration (0001_initial) can be applied and rolled
back against an in-memory sqlite database without errors. This guards against
typosin sa.Column definitions and op.* calls without requiring Postgres.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("alembic")

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from alembic.script import ScriptDirectory  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_INI = REPO_ROOT / "alembic.ini"


@pytest.fixture()
def alembic_cfg(tmp_path, monkeypatch):
    db_path = tmp_path / "alembic_test.sqlite"
    url = f"sqlite:///{db_path}"
    monkeypatch.setenv("GRANT_RADAR_DB_URL", url)
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def test_upgrade_head_creates_tables(alembic_cfg):
    command.upgrade(alembic_cfg, "head")
    # If we got here without raising, schema was created.


def test_revision_ids_fit_postgresql_alembic_version_column(alembic_cfg):
    """PostgreSQL's default Alembic version column is VARCHAR(32)."""
    revisions = ScriptDirectory.from_config(alembic_cfg).walk_revisions()
    oversized = [
        revision.revision for revision in revisions if len(revision.revision) > 32
    ]

    assert oversized == []


def test_downgrade_to_base_drops_tables(alembic_cfg):
    command.upgrade(alembic_cfg, "head")
    command.downgrade(alembic_cfg, "base")


def test_upgrade_idempotent_after_full_cycle(alembic_cfg):
    command.upgrade(alembic_cfg, "head")
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")


def test_upgrade_creates_sources_table(alembic_cfg):
    from sqlalchemy import create_engine, inspect

    command.upgrade(alembic_cfg, "head")
    engine = create_engine(alembic_cfg.get_main_option("sqlalchemy.url"))
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    assert "opportunities" in tables
    assert "dedup_keys" in tables
    assert "sources" in tables
    cols = {c["name"] for c in insp.get_columns("sources")}
    assert {"slug", "kind", "enabled", "last_run_at", "error_count"} <= cols


def test_stepwise_upgrade(alembic_cfg):
    """Each revision can be applied incrementally."""
    from sqlalchemy import create_engine, inspect

    engine = create_engine(alembic_cfg.get_main_option("sqlalchemy.url"))

    command.upgrade(alembic_cfg, "0001_initial")
    tables = set(inspect(engine).get_table_names())
    assert "opportunities" in tables
    assert "sources" not in tables

    command.upgrade(alembic_cfg, "0002_sources_table")
    tables = set(inspect(engine).get_table_names())
    assert "sources" in tables

    command.downgrade(alembic_cfg, "0001_initial")
    tables = set(inspect(engine).get_table_names())
    assert "sources" not in tables

    command.upgrade(alembic_cfg, "head")


def test_upgrade_creates_opportunity_indexes(alembic_cfg):
    from sqlalchemy import create_engine, inspect

    command.upgrade(alembic_cfg, "head")
    engine = create_engine(alembic_cfg.get_main_option("sqlalchemy.url"))
    insp = inspect(engine)
    index_names = {ix["name"] for ix in insp.get_indexes("opportunities")}
    assert "ix_opportunities_source" in index_names
    assert "ix_opportunities_deadline" in index_names
    assert "ix_opportunities_dedup_key" in index_names
    # dedup_key index must be unique
    dedup_ix = next(
        ix
        for ix in insp.get_indexes("opportunities")
        if ix["name"] == "ix_opportunities_dedup_key"
    )
    assert bool(dedup_ix["unique"]) is True


def test_downgrade_to_0002_drops_opportunity_indexes(alembic_cfg):
    from sqlalchemy import create_engine, inspect

    command.upgrade(alembic_cfg, "head")
    command.downgrade(alembic_cfg, "0002_sources_table")
    engine = create_engine(alembic_cfg.get_main_option("sqlalchemy.url"))
    insp = inspect(engine)
    index_names = {ix["name"] for ix in insp.get_indexes("opportunities")}
    assert "ix_opportunities_source" not in index_names
    assert "ix_opportunities_deadline" not in index_names
    assert "ix_opportunities_dedup_key" not in index_names


def test_upgrade_creates_runs_table(alembic_cfg):
    from sqlalchemy import create_engine, inspect

    command.upgrade(alembic_cfg, "head")
    engine = create_engine(alembic_cfg.get_main_option("sqlalchemy.url"))
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    assert "runs" in tables
    cols = {c["name"] for c in insp.get_columns("runs")}
    expected = {
        "id",
        "source",
        "started_at",
        "finished_at",
        "status",
        "items_seen",
        "items_new",
        "items_dup",
        "error",
    }
    assert expected <= cols
    index_names = {ix["name"] for ix in insp.get_indexes("runs")}
    assert {"ix_runs_source", "ix_runs_started_at", "ix_runs_status"} <= index_names


def test_upgrade_creates_opportunity_observation_ledger(alembic_cfg):
    from sqlalchemy import create_engine, inspect

    command.upgrade(alembic_cfg, "head")
    engine = create_engine(alembic_cfg.get_main_option("sqlalchemy.url"))
    insp = inspect(engine)
    assert "opportunity_observations" in set(insp.get_table_names())
    opportunity_cols = {c["name"] for c in insp.get_columns("opportunities")}
    assert {"first_seen_at", "last_seen_at", "content_hash"} <= opportunity_cols
    observation_cols = {c["name"] for c in insp.get_columns("opportunity_observations")}
    assert {
        "opportunity_id",
        "observed_at",
        "change_type",
        "content_hash",
        "changed_fields",
        "snapshot",
    } <= observation_cols
    index_names = {ix["name"] for ix in insp.get_indexes("opportunity_observations")}
    assert {
        "ix_opportunity_observations_opportunity_id",
        "ix_opportunity_observations_source",
        "ix_opportunity_observations_observed_at",
        "ix_opportunity_observations_change_type",
    } <= index_names


def test_observation_migration_seeds_recoverable_seen_timestamps(alembic_cfg):
    from sqlalchemy import create_engine, text

    command.upgrade(alembic_cfg, "0004_runs_table")
    engine = create_engine(alembic_cfg.get_main_option("sqlalchemy.url"))
    discovered_at = "2025-03-04 05:06:07"
    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO opportunities (
                    id, dedup_key, source, source_url, title, currency, discovered_at
                ) VALUES (
                    :id, :dedup_key, :source, :source_url, :title, :currency,
                    :discovered_at
                )
                """),
            {
                "id": "legacy-1",
                "dedup_key": "legacy-1",
                "source": "legacy",
                "source_url": "https://example.org/legacy",
                "title": "Legacy record",
                "currency": "KZT",
                "discovered_at": discovered_at,
            },
        )

    command.upgrade(alembic_cfg, "head")
    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT discovered_at, first_seen_at, last_seen_at "
                "FROM opportunities WHERE id = :id"
            ),
            {"id": "legacy-1"},
        ).one()
    assert str(row.first_seen_at) == str(row.discovered_at)
    assert str(row.last_seen_at) == str(row.discovered_at)


def test_downgrade_to_0003_drops_runs_table(alembic_cfg):
    from sqlalchemy import create_engine, inspect

    command.upgrade(alembic_cfg, "head")
    command.downgrade(alembic_cfg, "0003_opportunities_indexes")
    engine = create_engine(alembic_cfg.get_main_option("sqlalchemy.url"))
    insp = inspect(engine)
    assert "runs" not in set(insp.get_table_names())
