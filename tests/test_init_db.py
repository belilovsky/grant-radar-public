"""Tests for scripts/init_db.py CLI.

Uses sqlite file inside tmp_path to verify schema bootstrap end-to-end.
Skipped automatically when SQLAlchemy is not installed.
"""

from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy", reason="SQLAlchemy is required for init_db CLI")

from scripts.init_db import main as init_db_main  # noqa: E402


def test_init_db_creates_schema(tmp_path, monkeypatch, caplog):
    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    db_path = tmp_path / "grants.db"
    url = f"sqlite:///{db_path}"

    with caplog.at_level("INFO"):
        rc = init_db_main(["--url", url])

    assert rc == 0
    assert db_path.exists()
    from core.db import SqlRepository

    assert SqlRepository(url=url).size() == 0


def test_init_db_check_mode(tmp_path, monkeypatch):
    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    db_path = tmp_path / "grants.db"
    url = f"sqlite:///{db_path}"

    # First create the schema
    assert init_db_main(["--url", url]) == 0
    # --check should succeed and not modify schema
    assert init_db_main(["--url", url, "--check"]) == 0


def test_init_db_reset_drops_and_recreates(tmp_path, monkeypatch):
    from core.db import SqlRepository

    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    db_path = tmp_path / "grants.db"
    url = f"sqlite:///{db_path}"

    assert init_db_main(["--url", url]) == 0

    # Insert one record, then reset, then check size==0.
    repo = SqlRepository(url=url)
    repo.upsert(
        {
            "source": "s",
            "external_id": "x",
            "title": "t",
            "url": "https://e.org/x",
            "score": 1.0,
        }
    )
    assert repo.size() == 1

    assert init_db_main(["--url", url, "--reset"]) == 0
    repo2 = SqlRepository(url=url)
    assert repo2.size() == 0


def test_init_db_requires_url(monkeypatch):
    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    with pytest.raises(SystemExit):
        init_db_main([])


def test_init_db_uses_env_variable(tmp_path, monkeypatch):
    db_path = tmp_path / "grants.db"
    url = f"sqlite:///{db_path}"
    monkeypatch.setenv("GRANT_RADAR_DB_URL", url)
    assert init_db_main([]) == 0
    assert db_path.exists()
