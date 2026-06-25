"""Tests for runner_factory wiring of RunRecorder.

Verifies that:
* When ``GRANT_RADAR_DB_URL`` is unset, no recorder is attached.
* An explicit ``run_recorder`` argument overrides auto-detection.
* The auto-detected recorder degrades to no-op when SQLAlchemy is missing.
"""

from __future__ import annotations

import os

import pytest

from core.fetch_queue import FetchQueue
from core.runner_factory import build_default_runner


class _StubRepo:
    def fingerprint_exists(self, fp):  # pragma: no cover - trivial
        return False

    def save(self, record, fp):  # pragma: no cover - trivial
        return None


class _StubRecorder:
    def start(self):
        return 1

    def finish(self, run_id, processed=0, errors=0, status="ok"):
        return None

    def record_error(self, run_id):
        return None


def test_no_recorder_when_db_url_missing(monkeypatch):
    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    queue = FetchQueue()
    runner = build_default_runner(queue, repository=_StubRepo())
    assert runner.run_recorder is None


def test_explicit_recorder_overrides_auto_detection(monkeypatch):
    monkeypatch.setenv("GRANT_RADAR_DB_URL", "sqlite:///:memory:")
    queue = FetchQueue()
    explicit = _StubRecorder()
    runner = build_default_runner(queue, repository=_StubRepo(), run_recorder=explicit)
    assert runner.run_recorder is explicit


def test_auto_recorder_degrades_when_engine_unavailable(monkeypatch):
    """If get_engine raises, the recorder must be skipped silently."""
    monkeypatch.setenv("GRANT_RADAR_DB_URL", "not-a-real-url")

    import core.runner_factory as rf

    def _boom(url):  # pragma: no cover - exercised by patch
        raise RuntimeError("no engine")

    # Patch the lazy import target inside _maybe_build_recorder
    import core.db as db_mod

    monkeypatch.setattr(db_mod, "get_engine", _boom, raising=False)

    queue = FetchQueue()
    runner = rf.build_default_runner(queue, repository=_StubRepo())
    assert runner.run_recorder is None


def test_auto_recorder_attaches_when_runs_table_exists(tmp_path, monkeypatch):
    pytest.importorskip("sqlalchemy")
    pytest.importorskip("alembic")

    from alembic import command
    from alembic.config import Config

    repo_root = os.path.dirname(os.path.dirname(__file__))
    db_path = tmp_path / "runner-recorder.sqlite"
    url = f"sqlite:///{db_path}"
    monkeypatch.setenv("GRANT_RADAR_DB_URL", url)

    cfg = Config(os.path.join(repo_root, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(repo_root, "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    queue = FetchQueue()
    runner = build_default_runner(queue, repository=_StubRepo())
    assert runner.run_recorder is not None
