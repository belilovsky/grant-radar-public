from __future__ import annotations

from datetime import date

import httpx

from core import semantic_search
from core.models import Opportunity, OpportunityType
from core.semantic_search import search_opportunities


def _item() -> Opportunity:
    return Opportunity(
        source="astana_hub",
        source_url="https://example.org/opportunity",
        type=OpportunityType.GRANT,
        title="AI grant",
        deadline=date(2030, 1, 1),
    )


def test_semantic_search_uses_only_public_id_allowlist(monkeypatch):
    item = _item()
    seen: dict[str, object] = {}

    class Client:
        def post(self, path, json):
            seen["path"] = path
            seen["payload"] = json
            return httpx.Response(
                200,
                json={
                    "items": [
                        {"id": "not-an-allowed-id", "score": 1.0},
                        {"id": str(item.id), "score": 0.8},
                    ]
                },
                request=httpx.Request("POST", "http://semantic/search"),
            )

    monkeypatch.setenv("GRANT_RADAR_SEMANTIC_SEARCH_ENABLED", "1")
    monkeypatch.setenv("GRANT_RADAR_SEMANTIC_SEARCH_URL", "http://semantic:8010")
    monkeypatch.setattr("core.semantic_search._client", lambda *_: Client())

    hits = search_opportunities("find AI funding", [item], limit=50)

    assert [hit.opportunity_id for hit in hits] == [item.id]
    assert seen["path"] == "/search"
    assert seen["payload"] == {
        "query": "find AI funding",
        "allowed_ids": [str(item.id)],
        "limit": 1,
    }


def test_semantic_search_fails_closed_to_lexical_fallback(monkeypatch):
    item = _item()

    class Client:
        def post(self, *_args, **_kwargs):
            raise httpx.ConnectError("offline")

    monkeypatch.setenv("GRANT_RADAR_SEMANTIC_SEARCH_ENABLED", "1")
    monkeypatch.setenv("GRANT_RADAR_SEMANTIC_SEARCH_URL", "http://semantic:8010")
    monkeypatch.setattr("core.semantic_search._client", lambda *_: Client())

    assert search_opportunities("AI", [item], limit=20) == []


def test_semantic_timeout_is_bounded_for_the_public_api(monkeypatch):
    monkeypatch.setenv("GRANT_RADAR_SEMANTIC_TIMEOUT_SECONDS", "120")

    assert semantic_search._timeout_seconds() == 15.0
