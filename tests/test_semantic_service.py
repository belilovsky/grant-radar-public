import asyncio
import json
import sys
from datetime import UTC, datetime
from types import SimpleNamespace

import httpx

import semantic_service.app as semantic_app


def test_model_snapshot_omits_unused_inference_exports(monkeypatch):
    captured: dict[str, object] = {}

    def snapshot_download(repository, *, ignore_patterns):
        captured["repository"] = repository
        captured["ignore_patterns"] = ignore_patterns
        return "/models/snapshot"

    monkeypatch.setitem(
        sys.modules,
        "huggingface_hub",
        SimpleNamespace(snapshot_download=snapshot_download),
    )

    assert semantic_app._model_snapshot_path("BAAI/bge-m3") == "/models/snapshot"
    assert captured == {
        "repository": "BAAI/bge-m3",
        "ignore_patterns": ["onnx/*", "openvino/*"],
    }


def test_catalog_timeout_is_long_enough_for_the_public_catalog(monkeypatch):
    monkeypatch.setenv("GRANT_RADAR_SEMANTIC_CATALOG_TIMEOUT_SECONDS", "120")

    assert semantic_app._catalog_timeout_seconds() == 120.0


def test_index_loop_retries_quickly_until_first_success(monkeypatch):
    state = semantic_app.ServiceState()
    delays: list[float] = []
    attempts = 0

    async def fake_reindex(current_state):
        nonlocal attempts
        attempts += 1
        if attempts == 2:
            current_state.indexed_at = datetime.now(UTC)

    async def fake_sleep(delay):
        delays.append(delay)
        if len(delays) == 2:
            raise asyncio.CancelledError

    monkeypatch.setenv("GRANT_RADAR_SEMANTIC_REINDEX_INTERVAL_SECONDS", "600")
    monkeypatch.setenv("GRANT_RADAR_SEMANTIC_STARTUP_RETRY_SECONDS", "3")
    monkeypatch.setattr(semantic_app, "reindex", fake_reindex)
    monkeypatch.setattr(semantic_app.asyncio, "sleep", fake_sleep)

    try:
        asyncio.run(semantic_app._index_loop(state))
    except asyncio.CancelledError:
        pass

    assert attempts == 2
    assert delays == [3, 600]


def test_catalog_request_uses_public_host_for_internal_api(monkeypatch):
    captured_headers: dict[str, str] = {}

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        async def get(self, url, *, headers):
            captured_headers.update(headers)
            request = httpx.Request("GET", url, headers=headers)
            row = {
                "id": "opportunity-1",
                "title": "AI support",
                "summary": "For Kazakhstan teams",
            }
            return httpx.Response(200, text=json.dumps(row), request=request)

    monkeypatch.setenv("GRANT_RADAR_SEMANTIC_CATALOG_HOST", "qaz.fund")
    monkeypatch.setattr(semantic_app.httpx, "AsyncClient", lambda **_: Client())

    documents = asyncio.run(semantic_app._load_catalog())

    assert captured_headers == {"Host": "qaz.fund"}
    assert documents[0]["id"] == "opportunity-1"
