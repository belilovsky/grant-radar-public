"""Launch gates for immutable assets, route coverage, and safe data recovery."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select, text

from api import generated_assets
from api.main import app
from api.public_meta import analytics_head_html
from api.route_registry import build_route_registry, route_coverage
from core.db import OpportunityRow, SqlRepository
from scripts.reconcile_databases import reconcile


def _record(external_id: str, title: str) -> dict[str, object]:
    return {
        "source": "test_source",
        "external_id": external_id,
        "title": title,
        "url": f"https://example.org/{external_id}",
        "summary": "Kazakhstan support programme",
        "tags": ["kazakhstan"],
        "score": 0.9,
    }


def test_root_externalizes_large_assets_and_keeps_html_below_budget(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(generated_assets, "GENERATED_ASSET_DIR", tmp_path)
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert len(response.content) < 100_000
    generated = sorted(tmp_path.iterdir())
    assert {path.suffix for path in generated} == {".css", ".js"}
    for path in generated:
        asset = client.get(f"/assets/generated/{path.name}")
        assert asset.status_code == 200
        assert asset.headers["cache-control"] == ("public, max-age=31536000, immutable")
    assert client.get("/assets/generated/../../etc/passwd").status_code == 404


def test_route_registry_covers_all_fastapi_surfaces_and_head_contracts() -> None:
    coverage = route_coverage(build_route_registry(app))

    assert coverage["route_count"] == 91
    assert coverage["covered"] == coverage["total"] == 148
    assert coverage["percent"] == 100.0
    assert coverage["gaps"] == []
    assert coverage["languages"] == ["ru", "kk", "en"]
    assert "393x852" in coverage["viewports"]
    states = {
        state for route in coverage["routes"] for state in route.get("states", [])
    }
    assert {
        "open",
        "closing",
        "rolling",
        "forecast",
        "closed",
        "missing",
        "empty",
        "404",
        "semantic-degraded",
        "operator-unauthorized",
    }.issubset(states)


def test_public_pages_have_no_third_party_analytics_markup() -> None:
    assert analytics_head_html() == ""


def test_archived_reconciliation_rows_stay_private_until_fresh_upsert(
    tmp_path, monkeypatch
) -> None:
    url = f"sqlite:///{tmp_path / 'public.db'}"
    repository = SqlRepository(url)
    repository.upsert(_record("private", "Archived candidate"))
    with repository._Session() as session:  # noqa: SLF001 - publication gate proof.
        row = session.get(OpportunityRow, "test_source:private")
        row.publication_state = "archived_unverified"
        session.commit()

    monkeypatch.setenv("GRANT_RADAR_DB_URL", url)
    from api import main as api_main

    api_main._repository_for_url.cache_clear()
    assert api_main._stored_items("en") == []

    active_repository = api_main._configured_repository()
    assert active_repository is not None
    active_repository.upsert(_record("private", "Fresh confirmed candidate"))
    rows = api_main._stored_items("en")
    assert [item.title for item in rows] == ["Fresh confirmed candidate"]


def test_database_reconciliation_is_dry_run_by_default_and_idempotent(tmp_path) -> None:
    source_url = f"sqlite:///{tmp_path / 'source.db'}"
    target_url = f"sqlite:///{tmp_path / 'target.db'}"
    source = SqlRepository(source_url)
    target = SqlRepository(target_url)
    source.upsert(_record("common", "New confirmed title"))
    source.upsert(_record("archive", "Historical source-only record"))
    target.upsert(_record("common", "Canonical old title"))

    with source.engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE runs ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, source VARCHAR(128) NOT NULL, "
                "started_at DATETIME NOT NULL, finished_at DATETIME, "
                "status VARCHAR(32) NOT NULL, items_seen INTEGER NOT NULL DEFAULT 0, "
                "items_new INTEGER NOT NULL DEFAULT 0, items_dup INTEGER NOT NULL DEFAULT 0, "
                "error TEXT)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO runs "
                "(source, started_at, finished_at, status, items_seen, items_new, items_dup) "
                "VALUES ('test_source', '2026-08-21 00:00:00', "
                "'2026-08-21 00:01:00', 'success', 2, 2, 0)"
            )
        )
        connection.execute(
            text("UPDATE opportunities SET last_seen_at='2026-08-20 12:00:00'")
        )
    with target.engine.begin() as connection:
        connection.execute(
            text("UPDATE opportunities SET last_seen_at='2026-08-19 12:00:00'")
        )

    dry_run = reconcile(
        source_url=source_url,
        target_url=target_url,
        expected_source_count=2,
        expected_target_count=1,
    )
    assert dry_run["mode"] == "dry-run"
    assert target.size() == 1

    applied = reconcile(
        source_url=source_url,
        target_url=target_url,
        apply=True,
        expected_source_count=2,
        expected_target_count=1,
    )
    assert applied["target_after"]["opportunities"] == 2
    assert applied["target_after"]["published"] == 1
    assert applied["target_after"]["archived_unverified"] == 1
    assert applied["stats"]["common_source_selected"] == 1

    with target._Session() as session:  # noqa: SLF001 - persisted merge proof.
        rows = {
            row.dedup_key: row for row in session.scalars(select(OpportunityRow)).all()
        }
    assert rows["test_source:common"].title == "New confirmed title"
    assert rows["test_source:common"].publication_state == "published"
    assert rows["test_source:archive"].publication_state == "archived_unverified"

    repeated = reconcile(source_url=source_url, target_url=target_url, apply=True)
    assert repeated["target_after"]["opportunities"] == 2
    assert repeated["stats"]["source_only_archived"] == 0
    assert repeated["stats"]["observations_added"] == 0
