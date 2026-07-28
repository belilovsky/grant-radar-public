from __future__ import annotations

import httpx

from scripts.performance_smoke import run_probe


def test_performance_smoke_measures_get_head_and_cache_headers() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text="ok",
            headers={
                "cache-control": "public, max-age=60",
                "etag": 'W/"sample"',
            },
        )

    payload = run_probe(
        base_url="https://example.org",
        paths=("/insights?lang=ru",),
        samples=3,
        max_warm_ms=10_000,
        transport=httpx.MockTransport(handler),
    )

    assert payload["status"] == "ok"
    assert payload["failures"] == []
    assert payload["results"][0]["path"] == "/insights?lang=ru"
    assert payload["results"][0]["response_bytes"] == 2
    assert payload["results"][0]["cache_control"] == "public, max-age=60"
    assert payload["results"][0]["etag"] == 'W/"sample"'


def test_performance_smoke_retries_transient_disconnect() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.RemoteProtocolError(
                "Server disconnected without sending a response."
            )
        return httpx.Response(200, text="ok")

    payload = run_probe(
        base_url="https://example.org",
        paths=("/api/v1/insights?lang=ru",),
        samples=2,
        transport=httpx.MockTransport(handler),
    )

    assert payload["status"] == "ok"
    assert calls == 4
