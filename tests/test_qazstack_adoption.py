from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient

from api import main as api_main
from core.models import Opportunity, OpportunityType
from core.persistence import compute_fingerprint
from core.source_text import clean_plain_source_text, clean_source_text


def _opportunity(*, source: str, index: int, score: float) -> Opportunity:
    return Opportunity(
        source=source,
        source_url=f"https://example.org/{source}/{index}?utm_source=test",
        type=OpportunityType.GRANT,
        title=f"Kazakhstan support programme {source} {index}",
        summary="Support for projects and organisations in Kazakhstan.",
        deadline=date.today() + timedelta(days=30),
        tags=["kazakhstan", "support"],
        score=score,
        discovered_at=datetime(2026, 7, 15, 10, index),
    )


def _reset_api_state(monkeypatch) -> None:
    monkeypatch.delenv("GRANT_RADAR_DB_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    api_main._repository_for_url.cache_clear()
    api_main._cache.clear()
    api_main._clear_public_items_cache()


def test_qazstack_source_primitives_canonicalize_fingerprints() -> None:
    item = Opportunity(
        source="official",
        source_url=(
            "HTTPS://Example.ORG/program/?utm_source=newsletter&ref=public#apply"
        ),
        type=OpportunityType.GRANT,
        title="Programme",
    )

    assert item.fingerprint() == "official:https://example.org/program/?ref=public"
    assert (
        compute_fingerprint(
            {
                "url": "https://example.org/program?utm_campaign=spring#details",
            }
        )
        == "url:https://example.org/program"
    )


def test_qazstack_text_primitive_replaces_source_html_cleanup() -> None:
    assert clean_source_text("<p>Grant&nbsp; <strong>programme</strong></p>") == (
        "Grant programme"
    )
    assert clean_source_text(None) == ""
    assert clean_plain_source_text("Terms&nbsp; A < B") == "Terms A < B"


def test_digest_promotes_source_diversity_without_dropping_results(monkeypatch) -> None:
    _reset_api_state(monkeypatch)
    api_main._cache.extend(
        [
            *[
                _opportunity(source="source_a", index=index, score=0.99 - index / 100)
                for index in range(4)
            ],
            _opportunity(source="source_b", index=5, score=0.80),
            _opportunity(source="source_b", index=6, score=0.79),
        ]
    )
    client = TestClient(api_main.app)

    response = client.get("/digest", params={"limit": 4, "min_score": 0.1})

    assert response.status_code == 200
    sources = [item["source"] for item in response.json()["items"]]
    assert Counter(sources) == {"source_a": 2, "source_b": 2}


def test_coverage_reports_public_evidence_states(monkeypatch) -> None:
    _reset_api_state(monkeypatch)
    api_main._cache.extend(
        [
            _opportunity(source="source_a", index=1, score=0.9),
            _opportunity(source="source_b", index=2, score=0.8),
        ]
    )
    client = TestClient(api_main.app)

    response = client.get("/coverage")

    assert response.status_code == 200
    assert response.json()["evidence_states"] == {
        "verified": 0,
        "sourced": 2,
        "archival": 0,
        "compiled": 0,
        "unlinked": 0,
    }


def test_ndjson_export_is_cacheable_and_ai_ready(monkeypatch) -> None:
    _reset_api_state(monkeypatch)
    api_main._cache.append(_opportunity(source="source_a", index=1, score=0.9))
    client = TestClient(api_main.app)

    response = client.get("/opportunities.ndjson", params={"limit": 10})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    assert response.headers["cache-control"].startswith("public, max-age=300")
    row = json.loads(response.text.strip())
    assert row["evidence_state"] == "sourced"
    assert row["source_url"].startswith("https://example.org/source_a/1")

    cached = client.get(
        "/opportunities.ndjson",
        params={"limit": 10},
        headers={"If-None-Match": response.headers["etag"]},
    )
    assert cached.status_code == 304
    assert cached.text == ""


def test_ndjson_export_supports_compact_payload(monkeypatch) -> None:
    _reset_api_state(monkeypatch)
    api_main._cache.append(
        _opportunity(source="source_a", index=1, score=0.9).model_copy(
            update={
                "raw": {
                    "decision_readiness": {"status": "complete"},
                    "source_html": "x" * 1000,
                }
            }
        )
    )
    client = TestClient(api_main.app)

    full = client.get("/opportunities.ndjson", params={"limit": 10})
    compact = client.get(
        "/opportunities.ndjson",
        params={"limit": 10, "compact": "true"},
    )

    assert full.status_code == 200
    assert compact.status_code == 200
    full_row = json.loads(full.text.strip())
    compact_row = json.loads(compact.text.strip())
    assert full_row["evidence_state"] == "sourced"
    assert compact_row["evidence_state"] == "sourced"
    assert full_row["raw"]["source_html"] == "x" * 1000
    assert "source_html" not in compact_row["raw"]
    assert compact_row["raw"]["decision_readiness"]["status"] == "partial"
    assert "ranking" in compact_row["raw"]
    assert len(compact.text) < len(full.text)
