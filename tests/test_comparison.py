from __future__ import annotations

from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from api import main as api_main
from api.comparison import build_comparison_snapshot, parse_comparison_ids
from core.models import Opportunity, OpportunityType


def _item(**overrides) -> Opportunity:
    values = {
        "source": "official_source",
        "source_url": "https://example.org/program",
        "type": OpportunityType.GRANT,
        "title": "Support programme",
        "summary": "For Kazakhstan teams.",
        "funder": "Official funder",
        "deadline": date(2027, 4, 1),
        "eligibility": ["Kazakhstan organisations"],
        "tags": ["kazakhstan", "business"],
        "amount_min": 1000,
        "amount_max": 5000,
        "currency": "USD",
    }
    values.update(overrides)
    return Opportunity(**values)


def test_parse_comparison_ids_is_stable_and_deduplicated() -> None:
    item_id = str(uuid4())
    assert parse_comparison_ids(f" {item_id},{item_id}, ") == [item_id]


def test_comparison_snapshot_keeps_unknown_fields_explicit() -> None:
    first = _item()
    second = _item(
        title="Second programme",
        funder=None,
        deadline=None,
        amount_min=None,
        amount_max=None,
        eligibility=[],
        tags=[],
    )
    payload = build_comparison_snapshot(
        [first, second],
        [str(first.id), str(second.id), str(uuid4())],
        lang="ru",
        as_of=date(2026, 8, 4),
    )
    assert payload["schema_version"] == "comparison.v1"
    assert payload["status"] == "partial"
    assert len(payload["cards"]) == 2
    assert "funder" in payload["cards"][1]["unknown_fields"]
    assert payload["field_coverage"]["funder"]["present"] == 1
    assert payload["selection"]["missing_ids"]
    assert payload["as_of"] == "2026-08-04"


def test_public_compare_json_is_source_grounded(monkeypatch) -> None:
    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    api_main._repository_for_url.cache_clear()
    api_main._cache.clear()
    api_main._clear_public_items_cache()
    first = _item()
    second = _item(title="Second programme", source="another_source")
    api_main._cache.extend([first, second])
    client = TestClient(api_main.app)

    response = client.get(
        "/compare.json",
        params={"ids": f"{first.id},{second.id}", "lang": "en"},
    )
    assert response.status_code == 200
    assert response.headers["cache-control"].startswith("public, max-age=60")
    payload = response.json()
    assert payload["schema_version"] == "comparison.v1"
    assert payload["status"] == "ready"
    assert payload["links"]["human"].endswith(
        f"/compare?ids={first.id},{second.id}&lang=en"
    )
    assert payload["cards"][0]["fields"]["source_url"] == str(first.source_url)

    page = client.get(
        "/compare",
        params={"ids": f"{first.id},{second.id}", "lang": "kk"},
    )
    assert page.status_code == 200
    assert '<html lang="kk"' in page.text
    assert 'lang="kk" aria-current="page">KAZ</a>' in page.text
    assert 'data-avds-component="comparison-table"' in page.text
    assert "Бағдарламаларды салыстыру" in page.text
    assert "JSON" in page.text
    assert "another_source" not in page.text
    assert "Дереккөзді ашу" in page.text

    empty_page = client.get("/compare", params={"lang": "en"})
    assert empty_page.status_code == 200
    assert "Choose at least two cards to compare." in empty_page.text

    invalid = client.get("/compare.json", params={"ids": "not-a-uuid"})
    assert invalid.status_code == 400

    too_many = client.get(
        "/compare.json",
        params={"ids": ",".join(str(uuid4()) for _ in range(5))},
    )
    assert too_many.status_code == 400
