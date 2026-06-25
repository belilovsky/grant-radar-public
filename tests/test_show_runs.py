"""Tests for scripts/show_runs.py."""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("alembic")

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from core.run_recorder import record_run  # noqa: E402
from scripts import show_runs  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_INI = REPO_ROOT / "alembic.ini"


@pytest.fixture()
def engine_with_runs(tmp_path, monkeypatch):
    from sqlalchemy import create_engine

    db_path = tmp_path / "show_runs.sqlite"
    url = f"sqlite:///{db_path}"
    monkeypatch.setenv("GRANT_RADAR_DB_URL", url)
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    eng = create_engine(url)

    # one ok run for grants_gov
    with record_run(eng, source="grants_gov") as stats:
        stats.saw(5)
        stats.added(4)
        stats.deduped(1)

    # one error run for astana_hub
    class Boom(RuntimeError):
        pass

    with pytest.raises(Boom):
        with record_run(eng, source="astana_hub") as stats:
            stats.saw(2)
            raise Boom("kaboom")

    return eng, url


def test_parse_since_accepts_units():
    now = _dt.datetime.now(_dt.timezone.utc)
    for token, seconds in (("30s", 30), ("5m", 300), ("2h", 7200), ("1d", 86400)):
        parsed = show_runs._parse_since(token)
        delta = (now - parsed).total_seconds()
        # within 5 seconds of expected window
        assert abs(delta - seconds) < 5


def test_parse_since_rejects_garbage():
    import argparse

    with pytest.raises(argparse.ArgumentTypeError):
        show_runs._parse_since("yesterday")


def test_format_table_empty():
    assert show_runs.format_table([]) == "(no runs)"


def test_format_table_renders_rows():
    row = {
        "id": 1,
        "source": "grants_gov",
        "status": "ok",
        "started_at": _dt.datetime(2026, 5, 20, 12, 0, 0, tzinfo=_dt.timezone.utc),
        "finished_at": _dt.datetime(2026, 5, 20, 12, 1, 30, tzinfo=_dt.timezone.utc),
        "items_seen": 10,
        "items_new": 7,
        "items_dup": 3,
        "error": None,
    }
    out = show_runs.format_table([row])
    assert "grants_gov" in out
    assert "\tok\t" in out
    assert "1m30s" in out
    assert "\t10\t7\t3\t" in out


def test_format_table_renders_running_duration():
    row = {
        "id": 2,
        "source": "worker",
        "status": "running",
        "started_at": _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(minutes=2),
        "finished_at": None,
        "items_seen": 0,
        "items_new": 0,
        "items_dup": 0,
        "error": None,
    }
    out = show_runs.format_table([row])
    assert "\trunning\t" in out
    assert "\t-\t0\t0\t0\t" not in out


def test_fetch_runs_returns_recent_first(engine_with_runs):
    _, url = engine_with_runs
    rows = show_runs.fetch_runs(url, limit=10)
    assert len(rows) == 2
    sources = [r["source"] for r in rows]
    # both runs present, ordered by started_at desc
    assert set(sources) == {"grants_gov", "astana_hub"}


def test_fetch_runs_filters_by_status(engine_with_runs):
    _, url = engine_with_runs
    err_rows = show_runs.fetch_runs(url, status="error")
    assert [r["source"] for r in err_rows] == ["astana_hub"]
    ok_rows = show_runs.fetch_runs(url, status="ok")
    assert [r["source"] for r in ok_rows] == ["grants_gov"]


def test_fetch_runs_filters_by_source(engine_with_runs):
    _, url = engine_with_runs
    rows = show_runs.fetch_runs(url, source="grants_gov")
    assert len(rows) == 1
    assert rows[0]["items_seen"] == 5
    assert rows[0]["items_new"] == 4
    assert rows[0]["items_dup"] == 1


def test_main_without_url_returns_error_code(monkeypatch, capsys):
    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    rc = show_runs.main([])
    assert rc == 2
    err = capsys.readouterr().err
    assert "GRANT_RADAR_DB_URL" in err


def test_main_prints_table(engine_with_runs, capsys, monkeypatch):
    _, url = engine_with_runs
    monkeypatch.setenv("GRANT_RADAR_DB_URL", url)
    rc = show_runs.main(["--limit", "10"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "grants_gov" in out
    assert "astana_hub" in out
