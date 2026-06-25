"""Tests for core.run_recorder.

Uses an in-memory sqlite database with the migrations applied up to head
so the runs table is real. Skips automatically when SQLAlchemy or Alembic
are not installed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("alembic")

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from core.run_recorder import record_run  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_INI = REPO_ROOT / "alembic.ini"


@pytest.fixture()
def engine(tmp_path, monkeypatch):
    from sqlalchemy import create_engine

    db_path = tmp_path / "recorder.sqlite"
    url = f"sqlite:///{db_path}"
    monkeypatch.setenv("GRANT_RADAR_DB_URL", url)
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    return create_engine(url)


def _fetch_run(engine, run_id):
    from sqlalchemy import MetaData, Table, select

    md = MetaData()
    runs = Table("runs", md, autoload_with=engine)
    with engine.connect() as conn:
        row = conn.execute(select(runs).where(runs.c.id == run_id)).mappings().one()
    return dict(row)


def _all_runs(engine):
    from sqlalchemy import MetaData, Table, select

    md = MetaData()
    runs = Table("runs", md, autoload_with=engine)
    with engine.connect() as conn:
        return [dict(r) for r in conn.execute(select(runs)).mappings().all()]


def test_record_run_success(engine):
    with record_run(engine, source="grants_gov") as stats:
        stats.saw(10)
        stats.added(7)
        stats.deduped(3)

    rows = _all_runs(engine)
    assert len(rows) == 1
    row = rows[0]
    assert row["source"] == "grants_gov"
    assert row["status"] == "ok"
    assert row["items_seen"] == 10
    assert row["items_new"] == 7
    assert row["items_dup"] == 3
    assert row["error"] is None
    assert row["started_at"] is not None
    assert row["finished_at"] is not None


def test_record_run_error_marks_status_and_reraises(engine):
    class Boom(RuntimeError):
        pass

    with pytest.raises(Boom):
        with record_run(engine, source="astana_hub") as stats:
            stats.saw(2)
            raise Boom("kaboom")

    rows = _all_runs(engine)
    assert len(rows) == 1
    row = rows[0]
    assert row["source"] == "astana_hub"
    assert row["status"] == "error"
    assert row["items_seen"] == 2
    assert row["items_new"] == 0
    assert row["items_dup"] == 0
    assert "Boom" in (row["error"] or "")
    assert "kaboom" in (row["error"] or "")


def test_record_run_noop_when_runs_table_missing(tmp_path):
    from sqlalchemy import create_engine

    # Fresh DB without migrations -> no runs table.
    db_path = tmp_path / "empty.sqlite"
    eng = create_engine(f"sqlite:///{db_path}")

    with record_run(eng, source="nowhere") as stats:
        stats.saw(1)
        stats.added(1)

    # Recorder must not blow up and must yield a usable stats object.
    assert stats.items_seen == 1
    assert stats.items_new == 1
